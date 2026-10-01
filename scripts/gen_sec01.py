import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 01: FUNDAMENTALS
# =========================================================================

save("docs/01-fundamentals/01-what-is-system-design-and-requirements.md", """# What System Design Is: Functional vs Non-Functional Requirements

## Overview
**System design** is the systematic process of defining the architecture, components, modules, interfaces, and data for a software system to satisfy specified business and technical constraints. In production engineering, it bridges the gap between high-level product vision and low-level code execution.

At its core, system design requires translating ambiguous user problems into well-defined, scalable, and resilient technical contracts categorized into **Functional Requirements (FR)** and **Non-Functional Requirements (NFR)**.

```mermaid
graph TD
    A[Ambiguous Product Goal] --> B{Requirements Analysis}
    B --> C[Functional Requirements: What the system does]
    B --> D[Non-Functional Requirements: How well it does it]
    C --> E[API Contracts & Schemas]
    D --> F[SLAs, SLIs, Topology & Capacity]
    E & F --> G[Production Architecture]
```

## Why It Matters
Without disciplined requirements scoping, systems suffer from two fatal failure modes:
1. **Under-engineering**: Building an architecture incapable of handling peak production traffic spikes, leading to cascading outages, data corruption, and SLA violations.
2. **Over-engineering**: Introducing distributed complexity (e.g., event sourcing, microservices, multi-region Raft clusters) for applications that could comfortably run on a single PostgreSQL instance, draining engineering velocity and inflating infrastructure costs.

## Core Concepts
- **Functional Requirements (FR)**: The concrete capabilities and user-facing workflows the system must support (e.g., *"Users can upload a video"*, *"Users can send money to a peer"*).
- **Non-Functional Requirements (NFR)**: The quality attributes, operational limits, and constraints under which the system must operate:
  - **Availability**: Percentage of time the system remains operational and accessible (e.g., 99.99%).
  - **Latency**: Bound on response duration, typically measured at percentiles (e.g., P99 < 100ms).
  - **Throughput**: Number of operations processed per unit time (e.g., 50,000 QPS).
  - **Consistency**: The degree of state uniformity across replicas (e.g., linearizable vs eventual).
  - **Durability**: Probability that stored records survive hardware loss (e.g., 99.999999999% in S3).

## How It Works: Scoping Requirements Step-by-Step
When architecting any system, follow a repeatable extraction framework:
1. **Define Core Verbs**: Identify the 2 to 4 mission-critical operations. Eliminate nice-to-have features into "Out of Scope".
2. **Quantify Workload Scale**:
   - Daily Active Users (DAU) & Monthly Active Users (MAU).
   - Read-to-Write Ratio (e.g., 100:1 for social feeds, 1:1 for telemetry).
   - Average and peak Queries Per Second (QPS).
3. **Establish Service Level Objectives (SLOs)**:
   - What is the acceptable P95 and P99 latency?
   - What data loss window is permissible (Recovery Point Objective - RPO)?
4. **Identify Regulatory & Geographic Constraints**:
   - Data residency (GDPR, HIPAA, PCI-DSS).

## Trade-offs
| Requirement Dimension | High Guarantee Benefit | Engineering Cost / Trade-off |
| :--- | :--- | :--- |
| **Strict Consistency (ACID/Linearizable)** | Zero stale reads, simplified app logic | Increased write latency, coordination bottlenecks, lower availability during partitions |
| **Ultra-High Availability (99.999%)** | Minimal downtime (< 5.26 mins/year) | Redundant multi-region infrastructure, automated failovers, high cloud cost |
| **Sub-10ms P99 Latency** | Superior user engagement and conversion | Multi-layer caching, in-memory data tiers, complexity of cache invalidation |

## When to Use / When NOT to Use
### When to Focus on Strict NFRs
- Financial ledgers, healthcare records, payment processors, and auth systems where data loss or inconsistency causes catastrophic business impact.

### When to Defer Complex NFRs
- Early-stage prototypes, internal tooling, and MVPs validating product-market fit where shipping speed outweighs five-nines availability.

## Real-World Examples
- **Stripe**: Treats consistency and durability as non-negotiable functional constraints. Every ledger entry requires double-entry accounting and synchronous replication across availability zones.
- **Twitter/X**: Sacrifices strict consistency for global availability. A 2-second delay in tweet delivery to follower feeds is an acceptable trade-off for handling 300,000 timeline reads per second.

## Common Pitfalls
- **Confusing Average Latency with P99**: Designing for average latency masks severe tail latency; a 50ms average can hide a P99 of 4,000ms affecting 1 out of every 100 requests.
- **Vague Requirements**: Writing *"The system must be fast and reliable"* instead of *"P99 latency < 150ms at 25,000 QPS with 99.99% monthly availability"*.

## Key Takeaways
- Functional requirements define **what** a system executes; non-functional requirements define **how well** it performs.
- Always quantify requirements with concrete numbers (QPS, storage, P99 latency) before choosing databases or frameworks.
- Clarify out-of-scope features early to avoid architectural bloat.

## Common Interview Questions
1. How do you prioritize conflicting requirements between low latency and strong consistency?
2. What questions would you ask a product manager when asked to "design a messaging service"?
3. How do you distinguish between system availability, reliability, and durability?

## Further Reading
- [Google Site Reliability Engineering: Chapter 3 (Service Level Objectives)](https://sre.google/sre-book/service-level-objectives/)
- [Designing Data-Intensive Applications: Chapter 1 (Reliable, Scalable, and Maintainable Systems)](https://dataintensive.net/)
""")

