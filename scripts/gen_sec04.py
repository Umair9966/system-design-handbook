import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 04: CACHING
# =========================================================================

save("docs/04-caching/01-cache-fundamentals-and-hit-ratio.md", """# Caching Fundamentals and Cache Hit Ratio

## Overview
A **cache** is a high-speed, temporary data storage layer that stores a subset of data—typically in fast memory (RAM)—so that future requests for that data are served significantly faster than querying the primary storage tier (SSD or hard disk).

The primary metric of cache performance is the **Cache Hit Ratio**:
$$\\text{Hit Ratio} = \\frac{\\text{Cache Hits}}{\\text{Cache Hits} + \\text{Cache Misses}}$$

```mermaid
graph LR
    Client[Client Request] --> Cache{In-Memory Cache}
    Cache -->|Cache Hit: 80-99%| Return[Sub-Millisecond Response]
    Cache -->|Cache Miss: 1-20%| DB[(Disk-Backed Database)]
    DB -->|Populate Cache| Cache
    DB --> Return
```

## Why It Matters
Reading data from in-memory RAM takes **~100 nanoseconds**, whereas reading from an SSD takes **~100 microseconds (1,000x slower)**, and querying a relational database across a network can take **10 to 50 milliseconds (100,000x slower)**. A high cache hit ratio directly reduces database server hardware costs by orders of magnitude while delivering snappy user experiences.

## Core Concepts
- **Effective Latency Formula**:
  $$\\text{Effective Latency} = (H \\times L_{cache}) + ((1 - H) \\times L_{backend})$$
  Where $H$ is the Hit Ratio, $L_{cache}$ is cache latency, and $L_{backend}$ is backend storage latency.
  *Example*: If $L_{cache} = 1\\text{ms}$ and $L_{backend} = 50\\text{ms}$:
  - At $80\\%$ Hit Ratio: $(0.8 \\times 1) + (0.2 \\times 50) = 0.8 + 10 = \\mathbf{10.8\\text{ ms}}$
  - At $99\\%$ Hit Ratio: $(0.99 \\times 1) + (0.01 \\times 50) = 0.99 + 0.5 = \\mathbf{1.49\\text{ ms}}$ (A **7.2x performance leap**!)
- **Principle of Locality**:
  - *Temporal Locality*: Data accessed recently is likely to be accessed again in the near future (e.g., viral news articles).
  - *Spatial Locality*: Data stored near recently accessed items is likely to be needed soon (e.g., sequential array memory or consecutive table rows).
- **Working Set Size (WSS)**: The total volume of active application data accessed during a given time window (e.g., 24 hours). If your physical cache size is smaller than your working set, cache thrashing occurs, causing hit ratios to plummet.

## Trade-offs
| Caching Priority | Advantage | Disadvantage / Risk |
| :--- | :--- | :--- |
| **High Hit Ratio Target (>95%)** | Maximum database protection & low latency | Requires massive RAM capacity; higher infrastructure cost |
| **Aggressive Short TTLs** | Data freshness guaranteed | Lower hit ratio; frequent database query spikes |
| **Long TTLs / No Expiration** | Maximum hit ratio | Severe risk of serving stale, invalid data to users |

## When to Use / When NOT to Use
### When Caching is Essential
- High read-to-write ratios ($> 10:1$), compute-intensive aggregation queries, static asset distribution, user session lookups.

### When Caching is an Anti-Pattern
- Pure write-heavy workloads with near-zero read re-use (e.g., raw IoT telemetry ingestion).
- Real-time safety-critical data where reading a stale value causes severe financial or physical harm.

## Real-World Examples
- **Facebook (Meta) Memcached Cluster**: Manages thousands of distributed Memcached servers caching trillions of items, sustaining billions of requests per second with an average cache hit ratio exceeding **98%**.
- **Twitter/X Timeline Cache**: Stores the personalized home timelines of active users entirely in Redis memory pools so opening the mobile app loads feeds in under 20ms.

## Common Pitfalls
- **Over-Sizing Cache for Stale Keys**: Caching items that are read only once, polluting memory and evicting truly valuable hot keys.
- **Ignoring Serialization Overhead**: Spending more CPU cycles serializing and deserializing JSON objects into Redis than the time saved by avoiding the database query.

## Key Takeaways
- The Cache Hit Ratio non-linearly impacts effective system latency; moving from 90% to 99% hit ratio slashes database load by 10x.
- Size your cache based on the **working set size**, not total database storage.
- Always monitor hit ratio, miss latency, and eviction rates in production telemetry.

## Common Interview Questions
1. If your system has an average cache hit ratio of 90%, what happens to database traffic if the hit ratio drops to 80%?
2. How do you calculate the working set size of an application?
3. Under what conditions does adding a cache actually degrade system latency?

## Further Reading
- [Facebook Engineering: Scaling Memcache at Facebook (NSDI 2013)](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala)
- [Martin Fowler: Two Hard Things in Computer Science](https://martinfowler.com/bliki/TwoHardThings.html)
""")

