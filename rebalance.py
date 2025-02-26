#!/usr/bin/env python3
import yfinance as yf
import sys

def get_current_price(ticker):
    """
    Retrieve the most recent closing price for a given ticker using yfinance.
    """
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if hist.empty:
            raise ValueError(f"No price data found for {ticker}.")
        # Use .iloc[0] to access the first element by position.
        return hist['Close'].iloc[0]
    except Exception as e:
        print(f"Error retrieving data for {ticker}: {e}")
        return None

def get_holdings(target_allocations):
    """Prompt the user for the number of shares held for each ticker."""
    shares = {}
    for ticker in target_allocations:
        while True:
            try:
                share_count = float(input(f"Enter number of shares held for {ticker}: "))
                shares[ticker] = share_count
                break
            except ValueError:
                print("Invalid input. Please enter a number.")
    return shares

def get_cash_total():
    """
    Ask the user for cash available in CHF and in USD.
    Convert CHF to USD using the conversion rate from Yahoo Finance, and return total cash in USD.
    """
    while True:
        try:
            cash_chf = float(input("Enter cash available in CHF: "))
            break
        except ValueError:
            print("Invalid input. Please enter a number for CHF cash.")
    while True:
        try:
            cash_usd = float(input("Enter cash available in USD: "))
            break
        except ValueError:
            print("Invalid input. Please enter a number for USD cash.")
    conversion_rate = get_current_price("CHFUSD=X")
    if conversion_rate is None:
        print("Could not retrieve CHF to USD conversion rate. Exiting.")
        sys.exit(1)
    cash_chf_usd = cash_chf * conversion_rate
    total_cash = cash_usd + cash_chf_usd
    print(f"\nCash in CHF converted to USD: ${cash_chf_usd:,.2f}")
    print(f"Cash in USD: ${cash_usd:,.2f}")
    print(f"Total Cash (USD): ${total_cash:,.2f}\n")
    return total_cash

def get_prices(target_allocations):
    """Retrieve current market prices for each ticker."""
    prices = {}
    for ticker in target_allocations:
        price = get_current_price(ticker)
        if price is None:
            print(f"Could not retrieve price for {ticker}. Exiting.")
            sys.exit(1)
        prices[ticker] = price
    return prices

def print_current_status_with_cash(target_allocations, shares, prices, cash_usd):
    """
    Print the current ETF positions and cash (converted to USD).
    The ETF allocation percentages are computed relative to the invested ETF value only.
    """
    current_values = {}
    invested_value = 0.0
    print("\nCurrent ETF Positions:")
    for ticker in target_allocations:
        value = shares[ticker] * prices[ticker]
        current_values[ticker] = value
        invested_value += value
        print(f"  {ticker}: {shares[ticker]} shares * ${prices[ticker]:.2f} = ${value:,.2f}")
    overall_portfolio = invested_value + cash_usd
    print(f"\nTotal Invested Value (ETFs): ${invested_value:,.2f}")
    print(f"Cash: ${cash_usd:,.2f}")
    print(f"Overall Portfolio Value (ETFs + Cash): ${overall_portfolio:,.2f}\n")
    
    print("ETF Allocation Percentages (based on Invested Value):")
    for ticker in target_allocations:
        current_pct = (current_values[ticker] / invested_value) * 100 if invested_value > 0 else 0
        target_pct = target_allocations[ticker] * 100
        print(f"  {ticker}: {current_pct:.2f}% (Target: {target_pct:.2f}%)")
    
    return current_values, invested_value

def mode_rebalance(target_allocations, shares, prices, cash_usd):
    """
    Provide rebalancing recommendations for the ETF portion.
    The target ETF values are computed based on the total invested (ETF) value.
    Cash (in USD) is included in the overall portfolio summary.
    After showing recommendations, the script simulates executing the trades and
    prints a final portfolio summary for double-checking.
    """
    current_values, invested_value = print_current_status_with_cash(target_allocations, shares, prices, cash_usd)
    overall_portfolio = invested_value + cash_usd

    print("\nRebalance Recommendations for ETFs (trades for ETF portion only):")
    trade_shares = {}
    for ticker in target_allocations:
        target_value = invested_value * target_allocations[ticker]
        current_value = current_values[ticker]
        difference_value = target_value - current_value
        share_price = prices[ticker]
        difference_shares = difference_value / share_price
        trade_shares[ticker] = difference_shares
        current_pct = (current_value / invested_value) * 100 if invested_value else 0
        target_pct = target_allocations[ticker] * 100
        if abs(difference_shares) < 1e-4:
            action = "No adjustment needed."
        elif difference_shares > 0:
            action = f"Buy {difference_shares:.4f} shares (approx. ${difference_value:,.2f})."
        else:
            action = f"Sell {abs(difference_shares):.4f} shares (approx. ${abs(difference_value):,.2f})."
        print(f"  {ticker}:")
        print(f"     Current Allocation: {current_pct:.2f}% | Target Allocation: {target_pct:.2f}%")
        print(f"     {action}")
    
    # Simulate executing the trades:
    print("\nSimulated Final ETF Holdings (if trades are executed):")
    final_holdings = {}
    final_values = {}
    final_invested_value = 0.0
    for ticker in target_allocations:
        final_holdings[ticker] = shares[ticker] + trade_shares[ticker]
        final_values[ticker] = final_holdings[ticker] * prices[ticker]
        final_invested_value += final_values[ticker]
        print(f"  {ticker}: {final_holdings[ticker]:.4f} shares, Value: ${final_values[ticker]:,.2f}")
    
    final_overall = final_invested_value + cash_usd
    print(f"\nFinal Invested ETF Value: ${final_invested_value:,.2f}")
    print(f"Cash (unchanged): ${cash_usd:,.2f}")
    print(f"Final Overall Portfolio Value: ${final_overall:,.2f}\n")
    
    print("Final ETF Allocation Percentages (relative to ETF portion):")
    for ticker in target_allocations:
        pct = (final_values[ticker] / final_invested_value) * 100 if final_invested_value else 0
        print(f"  {ticker}: {pct:.2f}% (Target: {target_allocations[ticker]*100:.2f}%)")
    
    print("\nFinal Overall Allocation (ETFs vs Cash):")
    etf_pct = (final_invested_value / final_overall) * 100 if final_overall else 0
    cash_pct = (cash_usd / final_overall) * 100 if final_overall else 0
    print(f"  ETFs: {etf_pct:.2f}%")
    print(f"  Cash: {cash_pct:.2f}%")