save("docs/01-fundamentals/02-scalability-vertical-vs-horizontal.md", """# Scalability: Vertical vs Horizontal Scaling

## Overview
**Scalability** is the measure of a system's ability to handle growing amounts of work by adding resources to the system. There are two primary paradigms for scaling:
- **Vertical Scaling (Scale-Up)**: Adding more processing power, memory, or storage to an existing single machine (e.g., upgrading from a 16-core to a 128-core bare-metal instance).
- **Horizontal Scaling (Scale-Out)**: Adding more discrete machines/nodes into a networked pool to distribute the workload (e.g., expanding from 5 to 50 stateless application instances behind a load balancer).

```mermaid
graph LR
    subgraph Vertical Scaling [Scale-Up]
        A[Small Server: 4 Core, 16GB] -->|Upgrade Hardware| B[Giant Server: 128 Core, 1TB]
    end
    subgraph Horizontal Scaling [Scale-Out]
        C[Load Balancer] --> D[Node 1]
        C --> E[Node 2]
        C --> F[Node N...]
    end
```

## Why It Matters
Workloads grow over time due to business adoption or sudden flash sales. Knowing when to scale vertically versus horizontally determines whether your infrastructure costs scale linearly or exponentially, and whether your system has a single point of failure (SPOF).

## Core Concepts
- **Amdahl's Law**: The theoretical speedup of a task is limited by the serial (non-parallelizable) portion of the program:
  $$S_{latency}(s) = \\frac{1}{(1 - p) + \\frac{p}{s}}$$
  Where $p$ is the fraction of parallelizable code, and $s$ is the speedup factor.
- **Shared-Nothing Architecture**: Distributed architecture where each independent node possesses its own private CPU, RAM, and disk. Nodes communicate solely through high-speed network protocols.
- **Stateless Distribution**: Application nodes maintain zero client session state across requests, allowing any incoming request to land on any server node arbitrarily.

## How It Works
1. **Vertical Mechanics**: Operating systems leverage symmetric multiprocessing (SMP) and Non-Uniform Memory Access (NUMA). Processes scale by spawning concurrent OS threads accessing a shared memory bus.
2. **Horizontal Mechanics**: Traffic hits an ingress Layer 4 / Layer 7 load balancer. The load balancer runs scheduling algorithms (e.g., Round Robin, Least Connections, Consistent Hashing) to distribute requests across the cluster.

## Trade-offs
| Dimension | Vertical Scaling (Scale-Up) | Horizontal Scaling (Scale-Out) |
| :--- | :--- | :--- |
| **Complexity** | Extremely low (zero distributed systems bugs) | High (requires service discovery, load balancing, consensus) |
| **Hardware Limits** | Hard ceiling (maximum CPU sockets and PCIe channels) | Theoretically unbounded (add thousands of nodes) |
| **Cost Scaling** | Exponential at the high end (specialized high-core servers) | Linear using commodity VMs or cloud instances |
| **Fault Tolerance** | Single Point of Failure (node crash = total outage) | High resilience (failure of 1 of 50 nodes is negligible) |
| **Network Overhead**| Zero network latency (inter-thread memory communication)| Network transport serialization and packet latency (0.5ms+)|

## When to Use / When NOT to Use
### When to Scale Vertically
- Early-stage startups prioritizing development speed.
- Relational databases (PostgreSQL/MySQL) up to moderate scale (~10,000 QPS) where ACID transactions are critical and read replicas suffice.

### When to Scale Horizontally
- Stateless application layers, API gateways, and web servers.
- Massive data stores requiring petabyte-scale storage and write throughput beyond a single disk controller (Cassandra, Bigtable, Kafka).

## Real-World Examples
- **Stack Overflow**: Famous for scaling predominantly vertically for years on a handful of powerful multi-socket Microsoft SQL Server machines, handling millions of pageviews with exceptional operational simplicity.
- **Netflix**: Scaled horizontally across tens of thousands of AWS EC2 instances, leveraging microservices and Chaos Monkey to withstand arbitrary instance terminations.

## Common Pitfalls
- **Premature Horizontal Decomposition**: Splitting an application into 30 microservices before identifying core domain boundaries, creating network serialization overhead and distributed transaction hell.
- **Ignoring NUMA Effects on Scale-Up**: Assuming a 128-core machine yields 8x the speed of a 16-core machine without accounting for inter-socket memory latency.

## Key Takeaways
- Start vertically whenever possible to minimize operational complexity; scale horizontally when physical limits, fault-tolerance needs, or economics demand it.
- Horizontal scaling requires making the application tier strictly **stateless**.
- Amdahl's Law dictates that serialization bottlenecks cap horizontal scaling efficiency.

## Common Interview Questions
1. At what point does vertical scaling become economically non-viable compared to horizontal scaling?
2. How do you design an application so that it can scale horizontally without session affinity?
3. What is the difference between Amdahl's Law and Gustafson's Law in scalable systems?

## Further Reading
- [Amdahl's Law: Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities (1967)](https://dl.acm.org/doi/10.1145/1465482.1465560)
- [Martin Fowler: MonolithFirst Pattern](https://martinfowler.com/bliki/MonolithFirst.html)
""")