save("docs/04-caching/02-caching-levels.md", """# Caching Across the Stack: Client to Database

## Overview
Caching in production is not a single layer; it is an integrated, multi-tiered hierarchy spanning the entire path from the user's device down to physical database silicon:
1. **Client / Browser Cache**: Local device storage (HTTP browser cache, Service Worker Cache API).
2. **CDN Edge Cache**: Hundreds of globally distributed Points of Presence (Cloudflare, CloudFront).
3. **API Gateway / Reverse Proxy Cache**: Front-door ingress caches (NGINX, Varnish).
4. **Application In-Memory Cache**: Process-local heap memory (Guava, Caffeine, Go sync.Map).
5. **Distributed In-Memory Cache**: Shared multi-node memory clusters (Redis, Memcached).
6. **Database Buffer Pool**: Internal database engine RAM pages (InnoDB Buffer Pool, Postgres Shared Buffers).

```mermaid
graph TD
    Client[1. Browser Cache: 0ms] -->|Miss| CDN[2. CDN Edge: 10ms]
    CDN -->|Miss| Gateway[3. API Gateway / Proxy: 2ms]
    Gateway -->|Miss| AppLocal[4. App Local Memory: 0.1ms]
    AppLocal -->|Miss| DistCache[(5. Distributed Redis: 1-2ms)]
    DistCache -->|Miss| DBBuffer[(6. DB Buffer Pool RAM: 5ms)]
    DBBuffer -->|Miss| Disk[(7. Database NVMe Disk: 20ms+)]
```

## Why It Matters
Terminating a request as close to the client as possible yields exponential latency and cost savings. An asset served from browser cache costs $0 and takes 0ms. If that request penetrates all the way to disk-backed storage, it consumes network bandwidth, proxy compute, application thread memory, and database I/O.

## Core Concepts & Tier Breakdown
- **Tier 1: Browser Cache**: Controlled via HTTP headers (`Cache-Control: max-age=3600, immutable`, `ETag`, `Last-Modified`). Zero network latency.
- **Tier 2: Edge CDN**: Caches static assets and public API payloads geographically adjacent to users.
- **Tier 3: Reverse Proxy (NGINX/Varnish)**: Sits in front of the application pool, serving cached HTML fragments or full responses.
- **Tier 4: Process-Local Memory (Caffeine/LruCache)**: Instantaneous nanosecond read access inside application heap memory, but state is lost on process restart and not shared across instances.
- **Tier 5: Distributed Cache (Redis)**: Centralized, shared in-memory cluster accessible by all stateless application instances over LAN in ~1ms.
- **Tier 6: Database Buffer Pool**: The database itself caches frequently read 16KB disk pages in RAM to avoid expensive disk seeks.

## Trade-offs
| Caching Tier | Read Latency | Consistency Coherence | Storage Capacity |
| :--- | :--- | :--- | :--- |
| **App Local RAM (Heap)**| **Nanoseconds** | Very Hard (Divergent across instances)| Limited by VM RAM (1-8 GB) |
| **Distributed (Redis)** | 1ms - 2ms | High (Single source of truth) | High (Terabytes across cluster)|
| **Edge CDN** | 10ms - 20ms | Eventual (Purge propagation delay) | Massive (Petabytes) |
| **Browser Cache** | **0ms** | Poor (Client-controlled) | Strictly limited by client device|

## When to Use / When NOT to Use
### When to Use Process-Local Memory Caching
- Static configuration values, cryptographic public keys, or immutable metadata read thousands of times per second per node.

### When to Use Distributed Caching (Redis)
- Shared user sessions, dynamic shopping carts, database query results, rate limiting counters.

## Real-World Examples
- **GitHub Page Rendering**: Employs a multi-layer cache: client browser caches assets, Fastly CDN caches public repo pages, internal Redis caches markdown-rendered HTML blobs, and MySQL buffer pools cache raw git commit metadata.

## Common Pitfalls
- **Cache Incoherence with Local Heap Caches**: Storing mutable user permissions in process-local application memory; Node 1 updates the user's role to banned, but Node 2 continues serving authorized requests for 10 minutes from its stale local cache.
- **Double Caching**: Caching the identical large data payload simultaneously in local heap memory, Redis, and reverse proxies, wasting expensive RAM across all tiers.

## Key Takeaways
- Design caching as a multi-tier defense in depth.
- Process-local caches are fast (nanoseconds) but risk state divergence across nodes.
- Distributed caches (Redis) provide consistent, shared state across horizontally scaled stateless application instances.

## Common Interview Questions
1. How does a database buffer pool interact with an external distributed cache like Redis?
2. When would you choose an in-process local cache over an external Redis cluster?
3. How do HTTP `ETag` and `If-None-Match` headers implement conditional caching at the browser tier?

## Further Reading
- [Ilya Grigorik: High Performance Browser Networking (HTTP Caching)](https://hpbn.co/http-caching/)
- [PostgreSQL Documentation: Chapter 19 - Resource Consumption (shared_buffers)](https://www.postgresql.org/docs/current/runtime-config-resource.html)
""")

