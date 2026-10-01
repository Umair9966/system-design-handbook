import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\19-case-studies"

studies = {
    "08-chat-messaging-app.md": """# Design a Real-Time Chat Messaging App (WhatsApp / Slack)

A real-time, end-to-end encrypted messaging service serving 500+ million daily active users, delivering one-on-one chats, group chats, message delivery receipts, and media attachments with sub-100ms latency.

```mermaid
graph TD
    ClientA[Sender Client] -->|WSS / TLS| WS_GW1[WebSocket Gateway 1]
    ClientB[Receiver Client] -->|WSS / TLS| WS_GW2[WebSocket Gateway 2]

    WS_GW1 --> ChatSvc[Chat Routing Service]
    ChatSvc --> Kafka[Kafka Message Ingestion Stream]
    Kafka --> MsgWorker[Message Persister Worker]
    MsgWorker --> MsgDB[(Message Store: Cassandra / ScyllaDB)]
    
    ChatSvc --> Redis[(Redis Session Table: User -> Gateway IP)]
    ChatSvc --> PushSvc[Push Notification Service: APNs / FCM]

    Redis -.->|Receiver on Gateway 2| WS_GW2
```

---

## 1. Requirements

### Functional Requirements:
1. One-on-one real-time text chat.
2. Group chats (up to 1,000 members).
3. Online/offline presence and typing indicators.
4. Message status receipts: Sent (1 check), Delivered (2 checks), Read (2 blue checks).
5. Media message sharing (images, videos, documents).

### Non-Functional Requirements:
- **Low Latency**: Message delivery p99 $< 100\text{ms}$.
- **High Availability**: 99.99% availability.
- **Message Ordering**: Strict per-chat causal message ordering.
- **Offline Support**: Undelivered messages buffered until recipient reconnects.

---

## 2. Capacity Estimation & Back-of-the-Envelope Math

- **Daily Active Users (DAU)**: 500 Million users.
- **Average Messages**: 40 messages per user per day $\implies \mathbf{20\text{ Billion messages/day}}$.
- **Write QPS**: $\frac{20,000,000,000}{86,400} \approx \mathbf{230,000\text{ messages/sec}}$ (Peak: $500,000\text{ msg/sec}$).
- **Storage Sizing (5 Years)**:
  - Average text message: 100 bytes (plus metadata: 60 bytes = 160B).
  - Daily Text Storage = $20\text{B} \times 160\text{B} = \mathbf{3.2\text{ TB/day}}$.
  - 5-Year Storage = $3.2\text{ TB} \times 365 \times 5 \approx \mathbf{5.84\text{ Petabytes}}$.
  - Requires wide-column horizontally partitioned storage (**Apache Cassandra / ScyllaDB**).

---

## 3. Database Schema (Apache Cassandra)

```sql
-- Partitioned by chat_id so all messages in a conversation are on the same node
CREATE TABLE messages (
    chat_id UUID,
    message_id TIMEUUID, -- Snowflake or TimeUUID guarantees chronological ordering
    sender_id UUID,
    content TEXT,
    media_url TEXT,
    status VARCHAR(16), -- 'SENT', 'DELIVERED', 'READ'
    created_at TIMESTAMP,
    PRIMARY KEY (chat_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
```

---

## 4. Deep Dive: Group Chat Fanout at Scale

In a group chat with 500 members, when 1 person sends a message, should the system duplicate the message 500 times?

```mermaid
graph TD
    subgraph "Small Groups (< 100 members): Fanout-on-Write"
        Sender1[Sender] --> GW1[Gateway]
        GW1 --> Copy[Deliver copies to all 99 member inboxes]
    end

    subgraph "Large Groups / Channels (Slack / Discord - Fanout-on-Read)"
        Sender2[Sender] --> GW2[Gateway]
        GW2 --> SingleMsg[(Single Group Channel Message Table)]
        SingleMsg -.-> Members[Members read directly from group stream]
    end
```

---

## 5. Key Takeaways

- Terminate persistent WebSocket connections at dedicated gateway clusters.
- Store messages in Apache Cassandra clustered by `TIMEUUID` for fast sequential pagination.
- Buffer offline messages in distributed queues, falling back to Apple APNs / Firebase FCM push notifications.
""",

    "09-news-feed-timeline.md": """# Design a Social Media News Feed (Facebook / Instagram)

A scalable social network news feed system delivering personalized, chronologically and algorithmically ranked feeds to 1 Billion users with sub-200ms latency.

```mermaid
graph TD
    Client[User App] --> CDN[Edge CDN]
    CDN --> LB[L7 Load Balancer]
    LB --> GW[API Gateway]

    subgraph Feed Publishing (Write Path)
        GW --> PostSvc[Post Service]
        PostSvc --> PostDB[(Post DB: PostgreSQL / Cassandra)]
        PostSvc --> FanoutWorker[Fanout Worker Pool]
        FanoutWorker --> FollowerCache[(Follower Timelines: Redis Cluster)]
    end

    subgraph Feed Reading (Read Path)
        GW --> FeedSvc[Feed Generation Service]
        FeedSvc --> FollowerCache
        FeedSvc --> Ranker[ML Ranking Engine]
        Ranker --> CDN
    end
```

---

## 1. Requirements

### Functional Requirements:
1. Users can post content (text, images, video links).
2. Users have a personalized News Feed showing updates from friends, pages, and followed creators.
3. Feeds are ranked using relevance algorithms (recency, engagement, relationships).
4. Pagination: Infinite scroll feed loading 20 items per batch.

### Non-Functional Requirements:
- **Feed Generation Latency**: p99 $< 200\text{ms}$.
- **Availability**: 99.99%.
- **Scale**: 500M DAU reading feeds 5 times per day.

---

## 2. Capacity & Fanout Sizing

- **DAU**: 500 Million.
- **Feed Views/Day**: $500\text{M} \times 5 = 2.5\text{ Billion feed loads/day}$.
- **Read QPS**: $\frac{2,500,000,000}{86,400} \approx \mathbf{30,000\text{ QPS}}$ (Peak: $60,000\text{ QPS}$).
- **Posts/Day**: 100 Million posts/day $\implies \mathbf{1,200\text{ write QPS}}$.

### The Fanout Hybrid Strategy:
```mermaid
graph LR
    Post[New Post Published] --> Check{Is Author a Celebrity? (>50K followers)}
    Check -->|No: Normal User| Push[Fanout-on-Write: Push PostID into all follower Redis lists]
    Check -->|Yes: Celebrity| Pull[Fanout-on-Read: Store in Celebrity Post List only]
    
    User[Follower Reads Feed] --> Merge[Timeline Service merges Redis list + Celebrity posts in RAM]
```

---

## 3. Feed Cache Structure (Redis Sorted Sets)

Store timeline feeds as Redis Sorted Sets (`ZSET`), where the **member** is `post_id` and the **score** is `timestamp` (or ranking score):
```
ZADD timeline:user_123 1696156800 post_9981
ZREVRANGEBYSCORE timeline:user_123 +inf -inf LIMIT 0 20
```

---

## 4. Key Takeaways

- Implement a Hybrid Fanout architecture: Fanout-on-Write for normal users, Fanout-on-Read for celebrities.
- Use Redis Sorted Sets (`ZSET`) keyed by `user_id` for instant pagination retrieval.
- Separate post content storage (S3 + DB) from feed index pointers (Redis).
""",

    "10-social-network-graph.md": """# Design a Social Network Graph (LinkedIn / Facebook Connections)

A graph storage and query system capable of managing 1 Billion users and 100+ Billion connection edges, executing fast $N$-degree separation searches ("People You May Know", mutual friends, company coworker graphs) within 50ms.

```mermaid
graph TD
    Client[Web / Mobile Client] --> GW[API Gateway]
    GW --> GraphAPI[Graph Query Service]
    GraphAPI --> Cache[(Graph In-Memory Cache: TAO / Redis)]
    GraphAPI --> GraphDB[(Distributed Graph DB: Neo4j / AWS Neptune)]
    
    GraphAPI --> BiBFS[Bidirectional BFS Search Engine]
```

---

## 1. Requirements

### Functional Requirements:
1. Add friend / follow relationship (directed or undirected graph edge).
2. Calculate mutual friends between two users.
3. Find shortest connection path (Degrees of Separation: 1st, 2nd, 3rd degree).
4. "People You May Know" (PYMK) recommendation queries.

### Non-Functional Requirements:
- **Low Latency**: 2nd degree query $< 30\text{ms}$.
- **Scale**: 1 Billion vertices, 100 Billion edges.
- **Eventual Consistency**: Friend graph updates replicate within 1-2 seconds.

---

## 2. Graph Algorithms: Bidirectional BFS for Degrees of Separation

Finding the shortest path between User A and User B:
- **Standard BFS**: Searches outward from User A. If branching factor $B \approx 100$, degree 3 explores $100^3 = \mathbf{1,000,000\text{ nodes}}$.
- **Bidirectional BFS**: Simultaneously searches forward from User A and backward from User B:
  $$2 \times 100^{1.5} \approx \mathbf{2,000\text{ nodes explored}}$$
  *(500x speedup with dramatically lower memory usage!).*

```mermaid
graph LR
    subgraph Forward Search from User A
        A[User A] --> F1[100 Friends]
        F1 --> F2[10,000 2nd Degree]
    end

    subgraph Intersection Frontier
        F2 <--> Intersection[Common Intersection Node Found!] <--> B2
    end

    subgraph Backward Search from User B
        B[User B] --> B1[100 Friends]
        B1 --> B2[10,000 2nd Degree]
    end
```

---

## 3. Storage Architecture: Meta's TAO Pattern

Relational databases fail at recursive graph traversal (`JOIN` recursion). Meta developed **TAO**:
- **Objects (Nodes)**: Typed entities (User, Page, Photo).
- **Assocs (Edges)**: Directed, timestamped relations (`(User_A, friend, User_B)`).
- **Two-Tier Cache**: Fast in-memory cache sitting in front of sharded MySQL storage.

---

## 4. Key Takeaways

- Use Bidirectional BFS to find shortest paths between graph nodes in milliseconds.
- Model graph relations as Objects and Associations (TAO model).
- Cache adjacency lists in Redis sets (`SMEMBERS`, `SINTER` for mutual friends).
""",

    "11-video-streaming-platform.md": """# Design a Global Video Streaming Platform (YouTube / Netflix)

A petabyte-scale video platform supporting user video uploads, asynchronous distributed transcoding into multi-bitrate profiles, global CDN edge caching, and adaptive bitrate streaming (HLS/DASH).

```mermaid
graph TD
    Creator[Content Creator] --> UploadGW[Upload Gateway]
    UploadGW --> RawS3[(Raw Video Bucket: S3)]
    RawS3 --> Kafka[Upload Event Topic]
    
    Kafka --> TranscodeMgr[Transcoding Pipeline Coordinator]
    TranscodeMgr --> WorkerPool[Distributed GPU Transcoder Nodes]
    WorkerPool --> TranscodeS3[(Packaged HLS Chunks S3)]
    
    TranscodeS3 --> CDN[Global CDN: Cloudflare / Fastly]
    CDN --> Viewer[Viewer Video Player (Adaptive Bitrate)]
```

---

## 1. Requirements

### Functional Requirements:
1. Video Upload: Creators can upload high-resolution videos (up to 4K, 50GB).
2. Video Transcoding: Automatically transcode source into multiple resolutions (1080p, 720p, 480p, 360p) in H.264/AV1.
3. Adaptive Bitrate Streaming: Client video player adjusts resolution dynamically based on network bandwidth.
4. Video Metadata & Search: Title, description, tags, view count.

### Non-Functional Requirements:
- **Zero Buffering**: Instant video start time ($< 1\text{ second}$).
- **Global Scale**: 100+ Million concurrent video streams globally.
- **High Durability**: Uploaded master videos must never be corrupted.

---

## 2. Video Processing Pipeline: Chunk-Based Transcoding

Transcoding a 2-hour 4K video as a single monolithic file on one server takes hours and fails completely if the server crashes at 98%.

```mermaid
graph LR
    Master[Uploaded 4K Video] --> Split[Splitter: Chunks into 10-second segments]
    Split --> Q[SQS Job Queue]
    Q --> W1[Worker 1: Transcodes Chunk 0-10s to 1080p/720p/360p]
    Q --> W2[Worker 2: Transcodes Chunk 10-20s to 1080p/720p/360p]
    Q --> WN[Worker N: Transcodes Chunk N]
    W1 --> Assembler[Packager: Generates HLS .m3u8 Playlist]
    W2 --> Assembler
    Assembler --> OutS3[(S3 Final Storage)]
```

---

## 3. CDN Caching Strategy for Video Chunks

Video files are immutable and read-heavy:
- 10-second `.ts` or `.m4s` video segments are aggressively cached at edge CDN locations with `Cache-Control: public, max-age=31536000`.
- 99% of video streaming bandwidth is absorbed by edge CDNs; origin S3 storage serves only the initial cache-fill requests.

---

## 4. Key Takeaways

- Chunk video uploads using S3 Multipart Upload and split videos into 10-second segments for parallel transcoding.
- Package videos using HLS/DASH for client-side Adaptive Bitrate (ABR) streaming.
- Offload 99% of bandwidth delivery to edge CDNs with immutable segment URLs.
""",

    "12-file-storage-and-sync.md": """# Design a Cloud File Storage and Sync Service (Dropbox / Google Drive)

A distributed file synchronization and storage service supporting cross-device synchronization, chunk-level deduplication, delta syncing, and offline editing.

```mermaid
graph TD
    ClientApp[Desktop / Mobile Sync Client] --> SyncAPI[Sync Gateway Service]
    SyncAPI --> BlockSvc[Block Storage Service]
    SyncAPI --> MetaSvc[Metadata Service]

    BlockSvc --> S3[(Encrypted Chunks Store: S3)]
    MetaSvc --> MetaDB[(Metadata Store: CockroachDB)]
    
    SyncAPI --> Notification[Notification Service: Long-Polling / WebSockets]
    Notification --> RemoteClient[Other Paired Devices]
```

---

## 1. Requirements

### Functional Requirements:
1. Users can upload, download, and sync files across desktop and mobile devices.
2. Delta Sync: When a file is modified, upload only changed chunks—not the entire file.
3. Offline Editing: Users can edit files offline; conflicts resolved upon reconnecting.
4. File versioning and rollback history (30-day version recovery).

### Non-Functional Requirements:
- **Efficiency**: Minimize network bandwidth consumption via block-level deduplication.
- **Strong Consistency**: File metadata must reflect the latest state across devices.
- **Data Durability**: 99.999999999% durability for stored files.

---

## 2. Chunking and Delta Synchronization

Files are divided into 4MB chunks (or variable-size chunks using Rabin Fingerprinting):

```mermaid
graph TD
    File[Original File: 16 MB] --> C1[Chunk 1 (4MB): Hash A]
    File --> C2[Chunk 2 (4MB): Hash B]
    File --> C3[Chunk 3 (4MB): Hash C]
    File --> C4[Chunk 4 (4MB): Hash D]

    UserEdits[User edits 1 sentence in Chunk 3] --> NewFile[Modified File]
    NewFile --> NC1[Chunk 1: Hash A - Unchanged]
    NewFile --> NC2[Chunk 2: Hash B - Unchanged]
    NewFile --> NC3[Chunk 3: Hash E - MODIFIED!]
    NewFile --> NC4[Chunk 4: Hash D - Unchanged]

    Note over NC3: Client uploads ONLY Chunk 3 (4MB)! Saves 12MB of bandwidth!
```

---

## 3. Metadata Schema (CockroachDB)

```sql
CREATE TABLE file_metadata (
    file_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    path TEXT NOT NULL,
    version INT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE file_blocks (
    file_id UUID,
    block_index INT,
    block_hash VARCHAR(64) NOT NULL, -- SHA-256
    size_bytes INT NOT NULL,
    PRIMARY KEY (file_id, block_index)
);
```

---

## 4. Key Takeaways

- Chunk files into 4MB blocks to support delta sync and client-side deduplication.
- Decouple metadata synchronization (relational CockroachDB) from binary chunk transport (S3).
- Notify paired devices of remote file changes in real time via persistent notification channels.
""",

    "13-ride-hailing-service.md": """# Design a Ride-Hailing Platform (Uber / Lyft)

A real-time geospatial dispatch and location-tracking system capable of tracking millions of active drivers, matching riders to nearby drivers, dynamic surge pricing, and trip routing.

```mermaid
graph TD
    Driver[Driver App] -->|WebSocket: Lat/Lng every 4s| LocationGW[Location Ingress Gateway]
    LocationGW --> GeoCache[(Geospatial Cache: Redis / Uber H3 Grid)]
    
    Rider[Rider App] -->|POST /rides/request| RideSvc[Ride Matching Service]
    RideSvc --> GeoCache
    RideSvc --> DispatchEngine[Dispatch & Route Optimizer]
    DispatchEngine --> MatchQueue[Driver Notification Engine]
    MatchQueue --> Driver
```

---

## 1. Requirements

### Functional Requirements:
1. Real-time driver location updates (every 4 seconds).
2. Rider requests ride: Find top $K$ nearest available drivers within 3 km.
3. Driver dispatch: Offer ride to selected driver; handle accept/decline timeout (15s).
4. Dynamic Surge Pricing: Increase fares in high-demand, low-supply geographic hexagons.

### Non-Functional Requirements:
- **Low Latency**: Driver search & matching $< 1\text{ second}$.
- **Massive Write QPS**: Ingesting location pings from 2 Million active drivers.
- **High Availability**: Service survives regional outages without stranding in-progress trips.

---

## 2. Geospatial Indexing: Uber H3 Hexagonal Grid

- The world is mapped into **H3 Hexagonal Hierarchical Cells** (Resolution 8 $\approx 460\text{m}$ edge length).
- Every driver's GPS coordinate maps to an `H3Index` (64-bit integer).
- In Redis, active drivers are stored in an in-memory set indexed by Hexagon ID:
  ```
  SADD drivers:hex:882681a339fffff driver_101
  ```
- **Radius Search**: Look up the rider's home hexagon + its 6 immediate neighboring hexagons to find all drivers within seconds!

```mermaid
graph TD
    RiderHex[Rider in Hexagon 0] --> N1[Neighbor Hex 1]
    RiderHex --> N2[Neighbor Hex 2]
    RiderHex --> N3[Neighbor Hex 3]
    RiderHex --> N4[Neighbor Hex 4]
    RiderHex --> N5[Neighbor Hex 5]
    RiderHex --> N6[Neighbor Hex 6]
    Note over RiderHex,N6: All 7 hexagons queried in parallel in Redis in < 2ms!
```

---

## 3. High-Throughput Write Path: Location Buffering

- 2 Million drivers pinging every 4 seconds $\implies \mathbf{500,000\text{ write QPS}}$.
- Writing 500,000 updates directly to disk databases will destroy I/O throughput.
- **Solution**: Keep live driver locations **strictly in RAM (Redis / Memory)**. Only persist trip start, pickup, and completion events to persistent PostgreSQL storage.

---

## 4. Key Takeaways

- Partition geospatial space using Uber H3 hexagonal cells for uniform neighbor distances.
- Store real-time transient location coordinates purely in in-memory caches (Redis).
- Implement a two-phase dispatch state machine with lease timeouts to prevent race conditions between riders claiming the same driver.
""",

    "14-food-delivery-platform.md": """# Design a Food Delivery Platform (DoorDash / UberEats)

A multi-sided marketplace connecting Customers, Restaurants, and Delivery Couriers, coordinating order state transitions, real-time preparation tracking, and courier dispatch.

```mermaid
graph TD
    Customer[Customer App] --> OrderAPI[Order Service]
    OrderAPI --> OrderDB[(Order Database: PostgreSQL)]
    OrderAPI --> KitchenSvc[Restaurant Kitchen Portal]
    KitchenSvc --> CourierDispatch[Courier Dispatch Engine]
    CourierDispatch --> Driver[Courier Mobile App]
```

---

## 1. Requirements

### Functional Requirements:
1. Restaurant menu browsing and cart checkout.
2. Three-sided order lifecycle:
   - Order Placed $\to$ Restaurant Confirms $\to$ Kitchen Preparing $\to$ Courier Dispatched $\to$ Picked Up $\to$ Delivered.
3. Real-time courier GPS tracking for the customer.
4. Estimated Time of Arrival (ETA) calculation.

### Non-Functional Requirements:
- **Consistency**: Zero double-ordering or race conditions on inventory/menu items.
- **Reliability**: Fault-tolerant state machines coordinating multi-actor workflows.
- **Low Latency**: Menu browsing $< 50\text{ms}$; order placement $< 500\text{ms}$.

---

## 2. Order State Machine & Orchestration

The order workflow is modeled as a distributed Saga coordinated by Temporal or AWS Step Functions:

```mermaid
stateDiagram-v2
    [*] --> Placed : Customer checks out
    Placed --> RestaurantConfirmed : Restaurant accepts within 3m
    Placed --> Cancelled : Restaurant rejects / timeout
    RestaurantConfirmed --> Preparing : Kitchen starts cooking
    Preparing --> CourierAssigned : Dispatch assigns driver
    CourierAssigned --> FoodPickedUp : Driver arrives & collects
    FoodPickedUp --> Delivered : Driver confirms delivery
    Delivered --> [*]
```

---

## 3. Real-Time Courier Tracking with Geofencing

- When the courier is within **100 meters** of the restaurant or customer delivery address, an automated **Geofence Event** triggers:
  - Notifies restaurant: *"Courier has arrived outside!"*
  - Notifies customer: *"Driver is approaching your doorstep!"*

---

## 4. Key Takeaways

- Model complex multi-actor order lifecycles using distributed workflow orchestrators (Temporal / Sagas).
- Decouple static restaurant menus (cached in CDN/Redis) from transactional order placement.
- Use automated geofence triggers to streamline handoffs between restaurants, couriers, and customers.
"""
}

for fname, content in studies.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Case Studies Batch 2 complete.")
