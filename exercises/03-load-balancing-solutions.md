# Section 03: Load Balancing and Proxies — Solutions

### Solution 1: Load Balancing Algorithm Selection
1. **Failure of Round Robin**: Round Robin distributes an equal number of requests to all nodes regardless of hardware capacity or current load. The 4-core servers will receive the identical request volume as 16-core servers, and long-running 8-second requests will quickly saturate the worker threads of the smaller nodes, causing request queuing and 504 Gateway Timeouts.
2. **Recommended Algorithm**: **Weighted Least Connections**.
   - "Weighted": Assign weights proportionally to server capacity (e.g., weight 4 for 16-core nodes, weight 1 for 4-core nodes).
   - "Least Connections": Dynamically dispatches requests to the server currently processing the fewest active concurrent requests, naturally accommodating variable execution times.

---

### Solution 2: Consistent Hashing Node Failure
1. **Impact without Virtual Nodes**:
   - Only keys mapped to the segment between node $A$ and node $B$ on the ring are affected (roughly $1/4$ or $25\%$ of keys).
   - Crucially, **100% of server B's keys fall entirely onto its immediate clockwise successor (Server C)**. Server C's load suddenly doubles from 25% to 50%, often triggering a cascading crash of Server C.
2. **Protection via Virtual Nodes**:
   - With virtual nodes (e.g., 200 vnodes per physical node), Server B's tokens are interleaved uniformly around the entire ring.
   - When Server B crashes, its keys are evenly distributed across *all* surviving nodes (A, C, and D), increasing each node's load by only $\approx 8.3\%$.

---

### Solution 3: Sticky Sessions vs External Session Stores
1. **Imbalance with Sticky Sessions**:
   - If clients are behind large corporate proxies or NAT gateways, or if traffic arrives through shared cookies or campaign links, sticky session hashes concentrate massive blocks of users onto a single node. That single server's memory and CPU become exhausted while the other 9 servers sit idle.
2. **Stateless App Servers with Redis**:
   - The load balancer can use pure Weighted Least Connections or Round Robin, distributing the 100,000 requests evenly across all 10 nodes ($10,000$ per node).
   - Each node fetches/updates session state from a centralized Redis cluster in < 1ms, eliminating hotspots.

---

### Solution 4: Active vs Passive Health Checks
1. **Shallow Health Checks**: A simple `/healthz` returning 200 merely proves the web server process is running, not that it can execute business logic or reach the database.
2. **Robust Strategy**:
   - Combine **Active Shallow Health Checks** (every 5s for process liveness) with **Passive In-Flight Monitoring** (circuit breaker tracking 5xx rates on real customer traffic).
   - If an instance's error rate exceeds 10% over a 10-second rolling window, the proxy automatically evicts the node from the active upstream pool.

---

### Solution 5: Anycast DNS vs Geo-DNS Routing
1. **Comparison**:
   - *Anycast*: The same IP address is advertised from multiple geographic locations using BGP. The internet routing infrastructure automatically routes packets to the topologically closest datacenter. Fast failover at the network layer.
   - *Geo-DNS*: Authoritative DNS servers inspect the client IP and return different regional IP addresses based on geographic databases.
2. **Geo-DNS Pitfall**:
   - If a user in Germany uses a DNS resolver hosted in Virginia, USA (without EDNS0-Client-Subnet support), the Geo-DNS server sees the resolver's Virginia IP and incorrectly routes the German user to a US datacenter, adding 150ms of cross-Atlantic latency.