save("docs/04-caching/03-caching-strategies.md", """# Caching Strategies: Cache-Aside, Write-Through, Write-Back, and Write-Around

## Overview
A **caching strategy** (or caching pattern) defines the sequence and ownership of data mutations and lookups between the application, the cache, and the underlying database:
- **Cache-Aside (Lazy Loading)**: Application manages cache lookups and writes explicitly.
- **Read-Through**: Application treats the cache as the primary store; the cache transparently fetches missing data from the database.
- **Write-Through**: Application writes data to the cache, which synchronously updates the database before acknowledging success.
- **Write-Back (Write-Behind)**: Application writes data to the cache, which acknowledges immediately and asynchronously flushes updates to the database in background batches.
- **Write-Around**: Writes bypass the cache completely, writing directly to the database.

```mermaid
sequenceDiagram
    autonumber
    Note over App, DB: Cache-Aside (Lazy Loading)
    App->>Cache: 1. Get user:123
    Cache-->>App: 2. Cache Miss!
    App->>DB: 3. Query user:123
    DB-->>App: 4. Return Record
    App->>Cache: 5. Set user:123 (TTL: 1hr)
    App-->>Client: 6. Return User Data
```

## Why It Matters
Selecting the wrong caching pattern causes subtle concurrency bugs, severe write latency spikes, or catastrophic data loss. For instance, using Write-Back without persistence guarantees can lose critical customer orders if the cache crashes before flushing to the database.

## Core Concepts & Step-by-Step Mechanics
1. **Cache-Aside (Lazy Loading)**:
   - *Read*: Check cache -> On miss, read DB -> Populate cache -> Return.
   - *Write*: Write DB -> Invalidate (delete) cache key.
   - *Advantage*: Only requested data is cached; cache node failures do not halt writes.
2. **Write-Through**:
   - Application writes to cache -> Cache writes synchronously to DB -> Cache returns success.
   - *Advantage*: Data in cache is never stale.
   - *Disadvantage*: Higher write latency (incurs two network writes).
3. **Write-Back (Write-Behind)**:
   - Application writes to cache -> Cache acknowledges immediately -> Background worker batches writes to DB.
   - *Advantage*: Unbelievably fast write latency and absorbs high write bursts.
   - *Risk*: **Data Loss**. If the cache crashes before the async flush, unwritten data is lost forever.
4. **Write-Around**:
   - Write goes directly to DB, bypassing cache.
   - *Advantage*: Prevents cache pollution from write-heavy data that is rarely read again.

## Trade-offs
| Pattern | Write Latency | Read Latency | Data Consistency Guarantee | Data Loss Risk |
| :--- | :--- | :--- | :--- | :--- |
| **Cache-Aside** | Low (direct to DB) | Fast on hits, slow on cold misses | Eventual (requires eviction) | **Zero** |
| **Write-Through** | Slow (incurs cache + DB sync write)| Instant (cache is always pre-warmed)| **Strong** | **Zero** |
| **Write-Back** | **Ultra-Fast (sub-1ms in RAM)** | Instant | Eventual | **High (if cache crashes)** |
| **Write-Around** | Low | Slow on first read (cold miss) | Eventual | **Zero** |

## When to Use / When NOT to Use
### When to Use Cache-Aside
- General-purpose read-heavy web applications, user profiles, product catalogs. The industry standard default.

### When to Use Write-Back
- High-frequency write-heavy workloads with tolerable loss windows (e.g., video view counters, IoT GPS coordinates, gaming telemetry).

### When to Use Write-Around
- Data written once and read infrequently (e.g., legal compliance audit logs, regulatory archival records).

## Real-World Examples
- **Operating System Page Cache**: Uses **Write-Back** caching. When a process writes to disk, the Linux kernel writes to RAM (dirty pages) and immediately returns; the `pdflush` kernel thread flushes dirty pages to physical disk asynchronously.
- **E-Commerce Inventory**: Employs **Cache-Aside** with cache invalidation upon checkout to ensure customers never purchase out-of-stock items.

## Common Pitfalls
- **Updating Cache Instead of Deleting in Cache-Aside**: Concurrently writing new values directly into the cache causes race conditions; always **delete** the cache key on DB update so the next read safely re-populates the latest committed state.
- **Unbounded Write-Back Buffers**: Allowing write-back queues to grow faster than database write throughput, leading to out-of-memory crashes and massive data loss.

## Key Takeaways
- **Cache-Aside** is the most versatile and resilient pattern for standard production systems.
- Always **invalidate (delete)** cache keys on database updates rather than updating them in place.
- Use **Write-Back** only when extreme write throughput justifies the inherent risk of data loss.

## Common Interview Questions
1. Why is deleting a cache key safer than updating it when writing data in Cache-Aside?
2. What are the operational failure modes of a Write-Back cache?
3. How does the Write-Through pattern impact write latency compared to Write-Around?

## Further Reading
- [AWS Architecture: Caching Strategies and Best Practices](https://aws.amazon.com/caching/best-practices/)
- [Martin Kleppmann: Transactions in Distributed Systems (DDIA Chapter 7)](https://dataintensive.net/)
""")

