import queue
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Token:
    """The unique cluster-wide privilege token."""
    # LN[i]: Sequence number of the most recently executed request by node i
    ln: List[int]
    # FIFO queue of node IDs waiting to acquire the token
    queue: deque


@dataclass
class RequestMessage:
    sender_id: int
    sequence_num: int


class SuzukiKasamiNode:
    """A distributed node contending for mutual exclusion using the Suzuki-Kasami token algorithm."""
    
    def __init__(self, node_id: int, total_nodes: int, initial_token_holder: bool = False):
        self.node_id = node_id
        self.total_nodes = total_nodes
        
        # RN[j]: The highest sequence number received so far in requests from node j
        self.rn = [0] * total_nodes
        
        self.has_token = initial_token_holder
        self.in_critical_section = False
        self.waiting_for_token = False
        
        # Token reference (None if node doesn't currently hold it)
        self.token: Optional[Token] = None
        if initial_token_holder:
            self.token = Token(ln=[0] * total_nodes, queue=deque())

        # Simulated async network buffers
        self.req_inbox: queue.Queue[RequestMessage] = queue.Queue()
        self.token_inbox: queue.Queue[Token] = queue.Queue()
        self.network_mesh: Dict[int, 'SuzukiKasamiNode'] = {}

    def connect(self, peer_nodes: Dict[int, 'SuzukiKasamiNode']) -> None:
        self.network_mesh = peer_nodes

    def request_critical_section(self) -> None:
        """Contends for the critical section."""
        if self.has_token:
            self.in_critical_section = True
            print(f"  >>> [GRANTED (0 MSG)] Node {self.node_id} already holds the token. ENTERED CS! <<<")
            return

        self.waiting_for_token = True
        self.rn[self.node_id] += 1
        seq = self.rn[self.node_id]

        print(f"  [Node {self.node_id}] Contending for CS. Broadcasting REQUEST(seq={seq})...")

        # Broadcast REQUEST to all other nodes in the network
        for peer_id, peer in self.network_mesh.items():
            if peer_id != self.node_id:
                peer.req_inbox.put(RequestMessage(sender_id=self.node_id, sequence_num=seq))

    def release_critical_section(self) -> None:
        """Exits critical section, updates token state LN, and passes token if candidates are queued."""
        if not self.in_critical_section or self.token is None:
            return

        self.in_critical_section = False
        # Record that node's current request sequence number has finished execution
        self.token.ln[self.node_id] = self.rn[self.node_id]

        # Scan for peers with unfulfilled requests not yet queued: RN[j] == LN[j] + 1
        for j in range(self.total_nodes):
            if j not in self.token.queue and j != self.node_id:
                if self.rn[j] == self.token.ln[j] + 1:
                    self.token.queue.append(j)

        print(f"  [Node {self.node_id}] Exited CS. Token LN={self.token.ln}, Queued Peers={list(self.token.queue)}")

        # If queue contains waiting nodes, pop the first and transfer the token directly
        if self.token.queue:
            next_node_id = self.token.queue.popleft()
            self._transfer_token_to(next_node_id)

    def _transfer_token_to(self, target_id: int) -> None:
        """Direct point-to-point transfer of the token to target node."""
        transferred_token = self.token
        self.token = None
        self.has_token = False
        print(f"  [TOKEN TRANSFER] Node {self.node_id} --> Node {target_id}")
        self.network_mesh[target_id].token_inbox.put(transferred_token)

    def process_incoming_messages(self) -> None:
        """Drains incoming request broadcasts and incoming token arrivals."""
        # 1. Process received REQUEST messages
        while not self.req_inbox.empty():
            msg = self.req_inbox.get_nowait()
            # Monotonically update highest seen sequence number
            self.rn[msg.sender_id] = max(self.rn[msg.sender_id], msg.sequence_num)

            # If this node holds the token and is NOT in the CS, check if this request is fresh
            if self.has_token and not self.in_critical_section and self.token is not None:
                if self.rn[msg.sender_id] == self.token.ln[msg.sender_id] + 1:
                    self._transfer_token_to(msg.sender_id)

        # 2. Process token arrival
        if not self.token_inbox.empty():
            self.token = self.token_inbox.get_nowait()
            self.has_token = True
            self.waiting_for_token = False
            self.in_critical_section = True
            print(f"\n  >>> [GRANTED (TOKEN ARRIVED)] Node {self.node_id} received token. ENTERED CS! <<<\n")


# --- Cluster Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing Suzuki-Kasami Token Mutual Exclusion Engine ---\n")

    TOTAL_NODES = 3
    # Node 0 initially holds the cluster token
    nodes = {i: SuzukiKasamiNode(node_id=i, total_nodes=TOTAL_NODES, initial_token_holder=(i == 0)) 
             for i in range(TOTAL_NODES)}
    for node in nodes.values():
        node.connect(nodes)

    print("[STEP 1: Zero-Message Fast Path for Token Holder]")
    nodes[0].request_critical_section()
    nodes[0].release_critical_section()
    print("-" * 65)

    print("\n[STEP 2: Concurrent Contention from Non-Holders]")
    # Node 1 and Node 2 simultaneously contest the critical section
    nodes[1].request_critical_section()
    nodes[2].request_critical_section()

    print("\n[STEP 3: Message Routing & Token Dispatch from Node 0]")
    # Deliver request messages to Node 0 and peers
    for _ in range(3):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"CS State -> Node 0: {nodes[0].in_critical_section} | Node 1: {nodes[1].in_critical_section} | Node 2: {nodes[2].in_critical_section}")

    print("\n[STEP 4: Node 1 Exits & Forwards Token to Queued Node 2]")
    nodes[1].release_critical_section()

    # Deliver the token handover from Node 1 to Node 2
    for _ in range(3):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"Post-Handover CS State -> Node 1: {nodes[1].in_critical_section} | Node 2: {nodes[2].in_critical_section}")
    print("-" * 65)
    print("[SUCCESS] Mutual exclusion achieved with 0 messages on hits, bounded to N messages on misses!")

# Output :
# --- Initializing Suzuki-Kasami Token Mutual Exclusion Engine ---

# [STEP 1: Zero-Message Fast Path for Token Holder]
#   >>> [GRANTED (0 MSG)] Node 0 already holds the token. ENTERED CS! <<<
#   [Node 0] Exited CS. Token LN=[0, 0, 0], Queued Peers=[]
# -----------------------------------------------------------------

# [STEP 2: Concurrent Contention from Non-Holders]
#   [Node 1] Contending for CS. Broadcasting REQUEST(seq=1)...
#   [Node 2] Contending for CS. Broadcasting REQUEST(seq=1)...

# [STEP 3: Message Routing & Token Dispatch from Node 0]
#   [TOKEN TRANSFER] Node 0 --> Node 1

#   >>> [GRANTED (TOKEN ARRIVED)] Node 1 received token. ENTERED CS! <<<

# CS State -> Node 0: False | Node 1: True | Node 2: False

# [STEP 4: Node 1 Exits & Forwards Token to Queued Node 2]
#   [Node 1] Exited CS. Token LN=[0, 1, 0], Queued Peers=[2]
#   [TOKEN TRANSFER] Node 1 --> Node 2

#   >>> [GRANTED (TOKEN ARRIVED)] Node 2 received token. ENTERED CS! <<<

# Post-Handover CS State -> Node 1: False | Node 2: True
# -----------------------------------------------------------------
# [SUCCESS] Mutual exclusion achieved with 0 messages on hits, bounded to N messages on misses!
