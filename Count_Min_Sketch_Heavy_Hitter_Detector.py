import math
import mmh3
from typing import Dict, List, Tuple

class CountMinSketch:
    """Probabilistic frequency estimator for continuous unbounded data streams."""
    
    def __init__(self, epsilon: float = 0.001, delta: float = 0.01):
        """
        Args:
            epsilon: Error factor (estimate will be within epsilon * N of true frequency).
            delta: Probability that the error bound is exceeded (1 - delta confidence).
        """
        # Optimal mathematical dimensioning: w = e / epsilon, d = ln(1 / delta)
        self.width = int(math.ceil(math.e / epsilon))
        self.depth = int(math.ceil(math.log(1.0 / delta)))
        
        # 2D table of integer counters: shape [depth x width]
        self.table = [[0] * self.width for _ in range(self.depth)]
        self.total_count = 0
        
        # Independent hash function seeds
        self.seeds = [i * 10007 for i in range(self.depth)]

    def _hash(self, item: str, row: int) -> int:
        """Computes column index for a given row using seeded MurmurHash3."""
        return abs(mmh3.hash(item, self.seeds[row])) % self.width

    def add(self, item: str, count: int = 1) -> None:
        """Increments the counter for an item across all hash rows."""
        self.total_count += count
        for row in range(self.depth):
            col = self._hash(item, row)
            self.table[row][col] += count

    def estimate(self, item: str) -> int:
        """Estimates frequency by taking the minimum across all mapped counters."""
        min_val = float('inf')
        for row in range(self.depth):
            col = self._hash(item, row)
            min_val = min(min_val, self.table[row][col])
        return int(min_val)


class HeavyHitterDetector:
    """Maintains a bounded Top-K priority queue over a Count-Min Sketch stream."""
    
    def __init__(self, k: int = 5, epsilon: float = 0.001, delta: float = 0.01):
        self.k = k
        self.sketch = CountMinSketch(epsilon, delta)
        self.top_k: Dict[str, int] = {}  # Tracks candidate heavy hitters

    def process(self, item: str, count: int = 1) -> None:
        """Ingests an event, updates sketch, and maintains Top-K ranking."""
        self.sketch.add(item, count)
        est = self.sketch.estimate(item)
        
        self.top_k[item] = est
        
        # Keep tracking map bounded to avoid unbounded RAM growth
        if len(self.top_k) > self.k * 3:
            # Prune lowest estimated candidates
            sorted_items = sorted(self.top_k.items(), key=lambda x: x[1], reverse=True)
            self.top_k = dict(sorted_items[:self.k * 2])

    def get_top_k(self) -> List[Tuple[str, int]]:
        """Returns the top K heavy hitters sorted by descending estimated frequency."""
        # Refresh current estimates
        for item in list(self.top_k.keys()):
            self.top_k[item] = self.sketch.estimate(item)
            
        sorted_top = sorted(self.top_k.items(), key=lambda x: x[1], reverse=True)
        return sorted_top[:self.k]


if __name__ == "__main__":
    print("--- Initializing Count-Min Sketch & Heavy Hitters Engine ---\n")

    # Error bound: within 0.1% of total stream volume with 99% confidence
    detector = HeavyHitterDetector(k=3, epsilon=0.001, delta=0.01)

    print("[SKETCH ALLOCATION]")
    print(f"  Table Width (w)  : {detector.sketch.width:,} buckets")
    print(f"  Table Depth (d)  : {detector.sketch.depth} hash rows")
    print(f"  Memory Footprint : ~{(detector.sketch.width * detector.sketch.depth * 4) / 1024:.2f} KB\n")

    # Ingest 100,000 streaming network events with skewed Zipfian distribution
    stream_data = [
        ("192.168.1.100 (DDoS Attacker)", 45_000),
        ("10.0.0.1 (API Gateway)",         25_000),
        ("172.16.0.5 (Database Replica)",  10_000),
        ("10.0.0.42 (Internal Auth)",       3_000),
    ]

    print("[STREAMING INGESTION] Processing 100,000 network telemetry packets...")
    for ip, freq in stream_data:
        detector.process(ip, freq)

    # Ingest 17,000 distinct noise IPs (1 hit each)
    for i in range(17_000):
        detector.process(f"noise_ip_{i}", 1)

    print(f"  Total Ingested Events: {detector.sketch.total_count:,}")
    print("-" * 65)

    print("\n[TOP-K HEAVY HITTERS DETECTED]")
    for rank, (item, est_freq) in enumerate(detector.get_top_k(), 1):
        print(f"  #{rank} {item:<32} -> Est. Frequency: {est_freq:,}")

    print("\n[POINT ESTIMATION ACCURACY]")
    test_target = "192.168.1.100 (DDoS Attacker)"
    print(f"  Target: '{test_target}'")
    print("  Actual Count    : 45,000")
    print(f"  Estimated Count : {detector.sketch.estimate(test_target):,}")

# Output :
# --- Initializing Count-Min Sketch & Heavy Hitters Engine ---

# [SKETCH ALLOCATION]
#   Table Width (w)  : 2,719 buckets
#   Table Depth (d)  : 5 hash rows
#   Memory Footprint : ~53.11 KB

# [STREAMING INGESTION] Processing 100,000 network telemetry packets...
#   Total Ingested Events: 100,000
# -----------------------------------------------------------------

# [TOP-K HEAVY HITTERS DETECTED]
#   #1 192.168.1.100 (DDoS Attacker)    -> Est. Frequency: 45,003
#   #2 10.0.0.1 (API Gateway)           -> Est. Frequency: 25,001
#   #3 172.16.0.5 (Database Replica)    -> Est. Frequency: 10,000

# [POINT ESTIMATION ACCURACY]
#   Target: '192.168.1.100 (DDoS Attacker)'
#   Actual Count    : 45,000
#   Estimated Count : 45,003
