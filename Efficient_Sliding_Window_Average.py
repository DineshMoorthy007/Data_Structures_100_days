from collections import deque

# Initialize a deque with a fixed maximum length
# This automatically "pops" the oldest item when a new one is added!
readings = deque(maxlen=5)

def add_reading(value):
    readings.append(value)
    average = sum(readings) / len(readings)
    return f"Current Window: {list(readings)} | Average: {average:.2f}"

# Simulating data arriving
data_stream = [20, 22, 24, 28, 32, 35, 30]

for val in data_stream:
    print(add_reading(val))

# Output :
# Current Window: [20] | Average: 20.00
# Current Window: [20, 22] | Average: 21.00
# Current Window: [20, 22, 24] | Average: 22.00
# Current Window: [20, 22, 24, 28] | Average: 23.50
# Current Window: [20, 22, 24, 28, 32] | Average: 25.20
# Current Window: [22, 24, 28, 32, 35] | Average: 28.20
# Current Window: [24, 28, 32, 35, 30] | Average: 29.80