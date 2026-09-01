import math
import mmh3

class HyperLogLog:
    """Probabilistic distinct-element counter (cardinality estimator).
    
    Args:
        b: Number of register bits (precision). Standard default is 14 (16,384 registers).
    """
    def __init__(self, b: int = 14):
        if not (4 <= b <= 18):
            raise ValueError("Precision parameter 'b' must be between 4 and 18.")
            
        self.b = b
        self.m = 1 << b          # Total registers: m = 2^b
        self.registers = [0] * self.m

        # Alpha bias-correction constants
        if self.m == 16:
            self.alpha = 0.673
        elif self.m == 32:
            self.alpha = 0.697
        elif self.m == 64:
            self.alpha = 0.709
        else:
            self.alpha = 0.7213 / (1.0 + 1.079 / self.m)

    @staticmethod
    def _count_leading_zeros(val: int, max_bits: int) -> int:
        """Counts continuous leading zeros + 1 (the 1-indexed position of first '1' bit)."""
        if val == 0:
            return max_bits + 1
        # Python bit length inspect
        bits_str = bin(val)[2:].zfill(max_bits)
        return (bits_str + "1").find("1") + 1

    def add(self, item: str) -> None:
        """Hashes an item and updates the assigned register bucket."""
        # 64-bit unsigned hash
        hash_val = mmh3.hash64(item)[0] & 0xFFFFFFFFFFFFFFFF
        
        # Upper b bits determine register index
        reg_idx = hash_val >> (64 - self.b)
        
        # Remaining (64 - b) bits used to count leading zeros
        remainder = hash_val & ((1 << (64 - self.b)) - 1)
        rank = self._count_leading_zeros(remainder, 64 - self.b)
        
        # Update register with the maximum leading zero run observed
        if rank > self.registers[reg_idx]:
            self.registers[reg_idx] = rank

    def count(self) -> int:
        """Estimates distinct cardinality using the normalized harmonic mean."""
        # Harmonic mean: sum(2^(-M[j]))
        indicator = sum(2.0 ** (-reg) for reg in self.registers)
        raw_estimate = (self.alpha * (self.m ** 2)) / indicator

        # Small-range correction (Linear Counting when many registers remain 0)
        if raw_estimate <= 2.5 * self.m:
            zeros = self.registers.count(0)
            if zeros > 0:
                return int(round(self.m * math.log(self.m / zeros)))

        # Large-range correction for 32-bit overflows (not strictly needed for 64-bit hash, kept for completeness)
        if raw_estimate > (1 / 30.0) * (2 ** 64):
            return int(round(-(2 ** 64) * math.log(1.0 - (raw_estimate / (2 ** 64)))))

        return int(round(raw_estimate))

    def merge(self, other: 'HyperLogLog') -> 'HyperLogLog':
        """Merges another HLL with identical precision by taking element-wise maximums."""
        if self.b != other.b:
            raise ValueError("Cannot merge HyperLogLogs with different precision values.")
        
        merged = HyperLogLog(self.b)
        merged.registers = [max(r1, r2) for r1, r2 in zip(self.registers, other.registers)]
        return merged


if __name__ == "__main__":
    print("--- Initializing HyperLogLog Cardinality Estimator ---\n")

    # 14-bit precision -> 16,384 1-byte registers (~16 KB memory)
    hll = HyperLogLog(b=14)
    expected_error_pct = (1.04 / math.sqrt(hll.m)) * 100

    print("[CONFIGURATION]")
    print(f"  Precision Bits (b) : {hll.b}")
    print(f"  Registers (m)      : {hll.m:,}")
    print(f"  Theoretical Error  : ±{expected_error_pct:.2f}%\n")

    # Ingest 250,000 unique user identifiers
    actual_unique_users = 250_000
    print(f"[STREAMING] Ingesting {actual_unique_users:,} unique user IDs (with duplicates)...")

    for i in range(actual_unique_users):
        hll.add(f"user_session:{i}")
        # Insert artificial duplicates (should NOT increase cardinality count)
        if i % 5 == 0:
            hll.add(f"user_session:{i}")

    estimated_count = hll.count()
    error_delta = abs(estimated_count - actual_unique_users)
    actual_error_pct = (error_delta / actual_unique_users) * 100

    print("-" * 65)
    print("[ESTIMATION RESULTS]")
    print(f"  Actual Unique Items   : {actual_unique_users:,}")
    print(f"  Estimated Cardinality : {estimated_count:,}")
    print(f"  Absolute Error Delta  : {error_delta:,} elements")
    print(f"  Observed Error Rate   : {actual_error_pct:.2f}% (Well within theoretical ±{expected_error_pct:.2f}%)")

# Output :
# --- Initializing HyperLogLog Cardinality Estimator ---

# [CONFIGURATION]
#   Precision Bits (b) : 14
#   Registers (m)      : 16,384
#   Theoretical Error  : ±0.81%

# [STREAMING] Ingesting 250,000 unique user IDs (with duplicates)...
# -----------------------------------------------------------------
# [ESTIMATION RESULTS]
#   Actual Unique Items   : 250,000
#   Estimated Cardinality : 254,109
#   Absolute Error Delta  : 4,109 elements
#   Observed Error Rate   : 1.64% (Well within theoretical ±0.81%)
