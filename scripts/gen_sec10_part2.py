import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\10-architecture-patterns"

files = {
    "06-hexagonal-and-clean-architecture.md": """# Hexagonal and Clean Architecture (Ports and Adapters)

Hexagonal Architecture (introduced by Alistair Cockburn) and Clean Architecture (Uncle Bob Martin) organize software systems such that business rules remain completely decoupled from databases, frameworks, transport protocols, and UI.

```mermaid
graph TD
    subgraph "External Adapters (Infrastructure Layer)"
        REST[REST Controller]
        CLI[CLI Command]
        KafkaConsumer[Kafka Consumer]
        Postgres[Postgres Repository]
        S3[S3 Storage Adapter]
        SendGrid[SendGrid Email Adapter]
    end

    subgraph "Ports (Interface Boundaries)"
        InPort1[Inbound Port: PlaceOrderUseCase]
        OutPort1[Outbound Port: OrderRepository]
        OutPort2[Outbound Port: PaymentGateway]
        OutPort3[Outbound Port: NotificationSender]
    end

    subgraph "Domain Core (Pure Business Logic - Zero External Dependencies)"
        Entities[Domain Entities: Order, LineItem, Money]
        Logic[Business Validation & Rules]
    end

    REST --> InPort1
    CLI --> InPort1
    KafkaConsumer --> InPort1

    InPort1 --> Logic
    Logic --> Entities

    Logic --> OutPort1
    Logic --> OutPort2
    Logic --> OutPort3

    Postgres -.->|Implements| OutPort1
    S3 -.->|Implements| OutPort2
    SendGrid -.->|Implements| OutPort3
```

---

## 1. The Dependency Inversion Principle (DIP)

The core tenet of Clean Architecture is: **Dependencies must point inward toward high-level business rules**. 

```mermaid
graph LR
    subgraph Traditional Layered Architecture (Tightly Coupled)
        UI[UI Layer] --> BLL[Business Logic]
        BLL --> DAL[Data Access / DB (Downstream!)]
    end

    subgraph Clean Architecture (Inverted)
        CleanBLL[Core Business Logic] --> PortInterface[Repository Interface (Port)]
        ConcreteRepo[Postgres Implementation] -.->|Implements / Inverts| PortInterface
    end
```

In Clean Architecture, your core domain knows nothing about SQL, ORMs (Hibernate, Prisma), AWS SDKs, or HTTP libraries. The database is a trivial plugin.

---

## 2. Ports and Adapters in Code

### 1. The Port (Core Domain Interface)
```go
package domain

type OrderRepository interface {
    Save(order *Order) error
    FindByID(id string) (*Order, error)
}
```

### 2. The Use Case (Application Service)
```go
type PlaceOrderUseCase struct {
    repo OrderRepository // Injected interface
}

func (uc *PlaceOrderUseCase) Execute(cmd PlaceOrderCommand) error {
    order := NewOrder(cmd.CustomerID, cmd.Items)
    return uc.repo.Save(order)
}
```

### 3. The Adapter (Infrastructure Implementation)
```go
package postgres

type PostgresOrderRepository struct {
    db *sql.DB
}

func (r *PostgresOrderRepository) Save(order *domain.Order) error {
    _, err := r.db.Exec("INSERT INTO orders (id, customer_id) VALUES ($1, $2)", order.ID, order.CustomerID)
    return err
}
```

---

## 3. Benefits and Trade-offs

| Dimension | Clean / Hexagonal Architecture | Traditional Layered Architecture |
| :--- | :--- | :--- |
| **Testability** | 100% pure in-memory unit tests with zero DB mocks | Requires spinning up Docker / test DBs |
| **Framework Independence** | Upgrade framework or DB with zero domain changes | Framework upgrades break business logic |
| **Boilerplate & Files** | Higher (requires DTO mappers, interfaces, adapters) | Lower initial setup |
| **Cognitive Load** | High for junior developers | Low (everyone writes in controllers/services) |

---

## 4. Key Takeaways

- Protect your domain model from database schemas and external API shapes.
- Use Inbound Ports for driving operations (HTTP, CLI, Kafka) and Outbound Ports for driven operations (DB, SMTP, S3).
- Swap persistence technologies or transport protocols without altering a single line of business validation logic.
""",

    "07-strangler-fig-and-migration-patterns.md": """# Strangler Fig and Legacy Migration Patterns

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
""",

    "08-bff-sidecar-ambassador-patterns.md": """# BFF, Sidecar, and Ambassador Patterns

Modern distributed architectures decouple peripheral cross-cutting concerns (transport security, logging, client formatting) from core application business logic using helper patterns.

```mermaid
graph TD
    subgraph "Backend-For-Frontend (BFF)"
        WebClient[Web Browser] --> BFF_Web[Web BFF (SSR / Rich Desktop Data)]
        MobileClient[Mobile App] --> BFF_Mobile[Mobile BFF (Aggregated / Compact Data)]
        BFF_Web --> Svc1[Microservice A]
        BFF_Web --> Svc2[Microservice B]
        BFF_Mobile --> Svc1
        BFF_Mobile --> Svc2
    end

    subgraph "Sidecar Pattern (Pod / Container Colocation)"
        subgraph Kubernetes Pod
            App[App Container (Node.js)] <-->|localhost / IPC| Sidecar[Envoy Proxy Sidecar]
        end
        Sidecar -->|mTLS, Tracing, Metrics| Mesh[Service Mesh Network]
    end
```

---

## 1. Backend-For-Frontend (BFF) Pattern

### The Problem:
A single generic API Gateway serving desktop web, iOS, Android, and smart watches forces compromises:
- Mobile needs tiny payloads and aggregated calls to conserve cellular battery and bandwidth.
- Desktop web needs rich relational data and server-side rendering (SSR).

### The BFF Solution:
Each frontend platform owns and maintains its dedicated backend service:
- **Mobile BFF**: Aggregates 5 internal microservices into one compact payload; strips unused fields.
- **Web BFF**: Handles cookie-based auth, Next.js server actions, and desktop-specific features.

---

## 2. Sidecar Pattern

A sidecar attaches an independent helper process to an application without altering application code. In Kubernetes, both containers run inside the same Pod, sharing the same network namespace (`localhost`) and filesystem volumes.

```mermaid
graph LR
    subgraph Kubernetes Pod
        Main[Main Application (Business Logic)]
        SC1[Sidecar: Envoy Proxy (mTLS & Routing)]
        SC2[Sidecar: Fluentbit (Log Forwarding)]
        Main <-->|localhost:15001| SC1
        Main -->|Writes /var/log/app.log| SC2
    end
    SC1 -->|External Traffic| Remote[Downstream Service]
    SC2 -->|Ship Logs| Elastic[(Elasticsearch)]
```

### Common Sidecar Use Cases:
1. **Service Mesh Proxies (Istio / Linkerd)**: Transparently intercepts all outbound/inbound traffic to handle mTLS encryption, circuit breaking, and telemetry.
2. **Log Collectors**: Fluentbit or Filebeat tails local log files and streams them to central aggregators.
3. **Secret Injectors**: HashiCorp Vault Agent sidecar periodically fetches dynamic database credentials and mounts them into a shared memory volume.

---

## 3. Ambassador Pattern

An Ambassador is a specialized out-of-process proxy that offloads network routing, retries, and protocol translation on behalf of an application.

```mermaid
graph LR
    App[Legacy Application] -->|Plain HTTP localhost:8080| Ambassador[Ambassador Proxy]
    Ambassador -->|gRPC + TLS + Retry with Jitter| RemoteSvc[Cloud Microservice]
```

- Application makes simple local HTTP calls.
- Ambassador manages complex transport: circuit breaking, timeouts, connection pooling, and credential refreshing.

---

## 4. Key Takeaways

- Use BFFs to allow frontend teams to iterate independently without bloating shared backend APIs.
- Use Sidecars to keep business logic pure while standardizing logging, metrics, and security.
- Ambassador proxies allow legacy applications to communicate with modern cloud services without modifying legacy source code.
""",

    "09-multi-tenant-architecture.md": """# Multi-Tenant Architecture (SaaS)

Multi-tenancy is an architectural model where a single software instance serves multiple distinct customer organizations (tenants), ensuring strict data isolation, cost efficiency, and performance predictability.

```mermaid
graph TD
    subgraph "1. Silo Model (Separate Everything)"
        T1_App[Tenant 1 App] --> T1_DB[(Tenant 1 DB)]
        T2_App[Tenant 2 App] --> T2_DB[(Tenant 2 DB)]
    end

    subgraph "2. Pool Model (Shared Everything)"
        SharedApp[Shared App Instances] --> SharedDB[(Shared Database)]
        Note over SharedDB: Every table has tenant_id column
    end

    subgraph "3. Hybrid (Bridge Model)"
        H_App[Shared App] --> H_DB_T1[(Tenant 1 DB - Enterprise)]
        H_App --> H_DB_Shared[(Shared DB - Free Tier)]
    end
```

---

## 1. Multi-Tenancy Models Comparison

| Dimension | Silo (Dedicated Database) | Pool (Shared DB, Shared Schema) | Bridge (Shared DB, Separate Schemas) |
| :--- | :--- | :--- | :--- |
| **Data Isolation** | Complete / Physical isolation | Logical isolation via `tenant_id` | Logical / Schema isolation |
| **Cost per Tenant** | High (expensive idle resources) | Minimal (maximum resource sharing) | Moderate |
| **Noisy Neighbor Risk** | Zero | High (requires rate limits) | Low to Moderate |
| **Schema Migration** | Slow ($N$ migrations for $N$ tenants) | Instant (1 migration updates all) | Moderate ($N$ schema updates) |
| **Compliance (HIPAA, SOC2)**| Trivial | Requires strict logical proof | Accepted by most auditors |

---

## 2. Preventing Cross-Tenant Data Leaks (The Golden Rule)

A multi-tenant application must **never** rely solely on application developers remembering to add `WHERE tenant_id = :id`. A single missed clause can cause catastrophic data leakage.

```mermaid
graph LR
    Req[Incoming Request with JWT] --> GW[Extract tenant_id: 'org_123']
    GW --> RLS[Postgres Row-Level Security (RLS)]
    RLS --> DB[(Database Tables)]
    Note over RLS: Enforces tenant_id = current_setting('app.current_tenant')<br/>Even 'SELECT * FROM users' returns only tenant rows!
```

### PostgreSQL Row-Level Security (RLS) Implementation:
```sql
-- 1. Enable RLS on table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 2. Create Security Policy
CREATE POLICY tenant_isolation_policy ON orders
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 3. On each request / connection acquisition:
SET LOCAL app.current_tenant_id = 'a1b2c3d4-e5f6-...';
```

---

## 3. Mitigating the "Noisy Neighbor" Problem

A single tenant generating millions of requests can consume all CPU, database connections, and cache space, starving other tenants.

```mermaid
graph TD
    Req[Tenant Requests] --> TR[Per-Tenant Token Bucket Rate Limiter]
    TR -->|Within Quota| App[App Workers]
    TR -->|Exceeded Limit| 429[HTTP 429 Too Many Requests]
    App --> PQ[Fair Queueing: Tenant Round-Robin Worker Pools]
```

### Defenses:
1. **Per-Tenant Rate Limiting**: Redis token buckets keyed by `tenant_id`.
2. **Fair Queueing**: Use separate queues or round-robin consumer loops so one tenant's backlog does not block others.
3. **Tenant Sharding**: Large enterprise tenants get dedicated shard clusters; small free-tier tenants share pool shards.

---

## 4. Key Takeaways

- Choose Pool model for standard SaaS cost efficiency; offer Silo for high-value enterprise tiers.
- Enforce database isolation at the engine level using PostgreSQL Row-Level Security (RLS) or schema-per-tenant.
- Implement per-tenant rate limiting and fair queueing to eliminate noisy neighbor degradation.
""",

    "10-service-discovery-and-dynamic-config.md": """# Service Discovery and Dynamic Configuration

In dynamic cloud environments where containers and VMs constantly scale, terminate, and restart with ephemeral IP addresses, service discovery and centralized dynamic configuration are mandatory.

```mermaid
graph TD
    subgraph "Server-Side Service Discovery"
        C1[Client] --> LB[Load Balancer / Ingress]
        LB --> Registry1[(Service Registry / Kube-DNS)]
        LB --> PodA[Backend Pod A]
        LB --> PodB[Backend Pod B]
    end

    subgraph "Client-Side Service Discovery"
        C2[Client] --> Registry2[(Service Registry: Consul / Eureka)]
        Registry2 -.->|Returns: [10.0.1.5, 10.0.1.6]| C2
        C2 -->|Direct RPC with P2C / Round Robin| PodC[Backend Pod C]
    end
```

---

## 1. Client-Side vs Server-Side Service Discovery

| Dimension | Client-Side Discovery | Server-Side Discovery |
| :--- | :--- | :--- |
| **How It Works** | Client queries registry and load balances directly | Client sends to load balancer; LB queries registry |
| **Network Hops** | 1 hop (Direct client-to-backend) | 2 hops (Client -> LB -> Backend) |
| **Client Complexity**| High (requires discovery SDK in each language) | Zero (client uses standard DNS or fixed IP) |
| **Used By** | Netflix Eureka / Finagle, gRPC xDS | Kubernetes (Kube-DNS + ClusterIP), AWS ALB |

---

## 2. Dynamic Configuration Management

Hardcoded configurations or environment variables that require application restarts to update are dangerous during outages (e.g., toggling a kill-switch or reducing rate limits).

```mermaid
sequenceDiagram
    autonumber
    participant Admin as Operator / Dashboard
    participant Store as Config Store (Consul / etcd)
    participant App as Application Pods

    Admin->>Store: Update "features.checkout_v2_enabled" = false
    Store-->>App: Long-Polling HTTP / Watch Notification Stream
    App->>App: Re-evaluates configuration in-memory (0 restart downtime!)
    App-->>Store: Acknowledged update
```

### Essential Rules for Dynamic Config:
1. **Schema Validation**: Reject invalid config values at the storage engine before propagating to nodes.
2. **Gradual Rollout (Canary Config)**: Deploy configuration changes to 5% of instances first, verify metrics, then rollout globally.
3. **Fallback Defaults**: Applications must hold hardcoded safe fallback defaults in case the dynamic config store becomes unreachable.

---

## 3. Real-World Case Studies

1. **Netflix**: Created Eureka for client-side discovery and Archaius for dynamic property management across thousands of AWS EC2 instances.
2. **Kubernetes**: Uses etcd as the backing store for all cluster state, CoreDNS for DNS-based service discovery, and ConfigMaps for dynamic volume mounts.
3. **Consul**: Provides multi-datacenter service discovery, health checking, and distributed K/V storage.

---

## 4. Key Takeaways

- Kubernetes built-in service discovery (CoreDNS + Services) is standard for cloud-native container workloads.
- Use dynamic configuration for feature flags, rate limits, and circuit breaker thresholds to modify system behavior without redeploying.
- Always implement health checking so dead instances are automatically pruned from service registries within seconds.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 10 Part 2 complete.")
