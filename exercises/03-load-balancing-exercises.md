# Section 03: Load Balancing and Proxies — Practice Exercises

---

### Problem 1: Load Balancing Algorithm Selection
You have a cluster of 8 application servers. Servers 1-4 have 16 vCPUs / 64 GB RAM, while servers 5-8 are legacy instances with 4 vCPUs / 16 GB RAM. Incoming requests have highly variable processing durations (from 5ms to 8,000ms).
1. Explain why standard Round Robin causes severe server degradation in this cluster.
2. Which load balancing algorithm should you deploy, and why?
> **Hint**: Consider both server capacity differences and request execution variability.

---

### Problem 2: Consistent Hashing Node Failure
A caching tier utilizes consistent hashing with a 32-bit integer ring ($0$ to $2^{32}-1$) across 4 physical cache servers without virtual nodes.
1. When cache server $B$ crashes, what fraction of total cached keys are invalidated? Which server absorbs server $B$'s traffic?
2. How do virtual nodes (vnodes) prevent cascading load failures when server $B$ crashes?
> **Hint**: Without virtual nodes, only the immediate successor absorbs the load.

---

### Problem 3: Sticky Sessions vs External Session Stores
An enterprise application enables sticky sessions using an `ALB_COOKIE` injected by an AWS Application Load Balancer.
1. During a flash sale, one specific marketing influencer posts a direct link clicked by 100,000 users in 2 minutes. Why does session stickiness create an extreme load imbalance across the 10-node cluster?
2. How does refactoring to stateless app servers with Redis session storage solve this issue?
> **Hint**: What happens if the sticky session cookie hash or IP hashing maps users non-uniformly?

---

### Problem 4: Active vs Passive Health Checks
An API instance begins encountering intermittent database connection timeouts, throwing HTTP 500 errors on 30% of requests, but its CPU utilization is only 15%.
1. Why would a naive HTTP `/healthz` endpoint returning HTTP 200 based purely on process availability fail to detect this failure?
2. Design a robust deep health-check strategy that prevents traffic black-holing without overwhelming downstream databases.
> **Hint**: Balance deep dependency checks against health-check cascading storms.

---

### Problem 5: Anycast DNS vs Geo-DNS Routing
A global video streaming service needs to route users in Tokyo to the Tokyo datacenter and users in London to the London datacenter.
1. Compare BGP Anycast routing with Geo-DNS (latency-based DNS resolution).
2. What are the operational pitfalls of Geo-DNS regarding public recursive DNS resolvers (e.g., users using a US-based public DNS while located in Europe)?
> **Hint**: Review EDNS Client Subnet (ECS) extension.

---

👉 **Solutions**: Check [Section 03 Solutions](03-load-balancing-solutions.md).
