# Section 06: Data Partitioning and Replication — Solutions

### Solution 1: Shard Key Trade-offs
1. **`order_id`**:
   - *Pros*: Extremely uniform write distribution across all shards.
   - *Cons*: Fetching a customer's order history (`WHERE customer_id = X`) requires an expensive scatter-gather query across all shards.
2. **`customer_id`**:
   - *Pros*: Excellent for customer queries—all orders for a user reside on a single shard, allowing local atomic transactions.
   - *Cons*: Risk of hotspots if commercial enterprise accounts place millions of orders.
3. **`order_date`**:
   - *Pros*: Great for archiving old data.
   - *Cons*: **Catastrophic write hotspot**! 100% of all current writes hit the single shard designated for today's date, while historic shards sit idle.
- **Verdict**: Sharding by `customer_id` is the industry standard for customer-facing applications.

---

### Solution 2: Celebrity Hotspot Mitigation
1. **Bottleneck**: Sharding by `user_id` places the celebrity's entire timeline and notifications on one physical node, causing network interface saturation and disk I/O throttling.
2. **Mitigation 1 (Key Salting)**:
   - Append a random suffix/salt to the celebrity ID: `user_id_1`, `user_id_2`, ..., `user_id_10`.
   - Writes are distributed across 10 distinct shards. Read queries scatter-gather across only these 10 shards.
3. **Mitigation 2 (Hybrid Fan-Out)**:
   - Normal users use fan-out-on-write (pushing to follower timeline caches).
   - Celebrity posts are NOT pushed to 60 million timelines; instead, followers fetch celebrity posts on read and merge them dynamically.

---

### Solution 3: Quorum Reads and Writes
1. **Proof of Strong Consistency**:
   - $N = 5, W = 3, R = 3$.
   - $R + W = 3 + 3 = 6$.
   - Since $R + W > N$ ($6 > 5$), the Pigeonhole Principle guarantees that the read quorum of 3 nodes and the write quorum of 3 nodes must overlap by at least **1 node**. That overlapping node will return the latest versioned data (highest timestamp).
2. **Anomalies with $W = 1, R = 2$**:
   - $R + W = 1 + 2 = 3 \le 5$. Quorums do not overlap!
   - A client may write to Node 1, and subsequent reads from Nodes 2 and 3 will return stale, outdated data (violating linearizability and read-your-writes).

---

### Solution 4: Read-Your-Writes Consistency
1. **The Bug**: The user uploads their photo, the page reloads, the read hits a replica that hasn't received the replication stream yet, and the user still sees their old profile picture. The user submits the form repeatedly, assuming the upload failed.
2. **Solutions**:
   - **Time-based Routing**: For 5 seconds following any write by User X, route User X's read queries directly to the Primary database. All other users read from replicas.
   - **Replication LSN / Timestamp Tracking**: Store the transaction Log Sequence Number (LSN) or update timestamp in the client's session cookie. The replica rejects the read or waits if its current LSN is behind the user's cookie LSN.

---

### Solution 5: Split-Brain Prevention
1. **Split-Brain Disaster**:
   - Datacenter 2 assumes Primary in Datacenter 1 is dead and promotes the Standby to Primary.
   - Datacenter 1's Primary is still alive and accepting writes from clients routed to it.
   - Both databases accept divergent writes simultaneously. Reconciling conflicting data later is mathematically impossible without data loss.
2. **Consensus & Fencing Tokens**:
   - Promotion requires a **strict majority quorum** across an odd number of voting nodes (e.g., 3 datacenters). A datacenter with only 1 out of 3 votes cannot promote itself.
   - Storage engines enforce **Fencing Tokens** (monotonically increasing epoch numbers). Storage nodes reject any write bearing an older epoch number from a zombie primary.
