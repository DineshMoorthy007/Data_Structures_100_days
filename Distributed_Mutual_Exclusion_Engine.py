import queue
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional

class MsgType(Enum):
    REQUEST = auto()
    REPLY = auto()
    RELEASE = auto()


@dataclass(order=True)
class RequestItem:
    """Represents a request in a node's local priority queue.
    
    Ordered by (logical_timestamp, node_id) to break ties deterministically.
    """
    timestamp: int
    node_id: int = field(compare=True)


@dataclass
class Message:
    msg_type: MsgType
    sender_id: int
    timestamp: int
    req_timestamp: Optional[int] = None  # Original timestamp of the resource request


class DistributedNode:
    """A distributed node contending for a shared critical section using Lamport's algorithm."""
    
    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.clock = 0
        
        # Local request queue tracking all active requests across the cluster
        self.request_queue: List[RequestItem] = []
        
        # Tracks peer replies received for current request: sender_id -> reply_received
        self.replies_received: Dict[int, bool] = {}
        self.in_critical_section = False
        self.my_active_request_ts: Optional[int] = None
        
        # Simulated network inbox
        self.inbox: queue.Queue[Message] = queue.Queue()
        self.network_mesh: Dict[int, 'DistributedNode'] = {}

    def connect(self, peer_nodes: Dict[int, 'DistributedNode']) -> None:
        """Connects node to the network mesh of all cluster peers."""
        self.network_mesh = peer_nodes

    def _tick(self) -> int:
        """Advances internal Lamport logical clock on internal event."""
        self.clock += 1
        return self.clock

    def _update_clock_on_receive(self, incoming_ts: int) -> None:
        """Lamport clock synchronization rule: max(local, received) + 1."""
        self.clock = max(self.clock, incoming_ts) + 1

    def request_critical_section(self) -> None:
        """Initiates a request to enter the critical section."""
        ts = self._tick()
        self.my_active_request_ts = ts
        self.replies_received = {peer_id: False for peer_id in self.network_mesh if peer_id != self.node_id}

        # Add own request to local queue
        req = RequestItem(timestamp=ts, node_id=self.node_id)
        self.request_queue.append(req)
        self.request_queue.sort()

        print(f"  [Node {self.node_id}] Requesting lock at Lamport TS={ts}. Broadcasting REQUEST...")
        
        # Broadcast REQUEST to all peers
        for peer_id, peer in self.network_mesh.items():
            if peer_id != self.node_id:
                peer.inbox.put(Message(MsgType.REQUEST, self.node_id, ts, req_timestamp=ts))

    def release_critical_section(self) -> None:
        """Exits critical section and broadcasts RELEASE to the cluster."""
        ts = self._tick()
        self.in_critical_section = False
        
        # Remove own request from local queue
        self.request_queue = [r for r in self.request_queue if r.node_id != self.node_id]
        self.my_active_request_ts = None
        self.replies_received.clear()

        print(f"  [Node {self.node_id}] Exiting CS. Broadcasting RELEASE at TS={ts}...")

        # Broadcast RELEASE to all peers
        for peer_id, peer in self.network_mesh.items():
            if peer_id != self.node_id:
                peer.inbox.put(Message(MsgType.RELEASE, self.node_id, ts))

    def process_incoming_messages(self) -> None:
        """Drains network inbox and evaluates condition to enter critical section."""
        while not self.inbox.empty():
            msg = self.inbox.get_nowait()
            self._update_clock_on_receive(msg.timestamp)

            if msg.msg_type == MsgType.REQUEST:
                # Add peer's request to local sorted queue
                self.request_queue.append(RequestItem(msg.req_timestamp, msg.sender_id))
                self.request_queue.sort()
                
                # Reply immediately with current logical clock
                reply_ts = self._tick()
                peer = self.network_mesh[msg.sender_id]
                peer.inbox.put(Message(MsgType.REPLY, self.node_id, reply_ts))

            elif msg.msg_type == MsgType.REPLY:
                self.replies_received[msg.sender_id] = True

            elif msg.msg_type == MsgType.RELEASE:
                # Remove sender's request from local queue
                self.request_queue = [r for r in self.request_queue if r.node_id != msg.sender_id]

        # Evaluate if this node can safely enter the Critical Section
        self._check_critical_section_entry()

    def _check_critical_section_entry(self) -> None:
        """Node can enter CS if and only if:
        1. Its own request is at the head of its local queue (earliest timestamp).
        2. It has received a message from every other node dated later than its request.
        """
        if self.my_active_request_ts is None or self.in_critical_section:
            return

        is_head = len(self.request_queue) > 0 and self.request_queue[0].node_id == self.node_id
        all_replied = all(self.replies_received.values())

        if is_head and all_replied:
            self.in_critical_section = True
            print(f"\n  >>> [GRANTED] Node {self.node_id} ENTERED Critical Section! (TS={self.my_active_request_ts}) <<<\n")


# --- Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing Lamport Distributed Mutual Exclusion Engine ---\n")

    TOTAL_NODES = 3
    nodes = {i: DistributedNode(node_id=i, total_nodes=TOTAL_NODES) for i in range(1, TOTAL_NODES + 1)}
    for node in nodes.values():
        node.connect(nodes)

    print("[STEP 1: Concurrent Lock Contention]")
    # Node 1 and Node 2 simultaneously contest the critical section
    nodes[1].request_critical_section()
    nodes[2].request_critical_section()

    print("\n[STEP 2: Network Message Propagation & Processing]")
    # Deliver messages until someone gains lock entry
    for _ in range(3):
        for node in nodes.values():
            node.process_incoming_messages()

    # Verify Node 1 is currently in Critical Section
    print(f"Lock Holder Check -> Node 1 in CS: {nodes[1].in_critical_section} | Node 2 in CS: {nodes[2].in_critical_section}")

    print("\n[STEP 3: Node 1 Releases Lock -> Node 2 Handover]")
    nodes[1].release_critical_section()

    # Drain messages to propagate release to Node 2
    for _ in range(3):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"Post-Release Check -> Node 1 in CS: {nodes[1].in_critical_section} | Node 2 in CS: {nodes[2].in_critical_section}")
    print("-" * 65)
    print("[RESULT] Mutual exclusion guaranteed across distributed actors without central coordinator!")

# Output :
# --- Initializing Lamport Distributed Mutual Exclusion Engine ---

# [STEP 1: Concurrent Lock Contention]
#   [Node 1] Requesting lock at Lamport TS=1. Broadcasting REQUEST...
#   [Node 2] Requesting lock at Lamport TS=1. Broadcasting REQUEST...

# [STEP 2: Network Message Propagation & Processing]

#   >>> [GRANTED] Node 1 ENTERED Critical Section! (TS=1) <<<

# Lock Holder Check -> Node 1 in CS: True | Node 2 in CS: False

# [STEP 3: Node 1 Releases Lock -> Node 2 Handover]
#   [Node 1] Exiting CS. Broadcasting RELEASE at TS=6...

#   >>> [GRANTED] Node 2 ENTERED Critical Section! (TS=1) <<<

# Post-Release Check -> Node 1 in CS: False | Node 2 in CS: True
# -----------------------------------------------------------------
# [RESULT] Mutual exclusion guaranteed across distributed actors without central coordinator!
