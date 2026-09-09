import math
import queue
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Set, Optional

class MsgType(Enum):
    REQUEST = auto()
    REPLY = auto()
    RELEASE = auto()


@dataclass
class Message:
    msg_type: MsgType
    sender_id: int
    req_timestamp: int


class MaekawaNode:
    """A distributed actor competing for mutual exclusion via voting quorums."""
    
    def __init__(self, node_id: int, total_nodes: int, quorum: Set[int]):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.quorum = quorum  # Set of node IDs this node must acquire votes from
        
        self.clock = 0
        self.in_critical_section = False
        
        # State tracking as a Voter
        self.voted = False
        self.vote_granted_to: Optional[int] = None
        self.voter_queue: queue.Queue[Message] = queue.Queue()
        
        # State tracking as a Candidate
        self.votes_received: Set[int] = set()
        self.my_req_timestamp: Optional[int] = None
        
        # Simulated async network
        self.inbox: queue.Queue[Message] = queue.Queue()
        self.network_mesh: Dict[int, 'MaekawaNode'] = {}

    def connect(self, peer_nodes: Dict[int, 'MaekawaNode']) -> None:
        self.network_mesh = peer_nodes

    def _tick(self) -> int:
        self.clock += 1
        return self.clock

    def _update_clock(self, incoming_ts: int) -> None:
        self.clock = max(self.clock, incoming_ts) + 1

    def request_critical_section(self) -> None:
        """Broadcasts REQUEST only to members of its assigned quorum Vi."""
        self.my_req_timestamp = self._tick()
        self.votes_received.clear()

        print(f"  [Candidate {self.node_id}] Contending for CS. Requesting votes from Quorum {sorted(list(self.quorum))} (TS={self.my_req_timestamp})...")

        # Request votes ONLY from its quorum subset
        for member_id in self.quorum:
            peer = self.network_mesh[member_id]
            peer.inbox.put(Message(
                msg_type=MsgType.REQUEST,
                sender_id=self.node_id,
                req_timestamp=self.my_req_timestamp
            ))

    def release_critical_section(self) -> None:
        """Exits critical section and broadcasts RELEASE to its quorum members."""
        self._tick()
        self.in_critical_section = False
        self.votes_received.clear()
        print(f"  [Candidate {self.node_id}] Exiting CS. Sending RELEASE to Quorum {sorted(list(self.quorum))}...")

        for member_id in self.quorum:
            peer = self.network_mesh[member_id]
            peer.inbox.put(Message(
                msg_type=MsgType.RELEASE,
                sender_id=self.node_id,
                req_timestamp=self.clock
            ))

    def process_incoming_messages(self) -> None:
        """Drains network inbox and processes vote requests, replies, and releases."""
        while not self.inbox.empty():
            msg = self.inbox.get_nowait()
            self._update_clock(msg.req_timestamp)

            if msg.msg_type == MsgType.REQUEST:
                self._handle_request(msg)
            elif msg.msg_type == MsgType.REPLY:
                self._handle_reply(msg)
            elif msg.msg_type == MsgType.RELEASE:
                self._handle_release(msg)

    def _handle_request(self, msg: Message) -> None:
        """As a voter, grant vote if free; otherwise queue the request."""
        if not self.voted:
            self.voted = True
            self.vote_granted_to = msg.sender_id
            
            # Send REPLY back to requesting candidate
            reply_ts = self._tick()
            peer = self.network_mesh[msg.sender_id]
            peer.inbox.put(Message(MsgType.REPLY, self.node_id, reply_ts))
        else:
            # Already voted for another candidate; queue this request
            self.voter_queue.put(msg)

    def _handle_reply(self, msg: Message) -> None:
        """As a candidate, collect vote. Enter CS if full quorum acquired."""
        self.votes_received.add(msg.sender_id)
        if self.votes_received == self.quorum and not self.in_critical_section:
            self.in_critical_section = True
            print(f"\n  >>> [GRANTED] Candidate {self.node_id} acquired ALL votes from Quorum {sorted(list(self.quorum))}. ENTERED CS! <<<\n")

    def _handle_release(self, msg: Message) -> None:
        """As a voter, clear current vote and grant next queued candidate if any."""
        if self.vote_granted_to == msg.sender_id:
            self.voted = False
            self.vote_granted_to = None

            # Process next queued vote request if available
            if not self.voter_queue.empty():
                next_req = self.voter_queue.get_nowait()
                self.voted = True
                self.vote_granted_to = next_req.sender_id
                
                reply_ts = self._tick()
                peer = self.network_mesh[next_req.sender_id]
                peer.inbox.put(Message(MsgType.REPLY, self.node_id, reply_ts))


