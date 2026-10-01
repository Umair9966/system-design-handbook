import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

save("docs/01-fundamentals/05-consistency-and-performance-tradeoffs.md", """# Consistency vs Performance and Scalability

## Overview
In distributed systems, **consistency** defines whether all participating nodes observe the exact same data values at any given point in time. Achieving strict consistency across physical networks requires coordination, synchronization, and locking mechanisms that directly conflict with **performance** (low latency) and **scalability** (high throughput across many nodes).

```mermaid
graph LR
    A[Client Write] --> B[Node 1]
    B -->|Synchronous Consensus & Network Wait| C[Node 2]
    B -->|Synchronous Consensus & Network Wait| D[Node 3]
    B -->|Delayed ACK to Client| E[Client Latency Penalty]
```

## Why It Matters
Physics imposes an immutable limit: data cannot travel faster than the speed of light. Every time a distributed system insists that multiple independent replicas must agree before acknowledging a write, it incurs physical network round-trip delays and coordination lock contention. Understanding this trade-off allows architects to select the right consistency model for each business domain.

## Core Concepts
- **Linearizability (Strong Consistency)**: The highest consistency guarantee. Operations appear to execute atomically at an exact global timestamp. Reads are guaranteed to observe the latest written value.
- **Eventual Consistency**: Replicas asynchronously converge over time. Reads may temporarily return stale values, but given sufficient time without new writes, all replicas will match.
- **The PACELC Theorem**: An extension of the CAP theorem stating that even in the absence of partitions ($E$ for Else), a system must trade Latency ($L$) versus Consistency ($C$).

## How It Works
1. **Synchronous Coordination**:
   - Master node receives write $W$.
   - Master broadcasts $W$ to $N$ replicas over TCP.
   - Master waits for $M$ replicas to acknowledge before returning success to the client.
   - *Result*: Strong consistency, but latency equals the slowest replica's network round trip.
2. **Asynchronous Propagation**:
   - Master receives write $W$, writes to local WAL, and immediately responds to the client (sub-1ms).
   - Master pushes $W$ to replicas asynchronously via a background stream.
   - *Result*: Ultra-low write latency and high throughput, but a concurrent read hitting a lagging replica returns stale data.

## Trade-offs
| Architecture Choice | Write Latency | Read Throughput | Data Freshness |
| :--- | :--- | :--- | :--- |
| **Synchronous Replication** (Raft/2PC) | High (waits for quorum) | Moderate | 100% Up-to-date (Linearizable) |
| **Asynchronous Replication** (MySQL Replicas) | Ultra-low (< 2ms) | Massive (distributed across replicas) | Stale reads possible (Replication Lag) |
| **Quorum Tunable** (DynamoDB / Cassandra) | Tunable via $W$ parameter | Tunable via $R$ parameter | Strong if $R + W > N$ |

## When to Use / When NOT to Use
### When to Choose Strict Consistency Over Performance
- Financial ledgers, stock trading order matching, inventory decrement during flash sales, seat booking systems.

### When to Choose Performance / Scalability Over Consistency
- Social media feeds, video view counts, analytics telemetry, collaborative document editing cursors.

## Real-World Examples
- **Google Spanner**: Invested in specialized atomic clocks and GPS receivers (TrueTime API) to bound clock uncertainty ($\le 7$ms), achieving global external consistency while keeping multi-region commit latencies within acceptable bounds (~50-100ms).
- **Amazon DynamoDB**: Allows engineers to specify consistency at the API call level: `ConsistentRead: true` incurs double the read capacity units and higher latency, whereas standard reads are eventually consistent and twice as fast/cheap.

## Common Pitfalls
- **Defaulting to Strong Consistency Everywhere**: Enforcing two-phase commit (2PC) across microservices, creating massive latency amplification and distributed deadlocks.
- **Neglecting Monotonic Read Violations**: In an eventually consistent system, refreshing a page can bounce a user between a fast replica and a lagging replica, causing deleted comments to intermittently reappear.

## Key Takeaways
- The speed of light guarantees that cross-node consensus always adds latency.
- The PACELC theorem proves that you must choose between Latency and Consistency even when your network is 100% healthy.
- Most large-scale architectures use strong consistency for financial transactions and eventual consistency for high-volume content.

## Common Interview Questions
1. How does PACELC expand upon the classic CAP theorem?
2. If an interviewer asks you to design a globally distributed inventory count system, how would you address consistency versus latency?
3. What is replication lag, and what user experience anomalies does it cause?

## Further Reading
- [Daniel Abadi: Consistency Tradeoffs in Modern Distributed Database System Design (PACELC)](https://cs-www.cs.yale.edu/homes/dna/papers/abadi-pacelc.pdf)
- [Werner Vogels: Eventually Consistent (Communications of the ACM, 2009)](https://cacm.acm.org/magazines/2009/1/15662-eventually-consistent/fulltext)
""")