save("docs/04-caching/04-cache-eviction-policies.md", """# Cache Eviction Policies: LRU, LFU, FIFO, and Adaptive Algorithms

## Overview
Caches operate in finite physical memory (RAM). When the cache becomes full and new data must be stored, a **cache eviction policy** algorithmically determines which existing data items must be removed to free memory space.

```mermaid
graph LR
    subgraph Doubly Linked List + Hash Map [LRU Architecture]
        Head[Head: Most Recently Used] <--> NodeA[Key A]
        NodeA <--> NodeB[Key B]
        NodeB <--> Tail[Tail: Least Recently Used -> EVICT FIRST]
    end
```

## Why It Matters
A poor eviction policy evicts valuable, frequently accessed hot keys, causing cache hit ratios to plunge and overloading downstream databases. Choosing the right algorithm ensures that memory is populated strictly by the high-value working set.

## Core Concepts & Algorithms
1. **LRU (Least Recently Used)**:
   - Evicts the item that has not been accessed for the longest duration of time.
   - Based on temporal locality: if you haven't read it recently, you probably won't read it soon.
   - Implemented in $O(1)$ time complexity using a **Hash Map paired with a Doubly Linked List**.
2. **LFU (Least Frequently Used)**:
   - Tracks an access counter for each key; evicts the item with the lowest total access frequency.
   - *Weakness*: Suffers from cache pollution from historical access bursts (e.g., an item accessed 1,000 times yesterday will linger in memory forever even if never accessed again).
3. **FIFO (First-In, First-Out)**:
   - Evicts items strictly in the order they were inserted, regardless of access patterns.
   - Vulnerable to Bélády’s Anomaly and poor hit ratios.
4. **W-TinyLFU (Window TinyLFU - Caffeine Cache)**:
   - Modern state-of-the-art policy. Combines a small LRU admission window with a frequency bloom filter (Count-Min Sketch) with aging/decay mechanisms to resist burst pollution.

## How It Works: LRU Implementation Mechanics
```python
# O(1) LRU Cache: Hash Map + Doubly Linked List
class Node:
    def __init__(self, key, value):
        self.key, self.value = key, value
        self.prev = self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {} # key -> Node
        self.head, self.tail = Node(0, 0), Node(0, 0)
        self.head.next, self.tail.prev = self.tail, self.head

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _add_to_head(self, node):
        node.next, node.prev = self.head.next, self.head
        self.head.next.prev = self.head.next = node

    def get(self, key: int) -> int:
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add_to_head(node) # Mark recently used
            return node.value
        return -1

    def put(self, key: int, value: int):
        if key in self.cache:
            self._remove(self.cache[key])
        node = Node(key, value)
        self._add_to_head(node)
        self.cache[key] = node
        if len(self.cache) > self.capacity:
            # Evict from tail (Least Recently Used)
            lru = self.tail.prev
            self._remove(lru)
            del self.cache[lru.key]
```

## Trade-offs
| Algorithm | Time Complexity | Memory Overhead | Resilience to Scan Scrapes |
| :--- | :--- | :--- | :--- |
| **LRU** | $O(1)$ | Moderate (2 pointers per node) | **Poor (large full-table scans flush entire cache)** |
| **LFU** | $O(1)$ | High (access counters + frequency lists)| Poor (historical items linger) |
| **FIFO** | $O(1)$ | Minimal | Terrible |
| **W-TinyLFU** | $O(1)$ | Very Low (4-bit frequency counters) | **Superior (near-optimal hit ratio)** |

## When to Use / When NOT to Use
### When to Use LRU / W-TinyLFU
- Standard web application and database query caching. Default choice for Redis (`allkeys-lru`) and in-memory caches.

### When to Avoid Simple LRU
- Systems where background batch analytics perform full sequential scans; a single scan will completely flush the active working set out of an LRU cache.

## Real-World Examples
- **Redis Maxmemory Policies**: Supports `allkeys-lru`, `volatile-lru`, `allkeys-lfu`, and `volatile-ttl`. Redis implements an **Approximated LRU** by sampling 5 random keys and evicting the oldest among the sample, achieving 99% of true LRU efficiency without the memory pointer overhead.
- **Caffeine (Java) / Ristretto (Go)**: Use **Window TinyLFU**, outperforming traditional LRU caches by 10-30% hit ratio across production benchmarks.

## Common Pitfalls
- **Unbounded Memory Caches**: Deploying an in-memory hash map without an eviction policy or maximum capacity limit, leading to catastrophic JVM OutOfMemoryError crashes under production traffic.
- **LFU Frequency Saturation**: Failing to implement frequency decay in LFU, allowing ancient viral content to permanently block new hot keys.

## Key Takeaways
- True LRU requires a **Hash Map + Doubly Linked List** to achieve $O(1)$ `get` and `put` operations.
- Redis uses an **approximated LRU** algorithm using random sampling to save memory.
- Modern high-performance systems use **W-TinyLFU** to prevent scan pollution.

## Common Interview Questions
1. How do you implement a thread-safe LRU cache with $O(1)$ time complexity?
2. What is the scan pollution problem in an LRU cache, and how do 2Q or W-TinyLFU algorithms solve it?
3. How does Redis approximate the LRU algorithm without maintaining a global linked list?

## Further Reading
- [Ben Manes: Designing a High Performance Cache (W-TinyLFU Paper, 2015)](https://arxiv.org/abs/1512.00727)
- [Redis Documentation: Key Eviction Policies](https://redis.io/docs/reference/eviction/)
""")

