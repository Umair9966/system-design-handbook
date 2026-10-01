import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 06: DATA PARTITIONING AND REPLICATION
# =========================================================================

save("docs/06-data-partitioning-and-replication/01-sharding-strategies.md", """# Database Sharding Strategies: Range, Hash, Directory, and Geo

## Overview
**Sharding** is the architectural pattern of horizontally partitioning a database into smaller, independent physical databases (shards) across multiple server instances. Unlike read replicas, each individual shard holds a distinct, mutually exclusive subset of the overall data.

```mermaid
graph TD
    Client[Client Query: user_id = 42] --> Router{Sharding Router}
    Router -->|Hash: hash 42 % 3 = 0| Shard0[(Shard 0: Users 0, 3, 6...)]
    Router -->|Hash: hash 42 % 3 = 1| Shard1[(Shard 1: Users 1, 4, 7...)]
    Router -->|Hash: hash 42 % 3 = 2| Shard2[(Shard 2: Users 2, 5, 8...)]
```

## Why It Matters
When a single database server hits its physical limits—storage exceeds 10 Terabytes, write throughput exceeds 20,000 IOPS, or memory working sets exhaust physical RAM—scaling up is impossible. Sharding enables theoretically unbounded horizontal scaling by distributing data across dozens or hundreds of commodity servers.

## Core Concepts & Sharding Strategies
1. **Range-Based Sharding**:
   - Data is partitioned based on contiguous ranges of a key (e.g., Shard 1 holds names A-F, Shard 2 holds G-M).
   - *Advantage*: Range queries (`WHERE name BETWEEN 'Alice' AND 'Bob'`) target a single shard.
   - *Fatal Flaw*: Massive write hotspots if keys are monotonic (e.g., sharding by timestamp causes 100% of all current writes to strike today's shard).
2. **Hash-Based Sharding**:
   - Applies a hash function (MD5, MurmurHash3) to the shard key:
     $$\\text{Shard ID} = \\text{Hash}(\\text{shard\\_key}) \\pmod N$$
   - *Advantage*: Uniform, random distribution of writes across all shards.
   - *Disadvantage*: Range scans require an expensive **Scatter-Gather** query querying all $N$ shards in parallel.
3. **Directory-Based (Lookup) Sharding**:
   - A central lookup service or table maps partition keys to physical shard locations (e.g., `Tenant_123 -> Shard_4`).
   - *Advantage*: Unbelievably flexible; individual hot tenants can be dynamically relocated to dedicated hardware.
   - *Disadvantage*: Central lookup table is a single point of failure and adds a network lookup hop.
4. **Geographic Sharding (Geo-Sharding)**:
   - Partitions data based on user geographic residency (e.g., European users on EU shards, US users on US shards).
   - Essential for complying with international data residency laws (GDPR).

## Trade-offs
| Sharding Strategy | Write Distribution | Range Query Efficiency | Operational Rebalancing |
| :--- | :--- | :--- | :--- |
| **Hash-Based** | **Uniform & Balanced** | Poor (Requires Scatter-Gather) | Hard (requires resharding data) |
| **Range-Based** | Prone to Severe Hotspots| **Excellent (Single-shard query)**| Easy (Split existing range) |
| **Directory-Based**| Highly Customizable | Moderate | **Trivial (Update lookup pointer)**|
| **Geo-Based** | Dependent on regional user base| High for local queries | Moderate |

## When to Use / When NOT to Use
### When to Shard
- Total data volume exceeds ~5 Terabytes and cannot fit on a single node.
- Write IOPS exceed the maximum physical throughput of high-end NVMe disk controllers.

### When NOT to Shard
- Premature optimization! If your database is under 1 Terabyte, vertical scaling and read replicas are 100x simpler, cheaper, and safer.

## Real-World Examples
- **Instagram (2011)**: Sharded PostgreSQL across multiple instances using custom 64-bit ID generation containing the Shard ID in the integer bits, routing writes without a central lookup table.
- **Discord**: Sharded ScyllaDB clusters across thousands of logical buckets by `channel_id`, ensuring all messages in a chat channel reside on the same shard.

## Common Pitfalls
- **Cross-Shard Joins**: Attempting to join tables residing on different physical shards, forcing the application tier to fetch millions of rows across the network and perform in-memory joins.
- **Cross-Shard Distributed Transactions**: Requiring Two-Phase Commit (2PC) across multiple shards, collapsing throughput from 20,000 QPS down to 200 QPS.

## Key Takeaways
- Select a **Shard Key** that groups related data accessed together onto the same physical node (e.g., `customer_id`).
- Hash-based sharding guarantees uniform write distribution; Range-based sharding optimizes range scans but risks hotspots.
- Sharding introduces immense operational complexity—exhaust all vertical and caching options first!

## Common Interview Questions
1. How do you choose the ideal shard key for an e-commerce platform with buyers and sellers?
2. What is a "scatter-gather" query, and why does it cause high tail latency across shards?
3. How do you execute zero-downtime resharding when expanding from 4 shards to 8 shards?

## Further Reading
- [Instagram Engineering: Sharding & IDs at Instagram](https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a05e5a3f)
- [Designing Data-Intensive Applications: Chapter 6 (Partitioning)](https://dataintensive.net/)
""")