save("docs/01-fundamentals/06-spof-redundancy-failover.md", """# Single Point of Failure (SPOF), Redundancy, and Failover

## Overview
A **Single Point of Failure (SPOF)** is any individual component or link in a system whose failure immediately halts the operation of the entire system. Eliminating SPOFs requires designing **redundancy** (duplicating critical hardware and software pathways) and implementing automated **failover** mechanisms that seamlessly transition workloads to healthy backups when an active component dies.

```mermaid
graph TD
    subgraph Vulnerable Architecture [With SPOF]
        A1[Client] --> B1[Single Load Balancer]
        B1 --> C1[Single Primary DB]
        style B1 fill:#ff9999,stroke:#333
        style C1 fill:#ff9999,stroke:#333
    end
    subgraph Resilient Architecture [Redundant Failover]
        A2[Client] --> B2[Active LB]
        A2 -.->|Heartbeat / VRRP| B3[Standby LB]
        B2 --> C2[Active App Pool]
        C2 --> D1[(Primary DB)]
        D1 -->|Sync Replication| D2[(Hot Standby DB)]
        D1 -.->|Consensus Health Ping| E[Consensus Manager / Patroni]
        E -.->|Promote on Crash| D2
    end
```

## Why It Matters
Modern cloud hardware fails continuously: disks corrupt, NICs drop packets, switches experience power outages, and OS kernels panic. A production system that cannot survive the loss of any single server, switch, or availability zone without downtime is fragile and unsuitable for enterprise scale.

## Core Concepts
- **Redundancy Models**:
  - **$N+1$ Redundancy**: If a system requires $N$ components to handle peak load, exactly 1 redundant component is provisioned.
  - **$2N$ (Active-Passive / Dual Modular)**: Exactly double the required capacity is provisioned.
- **Standby Tiers**:
  - **Cold Standby**: Backup instance is powered off; takes minutes/hours to provision and load state.
  - **Warm Standby**: Backup instance is running, receiving periodic state snapshots; takes seconds to promote.
  - **Hot Standby**: Backup instance runs concurrently, receives live synchronous replication, and assumes traffic in sub-second failover.
- **Heartbeat & Fencing**:
  - Continuous health pinging between nodes.
  - **Fencing (STONITH - Shoot The Other Node In The Head)**: Guarantees a severed primary node is forcefully powered down to prevent both nodes from acting as masters (Split-Brain).

## How It Works
1. **Detection**: Health monitors probe the active node (e.g., via TCP/HTTP pings every 500ms).
2. **Quorum Consensus**: A cluster of arbiters (Raft/ZooKeeper) agrees that the active node has failed after $K$ consecutive missed heartbeats.
3. **Isolation & Fencing**: The failed master is revoked of all write credentials and network VIPs.
4. **Promotion**: The hot standby with the latest WAL log sequence number (LSN) is promoted to Primary.
5. **Traffic Redirection**: The Virtual IP (VIP), DNS record, or Service Mesh router updates routing tables to the new master.

## Trade-offs
| Architecture Pattern | Availability / Recovery Speed | Cost Overhead | Split-Brain Risk |
| :--- | :--- | :--- | :--- |
| **Cold Standby** | Poor (RTO: 15-60 mins) | Minimal (pay only when needed) | Zero |
| **Active-Passive (Hot)** | Excellent (RTO: < 5 seconds) | 100% idle hardware waste | High without strict fencing |
| **Active-Active** | Instantaneous (RTO: 0) | High hardware utilization | Requires distributed conflict resolution |

## When to Use / When NOT to Use
### When to Implement Full Active-Active Redundancy
- Financial gateways, high-volume e-commerce checkouts, and identity providers where even a 30-second failover disrupts thousands of transactions.

### When Simple Warm Standbys Are Acceptable
- Data warehousing batch jobs, non-critical background report generators.

## Real-World Examples
- **GitHub Incident (2018)**: During a brief network partition, automated failover promoted a secondary database that was not fully synchronized with the primary, requiring 24 hours of manual data reconciliation.
- **AWS Direct Connect**: Recommends dual redundant connections terminating in two separate AWS edge routers located in different physical datacenters to avoid a single fiber cut severing corporate connectivity.

## Common Pitfalls
- **Split-Brain Disaster**: Network partition severs the heartbeat between primary and standby; both nodes promote themselves, accept divergent writes, and irreparably corrupt database consistency.
- **Flapping Failovers**: Overly aggressive timeout thresholds (e.g., failing over after 1 missed 100ms ping) trigger endless failover loops during transient network blips.

## Key Takeaways
- Redundancy without automated, tested failover is merely expensive spare hardware.
- Fencing tokens and majority quorum are mandatory to eliminate the split-brain hazard during failover.
- Always calculate Recovery Time Objective (RTO) and Recovery Point Objective (RPO) when designing failovers.

## Common Interview Questions
1. What is split-brain, and what specific architectural primitives prevent it during database failovers?
2. How does Active-Active differ from Active-Passive failover in terms of data replication and routing?
3. How would you design a heartbeat mechanism that avoids false-positive failovers during temporary network jitter?

## Further Reading
- [Patroni: A Template for PostgreSQL High Availability with ZooKeeper/etcd](https://github.com/patroni/patroni)
- [Martin Kleppmann: Please Stop Calling It Consistency (DDIA Chapter 8)](https://dataintensive.net/)
""")