save("docs/04-caching/05-cache-invalidation-and-anomalies.md", """# Cache Invalidation, Stampede, Penetration, and Avalanche

## Overview
Operating distributed caches introduces notorious production pathologies that can bring down entire systems within seconds:
- **Cache Stampede (Thundering Herd)**: A highly popular key expires, causing thousands of concurrent requests to hit the backend database simultaneously.
- **Cache Penetration**: Requests for non-existent keys bypass the cache completely and overwhelm the database.
- **Cache Avalanche**: A massive cluster of keys expires at the exact same second, unleashing a tidal wave of traffic onto the database.
- **Cache Breakdown**: A single super-hot key expires right during a viral traffic peak.

```mermaid
graph TD
    subgraph Pathologies and Antidotes
        P1[Cache Stampede: Expired Hot Key] --> S1[Antidote: Mutex Locking / Probabilistic XFetch]
        P2[Cache Penetration: Nonexistent Keys] --> S2[Antidote: Bloom Filter / Negative Caching]
        P3[Cache Avalanche: Simultaneous Expiry] --> S3[Antidote: Random TTL Jitter]
    end
```

## Why It Matters
Phil Karlton famously observed: *"There are only two hard things in Computer Science: cache invalidation and naming things."* Mismanaging cache invalidation is the leading cause of downstream database collapse and cascading cloud outages.

## Core Concepts & Mitigation Mechanics

### 1. Cache Stampede (Thundering Herd)
- **The Failure**: Key `celebrity:news` expires at 12:00:00. At 12:00:01, 50,000 users request it. All 50,000 requests find a cache miss, and all 50,000 query the database simultaneously.
- **Mitigation A (Distributed Mutex)**: Only the first request acquires a lock in Redis (`SET lock:key token NX EX 5`) and queries the DB; all other 49,999 requests wait and re-read from cache.
- **Mitigation B (Probabilistic Early Expiration - XFetch)**:
  Workers recompute the cache *before* it strictly expires based on read frequency and computation time:
  $$-\\beta \\times \\delta \\times \\ln(\\text{random}()) > \\text{TTL} - \\text{now}$$

### 2. Cache Penetration
- **The Failure**: An attacker queries random nonexistent user IDs (`/users/-9999`). The cache never stores these keys, so 100% of malicious requests bypass the cache and execute expensive database table scans.
- **Mitigation A (Bloom Filter)**: Maintain a compact Bloom filter in memory containing all valid IDs. If the filter returns false, reject with 404 immediately.
- **Mitigation B (Negative Caching)**: Cache `null` values with a short TTL (e.g., 60 seconds).

### 3. Cache Avalanche
- **The Failure**: A midnight batch job loads 500,000 products with `TTL = 86400` (24 hours). The following midnight, all 500,000 keys expire at the identical microsecond.
- **Mitigation (TTL Jitter)**: Add a randomized time delta to every TTL:
  $$\\text{Effective TTL} = \\text{Base TTL} + \\text{random}(-300\\text{s}, +300\\text{s})$$

## Trade-offs
| Pathology Defense | Implementation Complexity | Protection Level | Side Effects |
| :--- | :--- | :--- | :--- |
| **Distributed Mutex Lock** | Moderate (Redis Lua script) | **100% Stampede Protection** | Slight latency queuing on lock wait |
| **Probabilistic XFetch** | High (algorithmic tuning) | Excellent | Slight extra background recompute load |
| **Bloom Filter** | Moderate | **100% Penetration Protection**| Rare false positives require DB check |
| **TTL Jitter** | Minimal (one line of code) | **100% Avalanche Protection** | None |

## When to Use / When NOT to Use
### Mandatory Production Protections
- **TTL Jitter**: Mandatory for 100% of all cached keys in production.
- **Bloom Filters**: Essential for public-facing search endpoints vulnerable to scraping and bot attacks.

## Real-World Examples
- **Reddit Outages**: Historically suffered from cache stampedes on front-page comment threads, inspiring the development of probabilistic early expiration libraries and distributed single-flight request coalescing (Go `singleflight`).
- **AWS ElastiCache**: Recommends applying randomized TTL jitter across all caching tiers by default to avoid cascading database failovers.

## Common Pitfalls
- **Setting Uniform TTLs in Batch Syncs**: Setting `TTL = 3600` on 100,000 keys during an hourly cache warm-up script, guaranteeing an avalanche exactly 60 minutes later.
- **Lock Deadlocks in Mutex Stampede Protection**: Failing to set an auto-expiry on the distributed stampede lock, causing all subsequent reads to hang indefinitely if the worker thread crashes before releasing the lock.

## Key Takeaways
- Always add **TTL Jitter** to prevent cache avalanches.
- Use **Go `singleflight`** or **Redis Mutex locks** to protect against the Thundering Herd.
- Protect against cache penetration using **Bloom Filters** or **Negative Caching**.

## Common Interview Questions
1. How does the Thundering Herd problem occur, and how do distributed mutexes mitigate it?
2. How does a Bloom filter protect a relational database from cache penetration attacks?
3. How do you implement TTL jitter, and what is its mathematical impact on cache expiration?

## Further Reading
- [Vattani et al.: Optimal Probabilistic Cache Invalidation (XFetch Algorithm)](http://www.vldb.org/pvldb/vol8/p886-vattani.pdf)
- [Go singleflight Package Documentation](https://pkg.go.dev/golang.org/x/sync/singleflight)
""")

