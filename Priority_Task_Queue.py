import heapq

# Our data structure: A simple list that we will turn into a Heap
task_queue = []

def add_task(priority, task_name):
    # Pushes a tuple (priority, task) onto the heap
    # It stays sorted by priority automatically!
    heapq.heappush(task_queue, (priority, task_name))
    print(f"[ADDED] {task_name} (Priority: {priority})")

def process_next():
    if task_queue:
        # Removes and returns the smallest element (highest priority)
        priority, task = heapq.heappop(task_queue)
        print(f"  >>> [EXECUTING] {task} (Priority level {priority})")
    else:
        print("  >>> [IDLE] No tasks remaining.")

# --- Terminal Simulation ---
print("--- Initializing Scheduler ---")
add_task(3, "Update System Logs")
add_task(1, "Fix Critical Server Bug")
add_task(2, "Refactor API logic")

print("-" * 30)
process_next()  # Grabs Priority 1
process_next()  # Grabs Priority 2

# Output :

# --- Initializing Scheduler ---
# [ADDED] Update System Logs (Priority: 3)
# [ADDED] Fix Critical Server Bug (Priority: 1)
# [ADDED] Refactor API logic (Priority: 2)
# ------------------------------
#   >>> [EXECUTING] Fix Critical Server Bug (Priority level 1)
#   >>> [EXECUTING] Refactor API logic (Priority level 2)