save("docs/06-data-partitioning-and-replication/02-consistent-hashing.md", """# Consistent Hashing and Virtual Nodes

## Overview
In distributed caching and sharded storage systems, mapping keys to nodes using naive modulo hashing:
$$\\text{Node} = \\text{Hash}(\\text{Key}) \\pmod N$$
suffers from a fatal flaw: when a node is added or removed ($N$ changes to $N+1$ or $N-1$), **almost 100% of all keys remap to new locations**, causing catastrophic cache invalidation and database stampedes.

**Consistent Hashing** is an algorithmic distribution technique where changing the number of nodes requires remapping only **$K/N$ keys on average** (where $K$ is total keys and $N$ is total nodes).

```mermaid
graph TD
    subgraph 360-Degree Hash Ring
        NodeA["Node A (Position: 1,000,000)"]
        NodeB["Node B (Position: 2,000,000)"]
        NodeC["Node C (Position: 3,500,000)"]
        Key1["Key 1 (Hash: 1,500,000) -> Routes clockwise to Node B"]
        Key2["Key 2 (Hash: 2,800,000) -> Routes clockwise to Node C"]
        Key3["Key 3 (Hash: 3,900,000) -> Wraps clockwise to Node A"]
    end
```

## Why It Matters
In massive distributed systems like Amazon DynamoDB, Apache Cassandra, and Akamai CDNs, servers join and leave clusters continuously due to autoscaling, hardware crashes, and rolling deployments. Consistent hashing guarantees that server churn causes minimal data movement and zero downtime.

## Core Concepts & Step-by-Step Mechanics
1. **The Circular Hash Ring**:
   - The output range of a standard hash function (e.g., 32-bit integer range: $0$ to $2^{32}-1$) is conceptualized as a continuous circular ring.
2. **Mapping Nodes to the Ring**:
   - Each physical server node is hashed based on its IP address or hostname and placed onto the ring.
3. **Mapping Keys to the Ring**:
   - When a data key arrives, it is hashed to a position on the ring.
4. **Clockwise Routing**:
   - The key traverses the ring **clockwise** until it encounters the first server node. That node owns the key.
5. **Handling Node Failures**:
   - If Node B crashes, only the keys mapped between Node A and Node B are affected. They naturally fall onto the next clockwise node (Node C). Nodes A and D remain completely unaffected!

### The Non-Uniformity Problem & Virtual Nodes (Vnodes)
- **The Problem**: With a small number of physical nodes (e.g., 3 nodes), random placement can cluster nodes together, causing one server to own 80% of the ring while others hold 10%. Furthermore, when a node dies, its entire load collapses onto its immediate successor.
- **The Solution (Virtual Nodes)**:
  - Instead of assigning a physical node to 1 point on the ring, assign it **100 to 256 virtual nodes (vnodes)** distributed randomly across the ring (e.g., `NodeA#1`, `NodeA#2`, ..., `NodeA#200`).
  - *Result*: Guarantees mathematically uniform distribution of keys and distributes a dead node's workload evenly across **all** surviving nodes in the cluster.

```mermaid
graph TD
    subgraph Consistent Hashing with Virtual Nodes
        VA1["Node A - Vnode 1"]
        VB1["Node B - Vnode 1"]
        VA2["Node A - Vnode 2"]
        VB2["Node B - Vnode 2"]
        VC1["Node C - Vnode 1"]
        VA3["Node A - Vnode 3"]
    end
```

## Trade-offs
| Attribute | Modulo Hashing (`hash % N`) | Consistent Hashing with Vnodes |
| :--- | :--- | :--- |
| **Keys Remapped on Node Churn**| $\\approx 100\\%$ (Catastrophic cache loss) | **$1/N$ fraction only (Minimal data movement)** |
| **Lookup Time Complexity** | $O(1)$ | $O(\\log(\\text{Total Vnodes}))$ via Binary Search |
| **Memory Overhead** | Zero | Small in-memory routing table of vnode positions |
| **Load Distribution Uniformity**| High | **Near-perfect with 200+ vnodes per physical node** |

## When to Use / When NOT to Use
### When Consistent Hashing is Mandatory
- Distributed caches (Memcached clusters), P2P networks (BitTorrent DHT), distributed databases (Cassandra, DynamoDB, Riak), stateful connection routers.

### When NOT Needed
- Small static clusters with zero node churn where modulo hashing or standard round-robin suffices.

## Real-World Examples
- **Amazon Dynamo Paper (2007)**: Popularized consistent hashing with virtual nodes to distribute shopping cart data across thousands of commodity storage nodes with zero downtime.
- **Discord Gateway Routing**: Uses consistent hashing rings to assign millions of connected Discord guilds (servers) to specific gateway routing pods.

## Common Pitfalls
- **Too Few Virtual Nodes**: Using fewer than 50 vnodes per physical server, leading to noticeable load skew (variance > 25% between nodes).
- **Ignoring Cascading Failures without Vnodes**: Without vnodes, Server B's crash doubles the load on Server C, crashing Server C, which triples the load on Server D, cascading into total cluster collapse.

## Key Takeaways
- Consistent hashing remaps only $1/N$ keys when a node joins or leaves.
- **Virtual nodes (vnodes)** are mandatory to ensure uniform load distribution and prevent cascading failures.
- Binary search (`bisect` in Python or `std::lower_bound` in C++) resolves key lookups in $O(\\log M)$ time on the client.

## Common Interview Questions
1. Why does naive modulo hashing fail when scaling distributed caches up and down?
2. How do virtual nodes solve both load imbalance and cascading failovers in consistent hashing?
3. Walk through the exact algorithm to find the owning node for a key on a consistent hash ring.

## Further Reading
- [Karger et al.: Consistent Hashing and Random Trees (ACM STOC 1997)](https://dl.acm.org/doi/10.1145/258533.258660)
- [Amazon Dynamo: Highly Available Key-value Store (SOSP 2007)](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
""")

