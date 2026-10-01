# Section 04: Caching — Practice Exercises

---

### Problem 1: Cache Hit Ratio Economics
An e-commerce API serves 20,000 read requests per second. The underlying PostgreSQL database has an average read latency of 40ms. An in-memory Redis cache has an average read latency of 2ms.
1. Calculate the effective average latency if the cache hit ratio is 85%.
2. What happens to the effective latency and database load if the cache hit ratio improves to 98%?
> **Hint**: Effective Latency = $(\text{Hit Ratio} \times \text{Cache Latency}) + ((1 - \text{Hit Ratio}) \times \text{DB Latency})$.

---

### Problem 2: Cache-Aside vs Write-Through Concurrency
Two concurrent requests attempt to update and read user profile data under a Cache-Aside pattern:
- Thread 1 writes new user name "Alice" to the database.
- Thread 2 reads the user profile.
1. Outline the exact sequence of events that can result in stale data permanently residing in the cache.
2. How does setting a TTL or using transactional cache eviction mitigate this race condition?
> **Hint**: Trace DB write, cache delete, and concurrent cache reload order.

---

### Problem 3: Defending Against the Thundering Herd
A popular celebrity with 30 million followers posts a new message. The cached feed item expires at exactly midnight. At 00:00:01, 50,000 requests arrive within 100 milliseconds for that expired key.
1. What happens to the backing database under naive Cache-Aside?
2. Describe two distinct engineering solutions to prevent this Cache Stampede.
> **Hint**: Consider distributed mutex locking and probabilistic early expiration (XFetch).

---

### Problem 4: Bloom Filters for Cache Penetration
An attacker floods an API with 50,000 requests per second searching for randomly generated UUIDs that do not exist in the database.
1. Why does a standard cache fail to protect the database in this scenario?
2. Explain how placing a Bloom filter in front of the cache eliminates database load. What is the impact of false positives?
> **Hint**: Bloom filters guarantee zero false negatives.

---

### Problem 5: Cache Avalanche Prevention
An engineering team sets a 24-hour TTL on all product catalog entries during a midnight batch sync.
1. What failure occurs at midnight the following day?
2. Propose a code-level fix to prevent this avalanche.
> **Hint**: Think about TTL jitter.

---

👉 **Solutions**: Check [Section 04 Solutions](04-caching-solutions.md).
