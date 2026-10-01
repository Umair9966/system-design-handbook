# Distributed Systems & System Design Glossary 📖

An alphabetical reference dictionary of key distributed systems, database, networking, and system design terms.

---

### A
- **ACID**: Atomicity, Consistency, Isolation, Durability. Set of properties guaranteeing database transaction reliability.
- **Active-Active**: High-availability architecture where multiple nodes actively process requests simultaneously.
- **Active-Passive**: High-availability setup where standby nodes only process traffic upon primary node failure.
- **Amdahl's Law**: Formula predicting the theoretical maximum speedup of a program when using multiple processors.
- **Anycast**: Network addressing method where a single destination IP address is shared by multiple routing endpoints.
- **API Gateway**: Reverse proxy acting as a single entry point for clients, routing traffic and enforcing security policies.

### B
- **Backpressure**: Resistance or flow-control applied against the flow of data when a downstream consumer is overwhelmed.
- **Bloom Filter**: Space-efficient probabilistic data structure used to test set membership (false positives possible, no false negatives).
- **Bulkhead Pattern**: Resilience pattern that isolates elements into pools so failure of one does not bring down the whole system.
- **B-Tree / B+Tree**: Self-balancing tree data structure optimized for systems reading and writing large blocks of memory/disk.

### C
- **CAP Theorem**: Distributed systems theorem stating a partition-tolerant system can provide either Consistency or Availability, but not both.
- **Circuit Breaker**: Stability pattern that fails fast when a downstream dependency is unhealthy, preventing cascading crashes.
- **Columnar Storage**: Database storage architecture storing data tables by column rather than by row (ideal for OLAP).
- **Consistent Hashing**: Distributed hashing technique where addition/removal of a node minimizes key remapping.
- **CRDT (Conflict-Free Replicated Data Type)**: Data structure that can be replicated across nodes and resolved concurrently without central coordination.

### D
- **Dead-Letter Queue (DLQ)**: Queue holding messages that cannot be processed successfully after retry limits.
- **Denormalization**: Database optimization technique introducing intentional redundancy to improve read performance.
- **Distributed Lock**: Mechanism ensuring mutual exclusion among distributed processes accessing shared resources.
- **Durability**: The guarantee that once a transaction commits, its modifications persist permanently even across crashes.

### E
- **Event Sourcing**: Architectural pattern where state changes are stored as an append-only sequence of immutable events.
- **Exponential Backoff**: Retry algorithm multiplying wait intervals exponentially after consecutive failures.

### F
- **Failover**: Automatic switching to a redundant or standby system upon failure of an active node.
- **Fan-Out**: Mechanism where a single message or write is duplicated and dispatched to multiple destinations.
- **Fencing Token**: Monotonically increasing number distributed to lock holders to reject requests from expired/zombie clients.

### G
- **Gossip Protocol**: Decentralized communication protocol where nodes periodically share cluster state epidemically.
- **GSLB (Global Server Load Balancing)**: Load balancing technique directing traffic across geographically dispersed datacenters.

### H
- **Head-of-Line (HoL) Blocking**: Performance bottleneck where line-processing delay of the first item stalls subsequent items.
- **HyperLogLog**: Probabilistic algorithm used to approximate distinct count (cardinality) of high-volume datasets in fixed memory.

### I
- **Idempotency**: Property of an operation where applying it multiple times produces the identical result as applying it once.
- **Inverted Index**: Search engine index mapping individual words/tokens to the documents or locations where they appear.

### L
- **LSM-Tree (Log-Structured Merge-Tree)**: Write-optimized storage structure appending writes sequentially before merging SSTables.
- **Linearizability**: Strongest consistency model where all operations appear to take effect instantaneously at a distinct point in global time.
- **Little's Law**: Fundamental queueing theory relationship: $L = \lambda W$ (Average items in system = Arrival rate × Average wait time).

### M
- **MVCC (Multi-Version Concurrency Control)**: Concurrency control method where database maintains snapshots of data for concurrent readers.
- **mTLS (Mutual TLS)**: Security protocol where both client and server cryptographically verify each other's certificates.

### N
- **Negative Caching**: Pattern of caching nonexistent or missing query results (e.g., 404s) to shield backend databases from repetitive scans.

### O
- **OLAP (Online Analytical Processing)**: Systems optimized for complex, read-heavy analytical queries over vast aggregations.
- **OLTP (Online Transaction Processing)**: Systems optimized for high-throughput, low-latency concurrent read/write transactional updates.
- **Operational Transformation (OT)**: Centralized mathematical technique supporting real-time collaborative concurrent text editing.

### P
- **PACELC Theorem**: Extension of CAP stating: If there is a Partition (P), trade Availability (A) vs Consistency (C); Else (E), trade Latency (L) vs Consistency (C).
- **Paxos**: Classic family of consensus protocols ensuring agreement among unreliable distributed processors.

### Q
- **Quorum**: Minimum number of votes/nodes that must agree in a distributed system to safely complete a read or write operation.

### R
- **Raft**: Understandable distributed consensus algorithm utilizing leader election and log replication.
- **Read-Your-Writes Consistency**: Consistency model guaranteeing a client will always observe updates written by itself.
- **Reverse Proxy**: Server positioned in front of backend servers intercepting requests for routing, security, and caching.

### S
- **Saga Pattern**: Sequence of local transactions coordinated via events or orchestrators with compensating transactions for rollbacks.
- **Sharding**: Horizontal partitioning of a database table across multiple independent server instances.
- **Split-Brain**: Catastrophic distributed condition where network partition leads two nodes to independently believe they are the sole leader.

### T
- **Token Bucket**: Rate limiting algorithm allowing bursty traffic up to bucket capacity while refilling tokens at a constant rate.
- **Two-Phase Commit (2PC)**: Atomic commitment protocol ensuring distributed transactions commit or abort across all participating shards.

### V
- **Vector Clock**: Distributed logical clock algorithm used to detect causal relationships and concurrent update conflicts.
- **Virtual Nodes**: Placement technique in consistent hashing where a single physical node maps to multiple points on the hash ring.

### W
- **WAL (Write-Ahead Log)**: Append-only log recording transaction modifications before writing changes to database storage pages.
- **Working Set**: Subset of active application data and memory pages referenced by a process during a given time interval.