save("docs/06-data-partitioning-and-replication/03-hotspots-rebalancing-resharding.md", """# Hotspots, Resharding, and Partition Rebalancing

## Overview
Even with mathematical partitioning algorithms, production distributed systems frequently suffer from **hotspots**: severe imbalances where a tiny fraction of partition keys receives a disproportionate share of read or write traffic (the "Celebrity Problem").

Resolving hotspots requires proactive mitigation strategies, dynamic range splitting, and zero-downtime **partition rebalancing (resharding)**.

```mermaid
graph TD
    subgraph Hotspot Pathology: The Celebrity Problem
        User1[Normal User: 100 Followers] --> ShardA[(Shard A: 50 QPS)]
        Celebrity[Celebrity: 80M Followers] -->|Extreme Spike| ShardB[(Shard B: 150,000 QPS - COLLAPSE!)]
    end
    subgraph Antidote: Key Salting
        CelebrityPost[Celebrity Post] --> Salt{Add Salt: 1..10}
        Salt --> Shard1[(Shard B1)]
        Salt --> Shard2[(Shard B2)]
        Salt --> Shard3[(Shard B10)]
    end
```

## Why It Matters
A single viral tweet, flash sale item, or high-profile user account can generate 100,000 requests per second. If that entity's data maps to a single database shard, that individual shard's CPU and disk saturate, causing cascading connection timeouts across the entire platform while neighboring shards sit 95% idle.

## Core Concepts & Mitigation Mechanics

### 1. The Celebrity Problem & Key Salting
- **The Problem**: Key `user_id:999` belongs to a celebrity with 80 million followers. Every update or read strikes a single shard.
- **The Mitigation (Key Salting)**:
  - When writing data for the celebrity, append a random integer suffix (salt): `user_id:999_1`, `user_id:999_2`, ..., `user_id:999_10`.
  - The writes distribute uniformly across 10 distinct shards.
  - *Read Path*: Reads execute a parallel scatter-gather query across all 10 salted keys and merge the results.

### 2. Zero-Downtime Dynamic Resharding
When a shard reaches maximum capacity, expanding from $N$ to $2N$ shards must execute without stopping live customer traffic:
1. **Dual-Writing (Shadow Replication)**: Application writes to both old and new shard topologies concurrently.
2. **Backfill Snapshot**: Background batch process copies historical records from old shards to new shards.
3. **Catch-Up & Verification**: Read the replication change stream (CDC) to reconcile any missing delta records.
4. **Read Cutover**: Shift 1% -> 10% -> 100% of read traffic to the new shards via dynamic feature flags.
5. **Decommission**: Stop writes to old shards and safely delete old data.

## Trade-offs
| Mitigation Pattern | Benefit | Trade-off / Cost |
| :--- | :--- | :--- |
| **Key Salting** | Neutralizes write hotspots instantly | Reads must scatter-gather across all salt variants |
| **In-Memory Read Shielding**| Caches hot key reads in Redis/CDN | Does not solve write hotspots |
| **Dynamic Shard Splitting** | Long-term linear capacity growth | Complex orchestration and background disk I/O |

## When to Use / When NOT to Use
### When to Use Key Salting
- High-profile entities with asymmetric write/read spikes (e.g., trending hashtags, celebrity social profiles, viral product drops).

### When to Use Dynamic Range Splitting
- Storage engines (Google Spanner, CockroachDB, HBase) that automatically split a table partition into two halves when its size exceeds 64MB or when CPU load crosses 80%.

## Real-World Examples
- **Twitter/X**: When Taylor Swift or Elon Musk posts a tweet, Twitter does not push the tweet into 100 million follower timeline shards (which would take minutes); instead, follower feeds dynamically merge celebrity tweets at read time.
- **Amazon DynamoDB Adaptive Capacity**: Automatically detects unbalanced read/write request spikes on individual partitions and dynamically shifts unused throughput capacity from quiet partitions to the hot partition within minutes.

## Common Pitfalls
- **Over-Salting Uniform Keys**: Appending random salts to ordinary users with 100 followers, forcing unnecessary scatter-gather queries and multiplying read latency by 10x for zero benefit.
- **Resharding During Peak Hours**: Triggering heavy data migration and rebalancing scripts during peak traffic hours, saturating network interfaces and disk I/O when the system is already stressed.

## Key Takeaways
- Use **Key Salting** to distribute super-hot entity writes across multiple physical shards.
- Always implement zero-downtime resharding via **Dual-Writing -> Backfilling -> Verification -> Cutover**.
- Treat hot-key mitigation as an application-layer design requirement, not just a database property.

## Common Interview Questions
1. How does Key Salting resolve write hotspots in a distributed key-value store?
2. Walk through the step-by-step process of splitting a live database shard with zero downtime.
3. How does DynamoDB's adaptive capacity dynamically balance partitions?

## Further Reading
- [Amazon DynamoDB: How Partitioning Works and Adaptive Capacity](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.Partitions.html)
- [Google Cloud Spanner: Schema Design and Avoiding Hotspots](https://cloud.google.com/spanner/docs/schema-design#hotspots)
""")

