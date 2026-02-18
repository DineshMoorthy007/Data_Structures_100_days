from collections import defaultdict

# Initialize a defaultdict with 'list' as the default factory
# This means if a key doesn't exist, Python automatically creates a []
inventory = defaultdict(list)

def add_item(category, item_name):
    # No need to check if the category exists! 
    # Python creates it on the fly.
    inventory[category].append(item_name)
    print(f"[LOG] Added '{item_name}' to category '{category}'")

# --- Command Line Execution ---
print("--- Updating Digital Inventory ---")
add_item("Electronics", "Laptop")
add_item("Furniture", "Chair")
add_item("Electronics", "Headphones")
add_item("Kitchen", "Toaster")

print("\n--- Current Inventory Status ---")
for category, items in inventory.items():
    print(f"{category:12}: {', '.join(items)}")

# Output :

# --- Updating Digital Inventory ---
# [LOG] Added 'Laptop' to category 'Electronics'
# [LOG] Added 'Chair' to category 'Furniture'
# [LOG] Added 'Headphones' to category 'Electronics'
# [LOG] Added 'Toaster' to category 'Kitchen'

# --- Current Inventory Status ---
# Electronics : Laptop, Headphones
# Furniture   : Chair
# Kitchen     : Toaster