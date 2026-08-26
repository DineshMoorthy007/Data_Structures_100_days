import math
import random
import heapq
from typing import List, Dict, Set, Tuple

class HNSWIndex:
    """A Hierarchical Navigable Small World (HNSW) graph for vector similarity search."""
    
    def __init__(self, dim: int, m: int = 4, m0: int = 8, ef_construction: int = 16, ml: float = 1.0 / math.log(2)):
        """
        Args:
            dim: Dimension of vector embeddings.
            m: Max neighbor connections per node on higher layers.
            m0: Max neighbor connections per node on the bottom layer (Layer 0).
            ef_construction: Size of the dynamic candidate priority queue during build.
            ml: Normalization factor for probabilistic layer level generation.
        """
        self.dim = dim
        self.m = m
        self.m0 = m0
        self.ef_construction = ef_construction
        self.ml = ml

        self.vectors: Dict[int, List[float]] = {}
        # Layer graphs: layers[lvl][node_id] = set(neighbor_node_ids)
        self.layers: List[Dict[int, Set[int]]] = []
        self.enter_point: int | None = None
        self.max_level: int = -1

    @staticmethod
    def _l2_distance(v1: List[float], v2: List[float]) -> float:
        """Computes Euclidean (L2) distance between two dense vectors."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    def _random_level(self) -> int:
        """Decides top level using geometric decay probability (similar to Skip Lists)."""
        lvl = int(-math.log(random.random()) * self.ml)
        return lvl

    def _search_layer(self, query: List[float], enter_points: List[int], ef: int, level: int) -> List[Tuple[float, int]]:
        """Greedy beam search traversing a single HNSW graph layer."""
        v_dist = self._l2_distance
        
        # Min-heap of visited candidates to explore: (distance, node_id)
        candidates = [(v_dist(query, self.vectors[ep]), ep) for ep in enter_points]
        heapq.heapify(candidates)

        # Max-heap of top dynamic results: (-distance, node_id)
        w_results = [(-dist, ep) for dist, ep in candidates]
        heapq.heapify(w_results)

        visited: Set[int] = set(enter_points)

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            furthest_dist = -w_results[0][0]

            if c_dist > furthest_dist:
                break

            neighbors = self.layers[level].get(c_id, set())
            for n_id in neighbors:
                if n_id not in visited:
                    visited.add(n_id)
                    n_dist = v_dist(query, self.vectors[n_id])
                    furthest_dist = -w_results[0][0]

                    if n_dist < furthest_dist or len(w_results) < ef:
                        heapq.heappush(candidates, (n_dist, n_id))
                        heapq.heappush(w_results, (-n_dist, n_id))

                        if len(w_results) > ef:
                            heapq.heappop(w_results)

        # Return sorted list of (distance, node_id)
        return sorted([(-dist, nid) for dist, nid in w_results])

    def insert(self, node_id: int, vector: List[float]) -> None:
        """Inserts a vector into the HNSW hierarchical graph."""
        self.vectors[node_id] = vector
        node_level = self._random_level()

        # Ensure layers list is deep enough
        while len(self.layers) <= max(node_level, self.max_level):
            self.layers.append({})

        # Initialize node set across all levels it participates in
        for lvl in range(node_level + 1):
            self.layers[lvl].setdefault(node_id, set())

        # First node in index acts as initial global entry point
        if self.enter_point is None:
            self.enter_point = node_id
            self.max_level = node_level
            return

        curr_ep = [self.enter_point]
        curr_max = self.max_level

        # Step 1: Greedy top-down routing across upper layers (ef = 1)
        for lvl in range(curr_max, node_level, -1):
            results = self._search_layer(vector, curr_ep, ef=1, level=lvl)
            curr_ep = [results[0][1]]

        # Step 2: Multi-layer nearest neighbor connecting from min(node_level, curr_max) down to 0
        for lvl in range(min(node_level, curr_max), -1, -1):
            max_conn = self.m0 if lvl == 0 else self.m
            neighbors_candidates = self._search_layer(vector, curr_ep, ef=self.ef_construction, level=lvl)

            # Filter candidates: only keep neighbors actually present in this layer
            valid_candidates = [
                nid for _, nid in neighbors_candidates 
                if nid in self.layers[lvl] and nid != node_id
            ]

            selected_neighbors = valid_candidates[:max_conn]
            self.layers[lvl][node_id] = set(selected_neighbors)

            for neighbor_id in selected_neighbors:
                self.layers[lvl].setdefault(neighbor_id, set()).add(node_id)
                
                # Prune neighbor connections if degree breaches max connections
                if len(self.layers[lvl][neighbor_id]) > max_conn:
                    sorted_conns = sorted(
                        self.layers[lvl][neighbor_id],
                        key=lambda n: self._l2_distance(self.vectors[neighbor_id], self.vectors[n])
                    )
                    self.layers[lvl][neighbor_id] = set(sorted_conns[:max_conn])

            curr_ep = [nid for _, nid in neighbors_candidates]

        # Update global entry point if new node was assigned a higher top level
        if node_level > self.max_level:
            self.max_level = node_level
            self.enter_point = node_id

    def search_knn(self, query: List[float], k: int = 3, ef: int = 16) -> List[Tuple[int, float]]:
        """Locates the K Approximate Nearest Neighbors for a query vector."""
        if self.enter_point is None:
            return []

        curr_ep = [self.enter_point]
        # Fast 1-hop greedy routing on upper levels
        for lvl in range(self.max_level, 0, -1):
            results = self._search_layer(query, curr_ep, ef=1, level=lvl)
            curr_ep = [results[0][1]]

        # Beam search across dense Layer 0
        candidates = self._search_layer(query, curr_ep, ef=max(ef, k), level=0)
        return [(nid, dist) for dist, nid in candidates[:k]]


if __name__ == "__main__":
    print("--- Initializing HNSW Vector Similarity Search Engine ---\n")

    # 4-dimensional semantic embedding space simulation
    hnsw = HNSWIndex(dim=4, m=3, m0=6, ef_construction=16)

    # Ingest document embeddings
    doc_vectors = {
        1: [0.10, 0.85, 0.12, 0.05],  # Topic: Database Internals
        2: [0.12, 0.80, 0.15, 0.08],  # Topic: Distributed Storage
        3: [0.88, 0.05, 0.90, 0.75],  # Topic: Quantum Computing
        4: [0.85, 0.10, 0.92, 0.80],  # Topic: Quantum Physics
        5: [0.15, 0.78, 0.20, 0.04]   # Topic: Consensus Protocols
    }

    print(f"[INDEXING] Ingesting {len(doc_vectors)} dense vectors into HNSW graph...")
    for doc_id, vec in doc_vectors.items():
        hnsw.insert(doc_id, vec)

    print(f"  Graph Max Height: Layer {hnsw.max_level} | Entry Point Node: #{hnsw.enter_point}")
    print("-" * 65)

    # Query Vector close to Database & Distributed Systems (cluster 1, 2, 5)
    query_vector = [0.11, 0.82, 0.14, 0.06]
    print(f"[QUERY VECTOR] Searching k-NN for: {query_vector}\n")

    top_matches = hnsw.search_knn(query_vector, k=3, ef=8)

    print("[APPROXIMATE NEAREST NEIGHBORS]")
    for rank, (doc_id, dist) in enumerate(top_matches, 1):
        print(f"  #{rank} Doc #{doc_id} -> L2 Distance: {dist:.4f} | Vector: {hnsw.vectors[doc_id]}")

# Output :
# --- Initializing HNSW Vector Similarity Search Engine ---

# [INDEXING] Ingesting 5 dense vectors into HNSW graph...
#   Graph Max Height: Layer 2 | Entry Point Node: #2
# -----------------------------------------------------------------
# [QUERY VECTOR] Searching k-NN for: [0.11, 0.82, 0.14, 0.06]

# [APPROXIMATE NEAREST NEIGHBORS]
#   #1 Doc #2 -> L2 Distance: 0.0316 | Vector: [0.12, 0.8, 0.15, 0.08]
#   #2 Doc #1 -> L2 Distance: 0.0387 | Vector: [0.1, 0.85, 0.12, 0.05]
#   #3 Doc #5 -> L2 Distance: 0.0849 | Vector: [0.15, 0.78, 0.2, 0.04]