save("docs/06-data-partitioning-and-replication/04-replication-models.md", """# Replication Models: Single-Leader, Multi-Leader, and Leaderless

## Overview
**Replication** is the process of keeping a copy of the same data across multiple distinct physical machines connected via a network. Replication provides two indispensable benefits: **fault tolerance (high availability)** and **increased read throughput**.

Distributed data systems organize replication around three primary models:
1. **Single-Leader (Primary-Replica)**: One designated leader node accepts all writes; followers asynchronously or synchronously replicate changes to serve read traffic.
2. **Multi-Leader (Active-Active)**: Multiple nodes accept writes concurrently and replicate state changes to each other across datacenters.
3. **Leaderless (Dynamo-Style)**: Every replica accepts writes and reads directly from clients; consistency is managed via quorum consensus ($R + W > N$).

```mermaid
graph TD
    subgraph Single-Leader
        ClientW1[Write] --> Leader1[Leader Node]
        Leader1 -->|Replication Stream| F1[Follower 1: Reads]
        Leader1 -->|Replication Stream| F2[Follower 2: Reads]
    end
    subgraph Multi-Leader [Cross-Datacenter]
        W_US[Write US] --> L_US[Leader US-East]
        W_EU[Write EU] --> L_EU[Leader EU-West]
        L_US <==>|Asynchronous Cross-WAN Sync| L_EU
    end
    subgraph Leaderless [Dynamo / Cassandra]
        ClientW3[Write Quorum W=2] --> N1[Node 1] & N2[Node 2]
        ClientR3[Read Quorum R=2] --> N2 & N3[Node 3]
    end
```

## Why It Matters
Your replication topology dictates whether writes can survive a datacenter blackout, how long clients wait for write acknowledgments, and whether your database can experience concurrent write conflict anomalies.

## Core Concepts & Architectural Comparison
| Replication Model | Write Destinations | Read Destinations | Conflict Handling | Fault Tolerance |
| :--- | :--- | :--- | :--- | :--- |
| **Single-Leader** | Single Leader only | Leader + All Followers | **Zero write conflicts (Leader serializes writes)**| Leader is SPOF until failover completes |
| **Multi-Leader** | Any regional Leader | Any regional Leader | **Complex (Requires conflict resolution)** | High (Writes continue if 1 region dies)|
| **Leaderless** | Any $W$ nodes (Quorum)| Any $R$ nodes (Quorum) | **Handled at read time (Vector clocks / LWW)**| **Extreme (No single master to crash)** |

## Detailed Mechanics

### 1. Single-Leader Replication (MySQL, PostgreSQL, Redis)
- All mutations (`INSERT`, `UPDATE`, `DELETE`) route strictly to the Leader.
- Leader writes changes to its Write-Ahead Log (WAL) and streams them to Followers.
- *Strength*: Simple semantics; ACID transactions are easily enforced.
- *Limitation*: Write throughput is strictly bounded by the single leader's capacity.

### 2. Multi-Leader Replication (Multi-Datacenter Deployments)
- A leader exists in each geographic datacenter (e.g., US-East, Europe-West).
- Local writes complete in sub-millisecond local LAN time without crossing the ocean.
- **The Core Challenge (Write Conflicts)**: User A updates an order in the US to "Cancelled"; User B simultaneously updates the same order in Europe to "Shipped".
- *Resolution Strategies*:
  - *Last Write Wins (LWW)*: Wall-clock timestamp wins (risks silent data loss due to clock skew).
  - *Conflict-Free Replicated Data Types (CRDTs)*: Mathematical data structures that resolve concurrently without coordination.

### 3. Leaderless Replication (Apache Cassandra, Amazon Dynamo, Riak)
- Clients (or coordinator nodes) write directly to $N$ replicas.
- Success is returned as soon as $W$ replicas acknowledge.
- Reads query $R$ replicas in parallel, returning the version with the newest timestamp and triggering **Read Repair** on stale nodes.

## Trade-offs
| Model | Write Latency | Operational Simplicity | Conflict Risk |
| :--- | :--- | :--- | :--- |
| **Single-Leader** | Moderate | **High (Industry default)** | **Zero** |
| **Multi-Leader** | **Low (Local DC write)** | Very Hard | High (Requires domain merge logic) |
| **Leaderless** | Tunable ($W$) | Moderate | Handled via versioning & quorums |

## When to Use / When NOT to Use
### When to Choose Single-Leader
- 90% of business applications: PostgreSQL, MySQL, Redis. Financial ledgers, ERPs, user auth.

### When to Choose Multi-Leader
- Multi-datacenter architectures where local write latency is non-negotiable or offline collaboration tools (e.g., Git, CouchDB).

### When to Choose Leaderless
- High-velocity globally distributed systems with massive write volumes and high uptime requirements (Cassandra/DynamoDB).

## Real-World Examples
- **Git Version Control**: The ultimate distributed **Multi-Leader** system. Developers commit and merge branches locally (acting as independent leaders) and resolve merge conflicts explicitly during pull requests.
- **Netflix Cassandra Fleet**: Runs massive multi-region Cassandra clusters across AWS regions to survive entire AWS regional blackouts without losing active user streaming sessions.

## Common Pitfalls
- **Relying on Last-Write-Wins (LWW) Blindly**: In multi-leader or leaderless systems, LWW silently drops valid updates due to unaligned physical quartz clocks (clock skew).
- **Split-Brain during Single-Leader Failover**: Promoting a follower to leader while the old leader is still alive and accepting writes, partitioning the database into two divergent histories.

## Key Takeaways
- Single-leader is the simplest model; writes are serialized without conflict.
- Multi-leader reduces cross-region write latency but introduces complex write conflict resolution.
- Leaderless architectures rely on quorum mathematics ($R + W > N$) and anti-entropy to guarantee consistency.

## Common Interview Questions
1. How does a Multi-Leader database resolve concurrent write conflicts on the same record?
2. What are Conflict-Free Replicated Data Types (CRDTs), and where are they used?
3. How does Leaderless replication achieve high write availability during partial network partitions?

## Further Reading
- [Martin Kleppmann: Replication (DDIA Chapter 5)](https://dataintensive.net/)
- [Werner Vogels et al.: Dynamo: Amazon’s Highly Available Key-value Store](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
""")