save("docs/01-fundamentals/03-latency-throughput-bandwidth.md", """# Latency, Throughput, and Bandwidth

## Overview
Performance in distributed systems is defined by three interrelated dimensions:
- **Latency**: The time taken for a data packet or request to travel from its origin to its destination and return (measured in milliseconds or microseconds).
- **Throughput**: The volume of work completed by the system per unit of time (measured in Requests Per Second - RPS, Queries Per Second - QPS, or Transactions Per Second - TPS).
- **Bandwidth**: The maximum theoretical data transfer capacity of a communications channel (measured in bits per second, e.g., 10 Gbps).

```mermaid
graph LR
    subgraph Network Pipeline
        A[Client Request] -->|Latency: Time to Traverse| B[Server Processing]
        B -->|Throughput: Number of Requests Processed/Sec| C[Response]
    end
    D[Pipe Width = Bandwidth Gbps]
```

## Why It Matters
A system can possess massive bandwidth yet deliver terrible user experience due to high latency. Conversely, a low-latency system can buckle under load if its throughput capacity is exhausted. Understanding their exact mathematical relationships prevents performance bottlenecks.

## Core Concepts
- **Little's Law**: In a stable queueing system, the long-term average number of concurrent items $L$ is equal to the long-term average arrival rate $\\lambda$ multiplied by the average time $W$ that an item spends in the system:
  $$L = \\lambda \\times W$$
  *Example*: If your API receives $\\lambda = 10,000$ RPS and the average processing time is $W = 0.2$ seconds (200ms), your servers must concurrently sustain:
  $$L = 10,000 \\times 0.2 = 2,000\\text{ in-flight requests}$$
- **Tail Latency Amplification**: In distributed microservice graphs where a single user request fans out to $N$ downstream services in parallel, the user-perceived response time is governed by the *slowest* downstream service:
  $$P(\\text{User hits }> 99\\text{th percentile}) = 1 - (0.99)^N$$
  For $N = 100$ parallel backend calls, **63.4% of users experience latency worse than the 99th percentile**!

## How It Works
1. **Network Latency Components**:
   - *Propagation Delay*: Distance divided by speed of light in fiber ($\approx 200,000\\text{ km/s}$).
   - *Transmission Delay*: Packet size divided by channel bandwidth.
   - *Processing Delay*: Time taken by routers/firewalls to inspect headers.
   - *Queuing Delay*: Time spent waiting in network buffer queues before transmission.
2. **Measuring Latency Accurately**: Avoid arithmetic averages ($Mean$). Always measure percentiles: **P50 (Median)**, **P95**, **P99**, and **P99.9**.

## Trade-offs
| Optimization Strategy | Latency Impact | Throughput Impact |
| :--- | :--- | :--- |
| **Request Batching** (e.g., Kafka producer batching) | Increases latency (awaits buffer fill) | Dramatically increases throughput (amortizes network headers) |
| **Payload Compression** (gzip/Zstandard) | Adds CPU serialization latency | Decreases bandwidth consumption, boosts network throughput |
| **Connection Pooling** | Eliminates TCP/TLS handshake latency | Caps maximum concurrent throughput to pool size |

## When to Use / When NOT to Use
### When to Optimize for Ultra-Low Latency
- High-frequency financial trading, real-time gaming, autonomous vehicle telemetry.

### When to Prioritize Throughput over Latency
- Big data batch analytics (MapReduce/Spark), log processing pipelines, video transcoding queues.

## Real-World Examples
- **Google Search**: Proved that adding an artificial 400ms delay to search results caused a 0.44% drop in search traffic.
- **Amazon**: Discovered that every 100ms of additional latency reduced sales revenue by 1%.

## Common Pitfalls
- **Coordinated Omission**: Benchmarking tools that wait for a request to complete before sending the next one inadvertently omit the latency of queued requests, reporting deceptively optimistic percentiles.
- **Ignoring Network Hop Latency**: Assuming RPC calls between microservices inside AWS are negligible; inter-AZ round trips routinely introduce 1-2ms of baseline latency per hop.

## Key Takeaways
- Use **Little's Law** ($L = \\lambda W$) to accurately size thread pools and memory capacity.
- Never measure performance using averages—always monitor P95, P99, and P99.9 percentiles.
- In fan-out architectures, tail latency dominates overall user experience.

## Common Interview Questions
1. A service has an average response time of 50ms and receives 2,000 QPS. How many concurrent connections must it maintain?
2. Why is tail latency amplification particularly dangerous in microservice architectures?
3. How does increasing TCP window size affect throughput on high-latency links (BDP)?

## Further Reading
- [The Tail at Scale (Jeffrey Dean and Luiz André Barroso, Google, 2013)](https://research.google/pubs/pub40801/)
- [Gil Tene: Understanding Latency and Coordinated Omission](https://www.youtube.com/watch?v=lJ8ydIuPFeU)
""")

