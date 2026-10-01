import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\19-case-studies"

studies = {
    "01-url-shortener.md": """# Design a Production-Grade URL Shortener (Bitly)

A high-scale, globally distributed URL shortening service capable of transforming arbitrary long URLs into compact 7-character aliases, providing sub-10ms HTTP 301/302 redirections and real-time click analytics.

```mermaid
graph TD
    Client[Client Browser / App] --> CDN[Cloudflare Edge CDN]
    CDN -->|Cache Miss| LB[AWS ALB / L7 Load Balancer]
    LB --> GW[API Gateway]
    GW --> ShortenSvc[Shortener Service Pods]
    GW --> RedirectSvc[Redirection Service Pods]

    ShortenSvc --> KGS[(Key Generation Service / Zookeeper)]
    ShortenSvc --> PrimaryDB[(PostgreSQL / CockroachDB Sharded)]
    
    RedirectSvc --> Cache[(Redis Cluster: Hot 20% URLs)]
    RedirectSvc -.->|Cache Miss| ReadReplica[(DB Read Replicas)]
    RedirectSvc --> Kafka[Kafka: Click Event Stream]
    Kafka --> Analytics[Clickhouse Analytics Engine]
```

---

## 1. Requirements

### Functional Requirements:
1. Given a long URL, generate a unique, short 7-character alias (e.g., `https://bit.ly/3x8Ab9C`).
2. Redirection: When accessing a short link, redirect user to the original long URL with sub-10ms latency.
3. Custom Aliases: Users can optionally specify a custom alias (e.g., `https://bit.ly/system-design-guide`).
4. Expiration: URLs expire after a user-configured TTL (default 2 years).
5. Analytics: Track click metrics (click count, country, referrer, device, timestamp).

### Non-Functional Requirements:
- **High Availability**: 99.99% uptime. Link redirection must never fail.
- **Ultra-Low Latency**: Redirection p99 $< 15\text{ms}$.
- **Massive Read-to-Write Ratio**: 100:1 read heavy.
- **Predictable Collision Avoidance**: Zero hash collisions.

---

## 2. Capacity Estimation & Back-of-the-Envelope Math

- **New URLs Created**: 100 Million new URLs per month.
- **Write QPS**: $\frac{100,000,000}{30 \times 86,400} \approx \mathbf{40\text{ writes/sec}}$ (Peak: $100\text{ writes/sec}$).
- **Read-to-Write Ratio**: 100:1.
- **Read QPS (Redirections)**: $40 \times 100 = \mathbf{4,000\text{ reads/sec}}$ (Peak: $10,000\text{ reads/sec}$).
- **Storage Sizing (5 Years)**:
  - 100M URLs/month $\times 12$ months $\times 5$ years = **6 Billion URLs**.
  - Average record size: 500 bytes (ID: 8B, short_url: 7B, long_url: 400B, user_id: 16B, created_at: 8B).
  - Total Storage = $6\text{ Billion} \times 500\text{B} \approx \mathbf{3\text{ Terabytes}}$. (Easily fits on a single NVMe RAID, but sharded for high read IOPS).
- **Cache Sizing (RAM)**:
  - Daily Read Requests = $4,000 \times 86,400 \approx 350\text{ Million requests/day}$.
  - Daily Data Volume = $350\text{M} \times 500\text{B} = 175\text{ GB/day}$.
  - Pareto Principle (80/20 Rule): Cache 20% of hot URLs = $175\text{ GB} \times 0.20 = \mathbf{35\text{ GB RAM}}$ (Easily fits on a single 64GB Redis instance).

---

## 3. URL Encoding: Base62 vs MD5 Hashing

To create a 7-character string using characters `[0-9, a-z, A-Z]` ($10 + 26 + 26 = 62\text{ characters}$):
$$\text{Total Combinations} = 62^7 \approx \mathbf{3.52\text{ Trillion unique URLs}}$$
3.52 Trillion URLs is more than 500x our 5-year requirement (6 Billion).

```mermaid
graph LR
    subgraph "Approach 1: MD5 / SHA-256 Hash (Requires Collision Handling)"
        L1[Long URL] --> MD5[MD5 Hash: 128-bit]
        MD5 --> Take7[Take first 7 chars]
        Take7 --> Collide{Collision in DB?}
        Collide -->|Yes: Append Salt & Retry| MD5
        Collide -->|No| Save1[Save Short URL]
    end

    subgraph "Approach 2: Key Generation Service (KGS - Zero Collision)"
        Range[Zookeeper assigns Range 1,000,000 - 2,000,000] --> Node1[KGS Server 1]
        Node1 --> Base62[Convert Auto-Inc ID to Base62: 1000000 -> '4c92']
        Base62 --> Save2[Direct Insert (Guaranteed Unique!)]
    end
```

### The Key Generation Service (KGS) Pattern:
A standalone service pre-generates unique 64-bit sequence numbers. Distributed nodes coordinate via Apache ZooKeeper or etcd. Each KGS worker receives a token range (e.g., Worker 1 gets `1` to `1,000,000`; Worker 2 gets `1,000,001` to `2,000,000`). It converts the counter directly to Base62 without collisions or database round-trips.

---

## 4. API Design

### 1. Create Short URL
```http
POST /api/v1/urls
Content-Type: application/json
Idempotency-Key: 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d

{
  "long_url": "https://en.wikipedia.org/wiki/Distributed_computing",
  "custom_alias": "wiki-dist-sys",  // Optional
  "ttl_days": 730
}

HTTP/1.1 201 Created
{
  "short_url": "https://bit.ly/wiki-dist-sys",
  "long_url": "https://en.wikipedia.org/wiki/Distributed_computing",
  "expires_at": "2028-10-01T00:00:00Z"
}
```

### 2. Redirect Short URL
```http
GET /3x8Ab9C HTTP/1.1
Host: bit.ly

HTTP/1.1 301 Moved Permanently
Location: https://en.wikipedia.org/wiki/Distributed_computing
Cache-Control: public, max-age=86400
```
*(Use HTTP 301 for browser caching and lower backend load; use HTTP 302 if strict per-click analytics tracking is required).*

---

## 5. Database Schema (PostgreSQL / CockroachDB)

```sql
CREATE TABLE urls (
    short_code VARCHAR(16) PRIMARY KEY,
    long_url TEXT NOT NULL,
    user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_urls_expires_at ON urls (expires_at);

-- Clickstream Analytics (Loaded into ClickHouse / Kafka)
CREATE TABLE url_clicks (
    click_id BIGSERIAL PRIMARY KEY,
    short_code VARCHAR(16) NOT NULL,
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    country_code VARCHAR(2),
    referrer TEXT,
    user_agent TEXT
);
```

---

## 6. Deep Dive: Handling Hot URL Cache Stampedes

When a viral celebrity tweets a short URL, 100,000 users request the link in a single second. If the cache expires, all 100,000 requests hit the primary database simultaneously (**Cache Stampede**).

```mermaid
sequenceDiagram
    participant C1 as Client 1 (Fast)
    participant C2 as Client 2..10000
    participant Cache as Redis Cache
    participant DB as Postgres DB

    C1->>Cache: GET /3x8Ab9C (Expired!)
    C2->>Cache: GET /3x8Ab9C (Expired!)
    Note over C1: Acquires Redis Distributed Mutex (SETNX lock:3x8Ab9C 1 EX 5)
    C1->>DB: Single query: SELECT long_url FROM urls WHERE short_code='3x8Ab9C'
    Note over C2: Lock acquisition fails; sleeps 50ms & retries cache
    C1->>Cache: SETEX /3x8Ab9C 86400 <long_url>
    C1-->>Cache: Releases Mutex
    C2->>Cache: GET /3x8Ab9C (Cache Hit!)
```

---

## 7. Key Takeaways

- Base62 encoding combined with a distributed Key Generation Service (KGS) completely eliminates hash collision retries.
- 301 redirects maximize edge caching but bypass analytics; 302 redirects allow server-side click tracking.
- Protect against cache stampedes using distributed mutex locks (`SETNX`) or early probabilistic cache warming (XFetch).
""",

    "02-pastebin.md": """# Design a Scalable Pastebin Service

A text-sharing service (similar to Pastebin or GitHub Gist) that allows users to upload plain text snippets, code, or logs, generating a unique URL for sharing, with optional password protection, syntax highlighting, and automatic TTL expiration.

```mermaid
graph TD
    Client[Web / CLI Client] --> Edge[Cloudflare CDN]
    Edge --> LB[Load Balancer]
    LB --> API[Pastebin API Gateway]
    API --> PasteSvc[Paste Service Pods]

    PasteSvc --> S3[(Object Storage: S3 / MinIO - Raw Paste Text)]
    PasteSvc --> DB[(Metadata DB: PostgreSQL / MongoDB)]
    PasteSvc --> Cache[(Redis Cache: Hot Metadata & Pastes)]
```

---

## 1. Requirements

### Functional Requirements:
1. Users can upload a block of text (max 10MB) and receive a unique short URL.
2. Users can view uploaded text via the short URL.
3. Users can set expiration TTL (1 hour, 1 day, 1 week, never).
4. Optional custom slug and password protection.
5. Support raw text output (`/raw/:id`).

### Non-Functional Requirements:
- **Availability**: 99.99%.
- **Read-to-Write Ratio**: 20:1 read-heavy.
- **Latency**: P99 text read latency $< 30\text{ms}$.
- **Durability**: Pastes with no expiration must never be lost (99.999999999% object storage durability).

---

## 2. Capacity Estimation & Storage Separation

- **Daily New Pastes**: 1 Million pastes/day.
- **Average Paste Size**: 20 KB.
- **Daily Ingress Storage**: $1\text{M} \times 20\text{ KB} = \mathbf{20\text{ GB/day}}$.
- **5-Year Storage**: $20\text{ GB} \times 365 \times 5 \approx \mathbf{36.5\text{ Terabytes}}$.
- **Write QPS**: $\frac{1,000,000}{86,400} \approx \mathbf{12\text{ pastes/sec}}$.
- **Read QPS (20:1)**: $12 \times 20 = \mathbf{240\text{ reads/sec}}$ (Peak: $1,000\text{ reads/sec}$).

### Architectural Storage Separation:
Storing 20KB text blobs inside relational database rows quickly fragments database pages and bloats B+Tree indexes.
- **Metadata** (ID, author, expiration, hash, size) $\to$ **PostgreSQL / DynamoDB**.
- **Raw Text Payload** $\to$ **AWS S3 Object Storage** (keyed by `paste_id`).

---

## 3. API & Data Model

```http
POST /api/v1/pastes
Content-Type: application/json

{
  "content": "SELECT * FROM users WHERE active = true;",
  "language": "sql",
  "expires_in_seconds": 86400,
  "is_private": false
}

HTTP/1.1 201 Created
{
  "paste_id": "7f8b9a1c",
  "url": "https://paste.example.com/7f8b9a1c",
  "expires_at": "2026-10-02T20:00:00Z"
}
```

```sql
CREATE TABLE paste_metadata (
    paste_id VARCHAR(16) PRIMARY KEY,
    user_id UUID,
    s3_key VARCHAR(255) NOT NULL,
    content_size_bytes INT NOT NULL,
    language VARCHAR(32) DEFAULT 'text',
    password_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);
```

---

## 4. Deep Dive: Automated Expiration & Garbage Collection

Pastes with expired TTLs should not remain in storage forever.

```mermaid
graph TD
    Cron[Scheduled Kubernetes CronJob: Every Hour] --> Query[Query: SELECT paste_id, s3_key FROM paste_metadata WHERE expires_at < NOW() LIMIT 5000]
    Query --> S3Batch[Batch Delete from S3 Bucket]
    S3Batch --> DBDelete[DELETE FROM paste_metadata WHERE paste_id IN (...)]
    
    subgraph Alternative: S3 Native Lifecycle
        S3Object[S3 Object with Tag: 'TTL=7d'] --> S3Engine[S3 Lifecycle Engine Auto-Purges at 0 Cost!]
    end
```

---

## 5. Key Takeaways

- Decouple metadata (relational DB) from bulk text payload (S3 object storage).
- Use Base62 sequence generation for unique, URL-safe 8-character paste identifiers.
- Rely on S3 Lifecycle Policies for zero-compute automated expiration.
""",

    "03-rate-limiter.md": """# Design a Distributed Rate Limiting System

A mission-critical distributed rate limiter service that protects public and internal APIs from denial-of-service (DDoS) attacks, brute-force credential stuffing, and resource exhaustion.

```mermaid
graph TD
    Client[Incoming Client API Request] --> Edge[Envoy Proxy / API Gateway]
    Edge --> Filter[Rate Limiter HTTP Filter]
    Filter --> RL_Svc[Distributed Rate Limiter Service]
    RL_Svc --> Redis[(Redis Cluster: Lua Script Execution)]
    
    Filter -->|Allowed: Within Limit| Backend[Upstream Microservice]
    Filter -->|Exceeded Limit| 429[HTTP 429 Too Many Requests]
```

---

## 1. Requirements

### Functional Requirements:
1. Limit requests based on client IP, authenticated User ID, or API Key.
2. Support configurable tiered limits (e.g., 100 req/min for free users; 5,000 req/min for enterprise).
3. Return informative HTTP standard headers:
   - `X-RateLimit-Limit: 100`
   - `X-RateLimit-Remaining: 42`
   - `X-RateLimit-Reset: 1696156860`
   - `Retry-After: 30` (on HTTP 429).

### Non-Functional Requirements:
- **Ultra-Low Latency**: Adding rate limiting must not add $> 2\text{ms}$ overhead to API requests.
- **Distributed Accuracy**: Correct count enforcement across hundreds of distributed gateway pods.
- **Fail-Open Policy**: If the rate limiter crashes, requests must be allowed through (graceful degradation) rather than blocking all legitimate traffic.

---

## 2. Algorithm Comparison: Sliding Window Counter

| Algorithm | Accuracy | Memory Footprint | Burst Handling | Production Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Token Bucket** | High | Low ($O(1)$ memory) | Allows configured bursts | Excellent for API Gateways |
| **Leaky Bucket** | High | Moderate (Queue depth) | Smooths traffic to constant rate | Great for egress webhooks |
| **Fixed Window** | Low (Boundary spike allows 2x) | Ultra-Low ($O(1)$) | Vulnerable at window boundary | Not recommended |
| **Sliding Window Log**| 100% Exact | Extremely High ($O(N)$ memory) | Precise | Too expensive for high QPS |
| **Sliding Window Counter**| 99% Accurate Approximation | Ultra-Low ($O(1)$) | Smooth and accurate | **Best for high-scale distributed systems** |

---

## 3. Distributed Redis Lua Script (Atomic Execution)

In distributed architectures, running multiple Redis commands (`GET`, increment, `EXPIRE`) from application servers introduces race conditions. We execute the Sliding Window Counter atomically using a single Redis Lua script:

```lua
-- KEYS[1]: Rate limit key (e.g., "ratelimit:user_123:minute")
-- ARGV[1]: Current timestamp (seconds)
-- ARGV[2]: Window size in seconds (e.g., 60)
-- ARGV[3]: Max allowed requests

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local clearBefore = now - window
redis.call('ZREMRANGEBYSCORE', key, 0, clearBefore)

local currentRequests = redis.call('ZCARD', key)
if currentRequests < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window)
    return 1 -- Allowed
else
    return 0 -- Denied (Rate limited)
end
```

---

## 4. Key Takeaways

- Execute rate-limiting logic inside Redis via atomic Lua scripts to eliminate distributed race conditions.
- Standardize on `HTTP 429 Too Many Requests` with `Retry-After` headers.
- Always configure a Fail-Open architecture so rate-limiter outages do not bring down the entire company.
""",

    "04-unique-id-generator.md": """# Design a Distributed Unique ID Generator (Twitter Snowflake)

A high-performance distributed ID generation system capable of creating 64-bit, globally unique, roughly time-sorted integers at a rate of 100,000+ IDs per second with zero central database locks.

```mermaid
graph TD
    Client[Microservice / Client] --> Worker1[Snowflake ID Generator Node 1]
    Client --> Worker2[Snowflake ID Generator Node 2]
    Client --> Worker3[Snowflake ID Generator Node 3]

    ZK[(ZooKeeper / Consul: Node ID Assignment)]
    ZK -.->|Assigns Worker ID: 1| Worker1
    ZK -.->|Assigns Worker ID: 2| Worker2
    ZK -.->|Assigns Worker ID: 3| Worker3
```

---

## 1. Comparing Distributed ID Approaches

| Approach | Length | Sortable? | DB Central Bottleneck? | Production Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **UUIDv4** | 128-bit (String) | No (Completely random) | No | Poor DB indexing performance (B+Tree fragmentation) |
| **MySQL Auto-Increment (Ticket Server)**| 64-bit | Yes | **Yes (Single SPOF / High latency)** | Hard to scale globally |
| **UUIDv7** | 128-bit | Yes (Unix timestamp prefix) | No | Excellent for application-level generation |
| **Twitter Snowflake** | **64-bit (Integer)** | **Yes (Time-ordered)** | **No (In-memory generation)** | **Industry Gold Standard** |

---

## 2. Twitter Snowflake 64-Bit Bit-Allocation Structure

```
+--------------------------------------------------------------------------+
| 1 Bit |    41 Bits Timestamp    | 5 Bits Datacenter | 5 Bits Worker | 12 Bits Sequence |
| Sign  | (Milliseconds since epoch) |        ID         |      ID       |   (Per ms count)   |
+--------------------------------------------------------------------------+
```

### Breakdown of the 64 Bits:
1. **1 Bit (Sign)**: Always `0` to ensure the generated integer is positive.
2. **41 Bits (Timestamp)**: Milliseconds elapsed since a custom epoch (e.g., `2026-01-01T00:00:00Z`).
   - Range: $2^{41} - 1 \approx 2,199,023,255,551\text{ ms} \approx \mathbf{69.7\text{ years}}$ of operational lifetime.
3. **5 Bits (Datacenter ID)**: Supports up to $2^5 = 32$ distinct data centers.
4. **5 Bits (Worker Machine ID)**: Supports up to $2^5 = 32$ machines per data center (total 1,024 generator nodes).
5. **12 Bits (Sequence Number)**: Incremented for every ID generated within the exact same millisecond on the same node.
   - Range: $2^{12} = \mathbf{4,096\text{ unique IDs per millisecond per node}}$ ($\approx 4.096\text{ Million IDs/sec}$ per node).

---

## 3. Production Code Implementation (Python)

```python
import time
import threading

class SnowflakeIDGenerator:
    def __init__(self, datacenter_id: int, worker_id: int, epoch: int = 1767225600000):
        # 1767225600000 = 2026-01-01 00:00:00 UTC
        self.epoch = epoch
        self.datacenter_id = datacenter_id
        self.worker_id = worker_id
        
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()

        # Bit allocations
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.sequence_bits = 12

        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.sequence_mask = -1 ^ (-1 << self.sequence_bits)

        self.worker_shift = self.sequence_bits
        self.datacenter_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits

    def _current_timestamp_ms(self) -> int:
        return int(time.time() * 1000)

    def next_id(self) -> int:
        with self._lock:
            timestamp = self._current_timestamp_ms()

            if timestamp < self.last_timestamp:
                # Clock moved backward (NTP sync anomaly!)
                offset = self.last_timestamp - timestamp
                if offset <= 5: # Small skew: wait it out
                    time.sleep(offset / 1000.0)
                    timestamp = self._current_timestamp_ms()
                else:
                    raise RuntimeError(f"Clock moved backwards by {offset}ms. Refusing to generate ID.")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.sequence_mask
                if self.sequence == 0:
                    # Sequence exhausted for this millisecond: spin-wait until next millisecond
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_timestamp_ms()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return ((timestamp - self.epoch) << self.timestamp_shift) | \\
                   (self.datacenter_id << self.datacenter_shift) | \\
                   (self.worker_id << self.worker_shift) | \\
                   self.sequence
```

---

## 4. Key Takeaways

- Snowflake generates 64-bit integer IDs that fit natively inside standard database BIGINT columns.
- Natural time-ordering preserves B+Tree database index clustering and eliminates random I/O fragmentation.
- Handle NTP clock backwards drift gracefully by either spin-waiting small deltas or failing fast.
""",

    "05-distributed-key-value-store.md": """# Design a Distributed Key-Value Store (DynamoDB / Cassandra)

A highly available, horizontally scalable distributed key-value store modeled after Amazon Dynamo and Apache Cassandra, featuring consistent hashing, tunable consistency, and masterless replication.

```mermaid
graph TD
    Client[Client Application] --> NodeA[Coordinator Node A]
    
    subgraph "Masterless Consistent Hash Ring (Dynamo Topology)"
        NodeA <-->|Gossip Protocol: Heartbeats & Node State| NodeB[Node B]
        NodeB <--> NodeC[Node C]
        NodeC <--> NodeD[Node D]
        NodeD <--> NodeA
    end

    NodeA -->|Write: Quorum W=2| NodeB
    NodeA -->|Write: Quorum W=2| NodeC
```

---

## 1. Requirements

### Functional Requirements:
1. `put(key, value)`: Stores an arbitrary byte payload associated with a key.
2. `get(key)`: Retrieves the value associated with the key.

### Non-Functional Requirements:
- **Massive Scalability**: Scale to millions of writes and reads per second across hundreds of nodes.
- **Tunable Consistency**: Allow callers to select consistency level per request (Strong vs Eventual).
- **High Availability**: No Single Point of Failure (SPOF); survives node crashes and network partitions.

---

## 2. Core Architectural Pillars

```mermaid
graph LR
    P1[1. Consistent Hashing with Virtual Nodes] --> P2[2. Masterless Quorum (N, R, W)]
    P2 --> P3[3. LSM-Tree Storage Engine (SSTable + MemTable)]
    P3 --> P4[4. Gossip Protocol (Failure Detection)]
    P4 --> P5[5. Anti-Entropy with Merkle Trees]
```

### 1. Consistent Hashing with Virtual Nodes
Distributes keys evenly across physical storage nodes. Virtual nodes (e.g., 256 virtual tokens per physical server) eliminate hot spot imbalance and ensure smooth rebalancing when adding/removing nodes.

### 2. Tunable Quorum Consistency ($R + W > N$)
- $N$: Number of replicas storing each key.
- $W$: Number of replicas that must acknowledge a write before returning success.
- $R$: Number of replicas that must respond to a read before returning data.
- **Strong Consistency Formula**:
  $$R + W > N$$
  *(Guarantees that the read set and write set overlap on at least one replica node).*

---

## 3. Storage Engine: LSM-Tree Internals

Each node writes incoming data using an **LSM-Tree** (Log-Structured Merge-Tree) to achieve maximum write throughput:
1. Append to sequential **Write-Ahead Log (WAL)** on disk (crash recovery).
2. Insert into in-memory sorted **MemTable** (Red-Black or SkipList).
3. When MemTable reaches 64MB, flush sequentially to disk as an immutable **SSTable** (Sorted String Table).
4. Accelerate point read misses using an in-memory **Bloom Filter**.

---

## 4. Key Takeaways

- Masterless architectures (Dynamo) eliminate leader election downtime.
- Tune $R$ and $W$ per query to balance latency against strong consistency.
- Use LSM-Trees for ultra-high write throughput, backed by Bloom Filters to optimize read misses.
""",

    "06-web-crawler.md": """# Design a Distributed Web Crawler (Googlebot)

A petabyte-scale distributed web crawler capable of traversing billions of web pages, extracting links, deduplicating content, and feeding search index pipelines while respecting domain politeness.

```mermaid
graph TD
    Seeds[Seed URLs] --> Frontier[URL Frontier: Priority & Politeness Queues]
    Frontier --> FetcherPool[Distributed Fetcher Workers]
    FetcherPool --> DNSCache[DNS Cache Resolver]
    FetcherPool --> Web[Internet Web Servers]
    Web --> FetcherPool
    
    FetcherPool --> Parser[HTML Content Parser]
    Parser --> Dedup[Content Deduplication: SimHash]
    Dedup --> DocStore[(Document Storage: HDFS / S3)]
    
    Parser --> LinkExtract[Link Extractor]
    LinkExtract --> URLFilter[URL Filter & Bloom Filter]
    URLFilter --> Frontier
```

---

## 1. Requirements

### Functional Requirements:
1. Crawl 1 Billion web pages every month.
2. Parse HTML, extract hyperlinks, and discover new URLs.
3. Detect and discard duplicate content.
4. Honor `robots.txt` and domain rate limits (**Politeness**).

### Non-Functional Requirements:
- **Scalability**: Capable of ingesting 400+ pages/sec.
- **Politeness**: Never overload target web servers with concurrent requests.
- **Fault Tolerance**: Worker nodes crash without losing frontier state.

---

## 2. The URL Frontier: Balancing Priority and Politeness

The URL Frontier determines *which* URL to fetch next and *when* to fetch it.

```mermaid
graph TD
    subgraph "1. Priority Queues (FIFO / PageRank Scored)"
        In[Incoming URLs] --> Prioritizer[Priority Classifier]
        Prioritizer --> Q_High[High Priority: CNN, Wikipedia]
        Prioritizer --> Q_Low[Low Priority: Personal Blogs]
    end

    subgraph "2. Politeness Queues (Host-Partitioned)"
        Q_High --> HostRouter[Host Router: Hash(domain)]
        Q_Low --> HostRouter
        HostRouter --> HostQ1[Queue: cnn.com]
        HostRouter --> HostQ2[Queue: nytimes.com]
        HostRouter --> HostQN[Queue: wikipedia.org]
    end

    subgraph "3. Politeness Delay Dispatcher"
        HostQ1 --> Delay1[Delay Enforcer: Min 1s gap per host]
        Delay1 --> Worker[Fetcher Thread Pool]
    end
```

---

## 3. Duplicate Detection: SimHash and Bloom Filters

1. **URL Seen Filter**: A distributed **Bloom Filter** holding 5 Billion URLs in ~6 GB of RAM prevents crawling the exact same URL twice.
2. **Near-Duplicate Content Detection (SimHash)**:
   - Web pages with identical text but different banner ads are near-duplicates.
   - **SimHash** maps high-dimensional text to a 64-bit fingerprint. If Hamming distance $\le 3$, documents are considered duplicates and discarded.

---

## 4. Key Takeaways

- Enforce domain politeness using two-tier queues (Priority $\to$ Host Queues with delay timers).
- Use Bloom Filters to prevent circular crawling loops across billions of URLs in memory.
- Use SimHash to detect near-duplicate pages and prevent index pollution.
""",

    "07-notification-system.md": """# Design a Scalable Notification System (Apple APNs / Twilio)

A high-throughput, multi-platform notification system capable of delivering 100+ million notifications per day across iOS Push (APNs), Android Push (FCM), SMS (Twilio), and Email (SendGrid).

```mermaid
graph TD
    Clients[Internal Microservices: Order, Billing, Marketing] --> GW[Notification API Gateway]
    GW --> RateLimit[User Rate Limiter & Deduplicator]
    RateLimit --> UserPrefs[(User Preference Store)]
    
    RateLimit --> Kafka[Kafka Notification Topic: Partitioned by Priority]
    Kafka --> PriorityWorker[High Priority Workers: OTP / 2FA]
    Kafka --> BulkWorker[Bulk Workers: Marketing / News]

    PriorityWorker --> ThirdParty
    BulkWorker --> ThirdParty

    subgraph ThirdParty [Third-Party Delivery Providers]
        APNs[Apple APNs: iOS Push]
        FCM[Firebase FCM: Android Push]
        Twilio[Twilio: SMS]
        SendGrid[SendGrid: Email]
    end
```

---

## 1. Requirements

### Functional Requirements:
1. Support 4 notification types: Mobile Push, SMS, Email, In-App.
2. Priority Levels: Critical (OTPs, flight alerts) vs Bulk (promotions).
3. User Preferences: Opt-in / opt-out controls per channel and quiet hours.
4. Delivery status tracking and retry with exponential backoff on failure.

### Non-Functional Requirements:
- **Low Latency**: OTP SMS/Push delivered in $< 3\text{ seconds}$.
- **Massive Throughput**: Handle 10,000+ notifications per second during breaking news.
- **At-Least-Once Delivery**: No critical notification is lost.

---

## 2. Deduplication and Rate Limiting

To prevent bugged microservices from spamming users with 10 duplicate SMS messages:
1. **Deduplication Hash**:
   $$\text{DedupKey} = \text{SHA256}(\text{user\_id} + \text{channel} + \text{message\_digest})$$
   Stored in Redis with a 5-minute TTL:
   ```
   SET dedup:usr_101:sms:hash99 1 NX EX 300
   ```
   If `SET ... NX` returns nil, drop the duplicate notification.
2. **User Rate Limiting**: Max 5 notifications per user per hour (except critical OTPs).

---

## 3. Key Takeaways

- Decouple senders from third-party delivery providers using partitioned message queues (Kafka / RabbitMQ).
- Partition queues by priority so bulk marketing blasts do not block critical 2FA OTP codes.
- Implement Redis deduplication keys to prevent runaway duplicate notifications.
"""
}

for fname, content in studies.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Case Studies Batch 1 complete.")