save("docs/06-data-partitioning-and-replication/05-sync-vs-async-replication-and-lag.md", """# Synchronous vs Asynchronous Replication and Replication Lag

## Overview
When replicating data from a primary leader to replica followers, a distributed system must choose its synchronization boundary:
- **Synchronous Replication**: The leader waits for the replica to write the change to disk before returning success to the client.
- **Asynchronous Replication**: The leader writes to local disk, returns success to the client immediately, and pushes the change to replicas in the background.
- **Semi-Synchronous Replication**: The leader waits for at least **one** replica to acknowledge, while remaining replicas replicate asynchronously.

```mermaid
sequenceDiagram
    autonumber
    Client->>Leader: Write X = 5
    Leader->>Leader: Write local WAL
    Note over Leader, SyncReplica: Synchronous Path
    Leader->>SyncReplica: Replicate X = 5
    SyncReplica-->>Leader: ACK Written
    Leader-->>Client: Success! (Sub-50ms)
    Note over Leader, AsyncReplica: Asynchronous Path
    Leader-)AsyncReplica: Async Stream X = 5 (Lag: 1.5 seconds)
```

## Why It Matters
Asynchronous replication makes writes blindingly fast (sub-2ms), but introduces **Replication Lag**: the time delay between a write committing on the leader and appearing on the replica. If an application routes reads to lagging replicas, users experience jarring consistency bugs where newly submitted comments vanish upon page reload.

## Core Concepts & Replication Lag Anomalies
1. **Reading Your Own Writes (Read-After-Write Consistency)**:
   - *The Bug*: User updates their profile photo -> Page reloads -> Read routes to a lagging replica -> User sees their old photo -> User assumes upload failed and submits 5 more times.
   - *Antidote*: Route reads for User X's profile directly to the **Leader** for 5 seconds following any write by User X. All other users continue reading from replicas.
2. **Monotonic Reads**:
   - *The Bug*: User refreshes the page repeatedly. Request 1 hits a fast replica (sees comment); Request 2 hits a lagging replica (comment disappears); Request 3 hits the fast replica (comment reappears).
   - *Antidote*: Pin user read sessions to a consistent replica using hash routing (e.g., `hash(user_id) % NumReplicas`).
3. **Consistent Prefix Reads (Causality Violation)**:
   - *The Bug*: Question arrives after Answer because questions and answers replicate across different shards with variable network delays.
   - *Antidote*: Keep causally related records on the same partition.

## Trade-offs
| Replication Mode | Write Latency | Durability on Leader Crash | Availability Impact |
| :--- | :--- | :--- | :--- |
| **Fully Synchronous** | High (bound by slowest replica) | **100% Guaranteed (Zero data loss)** | If 1 replica hangs, all writes freeze |
| **Fully Asynchronous**| **Ultra-Low (< 2ms local write)** | Risk of uncommitted write loss | Unaffected by replica outages |
| **Semi-Synchronous** | Moderate (waits for fastest replica)| **Excellent (At least 1 backup copy)** | High resilience |

## When to Use / When NOT to Use
### When to Use Synchronous / Semi-Synchronous
- Financial transactions, billing ledgers, authentication credential changes where losing the last 10 seconds of writes during a leader crash is unacceptable.

### When to Use Asynchronous
- High-throughput social networks, analytics pipelines, content platforms where sub-millisecond write latency outweighs brief replication lag.

## Real-World Examples
- **MySQL Semi-Synchronous Replication**: Widely deployed in production enterprise clusters. The leader waits until at least one replica has written the event to its **Relay Log** before returning success, guaranteeing that a sudden primary crash loses zero committed transactions.
- **PostgreSQL Synchronous Standby**: Allows engineers to specify `synchronous_commit = on` and `synchronous_standby_names = 'FIRST 1 (replica1, replica2)'`.

## Common Pitfalls
- **Global Read Routing to Replicas**: Routing 100% of read queries to read replicas without tracking user mutation timestamps, breaking Read-After-Write consistency across the entire application.
- **Unmonitored Replication Lag**: Failing to alert on replication lag metrics (e.g., `pg_stat_replication.replay_lag` in Postgres), allowing a replica to fall 4 hours behind without engineering awareness.

## Key Takeaways
- Fully synchronous replication halts write availability if any single replica hangs.
- **Semi-synchronous replication** provides the optimal balance of durability and write latency.
- Protect user experience against replication lag using **Read-After-Write** routing patterns.

## Common Interview Questions
1. What is replication lag, and what specific architectural strategies guarantee Read-After-Write consistency?
2. What are Monotonic Reads, and how do you prevent users from seeing data move backward in time?
3. How does Semi-Synchronous replication differ from fully synchronous and fully asynchronous replication?

## Further Reading
- [Martin Kleppmann: Problems with Replication Lag (DDIA Chapter 5)](https://dataintensive.net/)
- [MySQL Documentation: Semi-Synchronous Replication](https://dev.mysql.com/doc/refman/8.0/en/replication-semisync.html)
""")

