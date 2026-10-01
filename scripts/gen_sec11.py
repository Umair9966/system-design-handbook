import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\11-reliability-and-resilience"

files = {
    "01-timeouts-retries-and-jitter.md": """# Timeouts, Retries, and Jitter

Network requests in distributed systems fail constantly. Handling failures incorrectly—such as retrying immediately without backoff or omitting timeouts—inevitably triggers self-inflicted Distributed Denial of Service (DDoS) thundering herds that collapse recovering backends.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Application
    participant Svc as Downstream Service (Overloaded)

    Client->>Svc: Request 1
    Note over Svc: Processing stalled...
    Note over Client: Timeout fires at 500ms! (Cancels socket)
    
    Note over Client: Backoff 1: Wait 200ms + Jitter
    Client->>Svc: Retry Attempt 1
    Note over Svc: Error 503 Service Unavailable
    
    Note over Client: Backoff 2: Wait 400ms + Jitter
    Client->>Svc: Retry Attempt 2
    Svc-->>Client: 200 OK (Succeeded)
```

---

## 1. Timeouts: The First Line of Defense

Every remote network call must have an explicit timeout. A thread or goroutine waiting indefinitely on a socket leak locks, connections, and memory until the caller crashes.

### Timeout Granularity:
- **Connection Timeout**: Time allowed to establish the TCP/TLS handshake (typically 1-3 seconds).
- **Socket / Read Timeout**: Maximum time between two successive data packets (typically 500ms - 2s).
- **End-to-End Deadline**: Total maximum duration for the entire RPC operation, including all retries.

```mermaid
graph LR
    subgraph "Deadline Propagation across Hops"
        GW[Gateway: 1000ms Budget] -->|Spends 200ms, Passes 800ms Deadline| S1[Service A]
        S1 -->|Spends 300ms, Passes 500ms Deadline| S2[Service B]
        S2 -->|If local operation takes > 500ms: ABORT immediately!| DB[(Database)]
    end
```

---

## 2. Exponential Backoff and Jitter Algorithms

Naive retries retry immediately at fixed intervals ($t, t, t$), synchronizing thousands of failed clients into periodic massive traffic waves.

### 1. Exponential Backoff Formula
$$T_{\text{backoff}} = \min(T_{\text{max}}, T_{\text{base}} \times 2^{\text{attempt}})$$

### 2. The Power of Full Jitter (AWS Research)
Adding randomness (jitter) desynchronizes retries completely across the timeline:

$$\text{Full Jitter Sleep} = \text{random}(0, \min(T_{\text{max}}, T_{\text{base}} \times 2^{\text{attempt}}))$$

```mermaid
graph TD
    subgraph "Without Jitter (Thundering Herd)"
        C1[Client 1] -->|Fails at t=0| T1[Sleeps exactly 1.0s] --> Wave[Huge Traffic Spike at t=1.0s!]
        C2[Client 2] -->|Fails at t=0| T2[Sleeps exactly 1.0s] --> Wave
        C3[Client 3] -->|Fails at t=0| T3[Sleeps exactly 1.0s] --> Wave
    end

    subgraph "With Full Jitter (Evenly Distributed)"
        J1[Client 1] -->|Fails at t=0| S1[Sleeps random: 0.23s]
        J2[Client 2] -->|Fails at t=0| S2[Sleeps random: 0.87s]
        J3[Client 3] -->|Fails at t=0| S3[Sleeps random: 0.51s]
        Note over S1,S3: Downstream receives smooth, manageable stream of retries
    end
```

---

## 3. Retry Budgets and Amplification

In a call chain $A \to B \to C \to D$, if each service retries 3 times on failure:
$$\text{Total Calls to D} = 3 \times 3 \times 3 = 27\text{ requests!}$$
A small 5% failure at service D gets amplified into a 2,700% traffic storm that destroys D.

### Defenses:
1. **Retry Budgeting**: Limit retries to at most **10%** of total request volume across a 1-minute window. If overall failures exceed 10%, drop retries and fail fast.
2. **Retry Only Idempotent Operations**: Never retry non-idempotent HTTP POST payments or order placements without an `Idempotency-Key`.
3. **Retry Only Transient Errors**: Retry on `503 Service Unavailable`, `429 Too Many Requests`, and network timeouts; never retry `400 Bad Request`, `401 Unauthorized`, or `404 Not Found`.

---

## 4. Key Takeaways

- Every network client must enforce connection, read, and global context deadlines.
- Always use Exponential Backoff with Full Jitter for retry loops.
- Implement retry budgets to prevent cascading retry amplification storms.
- Only retry safe, idempotent operations on transient error codes.
""",

    "02-circuit-breaker-bulkhead-load-shedding.md": """# Circuit Breaker, Bulkhead, and Load Shedding

Cascading failures are the primary killer of distributed architectures. When downstream dependencies degrade, callers must isolate failures to protect overall system availability.

```mermaid
stateDiagram-v2
    [*] --> Closed
    
    Closed --> Open : Failure Rate > Threshold (e.g. 50% over 10s)
    note right of Closed : Normal operation. All requests pass through.
    
    Open --> HalfOpen : Sleep Window Expires (e.g. after 30s)
    note right of Open : Fail-Fast! Immediate error or fallback returned without calling downstream.
    
    HalfOpen --> Closed : Trial requests succeed (e.g. 5 consecutive 200s)
    HalfOpen --> Open : Any trial request fails
    note right of HalfOpen : Limited trial requests probed to test dependency recovery.
```

---

## 1. Circuit Breaker Pattern

The Circuit Breaker pattern prevents an application from repeatedly trying to execute an operation that is almost certain to fail.

### State Transitions:
1. **Closed**: Requests flow normally. The circuit monitors rolling error rates (e.g., via sliding window of the last 100 requests).
2. **Open**: If failure rate exceeds threshold (e.g., 50% errors or p99 latency > 2s), the circuit **trips open**. All incoming calls fail immediately or return a fallback without hitting the downstream network socket.
3. **Half-Open**: After a cooldown period (e.g., 30s), the circuit allows a small number of canary probe requests through. If they succeed, it closes; if any fail, it trips open again.

---

## 2. Bulkhead Pattern (Resource Isolation)

Named after the watertight compartments in a ship's hull: if one compartment floods, the others remain sealed and the ship stays afloat.

```mermaid
graph TD
    subgraph "Unprotected Thread Pool (Sinks the Ship)"
        SharedPool[Shared Thread Pool: 100 Threads]
        ReqA[Order Requests] --> SharedPool
        ReqB[Recommendation Requests] --> SharedPool
        SharedPool --> DownstreamHang[Hanging Rec Engine - Consumes all 100 Threads!]
        Note over ReqA: Critical Orders Starved and Fail!
    end

    subgraph "Bulkhead Isolated Thread Pools"
        OrderPool[Order Pool: 70 Threads]
        RecPool[Recommendation Pool: 30 Threads]
        ReqA2[Order Requests] --> OrderPool --> OrderDB[(Order DB - Fast!)]
        ReqB2[Rec Requests] --> RecPool --> DownstreamHang2[Hanging Rec Engine]
        Note over OrderPool: Orders continue at full speed unaffected!
    end
```

### Bulkhead Implementations:
- **Thread Pool Bulkheads**: Separate worker pools per downstream dependency (used by Netflix Hystrix / Resilience4j).
- **Semaphore Bulkheads**: Atomic counter limiting concurrent in-flight requests per dependency without thread context-switching overhead.
- **Process / Pod Bulkheads**: Physical Kubernetes node taints/tolerations dedicating CPU/RAM to critical checkout services.

---

## 3. Load Shedding: Dropping Traffic to Save the System

When CPU or memory hits 95%, processing all requests will cause thrashing, out-of-memory (OOM) kernel panics, and complete outage. **Load shedding rejects excess traffic immediately so the remaining requests complete with normal latency.**

```mermaid
graph TD
    Traffic[Incoming 50,000 req/sec] --> Gate[API Gateway / Ingress]
    Gate --> QueueCheck{System Queue Latency > 200ms?}
    QueueCheck -->|Yes - System Saturated| Drop[Drop Non-Essential Traffic: 429 / 503]
    Drop --> DropRecs[Drop: Recommendations, Likes, Analytics]
    QueueCheck -->|No - Safe Capacity| Allow[Allow Critical Traffic]
    Allow --> OrderFlow[Process: Checkout, Payments, Auth]
```

### Load Shedding Strategies:
1. **Priority Tiers**: Categorize requests into Critical (checkout), High (login), and Low (recommendations). Drop lowest tiers first when CPU > 85%.
2. **Little's Law Based Shedding (CoDel / Vegas)**: Measure queued waiting time inside the worker queue. If a request has already waited 500ms just sitting in queue, discard it before processing—the client has likely timed out already.

---

## 4. Key Takeaways

- Wrap all external network calls with a circuit breaker to fail fast during outages.
- Partition thread pools and resource quotas using Bulkheads to prevent slow auxiliary features from starving core business flows.
- Implement proactive Load Shedding based on queue wait time to preserve throughput under extreme overload.
""",

    "03-graceful-degradation-and-fallbacks.md": """# Graceful Degradation and Fallbacks

Graceful degradation is the practice of designing a system to maintain core functionality at reduced fidelity when one or more subsystems, dependencies, or databases fail.

```mermaid
graph TD
    UserReq[User Requests Product Page] --> API[API Gateway / BFF]
    
    subgraph Core Features (Always Must Work)
        API --> PriceSvc[Pricing Service] --> PriceDB[(Price DB)]
        API --> StockSvc[Stock Service] --> StockDB[(Stock DB)]
    end

    subgraph Non-Critical Dependencies (With Fallbacks)
        API --> RecSvc[Personalized ML Recommendations]
        RecSvc -.->|Failed / Timeout!| FallbackRec[Fallback: Static Top 10 Best Sellers from Redis]
        
        API --> ReviewSvc[Customer Reviews Service]
        ReviewSvc -.->|Failed / Timeout!| FallbackRev[Fallback: Hide Reviews Tab Silently]
    end
```

---

## 1. Static vs Dynamic Fallbacks

When a downstream dependency fails or circuit breaker trips, systems should degrade gracefully rather than presenting an HTTP 500 error screen:

| Fallback Strategy | Mechanism | User Impact | Example |
| :--- | :--- | :--- | :--- |
| **Cached Stale Data** | Return data from local Redis cache with `X-Stale: true` | Sees slightly outdated content | News feed or catalog display |
| **Static Default** | Hardcoded generic response | Non-personalized content | Popular items instead of personalized ML picks |
| **Feature Toggling / Hiding**| Completely hide degraded UI section | UI renders cleanly without broken widget | Comments or reviews section omitted |
| **Asynchronous Enqueue** | Accept write to local disk/queue and confirm | Delayed confirmation | "Order received; confirmation will be emailed shortly" |

---

## 2. Netflix's Tiered Degradation Strategy

Netflix categorizes services into critical tiers:
- **Tier 1 (Non-Negotiable)**: Video playback start, user authentication, customer licensing. Must never fail.
- **Tier 2 (Degradable)**: Search, bookmarks, personalized recommendation carousels. If recommendation algorithms fail, fallback to a cached list of top 20 trending shows.
- **Tier 3 (Disposable)**: Viewing history tracking, analytics, thumbs-up ratings. Dropped instantly during peak load or degradation.

---

## 3. Designing Fallback Data Pipelines

```mermaid
sequenceDiagram
    autonumber
    participant Client as Web Browser
    participant API as Gateway / BFF
    participant ML as ML Personalization Engine
    participant StaleCache as Static Fallback Cache (S3 / CDN)

    Client->>API: GET /home-feed
    API->>ML: GET /recommendations?userId=123 (Timeout: 150ms)
    Note over ML: Latency spike: 500ms...
    Note over API: Timeout triggered! Circuit breaker records failure
    API->>StaleCache: GET /global-top-trending.json (Fast: 5ms)
    StaleCache-->>API: Returns static payload
    API-->>Client: 200 OK { recommendations: [...], degraded: true }
```

---

## 4. Key Takeaways

- Classify every microservice and feature into Tier 1 (critical), Tier 2 (degradable), or Tier 3 (disposable).
- Ensure frontends can render partial page layouts without crashing when secondary fields are omitted.
- Test fallbacks continuously in staging so fallback code paths do not silently break.
""",

    "04-disaster-recovery-rpo-rto.md": """# Disaster Recovery: RPO, RTO, and Multi-Region Strategies

Disaster Recovery (DR) defines the policies, tools, and procedures that enable the recovery or continuation of vital technology infrastructure and systems following a natural or human-induced disaster.

```mermaid
graph LR
    subgraph "Timeline of an Outage"
        LastBackup[Last Data Backup / Snapshot] -->|Data Loss Window: RPO| Outage[Disaster Hits Data Center!]
        Outage -->|Downtime Window: RTO| Restored[Systems Fully Restored & Serving Traffic]
    end
```

---

## 1. The Core Metrics: RPO and RTO

- **RPO (Recovery Point Objective)**: The maximum acceptable age of files that must be recovered from backup storage for normal operations to resume if a disaster occurs. **Measures maximum tolerable data loss.**
  - *Example*: If RPO is 1 hour, backups must occur at least hourly; at most 1 hour of writes can be lost.
- **RTO (Recovery Time Objective)**: The maximum acceptable length of time that your application can be offline before normal business operations resume. **Measures maximum tolerable downtime.**
  - *Example*: If RTO is 15 minutes, systems must detect the outage and failover to a healthy region within 15 minutes.

---

## 2. Multi-Region Disaster Recovery Strategies

Cloud DR strategies span a spectrum of cost versus RTO/RPO:

```mermaid
graph TD
    subgraph "1. Backup and Restore (Cold Standby)"
        BR[RPO: Hours | RTO: 24h+ | Cost: $]
    end

    subgraph "2. Pilot Light (Core DB replicated, zero compute)"
        PL[RPO: Minutes | RTO: 1-2h | Cost: $$]
    end

    subgraph "3. Warm Standby (Scaled-down running replica)"
        WS[RPO: Seconds | RTO: Minutes | Cost: $$$]
    end

    subgraph "4. Multi-Region Active-Active (Full duplicate active clusters)"
        AA[RPO: ~0 | RTO: Seconds (Instant) | Cost: $$$$$]
    end
```

### Detailed Comparison:

| Strategy | Architecture | RPO | RTO | Relative Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Backup & Restore** | Daily snapshots stored in remote S3 bucket; rebuild servers on disaster | 12-24 hours | 24-48 hours | Very Low |
| **Pilot Light** | DB replicated to DR region; minimal core infrastructure running; compute scaled on failure | < 5 minutes | 1-2 hours | Low |
| **Warm Standby** | Fully functioning scaled-down cluster running in DR region; resized on failover | Seconds | 5-15 minutes | Moderate |
| **Active-Active** | Both regions serve live traffic concurrently with Anycast / Route 53 GSLB | Zero to milliseconds | Near Zero (Instant) | Extremely High (2x-3x) |

---

## 3. Active-Active Challenges: Cross-Region Write Conflicts

Running true Active-Active across two regions separated by oceans is constrained by the speed of light:
- Latency between US-East and EU-West is $\approx 70\text{ms}$.
- Synchronous two-phase commit across regions adds $150\text{ms}+$ latency per write.

```mermaid
graph TD
    ClientUS[US User] --> RegUS[US-East Region: Active]
    ClientEU[EU User] --> RegEU[EU-Central Region: Active]
    RegUS <-->|Asynchronous WAN Replication (70ms lag)| RegEU
    Note over RegUS, RegEU: Conflict Resolution Required: LWW (Last-Write-Wins) or CRDTs
```

### Practical Solutions:
1. **User Pinning / Partitioning**: Users are homed to their local region. A US user's writes are always routed to US-East; an EU user writes to EU-Central.
2. **CRDTs (Conflict-free Replicated Data Types)**: Mathematically merge concurrent writes without central coordination.

---

## 4. Key Takeaways

- Clarify business RPO and RTO requirements before selecting expensive multi-region architectures.
- Pilot Light or Warm Standby provides the best balance of cost and recovery speed for 95% of enterprise applications.
- True multi-region Active-Active requires solving distributed write conflicts and handling asynchronous replication lag.
""",

    "05-chaos-engineering.md": """# Chaos Engineering and Failure Injection

Chaos Engineering is the discipline of experimenting on a distributed software system in production to build confidence in the system's capability to withstand turbulent conditions.

```mermaid
graph LR
    Hypothesis[1. Define Steady State Hypothesis] --> Inject[2. Inject Controlled Failure in Prod]
    Inject --> Observe[3. Observe Metrics & Blast Radius]
    Observe --> Verify{Steady State Preserved?}
    Verify -->|Yes| Confirmed[Hypothesis Confirmed]
    Verify -->|No - System Crashed!| Fix[Uncovered Hidden Bug -> Remediate]
```

---

## 1. Principles of Chaos Engineering

Coined by Netflix during the creation of **Chaos Monkey**:
1. **Formulate a Hypothesis**: "If an entire AWS Availability Zone (AZ) dies, user checkout success rate will remain above 99.9%."
2. **Introduce Real-World Variables**: Simulate node termination, packet loss, DNS outages, clock skew, and disk filling.
3. **Minimize Blast Radius**: Start experiments on 1% of canary traffic with automated abort triggers.
4. **Run in Production**: Production environments have unique traffic patterns, data scale, and cache states that staging environments can never replicate.

---

## 2. Common Chaos Experiments Matrix

```mermaid
graph TD
    Exp[Chaos Experiments]
    Exp --> Infra[Infrastructure Layer]
    Exp --> Net[Network Layer]
    Exp --> App[Application Layer]

    Infra --> I1[Kill Random VM / Pod]
    Infra --> I2[Fill Disk to 100%]
    Infra --> I3[Saturate CPU to 100%]

    Net --> N1[Inject 200ms Latency (Toxiproxy)]
    Net --> N2[Inject 10% Packet Loss]
    Net --> N3[Block Downstream Port / Blackhole]

    App --> A1[Inject HTTP 500 Responses]
    App --> A2[Corrupt Cache Payloads]
    App --> A3[Simulate Clock Drift (Time Travel)]
```

---

## 3. Tooling Ecosystem

- **Chaos Mesh & LitmusChaos**: Cloud-native Kubernetes chaos injection engines.
- **Toxiproxy**: Shopify's open-source TCP proxy for simulating network anomalies (flaky sockets, bandwidth limits, latency).
- **Gremlin**: Enterprise chaos engineering platform with automated safety stop mechanisms.

---

## 4. Key Takeaways

- The goal of chaos engineering is to uncover hidden single-points-of-failure before they cause customer-facing outages.
- Always implement an automated kill switch that halts the experiment if error budgets or SLIs are breached.
- Never run chaos tests without comprehensive distributed observability and monitoring.
""",

    "06-sli-slo-sla-and-error-budgets.md": """# SLIs, SLOs, SLAs, and Error Budgets

Site Reliability Engineering (SRE), pioneered by Google, aligns product engineering velocity with system reliability using mathematical error budgets.

```mermaid
graph TD
    SLI[SLI: Service Level Indicator<br/>What is the actual measured metric?]
    SLO[SLO: Service Level Objective<br/>What is our internal target goal?]
    SLA[SLA: Service Level Agreement<br/>What is our contractual commitment to customers?]
    EB[Error Budget<br/>100% - SLO: The allowed unreliability budget]

    SLI -->|Evaluated against| SLO
    SLO -->|Tighter than| SLA
    SLO -->|Calculates| EB
```

---

## 1. Definitions and Formulations

### 1. Service Level Indicator (SLI)
A quantifiable metric measuring service performance:
$$\text{SLI} = \frac{\text{Good Events}}{\text{Total Events}} \times 100$$
- *Example*: Percentage of HTTP requests returning `< 500` status within `200ms`.

### 2. Service Level Objective (SLO)
The internal target reliability percentage set by engineering and product:
- *Example*: "99.9% of checkout requests must succeed with latency < 300ms over a rolling 30-day window."

### 3. Service Level Agreement (SLA)
The legally binding contract with customers specifying financial penalties, service credits, or refunds if breached:
- *Rule*: **SLA must always be more lenient than SLO!**
  - SLO = $99.9\%$ (Internal alert fires)
  - SLA = $99.0\%$ (Company pays customer penalty)

---

## 2. The Error Budget: Balancing Velocity and Stability

An error budget is the inverse of an SLO:
$$\text{Error Budget} = 100\% - \text{SLO}$$

For a 99.9% SLO on 10,000,000 requests per month:
$$\text{Allowed Failures} = 10,000,000 \times 0.001 = 10,000\text{ requests}$$

```mermaid
graph LR
    subgraph "Error Budget Policy"
        EB[Error Budget Remaining: 80%] -->|Green Light| FastDeploy[Feature Releases, Fast Experiments, Risky Changes]
        EB2[Error Budget Exhausted: 0%!] -->|Red Light / Freeze| CodeFreeze[Feature Freeze! 100% Focus on Tech Debt & Reliability Fixes]
    end
```

---

## 3. Key Takeaways

- Measure SLIs as the ratio of good events over valid total events.
- Never set a 100% SLO—100% reliability is economically unviable and stalls product innovation.
- Use Error Budgets as an objective decision framework to resolve tension between product development speed and operational stability.
""",

    "07-capacity-planning-and-autoscaling.md": """# Capacity Planning and Autoscaling

Capacity planning ensures a system has sufficient compute, memory, storage, and network bandwidth to meet expected load with acceptable latency while minimizing infrastructure costs.

```mermaid
graph TD
    Metrics[System Metrics: CPU, Memory, Queue Depth, Req/sec] --> MetricsServer[Kubernetes Metrics Server / Prometheus]
    MetricsServer --> HPA[Horizontal Pod Autoscaler (HPA)]
    HPA -->|Pod Replicas: Scales 10 -> 80| Deploy[Application Deployment]
    Deploy --> CA[Cluster Autoscaler / Karpenter]
    CA -->|Provisions New Cloud VM Nodes| Cloud[AWS EC2 / GCP Compute]
```

---

## 1. Vertical vs Horizontal Autoscaling

- **HPA (Horizontal Pod Autoscaler)**: Increases or decreases the number of pod or container replicas based on real-time load.
- **VPA (Vertical Pod Autoscaler)**: Dynamically adjusts CPU and memory resource requests/limits of existing containers.
- **Cluster Autoscaler (Karpenter)**: Adds physical or virtual cloud worker nodes to the Kubernetes cluster when pending pods cannot be scheduled due to insufficient node resources.

---

## 2. Autoscaling Metrics: Choosing the Right Trigger

| Metric | Scaling Speed | Pitfalls / Gotchas | Best For |
| :--- | :--- | :--- | :--- |
| **CPU Utilization** | Moderate | CPU is a lagging indicator; spike arrives before CPU registers | General compute workloads |
| **Memory Utilization** | Very Slow | Garbage collected languages (Java, Go) retain memory; won't trigger scale down | Memory leaks, cache nodes |
| **Queue Depth (SQS / Kafka Lag)**| Fast & Predictive | If consumers crash, queue expands and spawns infinite pods | Asynchronous worker pipelines |
| **Request Rate (RPS)** | Instant | Requires custom metrics via Prometheus adapter | Public HTTP API gateways |

---

## 3. The Autoscaling Thrashing Problem (Flapping)

Rapid oscillation between scaling up and scaling down due to short bursts:

```mermaid
graph TD
    Spike[Sudden 30s Spike] --> ScaleUp[Scale Up to 100 Pods]
    SpikeEnd[Spike Clears] --> ScaleDown[Scale Down to 10 Pods]
    Spike2[Another Burst] --> ScaleUp2[Scale Up Again!]
    Note over ScaleUp,ScaleUp2: Causes continuous container cold starts and waste
```

### Prevention:
- **Cooldown / Stabilization Windows**: Require a metric to remain low for at least 5 minutes before initiating a scale-down.
- **Scale-Up Aggressive, Scale-Down Conservative**: Scale up instantly (e.g., +100% capacity), scale down slowly (e.g., -10% every 5 minutes).

---

## 4. Key Takeaways

- Scale horizontally on request rate or queue depth rather than lagging CPU metrics whenever possible.
- Configure aggressive scale-up policies paired with conservative scale-down cooldown windows to prevent thrashing.
- Align container autoscaling (HPA) with node autoscaling (Karpenter) to avoid scheduling deadlocks.
""",

    "08-zero-downtime-deployments.md": """# Zero-Downtime Deployment Strategies

Zero-downtime deployment patterns release new software versions into production without interrupting active user traffic, dropping requests, or degrading availability.

```mermaid
graph TD
    subgraph "1. Rolling Deployment"
        R_Old[Old Pods: 3] --> R_Transit[Replace 1 by 1] --> R_New[New Pods: 3]
    end

    subgraph "2. Blue-Green Deployment"
        Router[Router / Load Balancer]
        Router -->|100% Traffic| Blue[Blue Environment (v1.0)]
        Router -.->|0% Traffic (Staged & Tested)| Green[Green Environment (v2.0)]
        Note over Router: Instant cutover flips pointer from Blue to Green
    end

    subgraph "3. Canary Deployment"
        C_Router[Ingress Controller]
        C_Router -->|95% Live Traffic| C_Stable[Stable Baseline (v1.0)]
        C_Router -->|5% Canary Traffic| C_Canary[Canary Test (v2.0)]
    end
```

---

## 1. Comparing Deployment Strategies

| Dimension | Rolling | Blue-Green | Canary |
| :--- | :--- | :--- | :--- |
| **Downtime** | Zero | Zero | Zero |
| **Infrastructure Cost** | Low (only needs +20% surge capacity) | High (requires 2x full production hardware) | Low (requires 5-10% extra capacity) |
| **Rollback Speed** | Slow (must roll back pod by pod) | Instant (re-route load balancer back to Blue) | Instant (drop canary traffic routing) |
| **Blast Radius** | Medium (all users hit new version gradually) | All-or-nothing cutover | Minimal (only 1-5% of users exposed) |
| **Database Compatibility**| Requires strict backward compatibility | Requires strict backward compatibility | Requires strict backward compatibility |

---

## 2. Canary Deployments with Automated Metric Analysis (Kayenta)

```mermaid
graph LR
    Canary[Canary Deployment (v2.0 - 5%)] --> Telemetry[Prometheus / Datadog Metrics]
    Telemetry --> Kayenta[Canary Analysis Engine]
    Kayenta --> Check{Error Rate or Latency Spike?}
    Check -->|No - Safe| Promote[Promote to 10%, 25%, 100%]
    Check -->|Yes - Anomaly Detected!| Rollback[Automated Rollback to v1.0 within 30s]
```

---

## 3. The Expand-Contract (Parallel Run) Database Migration Pattern

Zero-downtime deployments fail if a new version requires a database schema change that breaks the old version (e.g., renaming a column).

```mermaid
sequenceDiagram
    autonumber
    participant AppV1 as Application v1.0
    participant AppV2 as Application v2.0
    participant DB as Relational Database

    Note over DB: Step 1: Expand (Add new column alongside old)
    DB->>DB: ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
    
    Note over AppV1: Step 2: Deploy Dual-Writing v1.1
    AppV1->>DB: Writes both first_name + last_name AND full_name
    
    Note over DB: Step 3: Backfill historical rows in background
    DB->>DB: UPDATE users SET full_name = first_name || ' ' || last_name;
    
    Note over AppV2: Step 4: Deploy v2.0 (Reads & Writes only full_name)
    AppV2->>DB: SELECT full_name FROM users;
    
    Note over DB: Step 5: Contract (Drop old deprecated columns)
    DB->>DB: ALTER TABLE users DROP COLUMN first_name, DROP COLUMN last_name;
```

---

## 4. Key Takeaways

- Prefer Canary deployments with automated metric analysis for high-traffic mission-critical services.
- Never rename database columns directly in production; always use the multi-step Expand-Contract pattern.
- Ensure applications implement graceful shutdown (handling SIGTERM, closing database connections, finishing in-flight requests) before terminating.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 11 complete.")
