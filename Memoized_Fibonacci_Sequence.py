# Standard Dictionary to store our 'Memory' (Memoization)
memo = {}

def fib_dp(n):
    # Base Cases
    if n <= 1:
        return n
    
    # 1. Check if we have already calculated this number
    if n in memo:
        return memo[n]
    
    # 2. If not, calculate it and STORE it in the memo
    memo[n] = fib_dp(n - 1) + fib_dp(n - 2)
    
    return memo[n]

n_value = 50 
print(f"--- Calculating the {n_value}th Fibonacci Number ---")
result = fib_dp(n_value)
print(f"Result: {result}")
print(f"Steps saved: Millions of redundant calculations avoided!")

# Output :

# --- Calculating the 50th Fibonacci Number ---
# Result: 12586269025
# Steps saved: Millions of redundant calculations avoided!