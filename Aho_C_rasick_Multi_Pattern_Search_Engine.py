from collections import deque
from typing import Dict, List, Tuple

class AhoNode:
    """A single state node in the Aho-Corasick automaton."""
    def __init__(self):
        self.children: Dict[str, 'AhoNode'] = {}
        self.fail: 'AhoNode | None' = None      # Fallback state on mismatch
        self.output: List[str] = []             # Matching patterns ending at this state
        self.dict_link: 'AhoNode | None' = None  # Direct shortcut to the nearest ancestor with matches


class AhoCorasick:
    """Multi-pattern string matching automaton executing in linear O(N + M) time."""
    
    def __init__(self, patterns: List[str]):
        self.root = AhoNode()
        self._build_trie(patterns)
        self._build_failure_and_dict_links()

    def _build_trie(self, patterns: List[str]) -> None:
        """Constructs the underlying prefix trie for all search patterns."""
        for pattern in patterns:
            if not pattern:
                continue
            curr = self.root
            for char in pattern:
                if char not in curr.children:
                    curr.children[char] = AhoNode()
                curr = curr.children[char]
            curr.output.append(pattern)

    def _build_failure_and_dict_links(self) -> None:
        """Computes failure transitions and output links using breadth-first search (BFS)."""
        queue = deque()

        # Phase 1: Set depth-1 nodes to fail back to root
        for char, child in self.root.children.items():
            child.fail = self.root
            queue.append(child)

        # Phase 2: Traverse Trie in BFS order
        while queue:
            curr_node = queue.popleft()

            for char, child_node in curr_node.children.items():
                queue.append(child_node)

                # Trace fallback pointer to determine child's failure transition
                fallback = curr_node.fail
                while fallback is not None and char not in fallback.children:
                    fallback = fallback.fail

                # If a valid transition exists from fallback, link it; otherwise link to root
                child_node.fail = fallback.children[char] if fallback else self.root

                # Build Dictionary Link: Shortcut to nearest ancestor with non-empty output
                if child_node.fail.output:
                    child_node.dict_link = child_node.fail
                else:
                    child_node.dict_link = child_node.fail.dict_link

    def search(self, text: str) -> List[Tuple[int, str]]:
        """Scans input text and returns all matches as (end_index, pattern_string)."""
        matches: List[Tuple[int, str]] = []
        curr = self.root

        for idx, char in enumerate(text):
            # Fallback on failure transitions if the character cannot be matched
            while curr is not None and char not in curr.children:
                curr = curr.fail

            if curr is None:
                curr = self.root
                continue

            curr = curr.children[char]

            # 1. Collect direct pattern matches ending at the current state
            for pattern in curr.output:
                matches.append((idx - len(pattern) + 1, pattern))

            # 2. Traverse dictionary links to collect overlapping/embedded sub-patterns
            temp_link = curr.dict_link
            while temp_link is not None:
                for pattern in temp_link.output:
                    matches.append((idx - len(pattern) + 1, pattern))
                temp_link = temp_link.dict_link

        return matches


if __name__ == "__main__":
    print("--- Initializing Aho-Corasick Multi-Pattern Search Engine ---\n")

    # Keyword database for packet inspection / lexical scanning
    keyword_rules = ["he", "she", "his", "hers", "hero", "era"]
    engine = AhoCorasick(keyword_rules)

    sample_text = "usherssawtheheroinherapartment"
    
    print(f"[RULES CONFIGURED] Patterns : {keyword_rules}")
    print(f"[STREAMING TEXT]   Payload  : '{sample_text}'\n")

    results = engine.search(sample_text)

    print("-" * 65)
    print(f"[MATCH RESULTS] Discovered {len(results)} total occurrences:")
    for start_pos, matched_keyword in results:
        end_pos = start_pos + len(matched_keyword)
        snippet = sample_text[max(0, start_pos - 3):min(len(sample_text), end_pos + 3)]
        print(f"  Match: '{matched_keyword:<5}' at Index [{start_pos:>2}..{end_pos:>2}] | Context: '...{snippet}...'")

# Output :
# --- Initializing Aho-Corasick Multi-Pattern Search Engine ---

# [RULES CONFIGURED] Patterns : ['he', 'she', 'his', 'hers', 'hero', 'era']
# [STREAMING TEXT]   Payload  : 'usherssawtheheroinherapartment'

# -----------------------------------------------------------------
# [MATCH RESULTS] Discovered 8 total occurrences:
#   Match: 'she  ' at Index [ 1.. 4] | Context: '...usherss...'
#   Match: 'he   ' at Index [ 2.. 4] | Context: '...usherss...'
#   Match: 'hers ' at Index [ 2.. 6] | Context: '...usherssaw...'
#   Match: 'he   ' at Index [10..12] | Context: '...awtheher...'
#   Match: 'he   ' at Index [12..14] | Context: '...theheroi...'
#   Match: 'hero ' at Index [12..16] | Context: '...theheroinh...'
#   Match: 'he   ' at Index [18..20] | Context: '...oinherap...'
#   Match: 'era  ' at Index [19..22] | Context: '...inherapar...'
