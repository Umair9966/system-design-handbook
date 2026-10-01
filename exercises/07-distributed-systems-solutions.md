# Solutions: Distributed Systems Theory

---

### Solution 1: PACELC Analysis
- **Classification**: **PC/EC** (Consistent under Partition; Consistent under Normal execution).
- **Latency Consequences**: Every read and write requires waiting for consensus quorum across nodes ($R+W > N$). Under normal operation (no partition), writes must coordinate synchronously across replicas, adding WAN round-trip latency ($pprox 70	ext{ms}$). Availability is sacrificed during network partitions if a quorum cannot be formed.

---

### Solution 2: Raft Split-Vote Simulation
- **Mechanism**: **Randomized Election Timeouts** (typically 150ms - 300ms).
- When a split vote occurs, neither candidate attains a majority of 3 votes. Both election timers expire.
- Because each node picks a random timeout, one node (e.g., Node 2) will time out first (say, at 170ms vs Node 3's 250ms), increment term to 3, and broadcast `RequestVote`. It receives votes from Node 4 and Node 5 before Node 3's timer fires, winning the majority and establishing leadership.

---

### Solution 3: Lamport Clock vs Vector Clock
- **Scenario**: Node 1 increments counter to 1 and executes Event A. Completely independently on Node 2 (with zero network messages between them), Node 2 processes two internal events, setting its counter to 2 (Event B).
- **Evaluation**: $L(A) = 1 < L(B) = 2$, but Event A and Event B are **concurrent** ($A \parallel B$). Event A did not cause Event B.
- **Vector Clock Resolution**: Vector clocks maintain a vector per node: $V(A) = [1, 0]$ and $V(B) = [0, 2]$. Because neither vector is strictly greater than the other, vector clocks accurately detect that the events are concurrent.