save("docs/01-fundamentals/07-stateless-vs-stateful-services.md", """# Stateless vs Stateful Architecture

## Overview
The distinction between **stateless** and **stateful** services is one of the most critical structural decisions in system architecture:
- **Stateless Services**: Treat every request as an independent transaction completely unlinked to any previous request. Application servers retain no local memory or disk state between client calls. Any server in the cluster can handle any request.
- **Stateful Services**: Maintain internal state, persistent context, or active memory across consecutive requests (e.g., open TCP/WebSocket connections, in-memory caches, database storage engines).

```mermaid
graph TD
    subgraph Stateless Architecture
        Client1[Client] --> LB[Load Balancer]
        LB --> NodeA[App Node A: Pure Logic]
        LB --> NodeB[App Node B: Pure Logic]
        NodeA --> Redis[(Shared Redis State)]
        NodeB --> Redis
    end
    subgraph Stateful Architecture
        Client2[Client] --> StickyLB[Sticky Load Balancer]
        StickyLB -->|Session Locked| NodeC[Stateful Node C: Local RAM]
        StickyLB -.->|Cannot Route| NodeD[Stateful Node D: Local RAM]
    end
```

## Why It Matters
Stateless applications scale effortlessly: increasing traffic by 10x merely requires launching more identical containers behind a round-robin load balancer. In contrast, scaling stateful systems requires complex data partitioning, session affinity, replication protocols, and failover coordination.

## Core Concepts
- **Session Offloading**: Removing session cookies and shopping cart items from application server memory (`HttpSession`) and storing them in an external high-speed distributed cache (e.g., Redis Cluster, DynamoDB).
- **Sticky Sessions (Session Affinity)**: Routing all requests from a specific user to the exact same physical server instance based on an IP hash or routing cookie. A notorious anti-pattern that inhibits autoscaling and causes traffic hotspots.
- **Ephemeral Containers**: Architectural design where instances can be destroyed, restarted, or rescheduled at any second without data loss or user disruption.

## How It Works
1. **Stateless Flow**:
   - Client sends request with a cryptographically signed Bearer JWT or Session ID header.
   - Load balancer routes request to whichever app node has the least active connections.
   - Node validates JWT locally (statelessly) or queries the centralized Redis cluster in < 1ms to fetch user permissions.
   - Node executes business logic, writes mutations to the primary database, and returns the response.
2. **Stateful Flow (e.g., Database or Game Server)**:
   - Server holds authoritative state in RAM (e.g., player position coordinates or database buffer pool).
   - If server crashes, state must be recovered from persistent disk logs (WAL) or re-synced from peer replicas.

## Trade-offs
| Attribute | Stateless Service | Stateful Service |
| :--- | :--- | :--- |
| **Horizontal Autoscaling** | Trivial (spin up or terminate nodes dynamically) | Hard (requires data repartitioning and rebalancing) |
| **Fault Tolerance** | Instant recovery (router retries on another node) | Slow recovery (requires log replay and replica sync) |
| **Local Read Latency** | Network hop to cache/DB required (0.5-2ms) | Ultra-fast in-memory CPU RAM access (nanoseconds) |
| **Operational Complexity** | Very Low | Very High |

## When to Use / When NOT to Use
### When to Build Stateless Services
- Web application backends, REST/GraphQL APIs, microservice orchestrators, mobile gateways.

### When Stateful Services Are Mandatory
- Relational and NoSQL storage engines, in-memory caches (Redis/Memcached), real-time collaborative document servers, authoritative multiplayer game servers, streaming connection managers.

## Real-World Examples
- **E-Commerce Shopping Carts**: Modern retail platforms (Shopify, Amazon) offload carts to distributed stores (DynamoDB/Redis) so customers can switch seamlessly between mobile apps and desktop browsers without losing cart contents.
- **Discord Voice Gateway**: Stateful infrastructure. Millions of concurrent voice connections terminate on specialized Elixir-based guild servers that hold in-memory routing tables of who is speaking in which audio room.

## Common Pitfalls
- **Local File Upload Anti-Pattern**: Allowing users to upload images or PDFs to the local application server filesystem (`/tmp/uploads`), causing 404 errors when subsequent requests land on different servers.
- **In-Memory Caching Without Invalidation**: Storing configuration or user profiles in a local static hash map inside application memory, leading to divergent, contradictory state across instances.

## Key Takeaways
- The stateless application tier is the secret to modern cloud autoscaling and zero-downtime rolling deployments.
- Push state out of compute instances into specialized, purpose-built stateful infrastructure (PostgreSQL, Redis, S3).
- Avoid sticky sessions whenever possible—they create load hotspots and complicate deployments.

## Common Interview Questions
1. Why is statelessness a prerequisite for horizontal autoscaling in Kubernetes?
2. How do you transition a legacy stateful session application to a modern stateless architecture?
3. What are the engineering challenges of building a stateful multiplayer game server compared to a stateless REST API?

## Further Reading
- [The Twelve-Factor App: VI. Processes (Execute the app as one or more stateless processes)](https://12factor.net/processes)
- [Discord Engineering: How Discord Scaled Elixir to 5,000,000 Concurrent Users](https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users)
""")