save("docs/06-data-partitioning-and-replication/06-read-replicas-failover-split-brain.md", """# Read Replicas, Automatic Failover, and Split-Brain Prevention

## Overview
As read traffic scales into tens of thousands of queries per second, a single primary database becomes saturated. Systems scale read throughput by attaching **read replicas** (follower nodes) to the primary leader.

When the primary leader fails, an **automatic failover** system must detect the outage, elect the most up-to-date replica, promote it to primary, and redirect client traffic—all while rigorously preventing the catastrophic condition known as **Split-Brain**.

```mermaid
graph TD
    subgraph Quorum Consensus Failover with Fencing
        Primary[(Old Primary Node: Fenced / Powered Off)]
        Standby[(Standby Replica: Promoted to New Primary)]
        Arbiter1[Consensus Node 1: Etcd]
        Arbiter2[Consensus Node 2: Etcd]
        Arbiter3[Consensus Node 3: Etcd]
        Arbiter1 & Arbiter2 & Arbiter3 -->|Majority Quorum Vote: 2 of 3| Standby
        Arbiter1 -.->|Issue Fencing Token: Epoch 43| Standby
        Storage[(Shared Storage / Backends)]
        Standby -->|Write with Epoch 43| Storage
        Primary -.->|Rejected: Epoch 42 Outdated!| Storage
    end
```

## Why It Matters
A split-brain disaster occurs when a network glitch severs communication between datacenters. Both the primary and the promoted replica believe they are the legitimate leader, simultaneously accepting conflicting writes from split clients. Reconciling two divergent databases after split-brain is mathematically impossible without permanent data loss.

## Core Concepts & Failover Mechanics
1. **Heartbeat Monitoring & Detection**:
   - Health agents ping the primary leader every 500ms.
   - To prevent false alarms from transient network hiccups, failover triggers only after $K$ consecutive missed heartbeats (e.g., 5 seconds).
2. **Leader Election via Majority Quorum**:
   - An odd number of consensus arbiters (3 or 5 nodes running Raft/etcd/ZooKeeper) vote on failover.
   - A node can only promote itself if it secures a **strict majority ($> 50\%$) of votes**. A partitioned datacenter holding only 1 out of 3 arbiters can never promote a master.
3. **Fencing Tokens (Generation Clocks)**:
   - Every time a new leader is promoted, the consensus cluster increments a monotonically increasing epoch number (e.g., Epoch 42 -> 43).
   - The new leader includes its fencing token with every write.
   - Shared storage tiers and downstreams **reject any write bearing an older token**, instantly neutralizing zombie former primaries.
4. **STONITH (Shoot The Other Node In The Head)**:
   - Hardware-level fencing. The cluster triggers an automated power switch (IPMI / smart PDU) to physically cut power to the old primary machine before promoting the secondary.

## Trade-offs
| Failover Strategy | Detection Speed | False-Positive Risk | Split-Brain Defense |
| :--- | :--- | :--- | :--- |
| **Aggressive Automated Failover (< 2s)**| Near-zero downtime (RTO < 5s) | **High (Network blips trigger needless failovers)**| Requires strict fencing |
| **Conservative Failover (30s - 60s)** | Higher downtime during true crash | Very Low | High stability |
| **Manual Human-in-the-Loop** | Slowest (RTO: 15-30 mins) | Zero false automated triggers | Safest against split-brain |

## When to Use / When NOT to Use
### When to Deploy Automated Consensus Failover
- Mission-critical databases requiring 99.99% availability (e.g., using Patroni for PostgreSQL or Orchestrator for MySQL).

### When Manual Failover is Acceptable
- Systems with low SLA requirements where human verification eliminates any risk of uncoordinated failover errors.

## Real-World Examples
- **GitHub Incident (2018)**: An internal fiber cut severed communications between datacenters. An automated failover script promoted a replica in the secondary datacenter that had 43 seconds of replication lag. Both datacenters accepted writes simultaneously, resulting in a 24-hour outage to manually resolve data conflicts.
- **Patroni (PostgreSQL)**: The industry-standard HA template for PostgreSQL. Uses **etcd** consensus to guarantee that exactly one node holds the leader key lease at any second; if the leader loses its etcd lease, it immediately demotes itself to read-only mode.

## Common Pitfalls
- **Two-Node Clusters**: Deploying exactly 2 database nodes without an external third arbiter. If the network link cuts, both nodes see 1 node alive and 1 dead, making majority voting mathematically impossible. (Always deploy an odd number: 3 or 5 consensus nodes!).
- **Unfenced Zombie Masters**: Failing to cut write access to the old primary; upon recovering from a temporary kernel freeze, the old master continues writing data until clients discover divergent states.

## Key Takeaways
- Always deploy an **odd number of consensus arbiters (3 or 5)** to guarantee majority voting.
- **Fencing tokens** (monotonically increasing epoch numbers) are mandatory to reject zombie primary writes.
- Never promote a read replica without verifying its replication log sequence number (LSN).

## Common Interview Questions
1. What is Split-Brain, and why is it considered the most catastrophic failure in distributed databases?
2. How do Fencing Tokens prevent a zombie primary from corrupting storage after a network partition heals?
3. Why can a two-node database cluster never safely implement automated leader election?

## Further Reading
- [Martin Kleppmann: How to do distributed locking (Fencing Tokens)](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
- [Zalando: Patroni PostgreSQL High Availability Documentation](https://patroni.readthedocs.io/en/latest/)
""")

