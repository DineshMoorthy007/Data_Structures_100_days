from collections import deque

# 1. Initialize the Queue
task_queue = deque(["Email Client", "Update Server", "Run Backups"])

print(f"--- Initial Queue ---")
print(list(task_queue))

# 2. Enqueue: Adding a new task to the end
print(f"\n[Action] Adding 'Generate Report' to the queue...")
task_queue.append("Generate Report")

# 3. Dequeue: Removing the task from the front (FIFO)
current_task = task_queue.popleft()
print(f"[Action] Processing task: {current_task}")

# 4. Final State
print(f"\n--- Remaining Tasks ---")
print(list(task_queue))

# Output :

# --- Initial Queue ---
# ['Email Client', 'Update Server', 'Run Backups']

# [Action] Adding 'Generate Report' to the queue...
# [Action] Processing task: Email Client

# --- Remaining Tasks ---
# ['Update Server', 'Run Backups', 'Generate Report']