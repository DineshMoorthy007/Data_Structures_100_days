from collections import deque, defaultdict

# 1. Define the Network (Adjacency List)
network = {
    "Alice": ["Bob", "Charlie"],
    "Bob": ["Alice", "David", "Eve"],
    "Charlie": ["Alice", "Frank"],
    "David": ["Bob"],
    "Eve": ["Bob", "Frank"],
    "Frank": ["Charlie", "Eve"]
}

def bfs_explore(graph, start_node):
    visited = set()             # To keep track of where we've been
    queue = deque([start_node]) # FIFO queue for layer-by-layer search
    visited.add(start_node)
    
    print(f"--- Starting BFS from {start_node} ---")
    
    while queue:
        # Pop the oldest person in the queue
        current = queue.popleft()
        print(f"[VISITING] {current}")
        
        # Check all their friends
        for friend in graph.get(current, []):
            if friend not in visited:
                visited.add(friend)
                queue.append(friend)

# --- Command Line Execution ---
bfs_explore(network, "Alice")

# Output :

# --- Starting BFS from Alice ---
# [VISITING] Alice
# [VISITING] Bob
# [VISITING] Charlie
# [VISITING] David
# [VISITING] Eve
# [VISITING] Frank