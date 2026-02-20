from collections import defaultdict

class SocialGraph:
    def __init__(self):
        # We use a defaultdict of sets so we don't get KeyErrors
        # and sets prevent duplicate friendships.
        self.graph = defaultdict(set)

    def add_friendship(self, person1, person2):
        # In an undirected graph, friendship goes both ways
        self.graph[person1].add(person2)
        self.graph[person2].add(person1)
        print(f"[LINK] {person1} <--> {person2}")

    def get_friends(self, person):
        # Returns the set of friends or an empty set if not found
        return self.graph.get(person, "User not found.")

# --- Command Line Execution ---
network = SocialGraph()

print("--- Building the Network ---")
network.add_friendship("Alice", "Bob")
network.add_friendship("Alice", "Charlie")
network.add_friendship("Bob", "David")

print("\n--- Network Queries ---")
print(f"Alice's Friends: {network.get_friends('Alice')}")
print(f"David's Friends: {network.get_friends('David')}")

# Output :

# --- Building the Network ---
# [LINK] Alice <--> Bob
# [LINK] Alice <--> Charlie
# [LINK] Bob <--> David

# --- Network Queries ---
# Alice's Friends: {'Bob', 'Charlie'}
# David's Friends: {'Bob'}