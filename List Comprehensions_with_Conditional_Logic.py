# List of Celsius temperatures
celsius_temps = [12, 25, 8, 31, 19, 22]

# The "One-Liner" List Comprehension
warm_fahrenheit = [(temp * 9/5) + 32 for temp in celsius_temps if temp > 20]

print(f"Warm days in Fahrenheit: {warm_fahrenheit}")
# Output: Warm days in Fahrenheit: [77.0, 87.8, 71.6]