save("docs/06-data-partitioning-and-replication/07-quorum-reads-and-writes.md", """# Quorum Reads and Writes in Leaderless Systems

## Overview
In leaderless distributed databases (such as Amazon Dynamo, Apache Cassandra, and ScyllaDB), any replica node can accept read and write operations directly from clients. To maintain data consistency without a central leader, these systems rely on **Quorum Consensus Mathematics**.

A **quorum** is the minimum number of participating replica nodes that must successfully acknowledge a read or write operation for the operation to be considered valid and complete.

```mermaid
graph TD
    ClientWrite[Client Write: W = 2] --> N1[Node 1: ACK]
    ClientWrite --> N2[Node 2: ACK]
    ClientWrite -.-> N3[Node 3: Offline / Slow]
    Note over ClientWrite, N2: Write Quorum Satisfied (2 of 3)
    ClientRead[Client Read: R = 2] --> N2[Node 2: Version 2]
    ClientRead --> N3[Node 3: Version 1 Stale]
    Note over ClientRead, N3: Read Overlaps Node 2! Version 2 Wins!
```

## Why It Matters
Quorums allow architects to dynamically tune the trade-off between **strong consistency** and **write availability** on a per-query basis. Understanding quorum equations ensures your system never serves stale data while surviving multiple node crashes.

## Core Concepts & The Quorum Equation
A leaderless cluster configures three fundamental parameters:
- **$N$**: The Replication Factor (number of nodes storing a copy of the data; typically $N = 3$ or $N = 5$).
- **$W$**: The Write Quorum (number of replicas that must confirm a write before returning success to the client).
- **$R$**: The Read Quorum (number of replicas queried in parallel when reading data).

### The Strong Consistency Condition
$$\\mathbf{R + W > N}$$
By the **Pigeonhole Principle**, if the sum of nodes read ($R$) and nodes written ($W$) exceeds the total replication factor ($N$), **the set of read nodes and the set of write nodes MUST overlap by at least one node**.
That overlapping node is guaranteed to return the latest versioned data (highest timestamp / version number).

### Standard Quorum Configurations ($N = 3$)
1. **Strong Consistency ($R = 2, W = 2$)**:
   - $R + W = 4 > 3$. Strong consistency guaranteed!
   - Can tolerate **1 node failure** for both reads and writes.
2. **Fast Writes / Weak Consistency ($W = 1, R = 2$)**:
   - $R + W = 3 \\ngtr 3$. Writes are sub-millisecond, but reads risk seeing stale data.
3. **Fast Reads ($W = 3, R = 1$)**:
   - Strong consistency, but any single node crash blocks all writes ($W = 3$ impossible).

## How It Works: Healing Stale Replicas
When $R$ replicas are read, they return their internal version timestamps. If Node 1 returns Version 2 and Node 2 returns Version 1, the client/coordinator returns Version 2 and initiates background healing:
1. **Read Repair**: The coordinator node asynchronously pushes the latest Version 2 data to Node 2 to bring it up to date.
2. **Sloppy Quorum & Hinted Handoff**:
   - If a network partition isolates primary replicas, the coordinator writes the update to temporary fallback nodes (Sloppy Quorum).
   - When the primary nodes rejoin, the fallback nodes deliver the saved updates (**Hinted Handoff**).
3. **Anti-Entropy with Merkle Trees**:
   - Background daemon comparing cryptographic hashes of data ranges (Merkle Trees) between replicas to detect and repair out-of-sync keys.

## Trade-offs
| Configuration ($N = 3$) | Read Latency | Write Latency | Consistency Guarantee | Fault Tolerance |
| :--- | :--- | :--- | :--- | :--- |
| **$W = 2, R = 2$ (Quorum)** | Moderate | Moderate | **Strong (Linearizable reads)**| Tolerates 1 dead node |
| **$W = 1, R = 1$ (Fastest)**| **Ultra-fast** | **Ultra-fast** | Eventual (High stale read risk)| Tolerates 2 dead nodes |
| **$W = 3, R = 1$ (All Writes)**| Fast | Slow | Strong | Zero write fault tolerance |

## When to Use / When NOT to Use
### When to Use Strong Quorums ($R + W > N$)
- User balance updates, inventory quantities, critical state machines in Cassandra/DynamoDB.

### When to Use Eventual Quorums ($W = 1, R = 1$)
- High-volume sensor logs, chat message history, activity feeds where speed and 100% write uptime outweigh brief staleness.

## Real-World Examples
- **Apache Cassandra**: Allows specifying consistency per query:
  `SELECT * FROM users WHERE id = 1 USING CONSISTENCY QUORUM;`
  `INSERT INTO logs (...) VALUES (...) USING CONSISTENCY ONE;`
- **Amazon DynamoDB**: Standard reads use $R = 1$ (eventually consistent, 0.5 RCU). Specifying `ConsistentRead = true` uses $R = 2$ (strong consistency, costs 1 full RCU).

## Common Pitfalls
- **Assuming $R + W > N$ Guarantees Linearizability under Edge Cases**: Concurrent writes with identical timestamps or failed writes that partially updated 1 node can still produce transient read anomalies.
- **Ignoring Clock Skew in Last-Write-Wins (LWW)**: In Cassandra, tie-breaking between replicas relies on client-side timestamps; NTP clock drift between client servers can cause an older write to overwrite a newer write.

## Key Takeaways
- **$R + W > N$** guarantees strong consistency via the Pigeonhole Principle.
- Replicas heal discrepancies via **Read Repair**, **Hinted Handoff**, and **Merkle Tree Anti-Entropy**.
- Tune $W=1$ for maximum write throughput, or $W=\text{Quorum}$ for data safety.

## Common Interview Questions
1. Why does $R + W > N$ mathematically guarantee that a client reads the latest write?
2. What is the difference between a Strict Quorum and a Sloppy Quorum?
3. How do Merkle Trees minimize network bandwidth during background anti-entropy repairs?

## Further Reading
- [Werner Vogels: Eventually Consistent (Communications of the ACM, 2009)](https://cacm.acm.org/magazines/2009/1/15662-eventually-consistent/fulltext)
- [Apache Cassandra Documentation: How is Consistency Configured?](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html#tunable-consistency)
""")

print("Section 06 complete.")