save("docs/01-fundamentals/08-monolith-vs-distributed-systems.md", """# Monoliths vs Distributed Systems

## Overview
The debate between **monoliths** and **distributed systems (microservices)** represents the classic tension between operational simplicity and organizational scale:
- **Monolith**: An application where the user interface, business logic, and database access layers are packaged and deployed as a single, unified codebase and runtime executable.
- **Modular Monolith**: A monolithic architecture structured into strictly isolated internal modules with explicit public interfaces, sharing a single deployment pipeline.
- **Distributed Microservices**: An architecture where an application is decomposed into independently deployable, loosely coupled services communicating over network protocols (HTTP/gRPC/Kafka).

```mermaid
graph TD
    subgraph Monolithic Architecture
        UI1[UI Layer] --> BL1[Business Logic Layer]
        BL1 --> DB1[(Single Shared DB)]
    end
    subgraph Microservices Architecture
        GW[API Gateway] --> S1[Order Service]
        GW --> S2[User Service]
        GW --> S3[Payment Service]
        S1 --> DB_S1[(Order DB)]
        S2 --> DB_S2[(User DB)]
        S3 --> DB_S3[(Payment DB)]
        S1 -.->|gRPC / Kafka| S3
    end
```

## Why It Matters
Adopting microservices too early introduces staggering distributed systems overhead—network latency, partial failure modes, distributed transactions, and deployment complexity—for zero business benefit. Conversely, a rapidly growing engineering team of hundreds working in a monolithic repository can suffer severe deployment bottlenecks and merge conflict hell.

## Core Concepts
- **Conway's Law**: *"Organizations which design systems are constrained to produce designs which are copies of the communication structures of these organizations."*
- **Bounded Contexts (DDD)**: Decomposing systems along natural business boundaries where business terminology is unambiguous and self-contained.
- **The Distributed Monolith Anti-Pattern**: An architecture possessing all the operational complexity and network latency of microservices, yet so tightly coupled that deploying one service requires coordinated lockstep deployments of all other services.

## How It Works
1. **Monolith Execution**: Inter-module communication occurs via in-memory function calls on the CPU stack. Data transactions are handled atomically via local ACID database transactions (`BEGIN ... COMMIT`).
2. **Microservices Execution**: Communication requires serializing objects into JSON/Protobuf, transmitting packets across physical networks over TCP/HTTP/2, and managing timeouts, retries, and circuit breakers.

## Trade-offs
| Architectural Dimension | Monolith / Modular Monolith | Distributed Microservices |
| :--- | :--- | :--- |
| **Development Velocity (Small Team)** | Extremely High | Low (heavy infrastructure tax) |
| **Deployment Independence** | Low (single deployment pipeline) | High (teams deploy independently) |
| **Network Latency Overhead** | Zero (in-memory function calls) | High (0.5ms - 5ms per network hop) |
| **Operational Complexity** | Minimal (single process, simple logs) | Staggering (Kubernetes, Envoy, OTel tracing) |
| **Data Consistency** | Simple ACID transactions | Eventual consistency, Sagas, Outbox pattern |

## When to Use / When NOT to Use
### When to Build a Monolith / Modular Monolith
- Early-stage startups, new products with evolving domain boundaries, teams with fewer than 30 engineers.
- Systems requiring ultra-low latency and strict transactional integrity.

### When to Transition to Microservices
- Large organizations with multiple engineering teams (50+ engineers) that need to ship features independently without blocking on a centralized release train.
- Specific sub-components require drastically divergent scaling characteristics (e.g., a video transcoding service needing GPU instances vs a lightweight auth service).

## Real-World Examples
- **Amazon Prime Video (2023)**: Migrated their video quality monitoring service from distributed AWS Step Functions and microservices back to a consolidated monolithic architecture, reducing infrastructure costs by **90%** and drastically improving performance.
- **Shopify**: Operates one of the world's largest Ruby on Rails applications as a disciplined **Modular Monolith**, processing over $100 billion in gross merchandise value with high developer productivity.

## Common Pitfalls
- **Shared Database Anti-Pattern**: Splitting code into separate microservices but pointing them all to the same shared PostgreSQL database, creating hidden coupling and defeating the purpose of independent deployments.
- **Distributed Transactions**: Attempting to execute distributed ACID transactions across multiple microservices instead of embracing event-driven Sagas and eventual consistency.

## Key Takeaways
- Start with a well-structured **Modular Monolith**; extract microservices only when organizational scale or distinct scaling profiles demand it.
- Microservices solve team scaling and deployment coordination bottlenecks, NOT code performance.
- Each microservice must own its private database—never share databases across service boundaries.

## Common Interview Questions
1. Under what circumstances would you recommend migrating from microservices back to a modular monolith?
2. How does Conway's Law influence system architecture decisions?
3. What is the "distributed monolith" anti-pattern, and how do you identify it?

## Further Reading
- [Martin Fowler: Microservice Prerequisites](https://martinfowler.com/bliki/MicroservicePrerequisites.html)
- [Prime Video Tech Blog: Scaling up the Prime Video audio/video monitoring service and reducing costs by 90%](https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90)
""")

