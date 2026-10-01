import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\13-observability"

files = {
    "01-three-pillars-of-observability.md": """# The Three Pillars of Observability: Metrics, Logs, and Traces

Observability is a measure of how well internal states of a system can be inferred solely from knowledge of its external outputs. In distributed architectures, observability relies on three complementary telemetry pillars: Metrics, Logs, and Traces.

```mermaid
graph TD
    subgraph "The Three Pillars"
        M[Metrics: Aggregable, Numeric Telemetry<br/>Prometheus / StatsD]
        L[Logs: Timestamped Discrete Records<br/>Elasticsearch / Loki]
        T[Traces: End-to-End Request Journeys<br/>OpenTelemetry / Jaeger]
    end

    M -.->|Alerts: 'Latency spiked to 3s!'| T
    T -.->|Pinpoints culprit span: 'OrderService DB hang'| L
    L -.->|Reveals exact root cause: 'Deadlock on row 42'| Bug[Root Cause Solved]
```

---

## 1. Comparing the Three Pillars

| Pillar | Definition | Cardinality / Volume | Retention | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Metrics** | Numeric aggregations over fixed time intervals ($t$) | Low to Medium | Long (1-2 years, downsampled) | Real-time alerting, dashboards, trend analysis |
| **Logs** | Structured text lines detailing discrete events | Massive (High cost) | Short (7-30 days) | Post-mortem deep forensic debugging |
| **Traces** | Directed Acyclic Graph (DAG) of spans representing request lifecycle | High (Sampled: 1-10%) | Short (3-14 days) | Pinpointing latency bottlenecks in microservices |

---

## 2. OpenTelemetry (OTel): The Unified Standard

Historically, teams maintained separate SDKs for Prometheus, StatsD, Fluentd, and Zipkin. **OpenTelemetry** standardizes telemetry APIs, SDKs, and wire protocols (OTLP) across all languages into a single vendor-neutral collector.

```mermaid
graph LR
    App[Application with OTel SDK] -->|OTLP gRPC| Collector[OpenTelemetry Collector]
    Collector -->|Batch & Filter| M_Store[(Prometheus / M3DB)]
    Collector -->|Batch & Filter| L_Store[(Grafana Loki)]
    Collector -->|Batch & Filter| T_Store[(Jaeger / Tempo)]
```

---

## 3. Key Takeaways

- Metrics notify you that a problem exists; Traces tell you *where* the bottleneck is; Logs tell you *why* it failed.
- Adopt OpenTelemetry (OTel) to prevent vendor lock-in to proprietary monitoring vendors.
- Sample traces intelligently (head or tail-based) to control storage and network ingestion costs.
""",

    "02-red-and-use-methods.md": """# Monitoring Methodologies: RED and USE Methods

Standardizing metrics across hundreds of heterogeneous microservices requires structured frameworks: the **RED Method** for request-driven services, and the **USE Method** for resource infrastructure.

```mermaid
graph TD
    subgraph "RED Method (Services & APIs)"
        R[Rate: Requests per second]
        E[Errors: Number of failed requests]
        D[Duration: Time taken to serve requests]
    end

    subgraph "USE Method (Hardware & OS Infrastructure)"
        U[Utilization: % time resource is busy]
        S[Saturation: Degree of queued work]
        Er[Errors: Hardware / driver error events]
    end
```

---

## 1. The RED Method (Services and Microservices)

Invented by Tom Wilkie, the RED method focuses on what matters to end-users:
1. **Rate**: Throughput (requests per second) being handled by the service.
2. **Errors**: The count of failing requests per second (HTTP 5xx, gRPC status errors).
3. **Duration**: Distribution of request latencies (measured in percentiles: p50, p95, p99).

```mermaid
graph LR
    Req[Incoming Traffic] --> MetricCollection[Prometheus Middleware]
    MetricCollection --> Rate[http_requests_total [Rate]]
    MetricCollection --> Errors[http_requests_total{status=~'5..'}]
    MetricCollection --> Duration[http_request_duration_seconds_bucket [Histogram]]
```

---

## 2. The USE Method (Resource Infrastructure)

Created by Brendan Gregg for analyzing system performance bottlenecks:
1. **Utilization**: Percentage of time a resource is actively performing work (e.g., CPU at 85%, Disk IO utilization).
2. **Saturation**: Extra work that cannot be processed immediately and is queued waiting (e.g., CPU run queue depth, TCP backlog, disk wait queue).
3. **Errors**: Count of error events (e.g., dropped network packets, disk write errors).

```mermaid
graph LR
    Resource[Storage / CPU / NIC] --> Check1[Utilization: 99% - Saturated!]
    Check1 --> Check2[Saturation: Queue Depth = 45 tasks waiting]
    Check2 --> Alert[Alert: Resource Exhausted -> Add Capacity]
```

---

## 3. Key Takeaways

- Apply the **RED Method** to all HTTP/RPC microservice endpoints to measure user experience.
- Apply the **USE Method** to all infrastructure resources (CPU, Memory, Disk, Network interfaces).
- Never alert solely on averages; always track latency using p90, p99, and p99.9 percentiles.
""",

    "03-structured-logging-and-correlation-ids.md": """# Structured Logging and Correlation IDs

Unstructured plain-text logs (`printf("User logged in")`) are virtually useless in distributed microservices. Structured JSON logging paired with Correlation IDs enables instant searchability and end-to-end request tracing.

```mermaid
sequenceDiagram
    autonumber
    participant Client as User Browser
    participant GW as API Gateway
    participant OrderSvc as Order Service
    participant PaySvc as Payment Service

    Client->>GW: POST /orders (No Correlation ID)
    Note over GW: Generates: X-Correlation-ID: 7a8b-9c0d-1e2f
    GW->>OrderSvc: POST /orders (Header: X-Correlation-ID: 7a8b-9c0d-1e2f)
    Note over OrderSvc: Logs with {"correlation_id": "7a8b-9c0d-1e2f", "action": "create"}
    OrderSvc->>PaySvc: POST /charge (Header: X-Correlation-ID: 7a8b-9c0d-1e2f)
    Note over PaySvc: Logs with {"correlation_id": "7a8b-9c0d-1e2f", "action": "charge_failed"}
    PaySvc-->>OrderSvc: 500 Error
    OrderSvc-->>GW: 500 Error
    GW-->>Client: 500 Internal Error (Response Header: X-Correlation-ID: 7a8b-9c0d-1e2f)
```

---

## 1. Structured JSON Log Schema

Logs should be emitted as single-line JSON objects to standard output (`stdout`), where log collectors (Fluentbit, Vector) ingest and index them:

```json
{
  "timestamp": "2026-10-01T20:25:00.123Z",
  "level": "ERROR",
  "service": "payment-service",
  "correlation_id": "7a8b-9c0d-1e2f",
  "user_id": "usr_9981",
  "order_id": "ord_5521",
  "message": "Payment gateway declined card: Insufficient funds",
  "gateway_error_code": "CARD_DECLINED",
  "duration_ms": 342,
  "stack_trace": "..."
}
```

---

## 2. Correlation ID Propagation Rules

1. **Edge Injection**: If incoming request lacks `X-Correlation-ID` (or `traceparent`), the Edge API Gateway generates a UUIDv4.
2. **Context Passing**: Transport headers into language context (e.g., Go `context.Context`, Node.js `AsyncLocalStorage`, Java `MDC`).
3. **Outbound Forwarding**: HTTP/gRPC client interceptors automatically inject the header into all outbound calls.
4. **Return in Errors**: Always return the Correlation ID in HTTP error responses so customers can share it with customer support.

---

## 3. Key Takeaways

- Always log in structured JSON format; never emit unstructured text strings.
- Pass Correlation IDs across every network hop and thread boundary.
- Mask PII (credit cards, passwords, SSNs) at the logger level before emitting.
""",

    "04-distributed-tracing.md": """# Distributed Tracing (OpenTelemetry and Jaeger)

Distributed tracing tracks the execution flow and performance of requests as they propagate across multi-tier microservices, message queues, and databases.

```mermaid
gantt
    title Distributed Trace Waterfall: POST /checkout (Total: 420ms)
    dateFormat X
    axisFormat %s ms

    section API Gateway
    Authenticate & Route : 0, 40
    section Order Service
    Validate Order       : 40, 90
    Create Order Record  : 90, 160
    section Payment Service
    Authorize Stripe Card : 160, 360
    section Kafka Broker
    Publish OrderPlaced   : 360, 390
    section Response
    Serialize JSON Response: 390, 420
```

---

## 1. Core Primitives: Traces and Spans

- **Span**: The fundamental unit of work. Contains a name, start time, duration, attributes (tags), status code, and optional events.
- **Trace**: A tree or Directed Acyclic Graph (DAG) of spans representing an entire end-to-end request.
- **Trace Context (W3C TraceContext)**: Standardized HTTP headers (`traceparent`):
  ```
  traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
               |  |                                |                |
             ver  Trace ID (16 bytes)              Span ID (8 bytes) Trace Flags
  ```

---

## 2. Trace Sampling Strategies

Tracing 100% of billions of requests exhausts storage and consumes up to 20% of network bandwidth.

```mermaid
graph TD
    subgraph "Head-Based Sampling (Decided at Gateway)"
        Req1[Incoming Request] --> HeadChoice{Random Sample 1%?}
        HeadChoice -->|Yes| TraceAll[Trace all downstream hops]
        HeadChoice -->|No| DropTrace[Drop tracing context]
    end

    subgraph "Tail-Based Sampling (Decided at OTel Collector)"
        Req2[All Spans Streamed to Collector Buffer] --> CollectorBuffer[Memory Buffer (30s)]
        CollectorBuffer --> TailCheck{Did Trace Error OR Exceed 1000ms?}
        TailCheck -->|Yes - Anomaly!| Keep[Keep 100% of Outlier Traces]
        TailCheck -->|No - Normal Fast Trace| Discard[Sample 0.1% of Normal Traces]
    end
```

---

## 3. Key Takeaways

- Adopt the W3C TraceContext standard (`traceparent`) across all internal microservice calls.
- Use Head-Based sampling for basic traffic control and Tail-Based sampling to capture 100% of errors and latency outliers.
- Annotate spans with useful high-cardinality metadata (e.g., `user.id`, `tenant.id`, `order.id`).
""",

    "05-alerting-best-practices-and-runbooks.md": """# Alerting Best Practices, Runbooks, and On-Call

Alerting must be actionable, symptom-based, and resilient against alert fatigue. An un-actionable alert woken up at 3:00 AM leads to burnout and missed production outages.

```mermaid
graph TD
    Event[System Telemetry / SLI Breach] --> AlertMgr[Alertmanager]
    AlertMgr --> SeverityCheck{Severity Level}
    SeverityCheck -->|P1/P2 Critical: Customers Impacted| PagerDuty[PagerDuty / VictorOps -> Page On-Call Engineer]
    SeverityCheck -->|P3 Minor: Degradation, but redundant| Slack[Slack / Teams Channel Alert]
    SeverityCheck -->|P4 Informational: Daily report| Jira[Create Jira Ticket / Backlog]
    PagerDuty --> Runbook[Open Linked Runbook -> Follow Remediation Steps]
```

---

## 1. Alert on Symptoms, Not Causes

- **Bad (Cause-Based)**: "Server 4 CPU at 92%!" (Who cares if users are experiencing zero errors and sub-50ms latency?)
- **Good (Symptom-Based)**: "Checkout error rate > 1.5% for 3 consecutive minutes!" (Direct customer impact requiring immediate intervention).

---

## 2. Anatomy of a Production Alert

Every critical on-call alert must contain four essential components:
1. **Summary & Impact**: "Payment processing failure rate is 8.2% (impacts ~500 users/minute)."
2. **Dashboard Link**: One-click link to Grafana dashboard showing relevant RED metrics.
3. **Runbook Link**: Clear step-by-step remediation guide.
4. **Trigger Condition**: Exact Prometheus PromQL query that tripped the alert.

```yaml
# Prometheus Alert Rule
- alert: HighPaymentFailureRate
  expr: (sum(rate(http_requests_total{service="payment",status=~"5.."}[5m])) 
        / sum(rate(http_requests_total{service="payment"}[5m]))) * 100 > 5
  for: 3m
  labels:
    severity: critical
  annotations:
    summary: "Payment Service error rate exceeds 5%"
    runbook_url: "https://wiki.company.internal/runbooks/payment-failure"
```

---

## 3. Key Takeaways

- Page humans only for critical, user-facing, actionable emergencies.
- Every alert must include a direct link to a tested Runbook.
- Continuously tune alerts; delete flapping alerts that do not require immediate human action.
""",

    "06-health-checks-and-dashboards.md": """# Health Checks and Operational Dashboards

Health checks allow orchestrators (Kubernetes, AWS ALB) to monitor service lifecycles, route traffic away from failing pods, and restart hung processes safely.

```mermaid
graph TD
    subgraph "Kubernetes Health Check Probes"
        Kubelet[Kubelet Controller]
        Kubelet -->|1. Startup Probe: Has app finished initializing?| P_Start[Startup Probe]
        Kubelet -->|2. Liveness Probe: Is app deadlocked / stuck?| P_Live[Liveness Probe]
        Kubelet -->|3. Readiness Probe: Can app accept new user traffic?| P_Ready[Readiness Probe]
    end

    P_Live -->|Fails 3x| Restart[Kill and Restart Container]
    P_Ready -->|Fails 1x| RemoveTraffic[Remove Pod IP from Load Balancer Endpoints]
```

---

## 1. The Three Health Probes

1. **Startup Probe**: Runs during initialization (loading ML models, warming caches). Disables liveness and readiness checks until it succeeds.
2. **Liveness Probe**: Determines if the application process is deadlocked or in an unrecoverable state. If it fails, Kubernetes kills and restarts the container.
   - *Pitfall*: Never check downstream dependencies (DB, Redis) in a liveness probe! If the DB goes down, killing all web pods will cause a catastrophic restart storm.
3. **Readiness Probe**: Determines if the pod is ready to accept incoming traffic. If the database connection pool is temporarily saturated, the readiness probe fails and the load balancer stops sending new requests until it recovers.

---

## 2. Designing Operational Dashboards

A great operational dashboard tells a complete story at a glance:
- **Top Row (Executive / Health)**: Overall Request Rate, Global Error Rate (5xx), p95/p99 Latency.
- **Middle Row (Service Dependencies)**: Database query latency, Redis cache hit ratio, external API dependency latency.
- **Bottom Row (Infrastructure / Saturation)**: CPU utilization, Memory usage (JVM Heap / RSS), Pod restart count.

---

## 3. Key Takeaways

- Never check downstream dependencies in Liveness probes.
- Use Readiness probes to shed traffic when local resource queues or connection pools fill up.
- Build hierarchical dashboards: high-level business SLIs at top, low-level infrastructure at bottom.
""",

    "07-incident-response-and-postmortems.md": """# Incident Response and Blameless Postmortems

Outages are inevitable in complex distributed systems. How organizations respond to incidents and learn from them separates resilient engineering teams from fragile ones.

```mermaid
graph LR
    Detect[1. Detection & Paging] --> Triage[2. Triage & Incident Commander Assigned]
    Triage --> Mitigate[3. Mitigation / Rollback / Failover]
    Mitigate --> Resolve[4. Verification & Incident Resolved]
    Resolve --> Postmortem[5. Blameless Postmortem & Corrective Actions]
```

---

## 1. The Incident Command System (ICS) Roles

During a major Sev-1 outage, clear roles prevent chaotic parallel actions:
- **Incident Commander (IC)**: Owns the incident. Directs the response, delegates investigation tasks, and has final authority on rollbacks or failovers. Does NOT write code or debug.
- **Operations Lead**: Technical lead investigating logs, executing commands, and applying mitigations.
- **Communications Lead**: Updates external status pages (Statuspage.io) and internal executive stakeholders every 15-30 minutes.

---

## 2. Principles of Blameless Postmortems

Pioneered by John Allspaw and Google SRE:
- **Assume Good Intent**: Engineers do not come to work to break production. Failures are systemic defects in tooling, guardrails, automated testing, or process.
- **Eliminate "Human Error"**: If a command typo deleted production data, the root cause is not "operator typed wrong command"—the root cause is *lack of role-based confirmation guards or read-only staging tooling*.
- **The "5 Whys" Technique**: Drill down past superficial symptoms to systemic flaws.

---

## 3. Key Takeaways

- First priority during an incident is **mitigation** (rollback, traffic shed, failover), not debugging root causes.
- Conduct blameless postmortems within 48 hours of every major outage.
- Track all postmortem action items in issue trackers with assigned owners and deadlines.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 13 complete.")
