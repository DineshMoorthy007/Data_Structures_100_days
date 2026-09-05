import queue
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional

class NodeState(Enum):
    IDLE = auto()      # Not interested in the critical section
    WANTED = auto()    # Actively requesting the critical section
    HELD = auto()      # Currently executing inside the critical section


class MsgType(Enum):
    REQUEST = auto()
    REPLY = auto()


@dataclass
class Message:
    msg_type: MsgType
    sender_id: int
    timestamp: int
    req_timestamp: Optional[int] = None


class RicartAgrawalaNode:
    """A distributed actor competing for a shared critical section with deferred replies."""
    
    def __init__(self, node_id: int, total_nodes: int):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.clock = 0
        
        self.state = NodeState.IDLE
        self.req_timestamp = 0
        
        # Tracks nodes whose replies are deferred until this node exits the CS
        self.deferred_replies: List[int] = []
        
        # Outstanding replies needed to enter CS
        self.replies_needed: int = 0
        
        # Network simulation
        self.inbox: queue.Queue[Message] = queue.Queue()
        self.network_mesh: Dict[int, 'RicartAgrawalaNode'] = {}

    def connect(self, peer_nodes: Dict[int, 'RicartAgrawalaNode']) -> None:
        self.network_mesh = peer_nodes

    def _tick(self) -> int:
        self.clock += 1
        return self.clock

    def _update_clock(self, incoming_ts: int) -> None:
        self.clock = max(self.clock, incoming_ts) + 1

    def request_critical_section(self) -> None:
        """Broadcasts REQUEST to all peers and sets state to WANTED."""
        self.state = NodeState.WANTED
        self.req_timestamp = self._tick()
        self.replies_needed = self.total_nodes - 1
        self.deferred_replies.clear()

        print(f"  [Node {self.node_id}] WANTED CS with Lamport TS={self.req_timestamp}. Broadcasting REQUEST...")

        if self.replies_needed == 0:
            self._enter_critical_section()
            return

        for peer_id, peer in self.network_mesh.items():
            if peer_id != self.node_id:
                peer.inbox.put(Message(
                    msg_type=MsgType.REQUEST,
                    sender_id=self.node_id,
                    timestamp=self.clock,
                    req_timestamp=self.req_timestamp
                ))

    def release_critical_section(self) -> None:
        """Exits critical section and immediately flushes all deferred replies."""
        self._tick()
        self.state = NodeState.IDLE
        print(f"  [Node {self.node_id}] Exiting CS. Flushing {len(self.deferred_replies)} deferred replies...")

        # Flush all deferred replies to waiting peers
        for peer_id in self.deferred_replies:
            reply_ts = self._tick()
            peer = self.network_mesh[peer_id]
            peer.inbox.put(Message(
                msg_type=MsgType.REPLY,
                sender_id=self.node_id,
                timestamp=reply_ts
            ))

        self.deferred_replies.clear()

    def process_incoming_messages(self) -> None:
        """Processes messages currently waiting in the incoming network queue."""
        while not self.inbox.empty():
            msg = self.inbox.get_nowait()
            self._update_clock(msg.timestamp)

            if msg.msg_type == MsgType.REQUEST:
                self._handle_request(msg)
            elif msg.msg_type == MsgType.REPLY:
                self._handle_reply(msg)

    def _handle_request(self, msg: Message) -> None:
        incoming_ts = msg.req_timestamp if msg.req_timestamp is not None else msg.timestamp
        sender_id = msg.sender_id

        # Determine priority: strictly lower (timestamp, node_id) wins
        our_priority = (self.req_timestamp, self.node_id)
        their_priority = (incoming_ts, sender_id)

        # Defer reply if we currently hold the lock OR if we want it with higher priority
        defer = (self.state == NodeState.HELD) or (
            self.state == NodeState.WANTED and our_priority < their_priority
        )

        if defer:
            self.deferred_replies.append(sender_id)
            print(f"    [Node {self.node_id}] Deferring REPLY to Node {sender_id} (Local priority higher).")
        else:
            # Grant permission immediately
            reply_ts = self._tick()
            peer = self.network_mesh[sender_id]
            peer.inbox.put(Message(
                msg_type=MsgType.REPLY,
                sender_id=self.node_id,
                timestamp=reply_ts
            ))

    def _handle_reply(self, msg: Message) -> None:
        if self.state == NodeState.WANTED:
            self.replies_needed -= 1
            if self.replies_needed == 0:
                self._enter_critical_section()

    def _enter_critical_section(self) -> None:
        self.state = NodeState.HELD
        print(f"\n  >>> [GRANTED] Node {self.node_id} ENTERED Critical Section! (TS={self.req_timestamp}) <<<\n")


# --- Simulation Script ---

if __name__ == "__main__":
    print("--- Initializing Ricart-Agrawala Distributed Mutex Engine ---\n")

    TOTAL_NODES = 3
    nodes = {i: RicartAgrawalaNode(node_id=i, total_nodes=TOTAL_NODES) for i in range(1, TOTAL_NODES + 1)}
    for node in nodes.values():
        node.connect(nodes)

    print("[STEP 1: Concurrent Request Contention]")
    # Node 1 and Node 2 simultaneously contest the lock
    nodes[1].request_critical_section()
    nodes[2].request_critical_section()

    print("\n[STEP 2: Message Passing & Priority Resolution]")
    # Deliver messages through the network mesh
    for _ in range(4):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"Lock Holder Check -> Node 1: {nodes[1].state.name} | Node 2: {nodes[2].state.name}")

    print("\n[STEP 3: Node 1 Exits CS & Unblocks Deferred Node 2]")
    nodes[1].release_critical_section()

    # Deliver the deferred reply from Node 1 to Node 2
    for _ in range(4):
        for node in nodes.values():
            node.process_incoming_messages()

    print(f"Post-Release Check -> Node 1: {nodes[1].state.name} | Node 2: {nodes[2].state.name}")
    print("-" * 65)
    print("[SUCCESS] Mutex achieved using only 2(N-1) messages with zero centralized dependencies!")
  