save("docs/01-fundamentals/09-back-of-the-envelope-estimation-intro.md", """# Back-of-the-Envelope Estimation Thinking

## Overview
**Back-of-the-envelope estimation** is the discipline of using quick mental math, dimensional analysis, and standard heuristics to rapidly approximate system capacity, traffic throughput, memory requirements, and network bandwidth. It allows engineers to validate whether an architectural proposal is physically and economically feasible before writing a single line of code.

```mermaid
graph LR
    A[Product Requirements: DAU & Actions] --> B[Dimensional Math & Powers of 2]
    B --> C[QPS / Bandwidth Estimates]
    B --> D[Storage & RAM Estimates]
    C & D --> E[Architecture Feasibility Decision]
```

## Why It Matters
System design without numbers is just hand-waving. If a proposed design requires storing 50 terabytes of data per day in an in-memory Redis cluster, back-of-the-envelope calculation instantly reveals that the hardware cost will be astronomically prohibitive, allowing you to pivot to SSD-backed LSM-Tree storage (RocksDB/Cassandra) within minutes.

## Core Concepts
- **Key Approximations to Memorize**:
  - Seconds per day: $24 \\times 60 \\times 60 = 86,400 \\approx 100,000\\text{ (10}^5\\text{) seconds}$ for quick estimates.
  - Queries Per Second rule of thumb:
    $$\\text{Average QPS} = \\frac{\\text{Daily Requests}}{86,400} \\approx \\frac{\\text{Daily Requests}}{10^5}$$
    *Example*: 100 Million daily requests $\\approx 1,000$ QPS (Peak typically $2\\times$ to $3\\times \\approx 2,500$ QPS).
- **The 80/20 Rule (Pareto Principle) for Caching**:
  - 20% of your data generates 80% of read traffic.
  - *Cache Sizing Rule*: Size your cache to hold **20% of your daily read working set** in RAM.
- **Powers of Two Anchors**:
  - $2^{10} = 1,024 \\approx 1\\text{ KB}$ (Kilobyte)
  - $2^{20} = 1,048,576 \\approx 1\\text{ MB}$ (Megabyte)
  - $2^{30} \\approx 1\\text{ GB}$ (Gigabyte)
  - $2^{40} \\approx 1\\text{ TB}$ (Terabyte)
  - $2^{50} \\approx 1\\text{ PB}$ (Petabyte)

## How It Works: Step-by-Step Calculation Walkthrough
Consider designing a photo sharing service with 500 Million Daily Active Users (DAU):
1. **Traffic Estimation**:
   - Assume each user views 20 photos and uploads 1 photo daily.
   - Upload QPS:
     $$\\frac{500,000,000 \\times 1}{10^5} = 5,000\\text{ writes/sec (Peak } \\approx 10,000\\text{ QPS)}$$
   - View QPS:
     $$\\frac{500,000,000 \\times 20}{10^5} = 100,000\\text{ reads/sec (Peak } \\approx 200,000\\text{ QPS)}$$
2. **Storage Estimation**:
   - Average photo size = 200 KB. Metadata = 500 bytes.
   - Daily media storage:
     $$500,000,000 \\times 200\\text{ KB} = 100\\text{ TB/day}$$
   - 5-Year Storage Capacity:
     $$100\\text{ TB/day} \\times 365 \\times 5 \\approx 182.5\\text{ Petabytes}$$
3. **Bandwidth Estimation**:
   - Ingress: $5,000\\text{ QPS} \\times 200\\text{ KB} = 1\\text{ GB/sec} = 8\\text{ Gbps}$.
   - Egress: $100,000\\text{ QPS} \\times 200\\text{ KB} = 20\\text{ GB/sec} = 160\\text{ Gbps}$ (Clearly requires CDN edge offloading!).

## Trade-offs
| Precision Level | Speed | Utility |
| :--- | :--- | :--- |
| **Exact Formulaic Accounting** | Slow (hours of spreadsheet work) | Necessary for final cloud procurement budgets |
| **Order-of-Magnitude Estimation** | Fast (60 seconds on a whiteboard) | Perfect for evaluating competing architectural proposals |

## When to Use / When NOT to Use
### When to Use
- During architectural whiteboarding, interview scoping, capacity planning, and early design reviews.

### When NOT to Use
- When purchasing physical hardware for bare-metal datacenters or allocating exact financial infrastructure budgets (use exact sizing).

## Real-World Examples
- **Enrico Fermi**: Famous for solving the "Fermi problem" (e.g., estimating the number of piano tuners in Chicago) using chain multiplications of estimated ratios. This technique forms the foundation of modern engineering capacity planning.
- **YouTube Ingestion**: Approximating 500 hours of video uploaded every minute immediately dictates that video transcoding must be an asynchronous distributed worker pipeline rather than an inline synchronous HTTP request.

## Common Pitfalls
- **Unit Conversion Errors**: Confusing **bits** with **bytes** (1 Byte = 8 bits). Network bandwidth is rated in bits per second (Gbps), whereas storage is measured in bytes (GB/TB).
- **Ignoring Peak Multipliers**: Designing a system exclusively for average QPS and crashing when evening traffic surges 3x.

## Key Takeaways
- Always round numbers aggressively ($86,400 \\approx 100,000$) to enable rapid mental arithmetic.
- Calculate QPS, storage over 5 years, network bandwidth, and 20% cache RAM for every design.
- Bandwidth calculations reveal whether an application requires CDN edge caching.

## Common Interview Questions
1. How do you estimate the cache RAM needed for a read-heavy service with 100 million daily active users?
2. If an API has an ingress bandwidth of 250 MB/sec, what is the network bandwidth requirement in Gbps?
3. How do you estimate the number of server instances needed to support 50,000 QPS?

## Further Reading
- [Section 20: Estimation and Interview Framework (Deep Dive)](../20-estimation-and-interview-framework/01-numbers-every-engineer-should-know.md)
- [Jeff Dean: Numbers Everyone Should Know](http://brenocon.com/dean_perf.html)
""")

print("Section 01 complete.")
