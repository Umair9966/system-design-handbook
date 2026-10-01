import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\19-case-studies"

studies = {
    "22-log-aggregation-system.md": """# Design a Distributed Log Aggregation System (ELK / Loki)

A high-throughput distributed log collection, indexing, and search architecture capable of ingesting tens of terabytes of log data daily across thousands of microservice containers with near real-time searchability.

```mermaid
graph TD
    AppPods[Application Containers: Pods 1..N] -->|stdout / stderr| Daemon[Fluentbit / Vector DaemonSet]
    Daemon -->|HTTP / OTLP Batch| Kafka[Kafka Log Stream]
    
    Kafka --> LogIngester[Log Ingestion Worker Pool]
    LogIngester --> S3[(Object Store: Raw Log Chunks S3)]
    LogIngester --> Indexer[(Distributed Indexer: Loki / OpenSearch)]
    
    Grafana[Grafana / OpenSearch Dashboards] --> Indexer
```

---

## 1. Requirements

### Functional Requirements:
1. Ingest logs from thousands of distributed application servers.
2. Support structured JSON and unstructured text parsing.
3. Full-text search with regex and label filtering (`app=order AND level=ERROR`).
4. Automated retention and lifecycle tiering (purge after 30 days).

### Non-Functional Requirements:
- **Zero Loss of Critical Logs**: Buffered against network partitions.
- **Cost Efficiency**: Minimize indexing storage overhead (Grafana Loki approach).
- **Search Latency**: Sub-second search for recent 1-hour logs.

---

## 2. OpenSearch vs Grafana Loki: The Indexing Trade-off

| Dimension | OpenSearch / Elasticsearch | Grafana Loki |
| :--- | :--- | :--- |
| **Indexing Strategy** | Full-text Inverted Index on every word | **Indexes metadata labels ONLY**; greps compressed chunks |
| **Index Size** | 100% - 150% of raw data size | **< 5% of raw data size** |
| **Storage Backend** | Costly local NVMe disks | Direct cheap **AWS S3 Object Storage** |
| **Ingestion Speed** | Moderate (heavy CPU for indexing) | Blazing fast (just writes compressed chunks) |
| **Best For** | Ad-hoc text search across billions of docs | High-volume Kubernetes container logs |

---

## 3. Key Takeaways

- Use lightweight agents (Vector / Fluentbit) as DaemonSets on every Kubernetes node.
- Buffer incoming log streams via Kafka to prevent log drops during traffic surges.
- Choose Loki's label-only indexing pattern to cut log storage infrastructure costs by 80%.
""",

    "23-distributed-cache.md": """# Design a Distributed Cache System (Redis Cluster / Memcached)

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
- **Sub-Millisecond Latency**: p99 $< 1\text{ms}$.
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
""",

    "24-real-time-leaderboard.md": """# Design a Real-Time Gaming Leaderboard (Redis Sorted Sets)

A real-time competitive gaming leaderboard capable of updating player scores and calculating global ranks among 25 Million active players within 10ms.

```mermaid
graph TD
    GameClient[Game Server] -->|POST /score/submit {user: 42, score: 980}| API[Leaderboard Service]
    API --> Redis[(Redis Cluster: Sorted Sets - ZSET)]
    API --> ArchivalDB[(PostgreSQL / Snowflake: Season History)]
    
    Viewer[Player Profile View] -->|GET /leaderboard/top10| API
    Viewer -->|GET /users/42/rank| API
```

---

## 1. Requirements

### Functional Requirements:
1. Update player score: `updateScore(userId, scoreDelta)`.
2. Get player's current global rank (e.g., "Rank #1,402 out of 10,000,000").
3. Get Top 10 / Top 100 global leaderboard.
4. Get surrounding leaderboard (e.g., 5 players above and 5 players below me).

### Non-Functional Requirements:
- **Ultra-Low Latency**: Rank calculation and updates $< 15\text{ms}$.
- **Massive Scale**: 25 Million registered players.
- **Real-Time Accuracy**: Zero delay in rank updates.

---

## 2. Data Structure: Redis Sorted Sets (SkipList + Hash Table)

Redis `ZSET` natively solves real-time leaderboards:
- **Hash Table**: Maps `user_id` $\to$ `score` in $O(1)$ time.
- **SkipList**: Maintains elements sorted by score in $O(\log N)$ time.

```
-- Update player score: O(log N)
ZINCRBY leaderboard:season_1 150 "user_42"

-- Get global rank: O(log N)
ZREVRANK leaderboard:season_1 "user_42"

-- Fetch Top 10 players: O(log N + M)
ZREVRANGE leaderboard:season_1 0 9 WITHSCORES

-- Fetch 5 players above and below user:
ZREVRANGE leaderboard:season_1 [Rank-5] [Rank+5] WITHSCORES
```

---

## 3. Sharding a Massive Leaderboard Across Shards

When a single Redis instance cannot fit all players:
- **Score-Range Partitioning**: Shard 1 holds scores 0-1,000; Shard 2 holds 1,001-5,000; Shard 3 holds 5,001-10,000.
- Calculating global rank: Sum the count of all players in higher score shards, then add the local rank within the player's shard.

---

## 4. Key Takeaways

- Redis Sorted Sets (`ZSET`) provide native $O(\log N)$ score updates and rank lookups.
- For multi-million player leaderboards, partition shards by score ranges to calculate global ranks accurately.
""",

    "25-collaborative-document-editor.md": """# Design a Real-Time Collaborative Document Editor (Google Docs / Notion)

A real-time rich-text document editing platform allowing multiple concurrent users to edit the same document simultaneously with offline synchronization, presence cursors, and conflict-free text merging.

```mermaid
graph TD
    ClientA[User A (Browser)] <-->|WebSocket: Local CRDT Edits| WS_GW[WebSocket Gateway]
    ClientB[User B (Browser)] <-->|WebSocket: Local CRDT Edits| WS_GW

    WS_GW --> DocSvc[Document Session Coordinator]
    DocSvc <--> Redis[(Redis: Ephemeral State & Presence)]
    DocSvc --> SnapshotWorker[Document Snapshot Worker]
    SnapshotWorker --> DocDB[(Document Store: MongoDB / S3)]
```

---

## 1. Requirements

### Functional Requirements:
1. Multi-user concurrent text and block editing.
2. Character-by-character real-time synchronization.
3. Show live user cursors and text selections.
4. Offline editing with automatic conflict resolution upon reconnect.

### Non-Functional Requirements:
- **Low Latency**: Peer edit synchronization $< 50\text{ms}$.
- **Consistency**: All concurrent users eventually converge on the exact identical document text.
- **Fault Tolerance**: No lost keystrokes during network drops.

---

## 2. CRDTs: Yjs / Automerge vs Operational Transformation

```mermaid
graph TD
    subgraph "CRDT Character Model (Fractional Indexing)"
        Char1["'H' (Pos: 0.5)"]
        Char2["'e' (Pos: 0.75)"]
        Char3["'l' (Pos: 0.875)"]
        Char4["'o' (Pos: 0.9375)"]
        Note over Char2,Char3: User inserts 'l' between 'e' and 'l':<br/>Assigned Pos: 0.8125! Zero index shifts!
    end
```

### Why Modern Systems Prefer CRDTs:
- Characters receive immutable fractional identifiers rather than array indices.
- Inserting a letter in the middle of a paragraph does not alter the coordinate IDs of subsequent characters.
- Merges are commutative and associative; clients can sync peer-to-peer without waiting for a central master server.

---

## 3. Key Takeaways

- Adopt CRDTs (such as Yjs or Automerge) for modern offline-first real-time collaboration.
- Track real-time presence (cursor position, selection) as ephemeral volatile state in Redis.
- Persist periodic document snapshots to object storage (S3) to avoid replaying millions of granular keystroke operations on load.
""",

    "26-online-code-judge.md": """# Design an Online Code Judge (LeetCode / HackerRank)

A secure, isolated code execution and grading engine capable of compiling, running, and benchmarking arbitrary untrusted user code (Python, C++, Java, Rust) against hidden test suites with strict CPU, memory, and security sandboxing.

```mermaid
graph TD
    User[Student / Candidate] --> API[Submission API]
    API --> MetaDB[(Submissions DB: PostgreSQL)]
    API --> Queue[Kafka / SQS Job Queue]
    
    Queue --> JudgeWorker[Judge Coordinator Worker]
    JudgeWorker --> Sandbox[Isolated Linux Sandbox: gVisor / Firecracker / Docker]
    
    Sandbox -->|Executes Code against Test Cases| TestCases[(Test Case Store: S3)]
    Sandbox --> JudgeWorker
    JudgeWorker --> ResultStore[(Results: Accepted / TLE / Memory Limit)]
```

---

## 1. Requirements

### Functional Requirements:
1. Submit code in multiple languages (Python, Java, C++, Go).
2. Execute code against hidden test cases.
3. Return grading status: Accepted (AC), Wrong Answer (WA), Time Limit Exceeded (TLE), Memory Limit Exceeded (MLE), Runtime Error (RE).
4. Measure exact execution runtime and memory usage.

### Non-Functional Requirements:
- **Security**: **Untrusted user code must NEVER escape the sandbox or access internal cloud networks**.
- **Fairness & Determinism**: Consistent execution timing across runs.
- **High Throughput**: Handle 1,000 concurrent submissions during coding competitions.

---

## 2. Sandboxing Architecture: Preventing Remote Code Execution (RCE)

Running arbitrary user code (`os.system("rm -rf /")` or `curl 169.254.169.254`) on a host VM is dangerous.

```mermaid
graph LR
    UserCode[Untrusted User Code] --> Cgroups[Linux Cgroups: Hard CPU & RAM Limits]
    Cgroups --> Seccomp[Seccomp: Blocks Network & Fork Syscalls]
    Seccomp --> MicroVM[gVisor / Firecracker MicroVM: User-Space Kernel Isolation]
    MicroVM --> HostOS[Host Linux OS (Protected!)]
```

### Security Layers:
1. **Linux Cgroups v2**: Enforces strict memory caps (e.g., 256MB) and CPU quotas (e.g., 1 CPU core).
2. **Seccomp Filters**: Whitelists only safe syscalls (`read`, `write`, `exit`). **Blocks network sockets (`socket`, `connect`) and process forks (`fork`, `clone`) to prevent fork bombs**.
3. **gVisor (Google)**: Intercepts all syscalls in a user-space sandbox, protecting the host Linux kernel from kernel privilege escalation exploits.

---

## 3. Key Takeaways

- Execute untrusted code inside multi-layered sandboxes (cgroups + seccomp + gVisor/Firecracker).
- Block all network access at the kernel socket layer to prevent SSRF and external attacks.
- Decouple code submission from grading execution using asynchronous message queues.
""",

    "27-proximity-service.md": """# Design a Proximity Service (Yelp / Google Places Nearby)

A location-based search service capable of finding nearby points of interest (restaurants, gas stations, ATMs) within a specified radius (e.g., "Find all Italian restaurants within 2 km of my location") with sub-50ms latency.

```mermaid
graph TD
    User[User Mobile App: Lat 37.77, Lng -122.41] --> API[Proximity Query Gateway]
    API --> GeohashCalc[Geohash / Quadtree Converter]
    GeohashCalc --> GeoCache[(Geospatial Cache: Redis GEO / Memory)]
    GeoCache --> PlaceDB[(Places Database: PostgreSQL + PostGIS)]
    
    PlaceDB --> S3[(Place Photos & Reviews Store)]
```

---

## 1. Requirements

### Functional Requirements:
1. Add, update, and delete places of interest (restaurants, bars, stores).
2. Given a latitude, longitude, and radius, return all matching places within the radius.
3. Filter by category, price, and customer rating.

### Non-Functional Requirements:
- **Low Latency**: Nearby search $< 50\text{ms}$.
- **High Read Scale**: 100:1 read-to-write ratio (places rarely move; users constantly search).
- **High Availability**: 99.99%.

---

## 2. Geospatial Indexing: Geohashes vs PostGIS

```mermaid
graph TD
    subgraph "Geohash Precision Hierarchy"
        G4["Geohash Length 4: ~39km x ~19km (City Level)"]
        G5["Geohash Length 5: ~4.9km x ~4.9km (Neighborhood Level)"]
        G6["Geohash Length 6: ~1.2km x ~0.6km (Street Level - Optimal!)"]
    end
```

### Radius Query Mechanics:
1. Convert user's latitude/longitude to a **6-character Geohash** (e.g., `9q8yyk`).
2. Calculate the **8 surrounding neighboring geohash cells** to eliminate boundary miss edge cases.
3. Query database or Redis using fast prefix matching:
   ```sql
   SELECT place_id, name, lat, lng 
   FROM places 
   WHERE geohash_prefix IN ('9q8yyk', '9q8yym', ...);
   ```
4. Filter matching candidates in memory using the Haversine distance formula.

---

## 3. Key Takeaways

- Geohash prefix matching reduces 2D geospatial searches to simple 1D database index range scans.
- Always query the target cell plus its 8 immediate neighboring cells to avoid edge boundary misses.
- Cache neighborhood query results at edge CDNs and in Redis to absorb 95% of read traffic.
""",

    "28-video-conferencing-system.md": """# Design a Real-Time Video Conferencing Platform (Zoom / Google Meet)

A low-latency, multi-party video conferencing architecture supporting 1,000+ participants per call, screen sharing, audio/video mixing, and adaptive bitrate encoding with sub-200ms glass-to-glass latency.

```mermaid
graph TD
    Participant1[Participant 1] -->|WebRTC UDP: SRTP Video/Audio| SFU[Selective Forwarding Unit - SFU]
    Participant2[Participant 2] -->|WebRTC UDP: SRTP Video/Audio| SFU
    Participant3[Participant 3] -->|WebRTC UDP: SRTP Video/Audio| SFU

    SFU --> Transcoder[Simulcast Quality Controller]
    
    SignalingSvc[Signaling Service: WebSocket SDP & ICE] <--> Participant1
    SignalingSvc <--> Participant2
    SignalingSvc <--> SFU
```

---

## 1. Requirements

### Functional Requirements:
1. Multi-party real-time audio and video calls (up to 1,000 participants).
2. Screen sharing and real-time text chat.
3. Call recording and cloud storage.

### Non-Functional Requirements:
- **Ultra-Low Latency**: End-to-end glass-to-glass latency $< 150\text{ms}$.
- **Adaptive Quality**: Smooth video playback across unstable cellular connections.
- **Resilience**: Handle 15% network packet loss without audio breakup.

---

## 2. Media Routing Topologies: Mesh vs MCU vs SFU

```mermaid
graph TD
    subgraph "1. Mesh (P2P - Max 4 Participants)"
        M1[Client A] <--> M2[Client B]
        M1 <--> M3[Client C]
        M2 <--> M3
        Note over M1: O(N^2) bandwidth! Saturates client upload.
    end

    subgraph "2. SFU (Selective Forwarding Unit - Zoom Standard)"
        C1[Client 1] -->|1 Upload| SFU_Node[SFU Media Server]
        C2[Client 2] -->|1 Upload| SFU_Node
        SFU_Node -->|Forwards Streams| C1
        SFU_Node -->|Forwards Streams| C2
        Note over SFU_Node: Zero transcoding CPU! Routes raw UDP packets directly!
    end
```

### Why the Industry Standard is SFU:
- **Multipoint Control Unit (MCU)**: Decodes and mixes all video streams into a single composite video on the server. Consumes massive CPU and introduces 200ms+ latency.
- **Selective Forwarding Unit (SFU)**: Receives video streams from each client and selectively forwards them to other participants without decoding or re-encoding. Server CPU remains low, and latency is $< 30\text{ms}$!

---

## 3. Simulcast for Dynamic Bandwidth Adaptation

Each client encodes video into **3 simultaneous resolutions** (e.g., 720p, 360p, 180p):
- The SFU intelligently forwards the **720p stream** for the active speaker.
- The SFU forwards **180p thumbnail streams** for the other 25 participants in gallery view.
- If a mobile user enters a poor connection, the SFU automatically downgrades their incoming stream to 180p without impacting other callers.

---

## 4. Key Takeaways

- Standardize on WebSockets for Signaling (SDP/ICE negotiation) and WebRTC over UDP for Media transport.
- Use Selective Forwarding Units (SFUs) to support multi-party video conferencing without server transcoding bottlenecks.
- Implement Simulcast so clients receive high-resolution feeds only for the active speaker.
"""
}

for fname, content in studies.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Case Studies Batch 4 complete.")