save("docs/04-caching/06-distributed-caching-redis-vs-memcached.md", """# Distributed Caching: Redis vs Memcached

## Overview
When an application tier scales horizontally across multiple servers, caching requires a dedicated distributed in-memory data store. Two open-source technologies dominate the enterprise:
- **Redis (Remote Dictionary Server)**: Feature-rich in-memory data structure store supporting strings, hashes, lists, sets, sorted sets, streams, Pub/Sub, persistence, and clustering.
- **Memcached**: High-performance, multithreaded, simple key-value memory caching system designed for pure string storage and horizontal scale-out.

```mermaid
graph TD
    subgraph Memcached Architecture
        MC[Multithreaded Slab Allocator: Pure Key-Value Strings]
    end
    subgraph Redis Architecture
        R1[Single-Threaded Event Loop Core]
        R2[Rich Data Structures: Hashes, ZSets, Bitmaps, Streams]
        R3[Disk Persistence: RDB Snapshots + AOF Logs]
        R4[Native Redis Cluster: 16,384 Hash Slots]
        R1 --- R2 & R3 & R4
    end
```

## Why It Matters
Deploying Memcached when you need atomic counters or sorted ranking sets forces complex, slow application-layer logic. Conversely, selecting Redis for basic caching without understanding its single-threaded CPU characteristics or memory overhead can lead to performance bottlenecks under simple massive scale.

## Core Concepts & Architectural Comparison
1. **Concurrency & Threading Model**:
   - *Memcached*: **Multithreaded**. Uses kernel locking and scales seamlessly across all CPU cores on a 64-core machine.
   - *Redis*: **Single-threaded event loop** for command execution (utilizing non-blocking `epoll`), supplemented by background threads for I/O and asynchronous deletion (`UNLINK`).
2. **Data Structure Versatility**:
   - *Memcached*: Pure string/blob key-value pairs (max key size 250 bytes, max value 1MB).
   - *Redis*: Native rich data structures with in-engine operations (e.g., `ZADD`, `HINCRBY`, `PFADD` for HyperLogLog).
3. **Memory Management**:
   - *Memcached*: **Slab Allocator**. Pre-allocates memory chunks of fixed sizes, completely preventing memory fragmentation at the cost of slight internal wasted space.
   - *Redis*: Uses dynamic allocators (Jemalloc), which can suffer from memory fragmentation over time under heavy mutation.
4. **Persistence & Clustering**:
   - *Memcached*: 100% Volatile RAM. Zero disk persistence. Clustering is handled client-side via consistent hashing.
   - *Redis*: Optional persistence via **RDB (Point-in-time snapshots)** and **AOF (Append-Only Log)**. Native server-side **Redis Cluster** with 16,384 hash slots.

## Trade-offs
| Feature | Redis | Memcached |
| :--- | :--- | :--- |
| **Data Types** | Rich (Strings, Hashes, Lists, ZSets, Geospatial)| Strings / Raw Blobs only |
| **Threading Model** | Single-threaded core execution | **Multithreaded (scales with CPU cores)**|
| **Persistence** | **Yes (RDB snapshots & AOF logs)** | None (Pure Volatile RAM) |
| **Replication / HA** | **Native Master-Replica + Sentinel/Cluster** | None (Client handles sharding) |
| **Memory Fragmentation**| Can be high (requires Jemalloc tuning) | **Zero (Slab allocator)** |
| **Max Value Size** | 512 MB | 1 MB (configurable up to custom limits) |

## When to Use / When NOT to Use
### When to Choose Redis
- The universal default for 90% of modern applications: sessions, real-time leaderboards (`ZSet`), rate limiters, pub/sub messaging, geospatial queries.

### When to Choose Memcached
- Pure, simple key-value caching where payloads are static text/HTML fragments, and machines have high core counts (32+ vCPUs) that can fully saturate multithreading.

## Real-World Examples
- **Twitter/X**: Uses **Redis** extensively for timeline caching and follower graphs, taking advantage of Redis list and set operations directly in RAM.
- **Facebook**: Deployed the world's largest **Memcached** deployment for dedicated, high-throughput social graph caching, optimizing the C codebase with custom slab classes.

## Common Pitfalls
- **Blocking Commands on Redis**: Executing $O(N)$ commands like `KEYS *` or huge `SMEMBERS` on production Redis clusters; because Redis is single-threaded, a 2-second command freezes all other operations across the entire cluster.
- **Over-Reliance on Redis Persistence**: Treating Redis as a primary durable database; under high write loads, background AOF disk syncs can stall the main thread (AOF fsync latency).

## Key Takeaways
- Redis is an in-memory **data structures server** with persistence, replication, and clustering.
- Memcached is a **multithreaded pure key-value cache** with superior memory slab allocation.
- Never run `KEYS *` in production Redis; always use `SCAN`.

## Common Interview Questions
1. Why is Redis considered single-threaded, and how does it still achieve over 100,000 QPS on a single instance?
2. How does Memcached's slab allocator prevent memory fragmentation compared to dynamic allocators?
3. How does Redis Cluster partition keys across its 16,384 hash slots?

## Further Reading
- [Redis Official Documentation](https://redis.io/docs/)
- [Antirez (Salvatore Sanfilippo): Redis Architecture Notes](http://antirez.com/)
""")

