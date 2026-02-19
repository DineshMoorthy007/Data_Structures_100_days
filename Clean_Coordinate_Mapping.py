from collections import namedtuple

# 1. Define the structure (Immutable and lightweight)
# This creates a 'class' called Point with fields x, y, and z
Point = namedtuple('Point', ['x', 'y', 'z'])

# 2. Create instances
p1 = Point(10, 20, 30)
p2 = Point(x=50, y=100, z=150)

def calculate_displacement(point_a, point_b):
    # Notice how readable this is! No more magic numbers like [0] or [1]
    dx = point_b.x - point_a.x
    dy = point_b.y - point_a.y
    dz = point_b.z - point_a.z
    return (dx, dy, dz)

# --- Command Line Output ---
print(f"--- Telemetry Data ---")
print(f"Current Position: {p1}")
print(f"Target Position:  {p2}")

dist = calculate_displacement(p1, p2)
print(f"\n[CALCULATION] Displacement needed: X:{dist[0]}, Y:{dist[1]}, Z:{dist[2]}")

# Output :

# --- Telemetry Data ---
# Current Position: Point(x=10, y=20, z=30)
# Target Position:  Point(x=50, y=100, z=150)

# [CALCULATION] Displacement needed: X:40, Y:80, Z:120