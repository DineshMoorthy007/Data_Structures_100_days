from typing import Dict, List

class State:
    """Represents a state (equivalence class of end positions) in the Suffix Automaton."""
    def __init__(self, length: int = 0, link: int = -1):
        self.len = length                      # Length of the longest substring in this equivalence class
        self.link = link                      # Suffix link to the longest proper suffix state
        self.transitions: Dict[str, int] = {}  # Transition edges: char -> target_state_index


class SuffixAutomaton:
    """Online construction of a Suffix Automaton in linear O(N) time and space."""
    
    def __init__(self, text: str = ""):
        # Initial root state (representing the empty string epsilon)
        self.states: List[State] = [State(length=0, link=-1)]
        self.last: int = 0  # Index of the state corresponding to the entire string so far
        
        for char in text:
            self.extend(char)

    def extend(self, char: str) -> None:
        """Online step: appends a single character to the indexed text in O(1) amortized time."""
        curr = len(self.states)
        self.states.append(State(length=self.states[self.last].len + 1))
        
        # Traverse suffix links from 'last' adding transitions for 'char'
        p = self.last
        while p != -1 and char not in self.states[p].transitions:
            self.states[p].transitions[char] = curr
            p = self.states[p].link

        if p == -1:
            # Reached root without finding existing transition
            self.states[curr].link = 0
        else:
            q = self.states[p].transitions[char]
            if self.states[p].len + 1 == self.states[q].len:
                # Continuous transition: link directly to state q
                self.states[curr].link = q
            else:
                # Non-continuous transition: clone state q to split equivalence classes
                clone = len(self.states)
                cloned_state = State(
                    length=self.states[p].len + 1,
                    link=self.states[q].link
                )
                cloned_state.transitions = self.states[q].transitions.copy()
                self.states.append(cloned_state)

                # Re-route suffix transitions pointing to q to clone instead
                while p != -1 and self.states[p].transitions.get(char) == q:
                    self.states[p].transitions[char] = clone
                    p = self.states[p].link

                # Update links
                self.states[q].link = clone
                self.states[curr].link = clone

        self.last = curr

    def contains(self, pattern: str) -> bool:
        """Checks if pattern is a valid substring in strictly O(|pattern|) time."""
        curr = 0
        for char in pattern:
            if char not in self.states[curr].transitions:
                return False
            curr = self.states[curr].transitions[char]
        return True

    def count_distinct_substrings(self) -> int:
        """Calculates total distinct substrings in O(|states|) = O(N) linear time."""
        # Every state u contributes (len(u) - len(link(u))) distinct substrings
        total = 0
        for u in range(1, len(self.states)):
            link_len = self.states[self.states[u].link].len if self.states[u].link != -1 else 0
            total += self.states[u].len - link_len
        return total


if __name__ == "__main__":
    print("--- Initializing Linear-Time Suffix Automaton Engine ---\n")

    corpus = "banana"
    sam = SuffixAutomaton(corpus)

    print(f"[INDEXED TEXT] '{corpus}'")
    print(f"  Total DFA States Generated: {len(sam.states)} (Guaranteed <= 2N - 1)")
    print(f"  Distinct Substrings Count : {sam.count_distinct_substrings()}")
    print("-" * 65)

    # 1. Instantaneous O(|P|) Substring Matching
    print("\n[SUBSTRING QUERIES]")
    test_patterns = ["an", "nan", "ban", "ana", "apple", "band"]
    for pat in test_patterns:
        is_present = sam.contains(pat)
        status = "FOUND" if is_present else "NOT FOUND"
        print(f"  Query '{pat:<6}' ---> {status}")

    # 2. Dynamic Online Extension
    print("\n[DYNAMIC EXTENSION] Appending 's' to form 'bananas'...")
    sam.extend("s")
    print(f"  Query 'bananas' ---> {'FOUND' if sam.contains('bananas') else 'NOT FOUND'}")
    print(f"  Query 'anas'    ---> {'FOUND' if sam.contains('anas') else 'NOT FOUND'}")
    print(f"  New Distinct Substrings : {sam.count_distinct_substrings()}")

# Output :
# --- Initializing Linear-Time Suffix Automaton Engine ---

# [INDEXED TEXT] 'banana'
#   Total DFA States Generated: 10 (Guaranteed <= 2N - 1)
#   Distinct Substrings Count : 15
# -----------------------------------------------------------------

# [SUBSTRING QUERIES]
#   Query 'an    ' ---> FOUND
#   Query 'nan   ' ---> FOUND
#   Query 'ban   ' ---> FOUND
#   Query 'ana   ' ---> FOUND
#   Query 'apple ' ---> NOT FOUND
#   Query 'band  ' ---> NOT FOUND

# [DYNAMIC EXTENSION] Appending 's' to form 'bananas'...
#   Query 'bananas' ---> FOUND
#   Query 'anas'    ---> FOUND
#   New Distinct Substrings : 22