def mode_add_money(target_allocations, prices):
    """
    For adding money, allocate the additional funds automatically by the target percentages.
    (This mode does not consider current ETF holdings.)
    """
    while True:
        try:
            add_amount = float(input("\nEnter the additional dollars you want to invest: $"))
            if add_amount < 0:
                print("Amount cannot be negative.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    print(f"\nAdditional Investment: ${add_amount:,.2f}")
    print("Investment Allocation for Additional Money:")
    for ticker in target_allocations:
        allocation = add_amount * target_allocations[ticker]
        share_price = prices[ticker]
        shares_to_buy = allocation / share_price
        print(f"  {ticker}: Invest ${allocation:,.2f} (approx. buy {shares_to_buy:.4f} shares).")

def mode_withdraw_money(target_allocations, shares, prices, current_values, total_invested):
    """
    Calculate how to withdraw money from the ETF positions while maintaining the target ratios.
    (This mode does not include cash.)
    """
    while True:
        try:
            withdraw_amount = float(input("\nEnter the dollars you want to withdraw: $"))
            if withdraw_amount < 0:
                print("Amount cannot be negative.")
                continue
            if withdraw_amount > total_invested:
                print("Withdrawal amount exceeds total ETF value. Please enter a valid amount.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    new_total = total_invested - withdraw_amount
    print(f"\nAfter withdrawing ${withdraw_amount:,.2f}, new ETF portfolio value will be approximately: ${new_total:,.2f}\n")
    print("Shares to Sell for Withdrawal (from ETFs):")
    for ticker in target_allocations:
        target_value = new_total * target_allocations[ticker]
        current_value = current_values[ticker]
        withdraw_from_ticker = current_value - target_value
        share_price = prices[ticker]
        shares_to_sell = withdraw_from_ticker / share_price
        if withdraw_from_ticker < 0:
            action = f"Underweight by ${-withdraw_from_ticker:,.2f} (no sale needed)."
        else:
            action = f"Sell {shares_to_sell:.4f} shares (approx. withdraw ${withdraw_from_ticker:,.2f})."
        print(f"  {ticker}: {action}")

def check_target_allocations(target_allocations):
    """
    Verify that the target allocations sum to 1.
    If they do not, print an error message and exit.
    """
    total_alloc = sum(target_allocations.values())
    if abs(total_alloc - 1.0) > 1e-6:
        print(f"Error: The target allocations must sum to 1, but they sum to {total_alloc:.2f}. Please fix the allocations.")
        sys.exit(1)

def main():
    # Define target allocations (fractions that sum to 1) for the ETFs.
    target_allocations = {
        'DBMF': 0.025,
        'EMQQ': 0.05,
        'GLDM': 0.075,
        'KMLM': 0.025,
        'SGOL': 0.075,
        'TLT': 0.1,
        'TQQQ': 0.05,
        'VBR': 0.15,
        'VCLT': 0.1,
        'VGT': 0.1,
        'VNQ': 0.05,
        'VNQI': 0.05,
        'VSS': 0.15
    }
    
    # Check that the target allocations add up to 1.
    check_target_allocations(target_allocations)
    
    print("Portfolio Manager")
    print("-----------------")
    print("Choose a mode:")
    print("  1: Rebalance existing portfolio (including cash in CHF & USD)")
    print("  2: Add money (automatic allocation by percentage)")
    print("  3: Withdraw money (reduce ETF portfolio by selling shares)")
    
    mode = input("Enter 1, 2, or 3: ").strip()
    if mode not in ('1', '2', '3'):
        print("Invalid mode selected. Exiting.")
        return

    if mode == '2':
        # Add money mode does not need current holdings.
        prices = get_prices(target_allocations)
        mode_add_money(target_allocations, prices)
    elif mode == '3':
        # Withdraw money mode: get current ETF holdings (cash is not considered here).
        shares = get_holdings(target_allocations)
        prices = get_prices(target_allocations)
        current_values = {}
        total_invested = 0.0
        print("\nCurrent ETF Positions:")
        for ticker in target_allocations:
            value = shares[ticker] * prices[ticker]
            current_values[ticker] = value
            total_invested += value
            print(f"  {ticker}: {shares[ticker]} shares * ${prices[ticker]:.2f} = ${value:,.2f}")
        print(f"\nTotal Invested ETF Value: ${total_invested:,.2f}")
        mode_withdraw_money(target_allocations, shares, prices, current_values, total_invested)
    elif mode == '1':
        # Rebalance mode: get current ETF holdings and cash in both CHF and USD.
        shares = get_holdings(target_allocations)
        prices = get_prices(target_allocations)
        cash_total = get_cash_total()
        mode_rebalance(target_allocations, shares, prices, cash_total)

if __name__ == '__main__':
    main()
