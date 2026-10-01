# Strangler Fig and Legacy Migration Patterns

The Strangler Fig pattern (coined by Martin Fowler) incrementally migrates a monolithic legacy system by replacing specific functional slices with new microservices until the legacy monolith can be safely retired.

```mermaid
graph TD
    subgraph Phase 1: Intercept at Gateway
        C1[Client Traffic] --> Proxy[Reverse Proxy / API Gateway]
        Proxy -->|95% Existing Traffic| Mono1[Legacy Monolith]
        Proxy -->|5% Migrated Traffic: /orders| Svc1[New Order Service]
    end

    subgraph Phase 2: Incremental Strangling
        C2[Client Traffic] --> Proxy2[API Gateway]
        Proxy2 -->|Legacy: /reporting, /crm| Mono2[Shrinking Monolith]
        Proxy2 -->|/orders| SvcO[Order Service]
        Proxy2 -->|/users| SvcU[User Service]
        Proxy2 -->|/payments| SvcP[Payment Service]
    end

    subgraph Phase 3: Monolith Deprecation
        C3[Client Traffic] --> Proxy3[API Gateway]
        Proxy3 --> SvcO2[Order Service]
        Proxy3 --> SvcU2[User Service]
        Proxy3 --> SvcP2[Payment Service]
        Note over Proxy3: Legacy Monolith Completely Decommissioned!
    end
```

---

## 1. Why "Big Bang" Rewrites Almost Always Fail

Large-scale "Big Bang" rewrites fail because:
1. **Moving Target Problem**: The legacy system continues evolving to support business needs during the 2-year rewrite.
2. **Hidden Business Rules**: Edge cases, undocumented bug workarounds, and implicit behaviors in legacy code are missed.
3. **High Deployment Risk**: Cutting over all traffic at once exposes the entire business to catastrophic failure.

The Strangler Fig replaces small, low-risk vertical slices incrementally, delivering production value immediately.

---

## 2. Data Migration: Dual-Write and CDC Reconciliation

Extracting a service requires migrating its underlying data without downtime:

```mermaid
sequenceDiagram
    autonumber
    participant App as Modern Proxy / Dual Writer
    participant LegacyDB as Legacy Monolith DB
    participant NewDB as New Microservice DB
    participant CDC as Debezium CDC / Worker

    Note over App: Phase 1: Dual Writing
    App->>NewDB: 1. Write to New DB (System of Record)
    App->>LegacyDB: 2. Write to Legacy DB (Async / Non-blocking)
    
    Note over CDC: Phase 2: Historical Backfill & CDC
    CDC->>LegacyDB: Reads 50M historical records in batches
    CDC->>NewDB: Upserts records into New DB schema
    
    Note over App: Phase 3: Shadow Reading (Dark Launch)
    App->>NewDB: Read from New DB
    App->>LegacyDB: Read from Legacy DB (in background)
    Note over App: Compares outputs; alerts on discrepancy!
    
    Note over App: Phase 4: Cutover & Sever Legacy Links
```

---

## 3. Migration Safety Patterns

1. **Feature Flags**: Dynamically toggle traffic between old and new implementations per user or percentage.
2. **Dark Launching (Shadow Traffic)**: Duplicate live production traffic (using Envoy `request_mirror_policy`). Send live response from legacy, while sending a shadow copy to the new service to benchmark latency and verify data correctness without impacting users.
3. **Canary Releases**: Route 1% of live traffic to the new service, monitoring error rates and latency before increasing to 10%, 50%, and 100%.

---

## 4. Real-World Case Studies

1. **Etsy**: Migrated their massive PHP monolith to an API-driven architecture incrementally using the Strangler Fig pattern over several years without downtime.
2. **Uber**: Strangled their initial Python monolithic backend ("Dispatch") into Golang and Java microservices as ride volume scaled globally.

---

## 5. Key Takeaways

- Never attempt a "Big Bang" complete system rewrite.
- Use API gateways or reverse proxies to route traffic on an endpoint-by-endpoint basis.
- Use Dual-Writing, CDC backfills, and shadow traffic comparison to ensure 100% data correctness before cutting over.
