# Section 01: Fundamentals — Practice Exercises

Test your understanding of core system design fundamentals. Try to solve these problems without looking at the solutions.

---

### Problem 1: Uptime and The Nines
A mission-critical financial system commits to 99.99% ("four nines") availability annually.
1. Calculate the maximum allowable downtime in minutes per year (assume 365 days).
2. If an unhandled database deadlock causes a 45-minute outage, did the service breach its annual SLA? What availability percentage does this single incident represent?
> **Hint**: 1 year = 365 × 24 × 60 = 525,600 minutes. Downtime = Total minutes × (1 - Availability).

---

### Problem 2: Latency and Little's Law
An API gateway receives a steady arrival rate of 12,000 requests per second (RPS). Downstream profiling reveals that the average request processing latency is 250 milliseconds.
1. Using Little's Law ($L = \lambda W$), how many concurrent in-flight requests must the gateway and downstream microservices hold simultaneously in memory?
2. If downstream database degradation increases average latency to 1.5 seconds while arrival rate remains constant, what happens to concurrent in-flight requests and memory pressure?
> **Hint**: Ensure time units match ($\lambda$ in seconds, $W$ in seconds).

---

### Problem 3: Horizontal vs Vertical Scaling Economics
A social networking startup runs its monolithic backend on a single 64-core, 256 GB RAM server costing $1,200/month. Traffic is projected to grow 4x over the next 6 months.
1. Analyze the technical risks and economic trade-offs of vertically upgrading to a 256-core server versus re-architecting into stateless horizontally scaled nodes behind a load balancer.
2. What software design changes are mandatory before the service can scale horizontally across multiple commodity VMs?
> **Hint**: Think about where in-memory sessions, local disk uploads, and scheduled cron jobs reside.

---

### Problem 4: Identifying Hidden SPOFs
Examine the following simplified production architecture:
`Clients -> Single Cloud L4 Load Balancer -> 5 Stateless App Servers -> 1 Primary PostgreSQL DB (with 2 Read Replicas) -> 1 Redis Cache Node`.
1. Identify all Single Points of Failure (SPOFs) in this topology.
2. Outline specific architectural upgrades to eliminate each identified SPOF.
> **Hint**: What happens if the primary database fails during a write? What happens if the Redis cache restarts?

---

### Problem 5: Statelessness and Session Offloading
An e-commerce website stores user shopping cart contents in web server application memory (`HttpSession`).
1. Why does this design prevent efficient auto-scaling and zero-downtime rolling deployments?
2. Propose two alternative architectural patterns for storing shopping cart state. Compare them in terms of latency, operational complexity, and network overhead.
> **Hint**: Consider client-side encrypted tokens vs centralized distributed stores (Redis/DynamoDB).

---

👉 **Solutions**: When you have completed your answers, check [Section 01 Solutions](01-fundamentals-solutions.md).
