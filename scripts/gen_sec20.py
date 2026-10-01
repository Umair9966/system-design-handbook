import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\20-estimation-and-interview-framework"

files = {
    "01-numbers-every-engineer-should-know.md": """# Latency and Capacity Numbers Every Engineer Should Know

System design calculations rely on knowing the orders of magnitude for computer hardware latency, bandwidth throughput, and powers of two.

```mermaid
gantt
    title Latency Comparison of Hardware Operations
    dateFormat X
    axisFormat %s

    section Fast (Nanoseconds)
    L1 Cache Reference (0.5 ns)       : 0, 1
    Branch Mispredict (3 ns)          : 0, 3
    L2 Cache Reference (7 ns)          : 0, 7
    Mutex Lock / Unlock (25 ns)        : 0, 25
    Main Memory Reference (100 ns)     : 0, 100

    section Medium (Microseconds)
    Compress 1KB with Zstd (2 us)      : 0, 2000
    Send 1KB over 10Gbps (10 us)       : 0, 10000
    Read 1MB sequentially from SSD (50 us): 0, 50000

    section Slow (Milliseconds)
    Round trip within Datacenter (0.5 ms): 0, 500000
    Read 1MB sequentially from HDD (2 ms): 0, 2000000
    Disk Seek (Rotational HDD) (10 ms) : 0, 10000000
    WAN Cross-Country (US to EU) (70 ms): 0, 70000000
```

---

## 1. Jeff Dean's Canonical Latency Numbers (Updated for NVMe)

| Operation | Latency (ns / us / ms) | Human Scale Equivalent (1ns = 1 sec) |
| :--- | :--- | :--- |
| **L1 CPU Cache Reference** | 0.5 - 1 ns | 1 second |
| **Branch Mispredict** | 3 - 5 ns | 5 seconds |
| **L2 CPU Cache Reference** | 4 - 7 ns | 7 seconds |
| **Mutex Lock / Unlock** | 25 ns | 25 seconds |
| **Main Memory (RAM) Access** | 100 ns | 1.6 minutes |
| **NVMe SSD Random Read** | 10 - 25 µs | 7 hours |
| **Read 1MB Sequentially from Memory**| 2.5 µs | 40 minutes |
| **Read 1MB Sequentially from SSD** | 50 µs | 14 hours |
| **Intra-Datacenter Round Trip** | 500 µs (0.5 ms) | 6 days |
| **Rotational HDD Seek** | 10 ms | 4 months |
| **Read 1MB Sequentially from HDD** | 20 ms | 8 months |
| **US to Europe Round-Trip (WAN)** | 70 ms | 2.2 years |
| **Global Packet Around Equator** | 130 ms | 4.1 years |

---

## 2. Capacity Powers of Two and Units

| Power of 2 | Value | Abbreviation | Common Approximation |
| :--- | :--- | :--- | :--- |
| $2^{10}$ | 1,024 | 1 KB (Kilobyte) | 1 Thousand Bytes |
| $2^{20}$ | 1,048,576 | 1 MB (Megabyte) | 1 Million Bytes |
| $2^{30}$ | 1,073,741,824 | 1 GB (Gigabyte) | 1 Billion Bytes |
| $2^{40}$ | 1,099,511,627,776 | 1 TB (Terabyte) | 1 Trillion Bytes |
| $2^{50}$ | 1,125,899,906,842,624 | 1 PB (Petabyte) | 1 Quadrillion Bytes |

### Seconds in Time Intervals:
- **1 Day** = 86,400 seconds $\approx \mathbf{10^5\text{ seconds}}$ ($\approx 86.4\text{K}$).
- **1 Month** $\approx 2.5 \times 10^6\text{ seconds}$.
- **1 Year** $\approx 3.15 \times 10^7\text{ seconds} \approx \mathbf{30\text{ Million seconds}}$.

---

## 3. Server Capacity Benchmarks

- **Single Modern Web Server (4-8 Cores, Go/Rust/Node)**: 10,000 to 50,000 concurrent light HTTP requests/sec.
- **Single Redis Instance**: 100,000 to 200,000 $O(1)$ operations/sec.
- **Relational DB (PostgreSQL on NVMe)**: 5,000 to 20,000 queries/sec (read-heavy with indexes); 2,000 to 5,000 writes/sec.
- **Apache Kafka Partition**: 10MB to 30MB write throughput per second.

---

## 4. Key Takeaways

- Memory is $\approx 100\times$ faster than NVMe SSD, and SSD is $\approx 100\times$ faster than rotational HDD.
- Network latency across continents ($\approx 70\text{ms}$) dwarfs compute time.
- Memorize that 1 day has $\approx 86,400$ (approx. $10^5$) seconds for fast interview QPS math.
""",

    "02-back-of-the-envelope-estimation-guide.md": """# Back-of-the-Envelope Estimation Guide

Back-of-the-envelope estimation allows system designers to quantitatively evaluate architectural choices, storage requirements, network bandwidth, and server counts within 5 minutes.

```mermaid
graph TD
    DAU[Daily Active Users (DAU)] --> RPS[Read & Write Queries Per Second (QPS)]
    RPS --> Bandwidth[Ingress & Egress Bandwidth]
    RPS --> Storage[Daily & 5-Year Storage Capacity]
    RPS --> Memory[Cache Sizing (80/20 Pareto Rule)]
    RPS --> Servers[Server Instance Estimation]
```

---

## 1. The 5 Core Estimation Equations

### 1. Queries Per Second (QPS)
$$\text{Average QPS} = \frac{\text{Total Daily Requests}}{86,400} \approx \frac{\text{Requests}}{10^5}$$
$$\text{Peak QPS} = \text{Average QPS} \times 2 \quad (\text{or } \times 5 \text{ for spiky traffic})$$

### 2. Storage Estimation
$$\text{Daily Storage} = \text{Daily Writes} \times \text{Average Payload Size}$$
$$\text{5-Year Storage} = \text{Daily Storage} \times 365 \times 5 \approx \text{Daily Storage} \times 2,000$$

### 3. Network Bandwidth
$$\text{Ingress Bandwidth} = \text{Write QPS} \times \text{Average Request Size}$$
$$\text{Egress Bandwidth} = \text{Read QPS} \times \text{Average Response Size}$$

### 4. Memory / Cache Sizing (The 80/20 Rule)
According to the Pareto Principle, 20% of content generates 80% of read traffic.
$$\text{Cache Size} = \text{Daily Read Data Volume} \times 0.20$$

---

## 2. Worked Example: Twitter / X Architecture Estimation

### Assumptions:
- **DAU**: 300 Million Daily Active Users.
- **Write Ratio**: Each user tweets twice per day on average.
- **Read Ratio**: Each user views 50 tweets per day on average.
- **Tweet Payload**: 300 bytes text + metadata. 1 in 5 tweets includes a 200KB image.

### Step 1: QPS Calculation
$$\text{Total Daily Tweets} = 300\text{M} \times 2 = 600\text{ Million tweets/day}$$
$$\text{Average Write QPS} = \frac{600,000,000}{86,400} \approx \mathbf{7,000\text{ writes/sec}}$$
$$\text{Peak Write QPS} = 7,000 \times 2 = \mathbf{14,000\text{ writes/sec}}$$

$$\text{Total Daily Reads} = 300\text{M} \times 50 = 15\text{ Billion reads/day}$$
$$\text{Average Read QPS} = \frac{15,000,000,000}{86,400} \approx \mathbf{175,000\text{ reads/sec}}$$
$$\text{Peak Read QPS} = 175,000 \times 2 = \mathbf{350,000\text{ reads/sec}}$$

### Step 2: Storage Sizing (5 Years)
$$\text{Daily Text Storage} = 600\text{M} \times 300\text{B} = 180\text{ GB/day}$$
$$\text{Daily Media Storage} = (600\text{M} \times 0.20) \times 200\text{KB} = 120\text{M} \times 200\text{KB} = 24\text{ TB/day}$$
$$\text{Total Daily Storage} \approx 24.2\text{ TB/day}$$
$$\text{5-Year Storage} = 24.2\text{ TB} \times 365 \times 5 \approx \mathbf{44.1\text{ Petabytes}}$$

### Step 3: Cache Sizing (Memory)
$$\text{Daily Active Working Set (Text)} = 180\text{ GB}$$
$$\text{Redis Cache (20% of Daily Reads)} = 180\text{ GB} \times 0.20 = \mathbf{36\text{ GB of RAM}}$$

---

## 3. Key Takeaways

- Round numbers to 1 or 2 significant digits during interviews ($86,400 \to 100,000$).
- Always separate Read QPS from Write QPS to identify read-heavy vs write-heavy architectures.
- Size cache RAM on 20% of daily read volume.
""",

    "03-the-6-step-interview-framework.md": """# The 6-Step System Design Interview Framework

A structured, predictable 45-minute blueprint for navigating senior and staff-level system design interviews.

```mermaid
gantt
    title 45-Minute System Design Interview Timeline
    dateFormat X
    axisFormat %s min

    section Step 1: Scope & Clarify
    Requirements & Constraints (5m) : 0, 5
    section Step 2: Capacity
    Back-of-Envelope Math (5m)       : 5, 10
    section Step 3: Interface
    API & Data Model (5m)            : 10, 15
    section Step 4: High-Level
    Core Architecture Diagram (10m)  : 15, 25
    section Step 5: Deep Dive
    Bottlenecks & Edge Cases (15m)   : 25, 40
    section Step 6: Wrap Up
    Failure Modes & Retrospective (5m): 40, 45
```

---

## 1. Step 1: Scope and Clarify Requirements (5 mins)
Never start drawing boxes immediately. Clarify the boundaries:
- **Functional Requirements**: Pick top 3-4 core use cases. (e.g., "1. User can post video. 2. User can view video feed. 3. User can search videos.").
- **Non-Functional Requirements**: High availability vs strong consistency, latency limits (p99 < 200ms), scalability (100M DAU).
- **Out of Scope**: Explicitly state what will NOT be built today (e.g., "Recommendation algorithms and comments are out of scope").

---

## 2. Step 2: Capacity Estimation (5 mins)
- Calculate Read and Write QPS.
- Estimate 5-year storage requirements.
- Calculate ingress/egress network bandwidth.

---

## 3. Step 3: API & Data Model Definition (5 mins)
- Define clean HTTP/gRPC endpoints with parameters.
- Sketch core database schema entities and primary keys.

---

## 4. Step 4: High-Level Architectural Design (10 mins)
- Draw end-to-end topology: Client $\to$ CDN $\to$ Load Balancer $\to$ API Gateway $\to$ Services $\to$ DB / Cache / Queues.
- Trace the primary read path and primary write path.

---

## 5. Step 5: Detailed Component Deep Dive (15 mins)
Drive the conversation into hard distributed problems:
- How does the system handle hot partitions or celebrity accounts?
- What happens if the database master fails during a write?
- Cache invalidation and stampede prevention.

---

## 6. Step 6: Failure Modes and Wrap Up (5 mins)
- Identify Single Points of Failure (SPOFs).
- Discuss metrics, alerting, monitoring, and future scale bottlenecks.
""",

    "04-communication-and-ambiguity.md": """# Communication Strategies and Navigating Ambiguity

System design interviews evaluate your ability to lead, clarify vague requirements, justify technical trade-offs, and collaborate as a technical peer.

```mermaid
graph TD
    Vague[Interviewer: 'Design Twitter'] --> Trap{Candidate Action}
    Trap -->|Silent assumption / Starts coding| Fail[Red Flag: Poor Communication & Assumptions]
    Trap -->|Asks clarifying questions & drives scope| Pass[Senior Behavior: Drives Consensus & Clarity]
```

---

## 1. Driving Rather than Being Led

- **Lead the Conversation**: Treat the interview as a collaborative design meeting with a colleague. Don't wait passively for instructions.
- **State Assumptions Explicitly**: "I will assume a 100:1 read-to-write ratio typical of social networks. Does that align with your expectations?"
- **Offer Architectural Options with Trade-offs**: Never say "We must use Redis." Say: "We have two options: Memcached for pure multi-threaded throughput, or Redis for rich data structures like Sorted Sets. Given our need to rank feeds by timestamp, Redis is the superior choice."

---

## 2. Navigating Interviewer Pushback

When an interviewer interrupts with: *"What if that database node crashes?"*
1. **Acknowledge and Validate**: "Great question. If that primary node crashes..."
2. **State Immediate Impact**: "Writes to that shard will fail for ~10-30 seconds until failover completes."
3. **Propose Automated Mitigation**: "We will configure automated Raft consensus failover to promote a replica to primary and notify the API Gateway."

---

## 3. Key Takeaways

- Clarify ambiguous requirements proactively before proposing solutions.
- Frame all technology choices in terms of concrete trade-offs (pros vs cons).
- Treat the interview as a collaborative architectural whiteboard session.
""",

    "05-common-interview-mistakes.md": """# Top 10 System Design Interview Mistakes

Understanding the anti-patterns that cause candidates to fail system design interviews.

```mermaid
graph TD
    Mistakes[Top Interview Pitfalls]
    Mistakes --> M1[1. Starting with Tech Buzzwords ('Let's use Kafka and Blockchain')]
    Mistakes --> M2[2. Silent Drawing without Explaining Thought Process]
    Mistakes --> M3[3. Ignoring Scale Numbers in Architectural Decisions]
    Mistakes --> M4[4. Single Point of Failure (SPOF) Blindness]
    Mistakes --> M5[5. Over-Engineering Simple Requirements]
```

---

## The 10 Deadly Sins:

1. **Premature Technology Naming**: Proposing Kafka or Cassandra before defining functional requirements or traffic scale.
2. **Monologuing without Checking In**: Speaking for 10 minutes continuously without pausing to confirm alignment with the interviewer.
3. **Ignoring Back-of-the-Envelope Math**: Designing an in-memory Redis cluster for a dataset that requires 100 Petabytes of disk storage.
4. **Drawing a "Magic Box"**: Labeling a component "Load Balancer" or "Message Queue" without being able to explain how it works internally under failure.
5. **Treating Databases as Black Boxes**: Ignoring indexing, replication lag, transaction isolation levels, and sharding strategies.
6. **Ignoring Failures**: Designing purely for the happy path and panicking when asked: "What happens if this network link severs?"
7. **Over-Engineering**: Proposing a 50-microservice Kubernetes mesh for a system serving 10 requests per minute.
8. **Neglecting Data Models**: Skipping the database schema and entity relationships.
9. **Rigidity and Defensiveness**: Arguing with the interviewer when they offer hints or challenge assumptions.
10. **Running Out of Time**: Spending 35 minutes on requirements and calculations, leaving 5 minutes for the actual architecture.

---

## Key Takeaways

- Focus on fundamentals: data models, access patterns, and fault tolerance.
- Check in with the interviewer every 3-4 minutes: *"Does this component address your primary concern, or should we dive into the storage engine next?"*
""",

    "06-mock-interview-evaluation-rubric.md": """# System Design Interview Evaluation Rubric (FAANG Standards)

How interviewers evaluate candidates across Staff and Principal engineering dimensions.

```mermaid
radar
    title Candidate Competency Dimensions
    "Requirements & Scoping" : 4
    "High-Level Architecture" : 5
    "Distributed Deep Dive" : 4
    "Trade-off Articulation" : 5
    "Fault Tolerance & Scale" : 4
    "Communication & Leadership" : 5
```

---

## The 4 Competency Levels

| Dimension | Junior / Mid (L4) | Senior (L5) | Staff / Principal (L6+) |
| :--- | :--- | :--- | :--- |
| **Scoping** | Waits for requirements to be handed down | Identifies key use cases and non-functional requirements | Clarifies business trade-offs, identifies ambiguous edge cases |
| **Architecture** | Simple 3-tier app (Client -> API -> DB) | Microservices, caching, read replicas, messaging queues | Elegant distributed topologies, handles partitioning and consensus |
| **Data Design** | Basic SQL table schema | Appropriate SQL vs NoSQL selection, indexing strategy | Sharding key selection, replication models, data consistency guarantees |
| **Resilience** | Mentions backups | Circuit breakers, health checks, multi-AZ deployment | Active-Active multi-region, split-brain mitigation, chaos engineering |
| **Communication**| Hesitant, needs prompting | Clear, drives standard framework | Inspiring, drives consensus, explains complex trade-offs simply |

---

## Scoring Grid

1. **Strong No Hire**: Silent, unable to handle scale, suggests single MySQL instance for 100M QPS, defends broken designs.
2. **No Hire**: Implements generic textbook architecture, unable to explain internals of proposed technologies, misses major failure modes.
3. **Hire**: Follows 6-step framework cleanly, makes justifiable tech choices, calculates accurate numbers, handles failure scenarios gracefully.
4. **Strong Hire**: Drives the session masterfully, proactively points out subtle distributed bugs (cache stampedes, clock skew, split-brain), evaluates trade-offs with mathematical rigor.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 20 complete.")