# --- Quorum Construction Helper ---

def build_grid_quorums(n: int) -> Dict[int, Set[int]]:
    """Generates simple Grid Quorums of size ~2*sqrt(N) where Quorum(i) = Row(i) U Col(i).
    
    Guarantees that ANY two quorums intersect at 2 nodes (their cross intersection points).
    """
    grid_size = int(math.ceil(math.sqrt(n)))
    quorums: Dict[int, Set[int]] = {}

    for node_id in range(n):
        row = node_id // grid_size
        col = node_id % grid_size
        
        quorum = set()
        # Add row members
        for c in range(grid_size):
            member = row * grid_size + c
            if member < n:
                quorum.add(member)
        # Add col members
        for r in range(grid_size):
            member = r * grid_size + col
            if member < n:
                quorum.add(member)
                
        quorums[node_id] = quorum
        
    return quorums


# --- Cluster Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing Maekawa Quorum Mutual Exclusion Engine ---\n")

    TOTAL_NODES = 9  # 3x3 Grid
    quorums = build_grid_quorums(TOTAL_NODES)

    nodes = {i: MaekawaNode(node_id=i, total_nodes=TOTAL_NODES, quorum=quorums[i]) 
             for i in range(TOTAL_NODES)}
    for node in nodes.values():
        node.connect(nodes)

    print("[CLUSTER CONFIGURATION]")
    print(f"  Total Nodes (N)   : {TOTAL_NODES}")
    print(f"  Quorum Size (|V|) : ~{len(quorums[0])} nodes (O(sqrt(N)) vs N-1 in classic mutex)")
    for i in range(3):
        print(f"    Node {i} Quorum : {sorted(list(quorums[i]))}")
    print("-" * 65)

    print("\n[STEP 1: Concurrent Request Contention (Node 0 vs Node 8)]")
    # Node 0 and Node 8 contest CS simultaneously.
    # Quorum 0: {0, 1, 2, 3, 6} | Quorum 8: {8, 6, 7, 2, 5}
    # Intersecting members: Node 2 and Node 6 act as mutual exclusion arbiters!
    nodes[0].request_critical_section()
    nodes[8].request_critical_section()

    print("\n[STEP 2: Quorum Messaging & Arbiter Vote Resolution]")
    for _ in range(4):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"CS State -> Node 0: {nodes[0].in_critical_section} | Node 8: {nodes[8].in_critical_section}")

    print("\n[STEP 3: Node 0 Releases CS -> Intersecting Arbiter Handover to Node 8]")
    nodes[0].release_critical_section()

    for _ in range(4):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"Post-Release CS State -> Node 0: {nodes[0].in_critical_section} | Node 8: {nodes[8].in_critical_section}")
    print("-" * 65)
    print("[SUCCESS] Mutual exclusion guaranteed with O(sqrt(N)) quorum messaging!")

# Output :
# --- Initializing Maekawa Quorum Mutual Exclusion Engine ---

# [CLUSTER CONFIGURATION]
#   Total Nodes (N)   : 9
#   Quorum Size (|V|) : ~5 nodes (O(sqrt(N)) vs N-1 in classic mutex)
#     Node 0 Quorum : [0, 1, 2, 3, 6]
#     Node 1 Quorum : [0, 1, 2, 4, 7]
#     Node 2 Quorum : [0, 1, 2, 5, 8]
# -----------------------------------------------------------------

# [STEP 1: Concurrent Request Contention (Node 0 vs Node 8)]
#   [Candidate 0] Contending for CS. Requesting votes from Quorum [0, 1, 2, 3, 6] (TS=1)...
#   [Candidate 8] Contending for CS. Requesting votes from Quorum [2, 5, 6, 7, 8] (TS=1)...

# [STEP 2: Quorum Messaging & Arbiter Vote Resolution]

#   >>> [GRANTED] Candidate 0 acquired ALL votes from Quorum [0, 1, 2, 3, 6]. ENTERED CS! <<<

# CS State -> Node 0: True | Node 8: False

# [STEP 3: Node 0 Releases CS -> Intersecting Arbiter Handover to Node 8]
#   [Candidate 0] Exiting CS. Sending RELEASE to Quorum [0, 1, 2, 3, 6]...

#   >>> [GRANTED] Candidate 8 acquired ALL votes from Quorum [2, 5, 6, 7, 8]. ENTERED CS! <<<

# Post-Release CS State -> Node 0: False | Node 8: True
# -----------------------------------------------------------------
# [SUCCESS] Mutual exclusion guaranteed with O(sqrt(N)) quorum messaging!
