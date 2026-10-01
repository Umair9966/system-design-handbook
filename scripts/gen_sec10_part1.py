import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\10-architecture-patterns"

files = {
    "01-monoliths-and-modular-monoliths.md": """# Monoliths and Modular Monoliths

A monolithic architecture structures an entire application as a single deployable artifact executing within a shared memory space. A **modular monolith** preserves this single deployment unit while strictly enforcing logical domain boundaries at compile-time.

```mermaid
graph TD
    subgraph "Spaghetti Monolith (Tightly Coupled)"
        UI1[Web UI] --> Core1[Shared State & Mixed Logic]
        Core1 --> DB1[(Single Shared DB Without Schemas)]
    end

    subgraph "Modular Monolith (Bounded Contexts)"
        API[API / Gateway Layer] --> ModA[User Module (Private Package)]
        API --> ModB[Billing Module (Private Package)]
        API --> ModC[Catalog Module (Private Package)]
        ModA -.->|Internal Event Bus / In-Memory Interface| ModB
        ModB -.->|Internal Event Bus / In-Memory Interface| ModC
        ModA --> DB_User[(User Schema)]
        ModB --> DB_Bill[(Billing Schema)]
        ModC --> DB_Cat[(Catalog Schema)]
    end
```

---

## 1. What It Is & Why It Matters

Teams often default to microservices too early, incurring severe distributed systems overhead: network latency, distributed transactions, observability complexity, and operational cost.

The modular monolith provides the best of both worlds:
- **Zero Network Overhead**: Inter-module communication consists of function calls and in-memory pointer passing rather than JSON/HTTP serialization over sockets.
- **Transactional Simplicity**: ACID transactions are natively available across modules when necessary.
- **Single Deployment Artifact**: Continuous deployment and infrastructure footprint remain straightforward (single Docker container or binary).
- **Enforced Boundaries**: Strict package visibility (e.g., Go internal packages, Java ArchUnit / JPMS, TypeScript project references) prevents cross-domain code pollution.

---

## 2. Enforcing Module Isolation

Without tooling, modular monoliths decay into "big balls of mud." Teams must enforce boundary rules programmatically:

```mermaid
graph LR
    subgraph "Order Module"
        OrderController[Order API] --> OrderService[Order Service]
        OrderService --> OrderRepo[Order Repository]
    end

    subgraph "Inventory Module"
        InvService[Inventory Service API] --> InvRepo[Inventory DB]
    end

    OrderService -->|ALLOWED: Public Interface Call| InvService
    OrderService -.->|FORBIDDEN: Direct DB Query| InvRepo
```

### Techniques for Boundary Enforcement:
1. **Public API Interface Contracts**: Modules expose only interface contracts (e.g., `inventory.CheckStock()`); internal classes, entities, and repositories remain package-private.
2. **Architecture Linter Tests (e.g., ArchUnit in Java, ESLint boundary rules)**:
   ```java
   // Example ArchUnit test
   noClasses().that().resideInAPackage("..order..")
       .should().accessClassesThat().resideInAPackage("..inventory.internal..")
       .check(importedClasses);
   ```
3. **Database Schema Separation**: Each module owns its own schema (`order_schema`, `inventory_schema`). Cross-schema foreign keys and direct cross-schema joins are prohibited.

---

## 3. Trade-offs: Modular Monolith vs Microservices

| Dimension | Modular Monolith | Microservices |
| :--- | :--- | :--- |
| **Communication Latency** | Nanoseconds (in-memory function call) | Milliseconds (TCP, TLS, L7 serialization) |
| **Operational Overhead** | Extremely Low (single binary, simple CI/CD) | High (Kubernetes, Envoy, distributed tracing) |
| **Deployment Independence** | None (whole binary deploys together) | High (independent deployments per service) |
| **Failure Blast Radius** | High (memory leak or panic crashes process) | Contained to single service |
| **Hardware Scaling** | Scale entire binary vertically or horizontally | Fine-grained scaling per resource-heavy service |
| **Data Consistency** | Local ACID transactions | Sagas / Eventual Consistency |

---

## 4. Real-World Case Studies

1. **Shopify**: Operates one of the world's largest modular monoliths in Ruby on Rails, serving hundreds of thousands of requests per second during Black Friday. Enforces strict module boundaries using `packwerk`.
2. **Stack Overflow**: Runs the entire multi-billion-page-view developer platform on a handful of monolithic .NET servers and SQL Server instances with sub-10ms response times.
3. **GitHub**: Built originally as a monolithic Rails application, evolving toward modularity while retaining a unified core for developer workflows.

---

## 5. Common Pitfalls

- **Leaking Domain Entities**: Passing raw database entities (`UserRecord`) across module boundaries instead of immutable Data Transfer Objects (DTOs).
- **Direct Cross-Module Database Joins**: Joining tables owned by another module defeats encapsulation and prevents future service extraction.
- **Uncontrolled Global State**: Shared mutable singletons that allow module A to side-effect module B silently.

---

## 6. Key Takeaways

- Start with a modular monolith before extracting microservices.
- Enforce domain boundaries in CI using architectural linters or language-level visibility.
- Isolate database schemas per module to make future microservice extraction trivial if scale demands it.
""",

    "02-microservices-architecture-and-pitfalls.md": """# Microservices Architecture and Distributed Pitfalls

Microservices architecture decomposes an application into a collection of independently deployable, loosely coupled services organized around business domains.

```mermaid
graph TD
    Client[Mobile / Web Client] --> AGW[API Gateway]
    AGW -->|Auth Token| AuthSvc[Auth Service]
    AGW -->|Order Request| OrderSvc[Order Service]
    AGW -->|User Profile| UserSvc[User Service]
    OrderSvc -.->|Publishes: OrderPlaced| Kafka[Event Bus / Kafka]
    Kafka -.->|Consumes: OrderPlaced| PaymentSvc[Payment Service]
    Kafka -.->|Consumes: OrderPlaced| EmailSvc[Notification Service]
    Kafka -.->|Consumes: OrderPlaced| InventorySvc[Inventory Service]
    OrderSvc --> DB_Order[(Order DB)]
    PaymentSvc --> DB_Pay[(Payment DB)]
    UserSvc --> DB_User[(User DB)]
```

---

## 1. When Microservices Make Sense

Microservices are primarily an **organizational scaling pattern** rather than a purely technical performance optimization.

### Good Reasons to Adopt Microservices:
- **Multiple Independent Engineering Teams**: 50+ engineers where monolithic merge conflicts, deployment queues, and coordination overhead stall velocity.
- **Heterogeneous Scaling Requirements**: One component requires GPU compute or 100,000 req/sec (e.g., video transcoding or real-time telemetry), while billing runs 10 req/sec.
- **Strict Compliance / Security Boundaries**: PCI-DSS payment handling isolated from the rest of the application to minimize compliance audit scope.

---

## 2. The Distributed Tax (Hidden Costs)

Moving from in-memory calls to network-based microservices introduces severe architectural taxes:

```mermaid
graph LR
    subgraph "In-Memory Monolith Call"
        A1[Caller] -->|0.0001 ms<br/>Zero Network Latency<br/>Atomic Transaction| B1[Callee]
    end

    subgraph "Distributed Microservice Call"
        A2[Caller] -->|DNS Lookup<br/>TCP/TLS Handshake<br/>Serialization (JSON/Proto)<br/>Routing (Envoy)<br/>Network Latency (1-10ms)<br/>Partial Failure Risk| B2[Callee]
    end
```

### The 4 Major Distributed Taxes:
1. **Network Latency & Fanout Amplification**: If an API gateway calls 10 microservices sequentially, latency sums up ($10 \times 15\text{ms} = 150\text{ms}$).
2. **Dual-Write & Partial Failure Problems**: Updating Service A and Service B requires distributed consensus or Sagas; network partitions can leave state permanently inconsistent.
3. **Operational Complexity**: Requires Kubernetes, service meshes (Istio/Envoy), distributed tracing (OpenTelemetry/Jaeger), central logging, and canary deployment pipelines.
4. **Data Duplication**: Cross-service querying requires denormalizing data or asynchronous event-driven replication.

---

## 3. Database-per-Service vs Shared Database

```mermaid
graph TD
    subgraph "Anti-Pattern: Shared Database"
        S1[Service 1] --> DB[(Shared DB)]
        S2[Service 2] --> DB
        Note over DB: Schema migration by S1 breaks S2 without warning
    end

    subgraph "Best Practice: Database-per-Service"
        S3[Service 1] --> DB1[(Service 1 DB)]
        S4[Service 2] --> DB2[(Service 2 DB)]
        S3 -.->|Asynchronous Event / API| S4
    end
```

The golden rule of microservices is **Database-per-Service**. If two services read and write to the same relational tables, you have a **distributed monolith**: all the network latency and deployment complexity of microservices, with all the coupling of a monolith.

---

## 4. Common Distributed Antipatterns

1. **Distributed Monolith**: Services must be deployed simultaneously in a specific order; changing one service requires modifying three others.
2. **Chatty Microservices**: Fine-grained entities making hundreds of network round-trips to assemble a single web page.
3. **Synchronous Cascade Outages**: Service A calls B, which calls C, which calls D. When D slows down, threads exhaust backward across the entire chain until the whole system crashes.

---

## 5. Real-World Case Studies

1. **Amazon**: Migrated from the "Obidos" monolith to service-oriented architectures in the early 2000s, establishing the two-pizza team structure and fueling AWS.
2. **Netflix**: Pioneered cloud-native microservices on AWS, inventing Eureka (discovery), Hystrix (circuit breaking), and Zuul (gateway) to survive frequent instance termination.
3. **Segment**: Migrated back from 140 microservices to a single monolithic repo/service for their event processing pipeline, cutting operational load and AWS costs significantly.

---

## 6. Key Takeaways

- Microservices solve team scalability and organizational bottlenecks, not code complexity.
- Always enforce Database-per-Service; never share databases across microservice boundaries.
- Build resilient communication with circuit breakers, timeouts, retries with jitter, and asynchronous events.
""",

    "03-event-driven-architecture.md": """# Event-Driven Architecture (EDA)

Event-Driven Architecture (EDA) is a design paradigm in which software components communicate by producing, detecting, and consuming asynchronous state changes known as **events**.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Web Client
    participant OrderSvc as Order Service
    participant Broker as Kafka / Event Broker
    participant InvSvc as Inventory Service
    participant PaySvc as Payment Service
    participant Analytics as Analytics Engine

    Client->>OrderSvc: POST /orders { user: "u1", items: [...] }
    Note over OrderSvc: Writes order (status: PENDING) to DB
    OrderSvc->>Broker: Publish: OrderCreatedEvent { id: "o1", total: 99.00 }
    OrderSvc-->>Client: 202 Accepted { orderId: "o1" }
    
    par Parallel Event Consumption
        Broker->>InvSvc: Deliver OrderCreatedEvent
        InvSvc->>InvSvc: Reserve Inventory Stock
    and
        Broker->>PaySvc: Deliver OrderCreatedEvent
        PaySvc->>PaySvc: Authorize Credit Card
    and
        Broker->>Analytics: Deliver OrderCreatedEvent
        Analytics->>Analytics: Update Real-time Revenue Dashboard
    end
```

---

## 1. Core Primitives: Events, Commands, and Queries

Understanding the semantic difference between events and commands is vital:

| Concept | Intent | Ownership | Naming Convention |
| :--- | :--- | :--- | :--- |
| **Command** | Directive: Requests an action to occur | Directed to a single specific receiver | Imperative (`CreateOrder`, `ChargeCard`) |
| **Event** | Notification: Announces a past factual occurrence | Published to broker; zero or multiple consumers | Past Tense (`OrderCreated`, `CardCharged`) |
| **Query** | Request: Asks for current state without side effects | Directed to a specific data provider | Read-only (`GetOrderById`) |

---

## 2. Event Notification vs Event-Carried State Transfer

```mermaid
graph TD
    subgraph "1. Event Notification (Thin Event)"
        P1[Publisher] -->|OrderCreated: {id: 101}| B1[Broker]
        B1 --> C1[Consumer]
        C1 -->|GET /orders/101 (HTTP callback)| P1
    end

    subgraph "2. Event-Carried State Transfer (Fat Event)"
        P2[Publisher] -->|OrderCreated: {id: 101, user: 'u1', items: [...], total: 99}| B2[Broker]
        B2 --> C2[Consumer]
        Note over C2: Processes event immediately without any upstream HTTP callback!
    end
```

- **Event Notification**: Lightweight notification containing only IDs. Minimizes payload size and data exposure, but forces consumers to query the publisher, creating downstream traffic spikes.
- **Event-Carried State Transfer (ECST)**: Full snapshot of state included in the payload. Eliminates downstream callback queries, decouples systems entirely, and enables consumers to maintain local materialized views.

---

## 3. Choreography vs Orchestration

When coordinating complex workflows across multiple services, teams must choose between decentralized choreography and centralized orchestration:

```mermaid
graph TD
    subgraph "Choreography (Decentralized Pub/Sub)"
        O1[Order Svc] -->|OrderCreated| P1[Payment Svc]
        P1 -->|PaymentProcessed| I1[Inventory Svc]
        I1 -->|InventoryReserved| S1[Shipping Svc]
    end

    subgraph "Orchestration (Central Coordinator / Workflow Engine)"
        Coord[Temporal / Step Functions Coordinator]
        Coord -->|Execute Payment| P2[Payment Svc]
        Coord -->|Reserve Stock| I2[Inventory Svc]
        Coord -->|Ship Goods| S2[Shipping Svc]
    end
```

| Dimension | Choreography | Orchestration |
| :--- | :--- | :--- |
| **Coupling** | Loosely coupled; services only know about events | Tightly coupled to central workflow definition |
| **Visibility** | Difficult to visualize full workflow state | Centralized state machine dashboard |
| **Failure Handling** | Complex distributed compensations | Built-in retry and compensating transaction engine |
| **Best For** | Simple 2-3 step notification pipelines | Complex, multi-step business transactions (Sagas) |

---

## 4. Real-World Case Studies

1. **LinkedIn**: Processes trillions of events daily through Apache Kafka, which was originally built at LinkedIn for activity tracking and metric pipelines.
2. **DoorDash**: Uses event-driven dispatch to match delivery drivers, merchants, and customers in real-time.
3. **Uber**: Churns billions of location update events per second through distributed messaging brokers to calculate surge pricing and dynamic ETAs.

---

## 5. Key Takeaways

- Prefer Event-Carried State Transfer to prevent thundering herd callbacks to the publisher.
- Use past-tense naming for events to preserve the semantic guarantee that facts cannot be cancelled or altered.
- Choose orchestration (Temporal, Camunda, AWS Step Functions) when coordinating critical multi-step business transactions.
""",

    "04-serverless-and-faas.md": """# Serverless and Function-as-a-Service (FaaS)

Serverless computing is an execution model where cloud providers dynamically manage the allocation, provisioning, and scaling of compute resources. Function-as-a-Service (FaaS) allows developers to deploy individual functions triggered by events.

```mermaid
graph LR
    subgraph Event Sources
        API[API Gateway HTTP]
        S3[S3 / Object Upload]
        Stream[Kafka / Kinesis Event]
        Cron[Scheduled Cron]
    end

    subgraph Serverless Execution Environment
        API --> Lambda[FaaS Container: AWS Lambda / Cloudflare Worker]
        S3 --> Lambda
        Stream --> Lambda
        Cron --> Lambda
        Lambda --> Scale[Auto-Scales from 0 to 10,000 instances]
    end

    subgraph Backends
        Lambda --> DB[(DynamoDB / Aurora Serverless)]
    end
```

---

## 1. What It Is: Ephemeral Compute with Scale-to-Zero

In traditional infrastructure (VMs, EC2, Kubernetes), you pay for provisioned capacity 24/7 regardless of incoming traffic.

Serverless introduces three core tenets:
1. **Scale-to-Zero**: When zero traffic arrives, zero compute runs and cost is zero.
2. **Event-Driven Invocation**: Functions execute strictly in response to events (HTTP request, queue message, file upload).
3. **Zero Server Management**: OS patching, security updates, and capacity provisioning are handled entirely by the cloud provider.

---

## 2. The Cold Start Problem and Container Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant Event as HTTP Event
    participant Manager as FaaS Control Plane
    participant Worker as Worker MicroVM (Firecracker)
    participant Func as User Function Code

    Event->>Manager: Invoke Function (No Warm Instance)
    Note over Manager, Worker: COLD START (50ms - 2000ms)
    Manager->>Worker: Provision MicroVM / Container
    Worker->>Func: Download & Load Runtime (Node.js/Python/Go)
    Worker->>Func: Execute Global / Static Init Code
    Func->>Func: Execute Request Handler
    Func-->>Event: Return HTTP 200 Response
    
    Note over Worker: WARM EXECUTION (2ms - 50ms)
    Event->>Worker: Subsequent Request arrives within 15 mins
    Worker->>Func: Reuses warm container & DB connection!
```

### Techniques to Minimize Cold Starts:
- **Language Selection**: Go, Rust, and Node.js have startup times of 10-50ms; JVM (Java) and .NET can take 1,000-3,000ms unless pre-compiled with GraalVM Native Image.
- **Provisioned Concurrency**: Keeps a pre-warmed pool of instances running (eliminates cold starts at a fixed baseline cost).
- **V8 Isolates (Edge Workers)**: Cloudflare Workers and Fastly Compute execute functions inside V8 isolates rather than separate containers, reducing cold starts to < 5ms.

---

## 3. Database Connection Exhaustion Problem

Traditional relational databases (PostgreSQL, MySQL) assign a thread or process per TCP connection. If 5,000 Lambda functions spin up concurrently during a traffic spike, they will open 5,000 simultaneous connections, immediately crashing the database connection pool.

```mermaid
graph LR
    subgraph Problem: Direct DB Connection
        L1[Lambda 1] --> DB[(Postgres: Max 200 Conns - CRASH!)]
        L2[Lambda 2] --> DB
        LN[... Lambda 5000] --> DB
    end

    subgraph Solution: Managed Connection Proxy
        L3[Lambda 1] --> Proxy[AWS RDS Proxy / PgBouncer]
        L4[Lambda 2] --> Proxy
        LM[... Lambda 5000] --> Proxy
        Proxy -->|Pools 50 Persistent Connections| DB2[(Postgres Database)]
    end
```

---

## 4. Trade-offs: Serverless vs Containers (Kubernetes)

| Dimension | Serverless (FaaS) | Containers / Kubernetes |
| :--- | :--- | :--- |
| **Scaling Speed** | Seconds (0 to 1,000+ instances instantly) | Minutes (HPA + Node Autoscaler spin-up) |
| **Idle Cost** | $0.00 (Scale-to-zero) | Continuous cost for reserved nodes |
| **Execution Limit** | Max 15 minutes (AWS Lambda) | Unlimited long-running processes |
| **Statefulness** | Strictly stateless | Stateful workloads supported (PVC, StatefulSets) |
| **Local Debugging** | Difficult (cloud mocking required) | Standard Docker container parity |
| **High Sustained Load Cost** | Extremely expensive at continuous high throughput | Significantly cheaper per compute unit |

---

## 5. Real-World Case Studies

1. **Coca-Cola**: Migrated vending machine telemetry and payment backend to AWS Lambda and API Gateway, reducing operational cost from $13,000/month to under $750/month.
2. **Netflix**: Uses AWS Lambda for automated video encoding pipelines, triggering functions on S3 chunk uploads to encode thousands of video segments in parallel.
3. **Cloudflare**: Powers edge computing with Cloudflare Workers using V8 Isolates across 300+ global data centers.

---

## 6. Key Takeaways

- Serverless is ideal for spiky, intermittent, event-driven, or asynchronous workloads.
- Avoid serverless for predictable, high-throughput, continuous 24/7 compute loads where reserved VM/container instances are vastly more cost-effective.
- Always place a connection pooler (RDS Proxy, PgBouncer) between FaaS functions and relational databases.
""",

    "05-domain-driven-design-foundations.md": """# Domain-Driven Design (DDD) Foundations

Domain-Driven Design (DDD) is a software design approach introduced by Eric Evans that centers development around a rich, evolving model of the business domain.

```mermaid
graph TD
    subgraph "Strategic DDD (Architecture & Boundaries)"
        Domain[Core Domain: E-Commerce] --> Sub1[Core Domain: Order & Pricing Engine]
        Domain --> Sub2[Supporting Domain: Inventory Management]
        Domain --> Sub3[Generic Domain: Billing & Notification]
        Sub1 --> BC1[Bounded Context: Order Context]
        Sub2 --> BC2[Bounded Context: Inventory Context]
    end

    subgraph "Tactical DDD (Inside a Bounded Context)"
        BC1 --> Agg[Aggregate Root: Order]
        Agg --> Entity[Entity: OrderItem]
        Agg --> VO[Value Object: Money, Address]
        Agg --> DomainEvent[Domain Event: OrderPlaced]
        Agg --> Repo[Repository: OrderRepository]
    end
```

---

## 1. Strategic Design: Bounded Contexts and Ubiquitous Language

### 1. Ubiquitous Language
A single, unambiguous language shared between software engineers and business domain experts. 
- *Bad*: Developers say `OrderRow` and `TransactionItem`, while business teams say `LineItem`.
- *DDD Rule*: Pick one term (`LineItem`) and use it everywhere: in conversation, requirements, class names, database tables, and API fields.

### 2. Bounded Context
A linguistic boundary within which a domain model applies consistently. The same real-world object can have different models in different contexts:

```mermaid
graph LR
    subgraph "Sales Bounded Context"
        P1[Product: Price, Description, Images, Discounts]
    end

    subgraph "Warehouse Bounded Context"
        P2[Product: Weight, Dimensions, Barcode, ShelfLocation]
    end

    subgraph "Customer Support Context"
        P3[Product: Warranty, ReturnPolicy, SerialNumber]
    end
```

---

## 2. Context Mapping Patterns

How bounded contexts integrate and share models:

```mermaid
graph LR
    subgraph Context Relationships
        U[Upstream: Core Billing] -->|Shared Kernel / Customer-Supplier| D1[Downstream: Invoice Service]
        D1 -->|Anti-Corruption Layer (ACL)| Legacy[Downstream: Legacy ERP]
    end
```

- **Shared Kernel**: Two contexts share a subset of code and database tables. High coupling; requires synchronized deployments.
- **Customer-Supplier**: Upstream provider delivers data needed by downstream consumer.
- **Anti-Corruption Layer (ACL)**: A translation layer that converts upstream foreign models into the downstream context's native domain model, protecting clean services from messy legacy schemas.

---

## 3. Tactical Design Building Blocks

| Building Block | Definition | Mutability | Equality By | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Entity** | Object with a unique, persistent thread of identity | Mutable | Unique Identifier (`ID`) | `User(id=42)`, `Order(id=99)` |
| **Value Object** | Immutable object defined solely by its attributes | Immutable | Attribute equality | `Money(amount=10, currency="USD")` |
| **Aggregate Root** | Cluster of entities and value objects treated as a single transactional unit | Mutable via Root | Root Entity ID | `Order` (root) containing `OrderItems` |
| **Domain Event** | Record of a business event that has occurred in the past | Immutable | Event ID + Timestamp | `OrderCancelledEvent` |
| **Repository** | Interface abstracting persistence and retrieval of aggregate roots | N/A | N/A | `OrderRepository.save(order)` |

---

## 4. The Aggregate Rule

External objects are **only allowed to hold references to the Aggregate Root**. Direct mutation of inner entities is strictly forbidden:

```java
// VIOLATION of Aggregate Invariant
order.getItems().get(0).setPrice(0.00); // Bypasses discount rules!

// CORRECT DDD Practice
order.applyDiscountCode("BLACKFRIDAY2026"); // Enforces validation inside the Aggregate Root
```

---

## 5. Key Takeaways

- Strategic DDD (Bounded Contexts) is the premier tool for establishing clean microservice boundaries.
- Define a strict Ubiquitous Language with business domain experts to eliminate translation errors.
- Protect clean domain models from legacy APIs using an Anti-Corruption Layer (ACL).
- Enforce transactional consistency boundaries around Aggregate Roots, keeping aggregates small.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 10 Part 1 complete.")
