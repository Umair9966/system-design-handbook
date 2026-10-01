import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\19-case-studies"

studies = {
    "15-ticket-and-hotel-booking.md": """# Design a Ticket and Hotel Booking System (Ticketmaster / Airbnb)

A high-concurrency reservation platform capable of handling extreme flash-sale traffic spikes (Taylor Swift concert sales) without double-booking, ensuring fair allocation and transactional seat locks.

```mermaid
graph TD
    Client[User Browser] --> QueueRoom[Virtual Waiting Room / Cloudflare Waiting Room]
    QueueRoom --> LB[Load Balancer]
    LB --> BookingAPI[Booking Service]
    
    BookingAPI --> LockStore[(Redis: Distributed Seat Leases / Redlock)]
    BookingAPI --> BookingDB[(Relational DB: PostgreSQL ACID)]
    BookingAPI --> PayGateway[Payment Gateway]
```

---

## 1. Requirements

### Functional Requirements:
1. Search events / hotels by location, date, and category.
2. View seat map / room availability in real time.
3. Temporary hold / reservation lock: Hold seat for 10 minutes while user enters payment details.
4. Process payment and issue digital ticket.
5. Auto-release seats if 10-minute payment countdown expires.

### Non-Functional Requirements:
- **Strict Consistency**: **ZERO DOUBLE BOOKING**. Two users must never be sold the same seat.
- **Extreme Burst Scalability**: Handle 100,000+ users clicking "Reserve" at the exact same second.
- **Fairness**: Virtual waiting room queuing to prevent bot scalpers.

---

## 2. Preventing Double-Booking: The Distributed Seat Lease Pattern

```mermaid
sequenceDiagram
    autonumber
    participant User as Customer
    participant API as Booking Service
    participant Redis as Redis Lock Store
    participant DB as Postgres DB

    User->>API: POST /seats/A-12/hold (UserId: 42)
    Note over API: Atomic Redis SET with NX and EX:
    API->>Redis: SET seat:concert_99:A12 "user_42" NX EX 600
    alt Lock Acquired (Returns OK)
        Redis-->>API: 1 (Success)
        API->>DB: INSERT INTO seat_holds (seat_id, user_id, expires_at)
        API-->>User: 200 OK: Seat held for 10 minutes!
    else Seat Already Held (Returns nil)
        Redis-->>API: 0 (Key already exists)
        API-->>User: 409 Conflict: Seat currently held by another user
    end
```

---

## 3. Database Schema (PostgreSQL with Row Locks)

```sql
CREATE TABLE seats (
    seat_id VARCHAR(32) PRIMARY KEY,
    event_id UUID NOT NULL,
    section VARCHAR(16),
    row_num VARCHAR(8),
    seat_num VARCHAR(8),
    status VARCHAR(16) NOT NULL DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'HELD', 'BOOKED'
    version INT NOT NULL DEFAULT 0 -- Optimistic Concurrency Control
);

-- Finalizing booking with Optimistic Locking:
UPDATE seats 
SET status = 'BOOKED', version = version + 1 
WHERE seat_id = 'A-12' 
  AND status = 'HELD' 
  AND version = :expected_version;
```

---

## 4. Key Takeaways

- Use a Virtual Waiting Room at the edge (Cloudflare) to smooth million-user flash bursts.
- Implement distributed seat leases in Redis using atomic `SET ... NX EX 600` (10-minute hold).
- Enforce strict ACID consistency at the database layer with Optimistic Concurrency Control (`version` column).
""",

    "16-ecommerce-platform.md": """# Design an E-Commerce Platform (Amazon / Shopify)

A distributed commerce platform handling product catalog browsing, search, shopping cart management, inventory reservation, and high-throughput checkout workflows.

```mermaid
graph TD
    Client[Shopper] --> CDN[Edge CDN / Fastly]
    CDN --> GW[API Gateway]

    GW --> CatalogSvc[Product Catalog Service] --> CatalogDB[(Elasticsearch + Postgres)]
    GW --> CartSvc[Shopping Cart Service] --> CartCache[(Redis / DynamoDB)]
    GW --> CheckoutSvc[Checkout Orchestrator (Saga)]
    
    CheckoutSvc --> InvSvc[Inventory Service] --> InvDB[(Inventory DB: Strict ACID)]
    CheckoutSvc --> OrderSvc[Order Service] --> OrderDB[(Order DB)]
    CheckoutSvc --> PaySvc[Payment Service]
```

---

## 1. Requirements

### Functional Requirements:
1. Product catalog browsing and search with filters (brand, price, ratings).
2. Shopping cart persistence across devices.
3. Inventory deduction with atomic check-and-decrement.
4. Order placement, payment processing, and confirmation email.

### Non-Functional Requirements:
- **High Availability**: Catalog browsing must never fail (99.999% uptime).
- **Strong Consistency for Inventory**: Never sell more items than exist in physical stock.
- **Low Latency**: Product page $< 50\text{ms}$; checkout $< 1\text{ second}$.

---

## 2. Inventory Reservation: Preventing Overselling

Relational databases guarantee ACID atomicity during checkout:

```sql
-- Atomic check and decrement in a single SQL statement:
UPDATE inventory
SET available_quantity = available_quantity - :purchased_quantity,
    version = version + 1
WHERE product_id = :product_id 
  AND available_quantity >= :purchased_quantity;
```
If the rows affected is `1`, the inventory was successfully reserved without table-level locking. If rows affected is `0`, stock was exhausted.

---

## 3. The Checkout Saga Pattern

```mermaid
graph LR
    Start[Checkout Initiated] --> S1[1. Reserve Inventory]
    S1 --> S2[2. Authorize Payment]
    S2 --> S3[3. Create Order]
    S3 --> S4[4. Emit OrderPlaced Event]

    S2 -.->|Payment Declined!| Comp1[Compensate: Release Reserved Inventory]
```

---

## 4. Key Takeaways

- Decouple read-heavy catalog browsing (Elasticsearch + CDN) from write-critical inventory deduction.
- Use atomic SQL `UPDATE ... WHERE available_quantity >= :qty` to eliminate overselling race conditions.
- Coordinate multi-service checkout workflows using Sagas with automated compensating transactions.
""",

    "17-payment-system.md": """# Design a Global Payment Processing System (Stripe / PayPal)

A mission-critical financial ledger and payment processing gateway requiring zero data loss, exact idempotency, ledger double-entry bookkeeping, and bank reconciliation.

```mermaid
graph TD
    Merchant[Merchant Client] --> GW[Payment API Gateway]
    GW --> Idemp[(Idempotency Store: Redis + Postgres)]
    GW --> PayEngine[Payment Processing Engine]
    
    PayEngine --> Ledger[(Immutable Double-Entry Ledger DB)]
    PayEngine --> BankProxy[Third-Party Bank / Card Network PSP Proxy]
    BankProxy --> VisaMastercard[Visa / Mastercard / Banks]
    
    PayEngine --> ReconcileWorker[Nightly Bank Reconciliation Engine]
```

---

## 1. Requirements

### Functional Requirements:
1. Charge credit cards and bank accounts.
2. Provide absolute idempotency: duplicate requests must never result in duplicate charges.
3. Maintain an immutable double-entry accounting ledger.
4. Nightly reconciliation against bank settlement settlement files.

### Non-Functional Requirements:
- **Zero Data Loss**: Highest durability and auditability standards (PCI-DSS Level 1 compliant).
- **Strict Idempotency**: Safe automatic client retries.
- **High Availability**: 99.999% uptime.

---

## 2. Double-Entry Bookkeeping Principles

In financial accounting, money never magically appears or vanishes; it moves between accounts. Every transaction must have **at least two entries** where:
$$\sum \text{Debits} = \sum \text{Credits}$$

```mermaid
graph LR
    subgraph "Customer Buys $100 Product (Double-Entry Ledger)"
        D1[Debit: Customer Cash Account +$100]
        C1[Credit: Merchant Payable Account +$97]
        C2[Credit: Stripe Fee Revenue Account +$3]
    end
    Note over D1,C2: Total Debits ($100) == Total Credits ($97 + $3 = $100)! Balanced!
```

---

## 3. Strict Idempotency Implementation

```mermaid
sequenceDiagram
    autonumber
    participant Client as Merchant App
    participant PaySvc as Payment Gateway
    participant DB as Postgres Idempotency Table
    participant Bank as Card Network

    Client->>PaySvc: POST /v1/charges (Header: Idempotency-Key: abc-123)
    Note over PaySvc: Checks DB: INSERT INTO idempotency_keys (key, status) VALUES ('abc-123', 'STARTED')
    alt Key already exists with COMPLETED status
        PaySvc-->>Client: Returns cached HTTP 200 response immediately (Zero bank charge!)
    else First time seen
        PaySvc->>Bank: Charge Card $100
        Bank-->>PaySvc: Charge Succeeded
        PaySvc->>DB: UPDATE idempotency_keys SET status='COMPLETED', response_body='...'
        PaySvc-->>Client: 200 OK (Charged)
    end
```

---

## 4. Key Takeaways

- Financial systems must enforce Double-Entry Bookkeeping where debits equal credits.
- All payment APIs must enforce unique client-supplied `Idempotency-Key` headers.
- Implement automated nightly reconciliation to detect discrepancies between internal ledgers and bank clearing files.
""",

    "18-search-autocomplete-typeahead.md": """# Design a Real-Time Search Autocomplete / Typeahead (Google Search)

A low-latency search typeahead system capable of returning top 5 query suggestions within 30ms as a user types each keystroke into a search bar.

```mermaid
graph TD
    User[User Types: 'sys...'] --> Edge[Edge CDN / Proxy]
    Edge --> TypeaheadSvc[Typeahead Query Service]
    TypeaheadSvc --> TrieCache[(In-Memory Distributed Trie Cluster)]
    
    LogStream[Search Logs: 1 Billion Queries/Day] --> Kafka[Kafka Query Log Stream]
    Kafka --> Flink[Apache Flink / Spark Aggregator]
    Flink --> TopKDB[(Aggregated Top-K Prefix Store)]
    TopKDB --> TrieBuilder[Trie Builder Worker]
    TrieBuilder --> TrieCache
```

---

## 1. Requirements

### Functional Requirements:
1. As the user types, suggest the top 5 most popular completions matching the prefix.
2. Update prefix rankings based on recent real-world query frequency.
3. Spell check and typo tolerance for minor spelling mistakes.

### Non-Functional Requirements:
- **Ultra-Low Latency**: Suggestions returned within $< 30\text{ms}$ per keystroke.
- **High Throughput**: 100,000+ keystroke queries per second.
- **High Availability**: 99.99%.

---

## 2. Data Structure: Trie with Precomputed Top-K Nodes

A standard Trie requires traversing all child branches to find top completions, resulting in slow $O(M)$ searches during query time.

### The Precomputed Trie Optimization:
Store the precomputed top 5 search terms directly inside **every parent Trie node**:

```mermaid
graph TD
    Root["Root: ['system', 'sports', 'star', 'stripe']"]
    Root --> S["Node 's': ['system', 'sports', 'star']"]
    S --> SY["Node 'sy': ['system design', 'python system', 'synonym']"]
    SY --> SYS["Node 'sys': ['system design (40M)', 'systematic (10M)', 'system 32 (5M)']"]
```
Now, querying the prefix `"sys"` takes **$O(L)$ time** where $L$ is the length of the prefix (3 operations), immediately returning the top 5 array in **0.01ms**!

---

## 3. Trie Partitioning across Shards

A complete global Trie of 100 Million prefixes consumes $\approx 50\text{GB}$ of memory.
- **Partitioning Strategy**: Consistent hashing on the **first 2 letters** of the prefix (`"aa" - "az"`, `"ba" - "bz"`).
- Hot prefixes (e.g., `"g"`, `"s"`) are replicated across multiple read-only server clusters.

---

## 4. Key Takeaways

- Store precomputed Top-K suggestions directly inside each Trie node for $O(L)$ prefix lookup.
- Aggregate search frequency asynchronously using stream processing (Kafka + Flink).
- Cache popular prefix responses at edge CDNs and in browser localStorage.
""",

    "19-web-search-engine.md": """# Design a Large-Scale Web Search Engine (Google Search)

A petabyte-scale search engine architecture handling the full lifecycle of internet search: distributed crawling, index building, inverted indexing, and multi-stage ranking (PageRank + BM25 + Deep Learning).

```mermaid
graph TD
    Query[User Query: 'distributed systems'] --> GW[Search API Gateway]
    GW --> Spell[Spellcheck & Query Rewriter]
    Spell --> Dispatcher[Search Index Dispatcher]

    Dispatcher --> Shard1[Index Shard 1]
    Dispatcher --> Shard2[Index Shard 2]
    Dispatcher --> ShardN[Index Shard N]

    Shard1 --> Merge[Priority Queue Result Merger]
    Shard2 --> Merge
    ShardN --> Merge

    Merge --> Ranker[ML Ranking Model: PageRank + BM25]
    Ranker --> SnippetSvc[Document Summary & Snippet Generator]
    SnippetSvc --> Query
```

---

## 1. Requirements

### Functional Requirements:
1. Search billions of web pages by keyword queries.
2. Return ranked list of 10 most relevant documents with titles, URLs, and snippet summaries.
3. Query suggestions and spelling correction.

### Non-Functional Requirements:
- **Ultra-Fast Latency**: p99 search query latency $< 200\text{ms}$.
- **Massive Scale**: Index tens of billions of web pages.
- **Relevance**: High precision and recall.

---

## 2. Inverted Index Partitioning: Term Partitioning vs Document Partitioning

```mermaid
graph TD
    subgraph "1. Term Partitioning (By Word)"
        NodeA["Node A holds all docs for words: 'apple' -> 'cat'"]
        NodeB["Node B holds all docs for words: 'dog' -> 'zebra'"]
        Note over NodeA: Single multi-word query must scatter-gather across nodes!
    end

    subgraph "2. Document Partitioning (By Doc ID - Standard Practice)"
        Node1["Node 1 holds words for Doc 1 to 10,000,000"]
        Node2["Node 2 holds words for Doc 10,000,001 to 20,000,000"]
        Note over Node1,Node2: Every node evaluates full query independently over local subset!
    end
```

Modern search engines use **Document Partitioning**: every shard evaluates the full multi-word query against its local subset of documents, minimizing cross-node network dependencies.

---

## 3. The PageRank Algorithm

Web pages are ranked not just by keyword density, but by authority measured by incoming links:
$$PR(u) = \frac{1-d}{N} + d \sum_{v \in B_u} \frac{PR(v)}{L(v)}$$
- $B_u$: Set of pages linking to page $u$.
- $L(v)$: Number of outbound links on page $v$.
- $d$: Damping factor (typically 0.85).

---

## 4. Key Takeaways

- Use Document Partitioning to build horizontally scalable inverted index clusters.
- Precompute PageRank and static quality scores offline.
- Execute two-stage ranking: fast inverted index candidate retrieval followed by deep neural ranking models.
""",

    "20-distributed-job-scheduler.md": """# Design a Distributed Job Scheduler (Cron / Celery / Airflow)

A resilient, horizontally scalable distributed task scheduling platform capable of executing millions of scheduled (cron) and ad-hoc background jobs with exact timing guarantees and fault tolerance.

```mermaid
graph TD
    Client[Client App] --> API[Job Submission API]
    API --> MetaDB[(Job Metadata Store: PostgreSQL)]
    
    Scheduler[Distributed Scheduler Master / Raft] --> MetaDB
    Scheduler --> DelayQueue[(Sorted Delay Queue: Redis / Kafka)]
    
    DelayQueue --> WorkerPool[Worker Node Cluster]
    WorkerPool --> Heartbeat[(Heartbeat & Lease Tracker)]
    WorkerPool --> ResultStore[(Job Result Store)]
```

---

## 1. Requirements

### Functional Requirements:
1. Schedule one-off delayed tasks (e.g., "Send email in 30 minutes").
2. Schedule recurring cron jobs (`0 0 * * *` = daily midnight).
3. Task dependency Directed Acyclic Graphs (DAGs) (Job B runs only after Job A succeeds).
4. Automatic retries with exponential backoff on worker crash.

### Non-Functional Requirements:
- **Fault Tolerance**: If a worker node crashes mid-execution, reassign the job to another worker.
- **At-Least-Once Execution**: No scheduled job is permanently dropped.
- **Scale**: Execute 10+ Million jobs per day.

---

## 2. Scheduling Delay Queue: Redis Sorted Sets vs Hierarchical Timing Wheels

To schedule jobs with future execution timestamps:

```mermaid
graph LR
    Job[Job: Execute at timestamp 1767225600] --> ZSet[Redis ZSET: key='scheduled_jobs', score=timestamp]
    Poller[Scheduler Poller] -->|ZRANGEBYSCORE scheduled_jobs 0 CurrentTime| Pop[Pops ready jobs]
    Pop --> Worker[Dispatches to Worker Pool]
```

### Hierarchical Timing Wheels:
For ultra-high-throughput sub-second scheduling, **Hierarchical Timing Wheels** (used by Kafka and Netty) execute timer registrations in $O(1)$ time without sorted list insertion overhead ($O(\log N)$).

---

## 3. Worker Heartbeating and Failure Recovery

Workers hold a lease on running jobs:
1. Worker acquires task: `UPDATE jobs SET status='RUNNING', heartbeat=NOW() WHERE id=:id`.
2. Worker sends a heartbeat ping every 10 seconds.
3. If heartbeat is missing for 60 seconds, Scheduler marks the job `FAILED` and re-queues it for another worker.

---

## 4. Key Takeaways

- Use Redis Sorted Sets or Timing Wheels for high-performance delayed job queues.
- Prevent duplicate execution using database row-level locking or distributed fencing tokens.
- Implement worker heartbeats with timeout leases to recover from worker hardware crashes.
""",

    "21-metrics-and-monitoring-system.md": """# Design a Distributed Metrics and Monitoring System (Datadog / Prometheus)

A massive-scale time-series metric collection, aggregation, and alerting pipeline capable of ingesting billions of metric data points per day and answering analytical aggregation queries in seconds.

```mermaid
graph TD
    App[Applications & Servers] --> Agent[Local Metric Agent / StatsD]
    Agent --> IngestGW[Metric Ingestion Gateway]
    IngestGW --> Kafka[Kafka Metric Stream]
    
    Kafka --> TSDB_Engine[Time-Series Storage Engine: VictoriaMetrics / M3DB]
    Kafka --> StreamAgg[Real-Time Aggregator: 10s Rollup Windows]
    
    StreamAgg --> AlertEngine[Alert Evaluation Engine]
    AlertEngine --> PagerDuty[PagerDuty / Slack Alerts]

    TSDB_Engine --> Grafana[Grafana Dashboard Queries]
```

---

## 1. Requirements

### Functional Requirements:
1. Ingest metric data points: `(metric_name, tags, timestamp, value)`.
2. Support high-cardinality tagging (`service=order`, `region=us-east`, `host=i-1234`).
3. Query aggregations: `sum(rate(http_requests[5m])) by (service)`.
4. Configurable threshold alerting rules.

### Non-Functional Requirements:
- **High Ingestion Throughput**: Ingest 10 Million metric points per second.
- **Query Performance**: Sub-second queries for dashboard graphs.
- **Storage Efficiency**: Aggressive compression (Gorilla compression: $< 2$ bytes per sample).

---

## 2. Gorilla Time-Series Compression Algorithm (Facebook)

Standard metric points require 16 bytes (8B timestamp + 8B float value). Facebook's **Gorilla** algorithm compresses this to an average of **1.37 bytes per data point**:

```mermaid
graph TD
    subgraph "Gorilla Compression Pipeline"
        T[Timestamps: Delta-of-Delta Variable Length Encoding]
        V[Float Values: XOR against Previous Float Value]
    end
    T --> Comp[Compressed Bitstream: 1.37 bytes per point!]
    V --> Comp
```

### 1. Timestamp Delta-of-Delta:
If metrics report every 60 seconds, the delta is 60. The delta-of-delta is $60 - 60 = 0$. A delta-of-delta of `0` is encoded as a **single bit `0`**!

### 2. Float XOR:
Successive float values share significant leading and trailing zeros. Storing only the XOR delta eliminates redundant bits.

---

## 3. Rollup and Downsampling Pipelines

Raw 1-second metrics are aggressively downsampled:
- **Raw (1s resolution)**: Retained for 7 days.
- **Rollup (1m resolution)**: Retained for 30 days.
- **Rollup (1h resolution)**: Retained for 1 year.

---

## 4. Key Takeaways

- Use Gorilla time-series compression (Delta-of-Delta + XOR) to reduce metric storage by 10x.
- Decouple metric ingestion via Kafka to absorb sudden traffic bursts.
- Downsample metrics into 1-minute and 1-hour rollup tiers to provide fast year-long queries.
"""
}

for fname, content in studies.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Case Studies Batch 3 complete.")
