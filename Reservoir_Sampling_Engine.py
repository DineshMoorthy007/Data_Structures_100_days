import random
import math
from typing import Iterator, List, Any

class ReservoirSampler:
    """Samples k uniform items from an unbounded, single-pass data stream."""

    @staticmethod
    def algorithm_r(stream: Iterator[Any], k: int) -> List[Any]:
        """Classic Alan G. Waterman Algorithm R.
        
        Evaluates each element with probability k / i.
        """
        reservoir: List[Any] = []

        # Step 1: Fill the reservoir with the first k elements
        for i, item in enumerate(stream, start=1):
            if i <= k:
                reservoir.append(item)
            else:
                # Step 2: For the i-th element, choose a random index in [0, i - 1]
                j = random.randint(0, i - 1)
                if j < k:
                    reservoir[j] = item

        return reservoir

    @staticmethod
    def algorithm_l(stream: Iterator[Any], k: int) -> List[Any]:
        """Li's Algorithm L (Optimal for large streams).
        
        Computes geometric skip distances to bypass generating random numbers
        for elements that will definitely not enter the reservoir.
        """
        iterator = iter(stream)
        reservoir: List[Any] = []

        # Step 1: Populate reservoir with first k elements
        try:
            for _ in range(k):
                reservoir.append(next(iterator))
        except StopIteration:
            return reservoir

        # Step 2: Initialize weight variable W
        # W represents the largest random weight among the current reservoir items
        w = math.exp(math.log(random.random()) / k)

        # Step 3: Compute geometric skip steps
        while True:
            # S is the number of stream items to skip
            s = int(math.floor(math.log(random.random()) / math.log(1.0 - w)))

            # Advance iterator by S elements
            item_to_consider = None
            try:
                for _ in range(s):
                    next(iterator)
                item_to_consider = next(iterator)
            except StopIteration:
                break

            # Replace a uniformly selected item in the reservoir
            replace_idx = random.randint(0, k - 1)
            reservoir[replace_idx] = item_to_consider

            # Update weight threshold W
            w *= math.exp(math.log(random.random()) / k)

        return reservoir


if __name__ == "__main__":
    print("--- Initializing Stream Reservoir Sampling Engine ---\n")

    # Target reservoir capacity
    K = 5
    # Total stream volume (unknown to the sampler beforehand)
    STREAM_SIZE = 100_000

    def stream_generator(n: int):
        for i in range(1, n + 1):
            yield f"packet_id_{i:06d}"

    print(f"[CONFIGURATION]")
    print(f"  Reservoir Size (k)    : {K}")
    print(f"  Stream Volume (N)     : {STREAM_SIZE:,} events")
    print(f"  Theoretical Item Prob : {K / STREAM_SIZE:.6f} ({K}/{STREAM_SIZE:,})")
    print("-" * 65)

    # 1. Execute Classic Algorithm R
    sample_r = ReservoirSampler.algorithm_r(stream_generator(STREAM_SIZE), k=K)
    print("\n[ALGORITHM R SAMPLE]")
    for rank, item in enumerate(sample_r, 1):
        print(f"  #{rank} -> {item}")

    # 2. Execute High-Throughput Algorithm L (Geometric Skipping)
    sample_l = ReservoirSampler.algorithm_l(stream_generator(STREAM_SIZE), k=K)
    print("\n[ALGORITHM L SAMPLE (OPTIMIZED SKIPS)]")
    for rank, item in enumerate(sample_l, 1):
        print(f"  #{rank} -> {item}")

    # 3. Uniformity Verification Test (Monte Carlo Proof)
    print("\n[UNIFORMITY PROOF] Simulating 10,000 runs over an 8-item stream (k=2)...")
    counts = {f"item_{i}": 0 for i in range(1, 9)}
    sim_runs = 10_000

    for _ in range(sim_runs):
        mini_stream = (f"item_{i}" for i in range(1, 9))
        sampled = ReservoirSampler.algorithm_r(mini_stream, k=2)
        for s in sampled:
            counts[s] += 1

    expected_freq = (2 / 8) * sim_runs
    print(f"  Expected Frequency per Item: ~{int(expected_freq)}")
    for item, freq in counts.items():
        print(f"    {item} : {freq} times (Observed Prob: {freq / sim_runs:.3f})")

# Output :
# --- Initializing Stream Reservoir Sampling Engine ---

# [CONFIGURATION]
#   Reservoir Size (k)    : 5
#   Stream Volume (N)     : 100,000 events
#   Theoretical Item Prob : 0.000050 (5/100,000)
# -----------------------------------------------------------------

# [ALGORITHM R SAMPLE]
#   #1 -> packet_id_047449
#   #2 -> packet_id_032930
#   #3 -> packet_id_099419
#   #4 -> packet_id_024172
#   #5 -> packet_id_091751

# [ALGORITHM L SAMPLE (OPTIMIZED SKIPS)]
#   #1 -> packet_id_002965
#   #2 -> packet_id_006413
#   #3 -> packet_id_024002
#   #4 -> packet_id_007991
#   #5 -> packet_id_021933

# [UNIFORMITY PROOF] Simulating 10,000 runs over an 8-item stream (k=2)...
#   Expected Frequency per Item: ~2500
#     item_1 : 2459 times (Observed Prob: 0.246)
#     item_2 : 2532 times (Observed Prob: 0.253)
#     item_3 : 2496 times (Observed Prob: 0.250)
#     item_4 : 2577 times (Observed Prob: 0.258)
#     item_5 : 2466 times (Observed Prob: 0.247)
#     item_6 : 2454 times (Observed Prob: 0.245)
#     item_7 : 2554 times (Observed Prob: 0.255)
#     item_8 : 2462 times (Observed Prob: 0.246)
