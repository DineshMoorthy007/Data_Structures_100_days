def count_ways_to_climb(n):
    if n <= 2:
        return n

    # 1. Initialize our "Table" (Data Structure)
    # We create a list of size n+1 to store solutions to sub-problems
    dp = [0] * (n + 1)
    
    # 2. Base Cases:
    # 1 step = 1 way ([1])
    # 2 steps = 2 ways ([1,1], [2])
    dp[1] = 1
    dp[2] = 2
    
    # 3. Fill the table iteratively (The "Bottom-Up" part)
    # To reach step 'i', you must have come from 'i-1' or 'i-2'
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
        
    return dp[n]

# --- Command Line Output ---
steps = 10
result = count_ways_to_climb(steps)
print(f"--- Solving Staircase Problem for {steps} steps ---")
print(f"Total distinct ways to reach the top: {result}")
