import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\19-case-studies"

studies = {
    "29-feature-flag-service.md": """# Design a Distributed Feature Flag Service (LaunchDarkly)

A low-latency, mission-critical feature flagging and configuration streaming platform capable of evaluating flags locally in-memory ($< 0.01\text{ms}$) across thousands of microservices with real-time updates pushed within seconds.

```mermaid
graph TD
    Admin[Engineering / Product Admin] --> Dashboard[Feature Flag Console]
    Dashboard --> FlagDB[(Flag Rules DB: PostgreSQL)]
    FlagDB --> StreamMgr[Streaming Control Plane]
    
    StreamMgr -->|SSE / WebSockets Server-Sent Events| EdgeApp1[App Pod 1: Local In-Memory Cache]
    StreamMgr -->|SSE / WebSockets Server-Sent Events| EdgeApp2[App Pod 2: Local In-Memory Cache]
    StreamMgr -->|SSE / WebSockets Server-Sent Events| EdgeAppN[App Pod N: Local In-Memory Cache]

    IncomingReq[User HTTP Request] --> EdgeApp1
    EdgeApp1 -->|0.005ms Pure In-Memory Hash Evaluation| Response[Serve Feature A or B]
```

---

## 1. Requirements

### Functional Requirements:
1. Boolean toggles and multivariate feature flags.
2. Percentage-based gradual rollouts (e.g., enable for 10% of users).
3. Contextual targeting rules (e.g., `country == 'CA' AND app_version >= '2.4.0'`).
4. Real-time updates delivered to all microservices within 2 seconds.

### Non-Functional Requirements:
- **Ultra-Low Evaluation Latency**: In-memory evaluation $< 0.01\text{ms}$ (must never make network calls during request paths).
- **High Resilience**: If control plane goes down, application pods keep using cached rules safely.

---

## 2. Deterministic Bucketing Algorithm (Consistent Hashing)

To ensure User 42 consistently stays in the 10% rollout bucket:
$$\text{Bucket} = \text{MurmurHash3}(\text{user\_id} + "\text{flag\_key}") \pmod{100}$$
If the rollout threshold is 25%, any user whose bucket value is $< 25$ receives the new feature. As the rollout increases to 50%, all previously enabled users remain enabled without storing state in a database!

---

## 3. Real-Time Streaming via Server-Sent Events (SSE)

Application SDKs maintain a persistent HTTP Server-Sent Events (SSE) connection to the control plane.
- When an operator flips a flag in the dashboard, the control plane broadcasts a small JSON delta payload over the SSE stream.
- The SDK updates its internal in-memory hash map instantly with zero container restarts.

---

## 4. Key Takeaways

- Never evaluate feature flags via remote HTTP calls; always evaluate locally in RAM using SDK-managed caches.
- Use MurmurHash3 for deterministic, stateless percentage rollouts.
- Push configuration updates using Server-Sent Events (SSE).
""",

    "30-api-gateway.md": """# Design a High-Performance API Gateway (Kong / Envoy)

A high-throughput L7 API Gateway sitting at the perimeter of a microservices architecture, providing SSL termination, authentication, rate limiting, request transformation, and dynamic routing.

```mermaid
graph TD
    Client[Mobile / Web Clients] --> Edge[Edge Anycast]
    Edge --> GW[Envoy / Kong API Gateway Cluster]
    
    subgraph Gateway Filter Pipeline
        GW --> F1[1. TLS 1.3 Termination & WAF]
        F1 --> F2[2. JWT Authentication & Claims Extraction]
        F2 --> F3[3. Rate Limiter (Redis Token Bucket)]
        F3 --> F4[4. Path Rewriting & Header Injection]
    end

    F4 --> SvcA[Order Microservice]
    F4 --> SvcB[User Microservice]
    F4 --> SvcC[Payment Microservice]
```

---

## 1. Requirements

### Functional Requirements:
1. Dynamic routing based on URI path, headers, and HTTP methods.
2. Centralized Authentication (validate JWTs, verify signatures).
3. Distributed Rate Limiting and quota management.
4. Observability: Generate unified access logs, Prometheus metrics, and distributed trace headers (`traceparent`).

### Non-Functional Requirements:
- **Ultra-High Throughput**: 100,000+ requests per second per node.
- **Minimal Latency Overhead**: Gateway processing overhead $< 2\text{ms}$.
- **Zero-Downtime Dynamic Configuration**: Reload routes via xDS API without restarting worker processes.

---

## 2. The Envoy Proxy xDS Control Plane

Modern API Gateways (Envoy) decouple the data plane from the control plane using the **xDS protocol**:
- **LDS (Listener Discovery Service)**: Dynamic port and TLS configuration.
- **RDS (Route Discovery Service)**: Dynamic URI routing rules.
- **CDS (Cluster Discovery Service)**: Backend service endpoints and health states.
- **EDS (Endpoint Discovery Service)**: Real-time Kubernetes pod IP updates.

---

## 3. Key Takeaways

- Terminate TLS and authenticate JWTs at the gateway to offload CPU from downstream microservices.
- Inject trusted identity headers (`X-User-Id`, `X-User-Roles`) into internal service requests.
- Use Envoy xDS APIs to dynamically update routes without dropping active TCP connections.
""",

    "31-distributed-email-service.md": """# Design a Distributed Email Delivery Service (SendGrid / AWS SES)

A petabyte-scale transactional and marketing email delivery infrastructure capable of delivering 1 Billion emails per day while maintaining high IP reputation, honoring bounce/spam feedback loops, and avoiding ISP blacklists.

```mermaid
graph TD
    Client[Application Client] --> API[Email API Gateway]
    API --> Queue[Kafka Ingestion Topic]
    
    Queue --> SchedPool[Delivery Scheduler & IP Pool Allocator]
    SchedPool --> MTA_Pool[Distributed Mail Transfer Agent - MTA Workers]
    
    MTA_Pool --> ISP[Target Email Servers: Gmail, Yahoo, Outlook]
    ISP -->|Feedback Loop / Bounces| BounceHandler[Bounce & Unsubscribe Worker]
    BounceHandler --> RepStore[(Suppression List: DynamoDB)]
```

---

## 1. Requirements

### Functional Requirements:
1. Send transactional emails (receipts, password resets) with sub-minute delivery.
2. Send bulk marketing campaigns (millions of recipients).
3. Handle bounces (hard vs soft), spam complaints, and unsubscribe links.
4. Domain verification via DNS records: SPF, DKIM, DMARC.

### Non-Functional Requirements:
- **High Ingestion Throughput**: Ingest 50,000 emails per second.
- **High Deliverability**: Strict IP reputation warming to prevent Gmail/Yahoo spam filtering.
- **At-Least-Once Delivery**: No transactional emails dropped.

---

## 2. Deliverability Fundamentals: SPF, DKIM, and DMARC

To prevent email spoofing and ensure delivery to user inboxes:
1. **SPF (Sender Policy Framework)**: DNS TXT record listing all IP addresses authorized to send emails on behalf of the domain.
2. **DKIM (DomainKeys Identified Mail)**: The outgoing email header is cryptographically signed with the sender's private key; the receiving ISP validates it using the public key published in DNS.
3. **DMARC**: Specifies policy (`reject`, `quarantine`) if SPF or DKIM validation fails.

---

## 3. Dedicated IP Warming and Suppression Lists

- **IP Warming**: New MTA IP addresses cannot blast 10 Million emails on day one (Gmail will instantly blackhole the IP). Traffic must ramp up gradually: Day 1: 50 emails $\to$ Day 5: 5,000 $\to$ Day 15: 500,000 $\to$ Day 30: 10 Million.
- **Suppression List**: If an email bounces as a **Hard Bounce** (invalid address) or user clicks "Spam", the address is added to an immutable suppression list. Future attempts to email this address are blocked immediately to protect domain reputation.

---

## 4. Key Takeaways

- Isolate transactional email IP pools from marketing email IP pools to protect critical 2FA delivery rates.
- Enforce cryptographic DKIM signatures and strict DMARC policies.
- Automatically drop requests to suppressed or hard-bounced email addresses.
""",

    "32-stock-exchange-matching-engine.md": """# Design an Ultra-Low-Latency Stock Exchange Matching Engine (LMAX / NASDAQ)

An ultra-low-latency financial order matching engine capable of executing limit orders, market orders, and cancellations with sub-microsecond determinism, zero garbage collection pauses, and strict FIFO price-time priority.

```mermaid
graph TD
    Trader[High-Frequency Trading Firms] -->|FIX Protocol / TCP Direct| Gateway[FIX Gateway (Kernel Bypass / Solarflare EF_VI)]
    Gateway --> Sequencer[Deterministic Sequencer (Raft / Hardware FPGA)]
    Sequencer --> Disruptor[LMAX Disruptor In-Memory Ring Buffer]
    Disruptor --> Engine[Order Book Matching Engine (Single Thread Core)]
    Engine --> MarketData[Market Data Multicast Feed: UDP ITCH]
    Engine --> Clearing[Clearing & Settlement Ledger]
```

---

## 1. Requirements

### Functional Requirements:
1. Submit, cancel, and modify Limit and Market orders.
2. Maintain Order Book with Price-Time Priority (FIFO at same price level).
3. Execute trades when bid price $\ge$ ask price.
4. Broadcast market data updates (level 2 order book) in real time.

### Non-Functional Requirements:
- **Ultra-Low Latency**: Sub-microsecond matching ($< 5\mu\text{s}$).
- **Determinism**: 100% reproducible execution sequence.
- **Zero Garbage Collection Pauses**: Mechanical sympathy and off-heap memory.

---

## 2. Architectural Secret: The Single-Threaded Core Pattern (LMAX Disruptor)

Traditional multi-threaded concurrent programming relies on mutex locks and context switching, introducing jitter and 10-50 microsecond delays.

### The LMAX Disruptor Architecture:
```mermaid
graph LR
    subgraph "Single-Threaded Pinned CPU Core"
        Ring[Disruptor Lock-Free Circular Ring Buffer] --> Matcher[Single-Threaded Matching Engine]
        Matcher --> Book[(In-Memory Doubly Linked Order Book)]
    end
    Note over Matcher: Pinned to exclusive CPU core with CPU cacheline padding.<br/>ZERO thread contention! ZERO lock overhead! 6 Million ops/sec!
```

- **Order Book Data Structure**:
  - **Limit Prices**: B+Tree or Red-Black Tree mapping Price $\to$ FIFO Queue.
  - **Order Queue**: Doubly linked list of orders at each price level.
  - Inserting an order: $O(1)$ at price tail; executing trade: $O(1)$ at opposite head.

---

## 3. Deterministic Sequencing and Journaling

Before entering the matching engine, every order passes through a **Deterministic Sequencer** that assigns an incrementing monotonic sequence number (`seq_id`). The input stream is written sequentially to NVMe storage. In the event of a catastrophic server reboot, replaying the sequence stream from disk produces the exact identical order book state.

---

## 4. Key Takeaways

- Use a single-threaded matching core pinned to a dedicated CPU core to eliminate lock contention.
- Implement the LMAX Disruptor circular lock-free ring buffer for inter-thread communication.
- Enforce strict Price-Time Priority (FIFO) using tree-indexed doubly linked lists.
""",

    "33-ad-click-aggregation.md": """# Design a Real-Time Ad Click Aggregation System (Google Ads / Facebook Ads)

A high-throughput distributed stream aggregation pipeline capable of processing billions of ad impression and click events per day, detecting fraudulent bot clicks, and aggregating real-time advertiser billing metrics.

```mermaid
graph TD
    AdClick[User Clicks Ad] --> Edge[Click Tracking Ingress Endpoint]
    Edge --> Kafka[Kafka Raw Click Stream (Partitioned by ad_id)]
    
    Kafka --> Flink[Apache Flink Stream Processor]
    
    subgraph Stream Processing Pipeline
        Flink --> FraudEngine[Fraud Detection: Bot IP & Velocity Filtering]
        FraudEngine --> WindowAgg[Sliding Window Aggregator: 1-min & 1-hr rollups]
    end

    WindowAgg --> OLAP[(Analytical Store: ClickHouse / StarRocks)]
    WindowAgg --> BillingDB[(Advertiser Billing Ledger: PostgreSQL)]
    OLAP --> AdvertiserDashboard[Advertiser Real-Time Analytics Dashboard]
```

---

## 1. Requirements

### Functional Requirements:
1. Track ad clicks and link them to corresponding impressions.
2. Aggregate click metrics by `ad_id`, `campaign_id`, and geographic region across 1-minute and 1-hour tumbling windows.
3. Detect fraudulent clicks (e.g., bot farms, duplicate clicks within 500ms).
4. Update advertiser campaign balances in real time.

### Non-Functional Requirements:
- **Exactly-Once Processing**: Advertisers must never be double-billed for duplicate events.
- **Massive Ingestion Scale**: 100,000+ clicks/sec ($10\text{ Billion clicks/day}$).
- **Low End-to-End Latency**: Metrics reflected in advertiser dashboard within 5 seconds.

---

## 2. Stream Processing with Apache Flink (Tumbling & Sliding Windows)

```mermaid
graph LR
    subgraph "Tumbling Window: 1 Minute"
        W1[Window: 12:00 - 12:01] --> Agg1[Sum Clicks = 4,210]
        W2[Window: 12:01 - 12:02] --> Agg2[Sum Clicks = 5,120]
    end
```

### Handling Late-Arriving Events with Watermarks:
Mobile network latency can delay click events by several minutes.
- **Watermarking**: Flink tracks event-time progress. A watermark of $T - 10\text{s}$ tells the engine: *"Assume all events with timestamp $< T - 10\text{s}$ have arrived; finalize the window."*
- Late events beyond the watermark trigger side-output streams to reconcile billing retroactively.

---

## 3. Fraud Detection Heuristics

1. **Duplicate Click Suppression**: Discard multiple clicks on the same ad from the same IP/Device within 1 second.
2. **Velocity Thresholds**: An IP address generating $> 50$ clicks per minute is tagged as a click farm and excluded from billing.
3. **User Agent & IP Reputation**: Cross-reference against datacenter proxy lists and headless browser signatures (Puppeteer/Selenium).

---

## 4. Key Takeaways

- Use Apache Flink for scalable event-time window aggregation with checkpointing for exactly-once guarantees.
- Ingest high-volume click streams through Kafka partitioned by `ad_id` to preserve per-ad ordering.
- Filter fraudulent and duplicate clicks prior to billing aggregations.
""",

    "34-recommendation-engine.md": """# Design a Real-Time Recommendation Engine (TikTok / Netflix)

A large-scale machine learning recommendation architecture capable of surfacing personalized video and product recommendations from a catalog of hundreds of millions of items with sub-50ms inference latency.

```mermaid
graph TD
    UserApp[User Opens Feed] --> RecGW[Recommendation API Gateway]
    RecGW --> FeatureFetch[Real-Time Feature Service: Redis Online Store]
    
    RecGW --> CandidateRetriever[Stage 1: Candidate Generation / Retrieval<br/>Reduces 100M -> 2,000 Candidates<br/>Two-Tower Embeddings + Milvus Vector Search]
    
    CandidateRetriever --> HeavyRanker[Stage 2: Heavy Neural Ranking<br/>Reduces 2,000 -> 50 Items<br/>Deep Learning DLRM on GPU Cluster]
    
    HeavyRanker --> ReRanker[Stage 3: Business Logic & Diversity Filter<br/>Reduces 50 -> 10 Items<br/>Deduplication, freshness, sponsored inject]
    
    ReRanker --> UserApp
```

---

## 1. Requirements

### Functional Requirements:
1. Deliver personalized home feeds tailored to user interests and historical interactions.
2. Incorporate real-time feedback (e.g., if user skips 3 dance videos in a row, update recommendations immediately).
3. Promote diversity (do not show 10 consecutive videos from the same creator or genre).

### Non-Functional Requirements:
- **Low Latency**: End-to-end feed recommendation returned in $< 50\text{ms}$.
- **Scale**: 500 Million DAU.
- **Freshness**: Incorporate new trending content within 15 minutes of upload.

---

## 2. The Two-Tower Neural Network Model

```mermaid
graph TD
    subgraph "User Tower"
        UserFeatures[User ID, Age, Country, Watch History] --> DenseUser[Dense Neural Layers]
        DenseUser --> UserVector[128-dim User Embedding Vector: U]
    end

    subgraph "Item Tower (Precomputed Offline)"
        ItemFeatures[Video ID, Creator, Tags, Audio Track] --> DenseItem[Dense Neural Layers]
        DenseItem --> ItemVector[128-dim Item Embedding Vector: V]
    end

    UserVector <-->|Dot Product / Cosine Similarity: U · V| ItemVector
```

- **Offline Indexing**: Precompute 128-dimensional embedding vectors for all 100 Million videos and index them inside **Milvus / Qdrant** using an HNSW graph.
- **Online Query**: Compute user vector in 2ms $\to$ Execute Approximate Nearest Neighbor (ANN) search over Milvus $\implies$ Return top 2,000 candidates in **8ms**!

---

## 3. Real-Time Feature Ingestion (TikTok Secret)

Why does TikTok adapt to user preferences so rapidly?
- As user watches a video, viewing percentage (e.g., watched 100% or skipped after 2s) is streamed via WebSockets to **Apache Flink**.
- Flink updates the user's real-time interest profile inside **Redis** within 500ms.
- Next feed swipe already reflects the updated interest vector!

---

## 4. Key Takeaways

- Divide recommendation into Candidate Retrieval (Two-Tower ANN search) and Heavy Ranking (Deep Learning).
- Precompute item embeddings offline and store in vector databases (Milvus).
- Stream live interaction signals to Redis to adapt recommendations within seconds.
""",

    "35-travel-search-aggregator.md": """# Design a Travel Search Aggregator (Kayak / Skyscanner)

A distributed travel search engine that aggregates real-time flight, hotel, and car rental prices from hundreds of third-party airline APIs and Global Distribution Systems (GDS: Amadeus, Sabre), handling high supplier latency and volatile pricing.

```mermaid
graph TD
    User[Traveler: NYC to LON on Oct 10] --> API[Search Aggregator Gateway]
    API --> Cache[(Aggregated Flight Price Cache: Redis)]
    
    API --> FanoutWorker[Supplier Fanout Dispatcher]
    
    par Parallel Supplier Queries (with 2-second deadline!)
        FanoutWorker --> Delta[Delta Airlines API]
        FanoutWorker --> United[United Airlines API]
        FanoutWorker --> BA[British Airways API]
        FanoutWorker --> GDS[Sabre / Amadeus GDS]
    end

    Delta --> StreamAgg[Streaming Aggregator / WebSockets]
    United --> StreamAgg
    BA --> StreamAgg
    GDS --> StreamAgg

    StreamAgg --> User
```

---

## 1. Requirements

### Functional Requirements:
1. Search round-trip and one-way flights across hundreds of airlines.
2. Filter and sort by price, duration, stops, and airline.
3. Stream results progressively to user browser as airlines respond.
4. Booking handoff: Redirect user to airline booking portal with verified pricing.

### Non-Functional Requirements:
- **Resilience to Slow Downstreams**: Airline partner APIs take 2-8 seconds to respond. Aggregator must never hang waiting for slow partners.
- **Massive Fanout**: A single user query spawns 50+ external HTTP requests.
- **Price Accuracy**: Prevent showing obsolete cached prices when flights sell out.

---

## 2. Progressive Streaming Search (WebSockets / SSE)

Waiting 8 seconds for all 50 airlines to respond before rendering the page results in high user bounce rates.

### The Progressive Streaming Pattern:
1. Client initiates search: `POST /api/v1/flight-searches`.
2. Gateway immediately opens a **Server-Sent Events (SSE)** or **WebSocket** connection.
3. Instant Response: Deliver cached flight estimates from Redis within **50ms**.
4. As individual airlines respond (at 500ms, 1.2s, 2.5s), stream newly discovered flight fares directly to the browser.
5. Strict Deadline: Cut off slow airline queries at $T = 3.0\text{ seconds}$ and finalize the search.

---

## 3. Caching Strategy for Volatile Airline Pricing

- Flight prices and seat availability change dynamically based on airline revenue management algorithms.
- **TTL Strategy**:
  - Hot routes (e.g., NYC to LON next week): 5-minute cache TTL.
  - Distant routes (e.g., flight 9 months away): 6-hour cache TTL.
- **Price Verification Step**: Before final redirect to booking, execute a synchronous real-time price check to confirm the fare is still available.

---

## 4. Key Takeaways

- Stream search results progressively using Server-Sent Events (SSE) or WebSockets to display instant results.
- Implement strict client deadlines (timeouts) on external supplier fanout calls.
- Apply dynamic cache TTLs based on departure date proximity and route popularity.
"""
}

for fname, content in studies.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Case Studies Batch 5 complete.")
