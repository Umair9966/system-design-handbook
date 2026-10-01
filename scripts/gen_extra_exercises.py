import os

exercises_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\exercises"

files = {
    "07-distributed-systems-exercises.md": """# Exercises: Distributed Systems Theory

Test your comprehension of consensus, CAP/PACELC, clocks, and distributed transactions.

---

### Exercise 1: PACELC Analysis
A financial ledger requires zero lost balance updates and strong consistency, even during WAN network partitions. How would you classify this system under PACELC? What are the latency consequences?

### Exercise 2: Raft Split-Vote Simulation
In a 5-node Raft cluster, Node 1 (leader) disconnects. Nodes 2 and 3 both simultaneously time out and increment their term to 2, voting for themselves. How does Raft resolve this split-vote scenario without deadlocking?

### Exercise 3: Lamport Clock vs Vector Clock
Explain a concrete scenario where Lamport timestamps indicate that Event A happened before Event B ($L(A) < L(B)$), but where Event A did NOT causally precede Event B ($A \not\to B$).
""",

    "07-distributed-systems-solutions.md": """# Solutions: Distributed Systems Theory

---

### Solution 1: PACELC Analysis
- **Classification**: **PC/EC** (Consistent under Partition; Consistent under Normal execution).
- **Latency Consequences**: Every read and write requires waiting for consensus quorum across nodes ($R+W > N$). Under normal operation (no partition), writes must coordinate synchronously across replicas, adding WAN round-trip latency ($\approx 70\text{ms}$). Availability is sacrificed during network partitions if a quorum cannot be formed.

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
""",

    "08-messaging-exercises.md": """# Exercises: Messaging and Event Streaming

---

### Exercise 1: Kafka Consumer Lag Spike
A Kafka topic with 12 partitions is consumed by a consumer group of 12 worker pods. Consumer lag suddenly surges to 500,000 messages. You scale the consumer deployment from 12 pods to 24 pods. Does this resolve the lag? Explain why or why not.

### Exercise 2: Outbox Pattern vs Two-Phase Commit
Why do modern microservice architectures strongly prefer the Transactional Outbox pattern with Change Data Capture (CDC) over distributed Two-Phase Commit (2PC) for publishing database state changes to Kafka?
""",

    "08-messaging-solutions.md": """# Solutions: Messaging and Event Streaming

---

### Solution 1: Kafka Consumer Lag Spike
- **Outcome**: **No, scaling to 24 pods will NOT resolve the lag.**
- **Reason**: In Kafka, each partition within a consumer group can be consumed by at most **one** consumer thread/pod at any time. With 12 partitions and 24 consumer pods, 12 pods will actively consume while the remaining 12 pods will sit completely **idle**.
- **Correct Solution**:
  1. Increase partition count of the topic to 24 (if ordering key constraints allow).
  2. Or, within each consumer pod, use a thread pool / worker queue to process independent message keys in parallel.
  3. Optimize the consumer processing logic to increase throughput per partition.

---

### Solution 2: Outbox Pattern vs 2PC
- **Drawbacks of 2PC**:
  - Blocking protocol: Locks database rows and broker resources across network round-trips.
  - Fragile: If the coordinator or broker network drops mid-commit, locks remain held, causing cascading connection pool exhaustion.
  - Unsupported: Modern message brokers (Kafka, SQS) do not support XA/2PC transactions with relational databases.
- **Advantages of Transactional Outbox + CDC**:
  - Pure local ACID transaction: The business entity and the outbox message are committed in the same local database transaction.
  - Asynchronous & Non-blocking: CDC tools (Debezium) tail the database Write-Ahead Log (WAL) to publish to Kafka with zero impact on database transaction latency.
""",

    "09-api-design-exercises.md": """# Exercises: API Design and Rate Limiting

---

### Exercise 1: Cursor vs Offset Pagination at Scale
Explain why `GET /api/v1/posts?offset=5000000&limit=20` causes severe database performance degradation, and rewrite the query using Cursor-based pagination.

### Exercise 2: Rate Limiting Race Condition
Explain the race condition that occurs when implementing a Token Bucket rate limiter in Redis using naive `GET` and `SET` commands. How does a Lua script eliminate this?
""",

    "09-api-design-solutions.md": """# Solutions: API Design and Rate Limiting

---

### Solution 1: Cursor vs Offset Pagination
- **Problem with Offset**: The SQL database must scan, sort, and materialize all 5,000,020 rows, then discard the first 5,000,000 rows. This is an $O(N)$ full index scan that consumes high I/O and causes latency to degrade linearly as the page number increases.
- **Cursor Solution**:
  ```sql
  SELECT id, title, created_at
  FROM posts
  WHERE (created_at, id) < (:last_seen_created_at, :last_seen_id)
  ORDER BY created_at DESC, id DESC
  LIMIT 20;
  ```
  - Leverages a composite index on `(created_at, id)` to seek directly to the target record in $O(\log N)$ time, skipping past millions of rows instantly.

---

### Solution 2: Rate Limiting Race Condition
- **Naive Race Condition**: Two concurrent requests from the same user arrive at Pod A and Pod B simultaneously. Both read `GET tokens` (e.g., returns 1). Both evaluate $1 \ge 1$, allow the request, decrement to 0, and write `SET tokens 0`. Both requests were allowed even though only 1 token was available!
- **Lua Script Fix**: Redis executes Lua scripts as a single atomic operation on the main execution thread. No other command or script can run concurrently between reading and updating the token count.
"""
}

for fname, content in files.items():
    fpath = os.path.join(exercises_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Additional exercises and solutions generated.")
