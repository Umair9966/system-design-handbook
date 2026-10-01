# Section 01: Fundamentals — Solutions

### Solution 1: Uptime and The Nines
1. **Allowable Downtime for 99.99%**:
   - Total minutes per year = $365 \times 24 \times 60 = 525,600\text{ minutes}$.
   - Allowed downtime = $525,600 \times (1 - 0.9999) = 525,600 \times 0.0001 = 52.56\text{ minutes/year}$.
2. **Impact of 45-minute Outage**:
   - The 45-minute outage consumed $45 / 52.56 \approx 85.6\%$ of the entire year's error budget in a single incident.
   - While technically not breaching 52.56 minutes, only $7.56$ minutes of downtime remain for the rest of the year.
   - Availability during this year (assuming no other downtime) = $(525,600 - 45) / 525,600 = 99.9914\%$.

---

### Solution 2: Latency and Little's Law
1. **Concurrent In-Flight Requests**:
   - $\lambda = 12,000\text{ requests/second}$, $W = 250\text{ ms} = 0.25\text{ seconds}$.
   - $L = \lambda \times W = 12,000 \times 0.25 = 3,000\text{ concurrent in-flight requests}$.
2. **Impact of Latency Spike to 1.5s**:
   - $L_{new} = 12,000 \times 1.5 = 18,000\text{ concurrent in-flight requests}$.
   - A 6x increase in concurrent connections causes socket exhaustion, thread pool saturation, memory exhaustion, and cascading timeouts across upstream services.

---

### Solution 3: Horizontal vs Vertical Scaling Economics
1. **Trade-offs**:
   - *Vertical*: Fast in the short term (zero code changes), but hits a strict physical ceiling (diminishing CPU returns due to NUMA/memory bus contention) and cost grows exponentially. If the single giant instance crashes, the entire platform goes down (100% downtime).
   - *Horizontal*: Cost scales linearly using commodity hardware. High resilience (if 1 node fails, remaining $N-1$ nodes absorb traffic).
2. **Mandatory Software Changes**:
   - Remove all in-memory user session state (offload to Redis or use signed JWTs).
   - Offload file uploads to centralized object storage (AWS S3) rather than local disk.
   - Decouple singleton background cron jobs using distributed schedulers or distributed locks.

---

### Solution 4: Identifying Hidden SPOFs
1. **Identified SPOFs**:
   - *Primary PostgreSQL DB*: If the primary database crashes, all write traffic fails immediately. Read replicas cannot take writes without promotion.
   - *Single Redis Cache Node*: If Redis crashes, all read requests suddenly stampede the primary DB, risking total database collapse.
   - *Single L4 Load Balancer*: While cloud provider load balancers are usually internally redundant, a single logical regional balancer without multi-region DNS failover is an availability risk.
2. **Mitigations**:
   - Implement automated database failover with active health monitoring and consensus-based replica promotion (e.g., Patroni / AWS RDS Multi-AZ).
   - Deploy Redis in Cluster or Sentinel mode with automatic master-replica failover.
   - Use multi-AZ deployment and configure Global Server Load Balancing (GSLB) with Route53 health checks.

---

### Solution 5: Statelessness and Session Offloading
1. **Problems with In-Memory Sessions**:
   - Requires "sticky sessions" at the load balancer, which prevents even distribution of traffic and causes hotspots.
   - During rolling deployments or node crashes, users pinned to terminated nodes lose their shopping carts and get logged out.
2. **Alternative Patterns**:
   - *Pattern A: Distributed Session Store (Redis)*. Application nodes read/write cart state from a shared Redis cluster. Latency is sub-2ms, highly reliable, and instances can scale from 1 to 100 dynamically.
   - *Pattern B: Client-Side Signed Cart Tokens (Cookies/LocalStorage)*. Cart data is serialized, encrypted/signed, and sent with each request. Zero server-side storage overhead, but increases request bandwidth and payload size.