save("docs/04-caching/07-negative-caching.md", """# Negative Caching: Mitigating Repeated Misses

## Overview
**Negative caching** is the architectural pattern of explicitly caching **negative query responses** (e.g., "Entity Not Found", HTTP 404, or `null` values) in the caching tier to protect downstream databases from repetitive lookups for nonexistent records.

```mermaid
sequenceDiagram
    autonumber
    Client->>Cache: 1. Get user:99999 (Nonexistent)
    Cache-->>Client: 2. Cache Miss
    Client->>DB: 3. SELECT * FROM users WHERE id = 99999
    DB-->>Client: 4. Empty Result (Record Not Found)
    Client->>Cache: 5. SET user:99999 = NULL (Short TTL: 60s)
    Note over Client, Cache: Subsequent Requests
    Client->>Cache: 6. Get user:99999
    Cache-->>Client: 7. Cache Hit: NULL (Fast 404 Return!)
```

## Why It Matters
Without negative caching, querying a non-existent entity is significantly more computationally expensive than querying a valid one. A query for an existing item hits the cache in 1ms. A query for a nonexistent item triggers a cache miss, forces a database table scan or index lookup, and yields nothing to cache—leaving the database completely unprotected against repeated identical requests.

## Core Concepts
- **Asymmetric Cost of Misses**: Valid records enjoy a 99% cache hit ratio. Invalid records suffer a **0% hit ratio**, repeatedly pummeling the database.
- **Short TTL Enforcement**: Negative entries must carry significantly shorter TTLs (e.g., 30 to 120 seconds) than positive entries (hours or days) to prevent locking out newly registered entities.
- **Negative Caching Sentinel Value**: Storing a compact tombstone token (e.g., `__NULL__` or a JSON `{"_nil": true}`) rather than an empty string to differentiate between an empty payload and a missing record.

## Trade-offs
| Strategy | Database Protection | Memory Footprint Overhead | Freshness Risk |
| :--- | :--- | :--- | :--- |
| **Negative Caching with Short TTL** | **High (absorbs repeat misses)** | Moderate (stores sentinel keys) | Brief delay (30-60s) if entity is created immediately after query |
| **No Negative Caching** | Zero (DB takes 100% of misses) | Zero RAM overhead | Immediate visibility upon creation |
| **Bloom Filter Filtering** | Absolute (zero DB misses) | Extremely low (few bits per key)| Complexity of maintaining distributed Bloom filters |

## When to Use / When NOT to Use
### When to Use Negative Caching
- Public-facing user profile lookups, username availability checkers, inventory SKU lookups, DNS resolution (NXDOMAIN).

### When NOT to Use
- Highly dynamic systems where records are created milliseconds after verification, unless the creation handler explicitly evicts the negative cache key.

## Real-World Examples
- **DNS NXDOMAIN Caching (RFC 2308)**: DNS recursive resolvers negatively cache `NXDOMAIN` (Non-Existent Domain) responses based on the authoritative zone's SOA record TTL, preventing the internet from repeatedly flooding root nameservers for mistyped domains.
- **E-Commerce Search**: Caching `null` results for out-of-catalog search terms typed by millions of users during advertising campaigns.

## Common Pitfalls
- **Long Negative TTLs**: Caching negative results for 24 hours; a user signs up with username `john_doe`, but friends cannot find the profile because the negative `null` cache entry persists for a day.
- **Memory Exhaustion via Key Bombing**: An attacker generates millions of random nonexistent keys; storing a negative cache entry for each random key exhausts Redis memory. (Mitigate using **Bloom filters** or strict maxmemory eviction).

## Key Takeaways
- Negative caching stores `null` or 404 responses to shield the database from repeated misses.
- Always assign negative cache entries a **much shorter TTL** than positive data.
- Pair negative caching with cache eviction on entity creation to ensure immediate visibility.

## Common Interview Questions
1. How does negative caching protect a database against scraping and malicious brute-force attacks?
2. What are the risks of setting an excessively long TTL on negative cache entries?
3. How does DNS implement negative caching via RFC 2308?

## Further Reading
- [RFC 2308: Negative Caching of DNS Queries (DNS NCACHE)](https://datatracker.ietf.org/doc/html/rfc2308)
- [Martin Fowler: Caching Patterns](https://martinfowler.com/eaaCatalog/identityMap.html)
""")

print("Section 04 complete.")
