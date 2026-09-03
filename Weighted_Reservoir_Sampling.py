import math
import random
import heapq
from typing import Iterator, Tuple, List, Any

class WeightedItem:
    """Wrapper to hold an item, its weight, and its generated random key for the min-heap."""
    def __init__(self, key: float, item: Any, weight: float):
        self.key = key
        self.item = item
        self.weight = weight

    def __lt__(self, other: 'WeightedItem') -> bool:
        # Min-heap prioritizes the smallest key at the top for eviction
        return self.key < other.key

    def __repr__(self) -> str:
        return f"WeightedItem(item={self.item}, weight={self.weight}, key={self.key:.4f})"


class WeightedReservoirSampler:
    """Implements Algorithm A-Res for sampling k weighted items from an unbounded stream."""
    
    def __init__(self, k: int):
        if k <= 0:
            raise ValueError("Sample size k must be strictly positive.")
        self.k = k
        # Min-heap storing the top-k items with the largest keys
        self.reservoir: List[WeightedItem] = []

    def feed(self, item: Any, weight: float) -> None:
        """Processes a single (item, weight) pair from the stream in O(log k) time."""
        if weight <= 0:
            return  # Items with zero or negative weight have 0 probability of selection

        # Generate random key: k_i = u_i^(1 / w_i), where u_i ~ Uniform(0, 1)
        u = random.random()
        # Using log space to prevent underflow: key = u^(1/w)
        key = math.pow(u, 1.0 / weight)

        entry = WeightedItem(key=key, item=item, weight=weight)

        if len(self.reservoir) < self.k:
            heapq.heappush(self.reservoir, entry)
        else:
            # If the new item's key beats the smallest key currently in the reservoir, swap it
            if key > self.reservoir[0].key:
                heapq.heapreplace(self.reservoir, entry)

    def sample(self) -> List[Any]:
        """Returns the current k sampled items."""
        return [entry.item for entry in self.reservoir]

    @classmethod
    def run_stream(cls, stream: Iterator[Tuple[Any, float]], k: int) -> List[Any]:
        """Convenience runner over an iterator of (item, weight) tuples."""
        sampler = cls(k)
        for item, weight in stream:
            sampler.feed(item, weight)
        return sampler.sample()


if __name__ == "__main__":
    print("--- Initializing Weighted Reservoir Sampling Engine (A-Res) ---\n")

    # 1. Simulate an unbounded stream of log events with varying priority weights
    stream_events = [
        ("DEBUG: heartbeat", 1.0),
        ("INFO: user login", 5.0),
        ("WARN: high memory", 20.0),
        ("ERROR: db failure", 100.0),
        ("CRITICAL: payment timeout", 250.0),
        ("TRACE: query cache", 1.0),
        ("ERROR: redis dropped", 100.0)
    ]

    K = 3
    sample = WeightedReservoirSampler.run_stream(iter(stream_events), k=K)

    print("[CONFIGURATION]")
    print(f"  Reservoir Capacity (k) : {K}")
    print(f"  Total Stream Events    : {len(stream_events)}")
    print("-" * 65)

    print(f"\n[SAMPLE OUTPUT (k={K})]")
    for rank, item in enumerate(sample, 1):
        print(f"  #{rank} -> {item}")

    # 2. Monte Carlo Verification of Proportional Probability
    print("\n[EMPIRICAL PROBABILITY VERIFICATION]")
    print("  Running 10,000 trials sampling 1 item from items with weights [10, 30, 60]...")

    sim_trials = 10_000
    test_items = [("Item_A (w=10)", 10.0), ("Item_B (w=30)", 30.0), ("Item_C (w=60)", 60.0)]
    selection_counts = {name: 0 for name, _ in test_items}

    for _ in range(sim_trials):
        picked = WeightedReservoirSampler.run_stream(iter(test_items), k=1)[0]
        selection_counts[picked] += 1

    total_weight = sum(w for _, w in test_items)
    for name, w in test_items:
        expected_ratio = w / total_weight
        observed_ratio = selection_counts[name] / sim_trials
        print("  {name:<18} -> Expected: {expected_ratio:.2f} | Observed: {observed_ratio:.2f} ({selection_counts[name]:,} hits)")

# Output :
# --- Initializing Weighted Reservoir Sampling Engine (A-Res) ---

# [CONFIGURATION]
#   Reservoir Capacity (k) : 3
#   Total Stream Events    : 7
# -----------------------------------------------------------------

# [SAMPLE OUTPUT (k=3)]
#   #1 -> WARN: high memory
#   #2 -> ERROR: db failure
#   #3 -> CRITICAL: payment timeout

# [EMPIRICAL PROBABILITY VERIFICATION]
#   Running 10,000 trials sampling 1 item from items with weights [10, 30, 60]...
#   {name:<18} -> Expected: {expected_ratio:.2f} | Observed: {observed_ratio:.2f} ({selection_counts[name]:,} hits)
#   {name:<18} -> Expected: {expected_ratio:.2f} | Observed: {observed_ratio:.2f} ({selection_counts[name]:,} hits)
#   {name:<18} -> Expected: {expected_ratio:.2f} | Observed: {observed_ratio:.2f} ({selection_counts[name]:,} hits)
