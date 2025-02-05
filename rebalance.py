#!/usr/bin/env python3
import yfinance as yf

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

def get_prices(target_allocations):
    """Retrieve current market prices for each ticker."""
    prices = {}
    for ticker in target_allocations:
        price = get_current_price(ticker)
        if price is None:
            print(f"Could not retrieve price for {ticker}. Exiting.")
            exit(1)
        prices[ticker] = price
    return prices

def print_current_status(target_allocations, shares, prices):
    """Print the current positions and allocation percentages."""
    current_values = {}
    total_value = 0.0
    print("\nCurrent Positions:")
    for ticker in target_allocations:
        value = shares[ticker] * prices[ticker]
        current_values[ticker] = value
        total_value += value
        print(f"  {ticker}: {shares[ticker]} shares * ${prices[ticker]:.2f} = ${value:,.2f}")
    print(f"\nTotal Portfolio Value: ${total_value:,.2f}")
    print("\nCurrent Allocation Percentages:")
    for ticker in target_allocations:
        current_pct = (current_values[ticker] / total_value) * 100 if total_value else 0
        target_pct = target_allocations[ticker] * 100
        print(f"  {ticker}: {current_pct:.2f}% (Target: {target_pct:.2f}%)")
    return current_values, total_value

def mode_rebalance(target_allocations, shares, prices, current_values, total_value):
    """Provide rebalancing recommendations for the current portfolio."""
    print("\nRebalance Recommendations:")
    for ticker in target_allocations:
        target_value = total_value * target_allocations[ticker]
        current_value = current_values[ticker]
        difference_value = target_value - current_value
        share_price = prices[ticker]
        difference_shares = difference_value / share_price
        current_pct = (current_value / total_value) * 100 if total_value else 0
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

def mode_add_money(target_allocations, prices):
    """
    For adding money, allocate the additional funds according to target percentages.
    This mode does not require current holdings.
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

def mode_withdraw_money(target_allocations, shares, prices, current_values, total_value):
    """Calculate how to withdraw money while maintaining the target ratios."""
    while True:
        try:
            withdraw_amount = float(input("\nEnter the dollars you want to withdraw: $"))
            if withdraw_amount < 0:
                print("Amount cannot be negative.")
                continue
            if withdraw_amount > total_value:
                print("Withdrawal amount exceeds total portfolio value. Please enter a valid amount.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    new_total = total_value - withdraw_amount
    print(f"\nAfter withdrawing ${withdraw_amount:,.2f}, new portfolio value will be approximately: ${new_total:,.2f}\n")
    print("Shares to Sell for Withdrawal:")
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

def main():
    # Define target allocations as fractions of the total portfolio value.
    target_allocations = {
        'VT': 0.42,
        'THNQ': 0.11,
        'UPRO': 0.05,
        'KMLM': 0.22,
        'DBMF': 0.10,
        'GLD': 0.03,
        'TLT': 0.07,
    }
    
    print("Portfolio Manager")
    print("-----------------")
    print("Choose a mode:")
    print("  1: Rebalance existing portfolio")
    print("  2: Add money (automatic allocation by percentage)")
    print("  3: Withdraw money (reduce portfolio by selling shares)")
    
    mode = input("Enter 1, 2, or 3: ").strip()
    if mode not in ('1', '2', '3'):
        print("Invalid mode selected. Exiting.")
        return

    if mode == '2':
        # For adding money, we don't need current holdings.
        prices = get_prices(target_allocations)
        mode_add_money(target_allocations, prices)
    else:
        # For rebalance or withdraw money, we need current holdings.
        shares = get_holdings(target_allocations)
        prices = get_prices(target_allocations)
        current_values, total_value = print_current_status(target_allocations, shares, prices)
        if mode == '1':
            mode_rebalance(target_allocations, shares, prices, current_values, total_value)
        elif mode == '3':
            mode_withdraw_money(target_allocations, shares, prices, current_values, total_value)

if __name__ == '__main__':
    main()
