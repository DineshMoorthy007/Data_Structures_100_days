import random
from typing import List

class ProductQuantizer:
    """Compresses dense vectors into compact byte codes via Product Quantization (PQ)."""
    
    def __init__(self, dim: int, num_subspaces: int = 4, num_centroids: int = 16):
        """
        Args:
            dim: Total dimension of incoming vectors (must be divisible by num_subspaces).
            num_subspaces: Number of orthogonal subspace slices (M).
            num_centroids: Number of centroid clusters per subspace (K <= 256 for 1-byte codes).
        """
        if dim % num_subspaces != 0:
            raise ValueError("Vector dimension must be evenly divisible by num_subspaces.")
        if num_centroids > 256:
            raise ValueError("Centroids per subspace must be <= 256 for 8-bit quantization.")

        self.dim = dim
        self.m = num_subspaces
        self.d_sub = dim // num_subspaces
        self.k = num_centroids

        # Codebook shape: [M subspaces][K centroids][D_sub dimensions]
        self.codebooks: List[List[List[float]]] = []

    @staticmethod
    def _sq_euclidean(v1: List[float], v2: List[float]) -> float:
        """Calculates squared Euclidean distance between two sub-vectors."""
        return sum((a - b) ** 2 for a, b in zip(v1, v2))

    def _train_kmeans(self, sub_vectors: List[List[float]], max_iters: int = 10) -> List[List[float]]:
        """Simple k-means clustering to construct codebook centroids for one subspace."""
        centroids = [list(sub_vectors[i]) for i in random.sample(range(len(sub_vectors)), self.k)]

        for _ in range(max_iters):
            clusters = [[] for _ in range(self.k)]
            for vec in sub_vectors:
                # Find nearest centroid
                best_idx = min(
                    range(self.k),
                    key=lambda idx: self._sq_euclidean(vec, centroids[idx])
                )
                clusters[best_idx].append(vec)

            # Recompute centroid means
            for idx in range(self.k):
                if clusters[idx]:
                    centroids[idx] = [
                        sum(col) / len(clusters[idx])
                        for col in zip(*clusters[idx])
                    ]
        return centroids

    def fit(self, training_vectors: List[List[float]]) -> None:
        """Trains centroid codebooks across each orthogonal subspace."""
        self.codebooks = []
        for sub_idx in range(self.m):
            start = sub_idx * self.d_sub
            end = start + self.d_sub

            # Extract sub-vectors for subspace M_i
            sub_vectors = [v[start:end] for v in training_vectors]
            centroids = self._train_kmeans(sub_vectors)
            self.codebooks.append(centroids)

    def encode(self, vector: List[float]) -> List[int]:
        """Quantizes a full vector into an M-byte discrete centroid index code."""
        code = []
        for sub_idx in range(self.m):
            start = sub_idx * self.d_sub
            end = start + self.d_sub
            sub_vec = vector[start:end]

            # Find closest centroid index in this subspace's codebook
            best_centroid_idx = min(
                range(self.k),
                key=lambda c_idx: self._sq_euclidean(sub_vec, self.codebooks[sub_idx][c_idx])
            )
            code.append(best_centroid_idx)
        return code

    def compute_distance_table(self, query: List[float]) -> List[List[float]]:
        """Precomputes squared distance lookup table between uncompressed query and all centroids."""
        # Table shape: [M subspaces][K centroids]
        lut = []
        for sub_idx in range(self.m):
            start = sub_idx * self.d_sub
            end = start + self.d_sub
            query_sub = query[start:end]

            sub_distances = [
                self._sq_euclidean(query_sub, centroid)
                for centroid in self.codebooks[sub_idx]
            ]
            lut.append(sub_distances)
        return lut

    def compute_asymmetric_distance(self, distance_table: List[List[float]], code: List[int]) -> float:
        """Computes Asymmetric Distance (ADC) in O(M) time using precomputed lookup table."""
        return sum(distance_table[sub_idx][code[sub_idx]] for sub_idx in range(self.m))


if __name__ == "__main__":
    print("--- Initializing Product Quantization (PQ) Vector Engine ---\n")

    # Generate synthetic 8-dimensional embedding dataset
    random.seed(42)
    dim = 8
    num_samples = 100
    dataset = [[round(random.uniform(-1.0, 1.0), 3) for _ in range(dim)] for _ in range(num_samples)]

    # 1. Initialize PQ: Split 8-dim vector into 4 subspaces (2-dim sub-vectors), 8 centroids each
    pq = ProductQuantizer(dim=8, num_subspaces=4, num_centroids=8)
    pq.fit(dataset)

    print("[CONFIGURATION]")
    print(f"  Vector Dimension (D)   : {dim}")
    print(f"  Subspaces (M)          : {pq.m} (Sub-vector dim: {pq.d_sub})")
    print(f"  Centroids per Subspace : {pq.k}")
    print("-" * 65)

    # 2. Compress the database into compact M-byte codes
    compressed_db = [pq.encode(vec) for vec in dataset]
    raw_size_bytes = num_samples * dim * 4  # 32-bit floats
    pq_size_bytes = num_samples * pq.m      # 8-bit bytes

    print("\n[COMPRESSION RATIO]")
    print(f"  Uncompressed Dataset Size : {raw_size_bytes} bytes")
    print(f"  PQ Compressed Code Size   : {pq_size_bytes} bytes")
    print(f"  Memory Reduction Factor   : {raw_size_bytes / pq_size_bytes:.1f}x compression\n")

    # 3. Asymmetric Distance Search (Query uncompressed vs Database compressed)
    query_vec = [round(random.uniform(-1.0, 1.0), 3) for _ in range(dim)]
    dist_table = pq.compute_distance_table(query_vec)

    # Score all compressed items using the precomputed distance table
    scored_candidates = []
    for doc_id, code in enumerate(compressed_db):
        adc_dist = pq.compute_asymmetric_distance(dist_table, code)
        scored_candidates.append((doc_id, adc_dist))

    # Sort nearest neighbors
    scored_candidates.sort(key=lambda x: x[1])

    print("[ASYMMETRIC DISTANCE TOP MATCHES]")
    for rank, (doc_id, dist) in enumerate(scored_candidates[:4], 1):
        print(f"  #{rank} Doc #{doc_id:>2} | ADC Sq Distance: {dist:.4f} | PQ Code: {compressed_db[doc_id]}")

# Output :
# --- Initializing Product Quantization (PQ) Vector Engine ---

# [CONFIGURATION]
#   Vector Dimension (D)   : 8
#   Subspaces (M)          : 4 (Sub-vector dim: 2)
#   Centroids per Subspace : 8
# -----------------------------------------------------------------

# [COMPRESSION RATIO]
#   Uncompressed Dataset Size : 3200 bytes
#   PQ Compressed Code Size   : 400 bytes
#   Memory Reduction Factor   : 8.0x compression

# [ASYMMETRIC DISTANCE TOP MATCHES]
#   #1 Doc #33 | ADC Sq Distance: 1.4779 | PQ Code: [7, 7, 1, 7]
#   #2 Doc #10 | ADC Sq Distance: 1.9925 | PQ Code: [1, 7, 6, 0]
#   #3 Doc #73 | ADC Sq Distance: 2.3232 | PQ Code: [5, 4, 6, 7]
#   #4 Doc #65 | ADC Sq Distance: 2.4703 | PQ Code: [5, 7, 0, 7]