save("docs/01-fundamentals/04-availability-reliability-durability.md", """# Availability, Reliability, Durability, and The Nines

## Overview
System dependability is measured through three distinct engineering dimensions:
- **Availability**: The percentage of time a system remains operational and capable of servicing requests.
- **Reliability**: The probability that a system will perform its required function without failure under specified conditions over a given duration (measured by Mean Time Between Failures - MTBF).
- **Durability**: The guarantee that stored data remains uncorrupted and intact over time, surviving physical hardware failures.

```mermaid
graph TD
    subgraph Dependability Triangle
        A[Availability: Is it responding right now?]
        B[Reliability: Does it execute correctly without crashing?]
        C[Durability: Will my data still exist 10 years from now?]
    end
```

## Why It Matters
A system can be 100% available while being completely unreliable (e.g., returning HTTP 500 errors within 1ms for every request). Conversely, an offline database backup is 100% durable even while having 0% operational availability. Distinguishing these concepts is essential when agreeing on contractual SLAs.

## Core Concepts
- **The "Nines" of Availability**:
  - $99\\%$ ("Two Nines"): $\\approx 3.65$ days of allowable downtime per year.
  - $99.9\\%$ ("Three Nines"): $\\approx 8.76$ hours of allowable downtime per year.
  - $99.99\\%$ ("Four Nines"): $\\approx 52.56$ minutes of allowable downtime per year.
  - $99.999\\%$ ("Five Nines"): $\\approx 5.26$ minutes of allowable downtime per year.
- **MTBF and MTTR**:
  $$\\text{Availability} = \\frac{\\text{MTBF}}{\\text{MTBF} + \\text{MTTR}}$$
  Where MTBF is Mean Time Between Failures, and MTTR is Mean Time To Repair / Recover.
- **Composite Availability**:
  - **Serial Components** (both must work):
    $$A_{total} = A_1 \\times A_2$$
    *Example*: If Web Tier ($99.9\\%$) relies on Database ($99.9\\%$), total availability = $0.999 \\times 0.999 = 99.8\\%$.
  - **Parallel Components** (redundant standby):
    $$A_{total} = 1 - (1 - A_1)(1 - A_2)$$
    *Example*: Two redundant $99.9\\%$ databases = $1 - (0.001)^2 = 99.9999\\%$.

## How It Works
To increase system availability:
1. **Reduce MTBF frequency**: Enforce code review, comprehensive unit/integration testing, canary rollouts, and chaos testing.
2. **Minimize MTTR**: Implement automated health checks, instant DNS failovers, self-healing container orchestrators (Kubernetes), and blameless incident runbooks.

## Trade-offs
| Availability Level | Downtime Allowance (Annual) | Required Engineering Investment |
| :--- | :--- | :--- |
| **99.9% (Three Nines)** | ~8.76 hours | Single cloud region, automated restarts, read replicas |
| **99.99% (Four Nines)** | ~52.56 minutes | Multi-AZ deployment, automated failover, zero-downtime schema migrations |
| **99.999% (Five Nines)** | ~5.26 minutes | Multi-region active-active, consensus protocols, chaos testing, 24/7 SRE |

## When to Use / When NOT to Use
### When to Target Five Nines (99.999%)
- Telecommunications 911 dispatch, air traffic control, medical telemetry, and central banking clearinghouses.

### When 99.9% is Sufficient
- Standard SaaS applications, B2B back-office dashboards, e-commerce storefronts during off-peak hours.

## Real-World Examples
- **AWS S3**: Advertises **99.99% availability** of service objects alongside **99.999999999% (11 9's) durability** by redundantly storing objects across multiple physically separated availability zones.
- **GitHub Outage (2018)**: A brief 43-second network split between US East and US West triggered an uncoordinated automated database failover, resulting in 24 hours of degraded read-only availability while resolving split-brain data.

## Common Pitfalls
- **Ignoring Cascading Availability Math**: Assuming that chaining 5 microservices each rated at 99.9% availability produces a 99.9% system; in reality, $0.999^5 = 99.5\\%$ availability!
- **Overpromising SLAs in Contracts**: Guaranteeing five nines without having multi-region automated active-active failover in place.

## Key Takeaways
- Availability is mathematically driven by Mean Time to Repair (MTTR); reducing recovery time improves availability faster than trying to prevent all failures.
- Serial dependencies multiply risk and lower overall availability; redundant parallel paths drastically improve composite availability.
- Durability is about data survival; availability is about service responsiveness.

## Common Interview Questions
1. If your system depends on three external microservices each offering 99.9% availability in serial, what is your theoretical maximum availability?
2. How does AWS S3 achieve 11 nines of durability?
3. How do you design an automated failover system that minimizes MTTR without risking split-brain?

## Further Reading
- [AWS Reliability Guardian: Availability Math](https://docs.aws.amazon.com/whitepapers/latest/real-time-communication-on-aws/availability-and-the-math.html)
- [Google SRE: Embracing Risk and Error Budgets](https://sre.google/sre-book/embracing-risk/)
""")

print("Section 01 generated.")
