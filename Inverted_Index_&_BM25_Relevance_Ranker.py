import math
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

class BM25SearchEngine:
    """An in-memory Inverted Index supporting BM25 document relevance ranking."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term frequency saturation parameter (typically between 1.2 and 2.0).
            b: Document length normalization parameter (0.0 = no normalization, 1.0 = full scaling).
        """
        self.k1 = k1
        self.b = b
        
        # Inverted Index mapping: term -> {doc_id: term_frequency}
        self.inverted_index: Dict[str, Dict[int, int]] = defaultdict(dict)
        
        # Corpus statistics
        self.doc_lengths: Dict[int, int] = {}
        self.doc_store: Dict[int, str] = {}
        self.num_docs: int = 0
        self.avg_doc_len: float = 0.0

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Lowercases and extracts alphanumeric word tokens."""
        return re.findall(r"\b[a-z0-9]+\b", text.lower())

    def add_document(self, doc_id: int, content: str) -> None:
        """Indexes a single text document into the inverted index."""
        tokens = self._tokenize(content)
        self.doc_lengths[doc_id] = len(tokens)
        self.doc_store[doc_id] = content
        
        # Compute term frequencies for the document
        term_counts = Counter(tokens)
        for term, freq in term_counts.items():
            self.inverted_index[term][doc_id] = freq

        self.num_docs += 1
        self.avg_doc_len = sum(self.doc_lengths.values()) / self.num_docs

    def _compute_idf(self, term: str) -> float:
        """Computes Robertson-Spärck Jones Inverse Document Frequency (IDF)."""
        doc_freq = len(self.inverted_index.get(term, {}))
        if doc_freq == 0:
            return 0.0
        # Standard Lucene/BM25 IDF formula with smoothing
        return math.log(1.0 + (self.num_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def search(self, query: str, top_n: int = 5) -> List[Tuple[int, float, str]]:
        """Scores documents against a search query using Okapi BM25.
        
        Returns:
            List of tuples: (doc_id, bm25_score, document_text)
        """
        query_terms = self._tokenize(query)
        scores: Dict[int, float] = defaultdict(float)

        for term in query_terms:
            if term not in self.inverted_index:
                continue

            idf = self._compute_idf(term)
            postings = self.inverted_index[term]

            for doc_id, tf in postings.items():
                doc_len = self.doc_lengths[doc_id]
                
                # BM25 Term Frequency Saturation & Length Normalization
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                
                term_score = idf * (numerator / denominator)
                scores[doc_id] += term_score

        # Sort candidate documents by descending score
        ranked_results = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]
        return [(doc_id, score, self.doc_store[doc_id]) for doc_id, score in ranked_results]


if __name__ == "__main__":
    print("--- Initializing BM25 Search & Indexing Engine ---\n")

    engine = BM25SearchEngine(k1=1.5, b=0.75)

    # Document corpus
    documents = {
        1: "Distributed consensus algorithms like Raft and Paxos ensure data consistency in clusters.",
        2: "Consistent hashing distributes cache keys across server nodes with minimal re-mapping.",
        3: "Write ahead logging and LSM-trees optimize database disk write throughput and durability.",
        4: "Raft consensus decomposes state machine replication into leader election and log synchronization.",
        5: "Skip lists provide logarithmic search and ordered range scanning for in-memory databases."
    }

    print(f"[INDEXING] Ingesting {len(documents)} system documents into Inverted Index...")
    for doc_id, text in documents.items():
        engine.add_document(doc_id, text)

    print(f"  Total Unique Indexed Terms : {len(engine.inverted_index)}")
    print(f"  Average Document Length    : {engine.avg_doc_len:.2f} tokens")
    print("-" * 65)

    # Search Query
    query = "Raft consensus replication"
    print(f"[SEARCH QUERY] '{query}'\n")

    results = engine.search(query, top_n=3)

    print("[RANKED SEARCH RESULTS]")
    for rank, (doc_id, score, text) in enumerate(results, 1):
        print(f"  #{rank} [Score: {score:.4f}] Doc {doc_id}: \"{text}\"")
