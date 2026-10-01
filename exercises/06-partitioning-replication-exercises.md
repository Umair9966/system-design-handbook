# Section 06: Data Partitioning and Replication — Practice Exercises

---

### Problem 1: Choosing a Shard Key
You are designing the sharding scheme for an e-commerce platform with 50 million users and 2 billion orders.
Analyze the following shard key candidates for the `orders` table:
1. `order_id` (Auto-incrementing integer / UUID)
2. `customer_id`
3. `order_date`
Identify the major strengths, query limitations, and potential hotspot vulnerabilities of each candidate.
> **Hint**: Consider cross-shard joins vs single-shard reads vs temporal write hotspots.

---

### Problem 2: Mitigating the Celebrity Hot Partition
In a social network sharded by `user_id`, a regular user has 150 followers, but a celebrity has 60 million followers.
1. When the celebrity posts a message, explain how standard hash partitioning creates extreme write and read bottlenecks on the shard holding that celebrity's data.
2. Propose two architectural techniques to distribute celebrity data evenly without degrading standard user performance.
> **Hint**: Explore key salting and hybrid fan-out strategies.

---

### Problem 3: Quorum Reads and Writes Tuning
A Dynamo-style distributed database replicates data across $N = 5$ nodes.
1. If the system configures $W = 3$ and $R = 3$, does this configuration guarantee strong consistency (reading the latest write)? Prove your answer mathematically.
2. If the team reconfigures the cluster for high write throughput with $W = 1$ and $R = 2$, what consistency anomalies can clients experience?
> **Hint**: Strong consistency condition: $R + W > N$.

---

### Problem 4: Replication Lag and Read-Your-Writes Consistency
A user updates their profile picture and is immediately redirected to their profile page.
The web application routes writes to the Primary DB and all reads to 5 Read Replicas. Due to network congestion, replication lag is currently 1.8 seconds.
1. Describe the user experience bug that occurs.
2. Outline two architectural solutions to guarantee "Read-Your-Writes" consistency without routing all read traffic to the primary database.
> **Hint**: Consider routing user-specific reads to primary for a short window, or checking replication timestamps.

---

### Problem 5: Split-Brain in Automatic Failover
A primary database in Datacenter 1 is replicated to a standby replica in Datacenter 2. A network partition severs communication between the two datacenters, but both datacenters remain connected to the internet.
1. Explain how naive timeout-based automatic promotion causes a "Split-Brain" disaster.
2. How do consensus mechanisms (Raft/Paxos) and fencing tokens prevent split-brain?
> **Hint**: A node must achieve a majority quorum ($> 50\%$) to promote itself.

---

👉 **Solutions**: Check [Section 06 Solutions](06-partitioning-replication-solutions.md).
