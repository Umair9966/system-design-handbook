# Section 04: Caching — Solutions

### Solution 1: Cache Hit Ratio Economics
1. **Effective Latency at 85% Hit Ratio**:
   - $\text{Latency} = (0.85 \times 2\text{ ms}) + (0.15 \times 40\text{ ms}) = 1.7\text{ ms} + 6.0\text{ ms} = 7.7\text{ ms}$.
   - Database receives $20,000 \times 0.15 = 3,000\text{ queries/second}$.
2. **Effective Latency at 98% Hit Ratio**:
   - $\text{Latency} = (0.98 \times 2\text{ ms}) + (0.02 \times 40\text{ ms}) = 1.96\text{ ms} + 0.8\text{ ms} = 2.76\text{ ms}$.
   - Database receives $20,000 \times 0.02 = 400\text{ queries/second}$.
   - **Result**: A 13% improvement in hit ratio yields a **2.8x latency reduction** and slashes database load by **86.7%**!

---

### Solution 2: Cache-Aside Race Condition
1. **The Race Condition**:
   - Cache currently contains old data "Bob".
   - Thread 1 updates database to "Alice".
   - Thread 1 attempts to evict cache key, but network delays the eviction packet.
   - Meanwhile, Thread 2 reads from cache, gets old value "Bob", or reads DB before Thread 1's commit finishes and writes "Bob" back into cache.
   - Result: Stale value "Bob" sits in cache indefinitely.
2. **Mitigations**:
   - Always set an absolute TTL (e.g., 5 minutes) so stale data is automatically purged.
   - Evict the cache key *after* the DB transaction commits successfully, or use delayed double-deletion.

---

### Solution 3: Thundering Herd Mitigation
1. **Database Impact**: All 50,000 requests find a cache miss simultaneously. All 50,000 requests query the database to reconstruct the identical key, causing connection pool exhaustion and database CPU saturation.
2. **Mitigation 1 (Distributed Mutex)**:
   - When a cache miss occurs, the worker attempts to acquire a short-lived distributed lock in Redis (`SET lock:key value NX EX 5`).
   - Only the single worker that acquires the lock queries the database and populates the cache. All other requests wait briefly and re-read from cache.
3. **Mitigation 2 (Probabilistic Early Expiration - XFetch)**:
   - Workers calculate an algorithmically jittered probability to recompute the cache *before* it strictly expires based on current read rate and compute cost.

---

### Solution 4: Bloom Filters for Cache Penetration
1. **Failure of Standard Cache**: Because the random UUIDs do not exist, the cache never contains them. Every single malicious request results in a cache miss and penetrates directly to the database.
2. **Bloom Filter Solution**:
   - All valid product IDs are added to a Bloom filter in memory.
   - When a request arrives, check the Bloom filter first. If the filter returns `false`, the item definitively does not exist in the database—reject immediately with HTTP 404 without querying cache or DB.
   - If it returns `true` (valid or rare false positive), query cache/DB. A 1% false positive rate still blocks 99% of attack traffic!

---

### Solution 5: Cache Avalanche Prevention
1. **Failure Scenario**: Setting identical 24-hour TTLs causes all cached keys to expire simultaneously at the exact same second. When this happens, massive traffic surges hit the database all at once.
2. **Fix (TTL Jitter)**:
   Add random jitter to the expiration timestamp:
   ```python
   base_ttl = 86400 # 24 hours
   jitter = random.randint(-3600, 3600) # +/- 1 hour
   redis.set(key, value, ex=base_ttl + jitter)
   ```
