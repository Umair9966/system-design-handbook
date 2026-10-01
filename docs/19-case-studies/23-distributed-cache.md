# Design a Distributed Cache System (Redis Cluster / Memcached)

A high-performance in-memory caching cluster providing sub-millisecond key-value operations, consistent hashing distribution, automated failover, and memory eviction policies.

```mermaid
graph TD
    Client[Application Client] --> HashRing[Client Consistent Hash Ring]
    HashRing --> Node1[Cache Shard 1 (Master)]
    HashRing --> Node2[Cache Shard 2 (Master)]
    HashRing --> Node3[Cache Shard 3 (Master)]

    Node1 -.->|Async Replication| Replica1[Shard 1 Replica]
    Node2 -.->|Async Replication| Replica2[Shard 2 Replica]
    Node3 -.->|Async Replication| Replica3[Shard 3 Replica]

    Consensus[Sentinel / Raft Supervisor] --> Node1
    Consensus --> Node2
    Consensus --> Node3
```

---

## 1. Requirements

### Functional Requirements:
1. `get(key)` and `set(key, value, ttl)`.
2. Support eviction algorithms: LRU, LFU, FIFO.
3. Automated key expiration via TTLs.

### Non-Functional Requirements:
- **Sub-Millisecond Latency**: p99 $< 1	ext{ms}$.
- **Horizontal Scalability**: Add or remove cache nodes dynamically with minimal cache misses.
- **High Availability**: Automated replica promotion on node failure.

---

## 2. Consistent Hashing with Virtual Nodes

Keys are mapped to a 32-bit integer ring ($0$ to $2^{32}-1$):
- Each physical node is assigned 256 virtual positions on the ring (`Hash("node1#1")`, `Hash("node1#2")`).
- When a new cache node is added, it claims keys only from its immediate clockwise neighbors, avoiding full cluster cache flushes.

---

## 3. Memory Eviction: Approximated LRU in Redis

Tracking true global LRU across 100 Million keys requires double-linked list pointers that consume excessive RAM (16 bytes per key).
- **Redis Approximated LRU**: Samples 5 random keys, inspects their idle times, and evicts the oldest key among the sample. At sample size 10, performance is mathematically indistinguishable from true LRU at zero memory overhead!

---

## 4. Key Takeaways

- Distribute cache keys using Consistent Hashing with virtual nodes.
- Use Approximated LRU sampling to save memory overhead.
- Employ Master-Replica pairs with automated failover (Redis Sentinel / Cluster gossip).
