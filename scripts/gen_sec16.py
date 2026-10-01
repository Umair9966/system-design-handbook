import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\16-real-time-systems"

files = {
    "01-real-time-communication-architecture.md": """# Real-Time Communication Architecture: WebSockets at Scale

Architecting systems to maintain millions of persistent, bidirectional, low-latency TCP connections (WebSockets) requires solving connection statefulness, edge proxy termination, and distributed message routing.

```mermaid
graph TD
    Client1[Mobile Client A] -->|WSS Persistent TCP| WS1[WebSocket Gateway Pod 1]
    Client2[Web Client B] -->|WSS Persistent TCP| WS2[WebSocket Gateway Pod 2]

    WS1 <--> PubSub[(Redis Pub/Sub / NATS Core)]
    WS2 <--> PubSub

    SessionStore[(Redis Session Table: User -> Pod IP)]
    WS1 -.->|Heartbeat Ping/Pong| SessionStore
    WS2 -.->|Heartbeat Ping/Pong| SessionStore
```

---

## 1. The Stateful Connection Challenge

Unlike stateless HTTP requests where any backend pod can fulfill any request, a WebSocket connection pins the client to a specific server instance for hours or days.

### Scaling Bottlenecks:
1. **File Descriptors (FD Limits)**: Every TCP socket consumes an OS file descriptor. Kernel tuning (`sysctl -w fs.file-max=2097152`, `ulimit -n 1048576`) is mandatory.
2. **RAM per Connection**: A kernel TCP socket buffer and TLS state consumes 4KB - 16KB of RAM. 1 million concurrent connections require $\approx 10\text{GB} - 16\text{GB}$ of pure memory just to maintain idle sockets.
3. **Cross-Server Routing**: When User A (connected to Pod 1) sends a chat message to User B (connected to Pod 2), Pod 1 cannot write to Pod 2's local memory.

---

## 2. Distributed Message Routing with Pub/Sub

To route messages between arbitrary gateway pods:

```mermaid
sequenceDiagram
    autonumber
    participant Alice as Alice (Client)
    participant Pod1 as WebSocket Pod 1
    participant Redis as Redis Cluster / NATS
    participant Pod2 as WebSocket Pod 2
    participant Bob as Bob (Client)

    Alice->>Pod1: Send: {"to": "bob", "text": "Hi Bob!"}
    Pod1->>Redis: PUBLISH channel:user:bob {"from": "alice", "text": "Hi Bob!"}
    Note over Redis: Fanout to all subscribed gateway nodes
    Redis-->>Pod2: Delivers payload (Pod 2 holds active socket for Bob)
    Pod2->>Bob: Push over WebSocket: {"from": "alice", "text": "Hi Bob!"}
```

---

## 3. Connection Lifecycles: Heartbeats and Reconnection Thundering Herds

- **Heartbeats (Ping/Pong)**: Fire every 30-60 seconds. Proxies (AWS ALB, Cloudflare) close idle TCP connections after 60-120 seconds.
- **Thundering Herd on Gateway Restart**: When a gateway node crashes, 50,000 clients attempt to reconnect simultaneously.
  - *Fix*: Mandatory **exponential backoff with full jitter** on client reconnect loops.

---

## 4. Key Takeaways

- Terminate WebSockets at dedicated, lightweight gateway edge clusters.
- Use high-throughput messaging backbones (Redis Pub/Sub, NATS, Kafka) to route messages across connection pods.
- Tune OS kernel file descriptors and socket buffer limits to support 100K+ concurrent connections per server.
""",

    "02-presence-and-status-tracking.md": """# Presence and Status Tracking at Scale (Online / Offline)

Tracking the online/offline presence status of hundreds of millions of users in real time (e.g., WhatsApp, Discord, Slack) requires handling intermittent mobile network drops, heartbeat aggregation, and fanout subscriptions.

```mermaid
graph TD
    Client[Client App] -->|Periodic Heartbeat: Every 30s| PresGW[Presence Ingress Worker]
    PresGW -->|SETEX presence:u123 45 "online"| Redis[(Redis Cluster)]
    Redis -->|Keyspace Expiry Event / Stream| ExpireWorker[Presence Status Broadcaster]
    ExpireWorker -->|Broadcast: User u123 is Offline| Friends[Subscribed Friends & Channels]
```

---

## 1. Heartbeat Model with TTL Expiration

A client cannot be relied upon to send an explicit "I am disconnecting" packet (battery dies, user enters a subway tunnel, app crashes).

### The Ephemeral Key Strategy:
1. Client sends a heartbeat ping every 30 seconds.
2. Ingress writes to Redis with a 45-second Time-To-Live (TTL):
   ```
   SET presence:user_101 "online" EX 45
   ```
3. If the user stays active, subsequent pings refresh the TTL.
4. If no ping arrives for 45 seconds, Redis expires the key, triggering a status update to `offline`.

---

## 2. Discord's Presence Architecture

Discord tracks over 200 million concurrent users across massive voice and text servers:
- **Presence Hash Rings**: Presence state is partitioned across a distributed cluster using consistent hashing on `user_id`.
- **Subscription Fanout Minimization**: If a user joins a 100,000-person server, broadcasting presence changes to all 100,000 users creates catastrophic $O(N^2)$ traffic.
  - *Optimization*: Only push presence updates for users **visible in the client's current scroll viewport** (top 50 users on screen).

---

## 3. Key Takeaways

- Rely on heartbeat timeouts with TTL expiration rather than explicit disconnect messages.
- Viewport-based presence subscriptions are essential to prevent quadratic message fanout storms in large groups.
- Decouple presence tracking from main transactional relational databases using Redis or distributed in-memory actors.
""",

    "03-fanout-architectures.md": """# Fanout Architectures: Push vs Pull (Twitter/X and Instagram)

Delivering new posts, tweets, and notifications to millions of followers requires balancing write amplification against read latency using Fanout-on-Write (Push) and Fanout-on-Read (Pull).

```mermaid
graph TD
    subgraph "1. Fanout-on-Write (Push Model)"
        Author1[Normal User (100 Followers)] --> Post1[Posts Tweet]
        Post1 --> PushWorker[Fanout Worker Pool]
        PushWorker -->|Write tweet ID to 100 follower timelines| Redis1[(Follower Timelines in Redis)]
        Note over Redis1: Reading feed is instant O(1) LRANGE!
    end

    subgraph "2. Fanout-on-Read (Pull Model for Celebrities)"
        Celeb[Celebrity / Elon Musk (150M Followers)] --> Post2[Posts Tweet]
        Post2 --> CelebDB[(Celebrity Posts Table)]
        Note over CelebDB: Zero write amplification!
        Follower[User Opens Feed] --> Merge[Timeline Service]
        Merge -->|Reads user timeline| Redis2[(Redis)]
        Merge -->|Fetches latest celebrity posts & merges on-the-fly| CelebDB
    end
```

---

## 1. Fanout-on-Write (Push Model)

- **How It Works**: When a user posts, a background worker looks up all their followers and inserts the post ID into each follower's timeline cache (Redis sorted set / list).
- **Pros**: Reading the timeline is an ultra-fast $O(1)$ cache hit (`LRANGE timeline:user_id 0 20`).
- **The Celebrity Problem**: If a user has 100 million followers, posting a single tweet generates **100,000,000 Redis write operations**, exhausting worker queues and delaying other users' notifications.

---

## 2. Hybrid Fanout Architecture (The Production Standard)

Modern social platforms use a hybrid model based on follower thresholds:
- **Normal Users (< 25,000 followers)**: Use **Fanout-on-Write (Push)**. When they post, their tweet is immediately pushed into all followers' timeline caches.
- **Celebrities / High-Follower Accounts (> 25,000 followers)**: Use **Fanout-on-Read (Pull)**. When they post, their tweet is written only to their personal post history. When a follower opens their app, the timeline service pulls the cached timeline and merges the latest posts from followed celebrities in-memory!

---

## 3. Key Takeaways

- Pure Push models break down under celebrity accounts (massive write amplification).
- Pure Pull models break down under heavy read traffic ($O(N)$ multi-table queries per feed load).
- Adopt a Hybrid model: Push for regular users, Pull for high-follower celebrity accounts.
""",

    "04-collaborative-editing-ot-and-crdts.md": """# Collaborative Editing: Operational Transformation vs CRDTs

Real-time multi-user collaborative editing (Google Docs, Figma, Notion) allows multiple participants to concurrently modify shared documents without conflict or lost edits.

```mermaid
graph TD
    subgraph "Operational Transformation (OT - Google Docs)"
        ClientA[Client A] -->|Sends Operation: Insert(pos=3, 'x')| CentralServer[Central Master Server]
        ClientB[Client B] -->|Sends Operation: Delete(pos=2)| CentralServer
        Note over CentralServer: Server transforms concurrent operations using global order
    end

    subgraph "CRDTs (Conflict-free Replicated Data Types - Figma / Automerge)"
        NodeA[Peer / Client A] <-->|Peer-to-Peer / Local Edit| NodeB[Peer / Client B]
        Note over NodeA, NodeB: Mathematically guaranteed to converge without any central coordinator!
    end
```

---

## 1. Operational Transformation (OT)

Pioneered by Google Docs:
- Edits are treated as operations: $\text{Insert}(\text{pos}, \text{char})$ or $\text{Delete}(\text{pos})$.
- Requires a **centralized server** that acts as the single source of truth for total ordering.
- If two users submit edits concurrently at the same index, the server transforms operation $B$ against operation $A$ so that both intent and layout remain preserved.

---

## 2. Conflict-free Replicated Data Types (CRDTs)

Modern collaborative systems (Figma, Notion, Apple Notes) prefer CRDTs:
- **No Central Coordinator Required**: Nodes can edit completely offline and merge asynchronously.
- **Mathematical Convergence**: The merge operation is mathematically proven to be **Commutative** ($A \cup B = B \cup A$), **Associative** ($(A \cup B) \cup C = A \cup (B \cup C)$), and **Idempotent** ($A \cup A = A$).
- **Unique Character IDs (RGA / Yjs)**: Characters are assigned fractional indices or unique Lamport IDs rather than array offsets, so insertions never alter the coordinates of existing letters.

---

## 3. Comparison Matrix

| Dimension | Operational Transformation (OT) | CRDTs (Yjs, Automerge) |
| :--- | :--- | :--- |
| **Topology** | Centralized client-server mandatory | Decentralized / P2P / Local-first supported |
| **Offline Editing** | Complex conflict resolution | Native and seamless |
| **Memory Overhead** | Minimal (stores only character array) | Higher (stores tombstones and metadata history) |
| **Pioneered By** | Google Wave, Google Docs | Figma, Apple Notes, Linear |

---

## 4. Key Takeaways

- Use CRDTs (such as Yjs or Automerge) for modern collaborative applications requiring offline support and peer-to-peer sync.
- Use Operational Transformation when a centralized server is already mandatory and client memory footprint must be minimized.
- In CRDTs, never delete items destructively—mark them with tombstones to maintain causal history.
""",

    "05-live-video-streaming-hls-dash.md": """# Live Video Streaming Architecture: HLS, DASH, and WebRTC

Live video distribution spans a strict trade-off between **ultra-low latency** (interactive bidding, gaming) and **massive global scale** (World Cup, Super Bowl).

```mermaid
graph LR
    Source[Camera / Video Feed] --> Encoder[Hardware Encoder / RTMP]
    Encoder --> Transcoder[Transcoding Service: Multi-bitrate H.264/AV1 Chunks]
    Transcoder --> Packager[Packager: HLS (.m3u8 + .ts) / DASH (.mpd + .m4s)]
    Packager --> S3[(Origin Storage / S3)]
    S3 --> CDN[Global CDN Edge: Cloudflare / Akamai]
    CDN --> Viewer1[Viewer Browser (HLS: 6s Latency)]
    CDN --> Viewer2[Viewer TV / Mobile]
```

---

## 1. Comparing Video Streaming Protocols

| Protocol | Transport | Latency | Scalability | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **WebRTC** | UDP (RTP/RTCP) | < 500ms (Sub-second) | Low to Moderate (Expensive peer/relay servers) | Zoom, Google Meet, live auctions, tele-health |
| **Low-Latency HLS (LL-HLS)**| HTTP/2 or HTTP/3 | 1.5s - 3s | High (Standard CDN chunk caching) | Twitch, live sports, live concerts |
| **Standard HLS / DASH** | HTTP/1.1 or HTTP/2 | 6s - 30s | Massive (Millions of viewers via edge CDNs) | Netflix, YouTube Live, broadcast sports |

---

## 2. Adaptive Bitrate Streaming (ABR)

Network bandwidth on mobile devices fluctuates continuously. ABR dynamically adjusts video quality without playback stalling:

```mermaid
graph TD
    Client[Video Player Client] --> Monitor[Bandwidth Estimator]
    Monitor -->|Bandwidth = 15 Mbps| High[Download 1080p Chunk (4 Mbps)]
    Monitor -->|Cellular Drops to 2 Mbps| Med[Download 720p Chunk (1.5 Mbps)]
    Monitor -->|Subway Tunnel: 500 Kbps| Low[Download 360p Chunk (300 Kbps)]
    Note over Client: Video plays continuously with ZERO buffering spinners!
```

---

## 3. Key Takeaways

- Use WebRTC for two-way sub-second interactive video (Zoom, Discord voice).
- Use HLS or DASH for one-to-many broadcast streaming to leverage commodity CDN edge caching.
- Generate multi-bitrate profiles (ABR) during packaging to ensure continuous playback across changing client bandwidth.
""",

    "06-game-networking-and-lag-compensation.md": """# Multiplayer Game Networking: Client Prediction and Lag Compensation

Real-time multiplayer games (FPS, battle royale) operate under stringent physics budgets where network round-trip times (50ms - 150ms) are intolerable without deterministic prediction and server reconciliation.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Local Player Client
    participant Server as Authoritative Game Server
    participant Remote as Remote Opponent

    Client->>Client: 1. Press W -> Predict Move Instantly (Local render: 0ms lag!)
    Client->>Server: 2. Send Input: {InputID: 101, Cmd: MOVE_FORWARD, Timestamp: t=100}
    Note over Server: Server simulates physics at tick rate (64 Hz)
    Server->>Server: Validates movement against collision map
    Server-->>Client: 3. Authoritative State: {AckInputID: 101, Pos: (10, 0, 5)}
    Server-->>Remote: Broadcast Position: (10, 0, 5)
    Note over Client: If client prediction matched server: Smooth playback!<br/>If mismatch (desync): Reconcile & Snap to server position
```

---

## 1. The Authoritative Server Model

Clients are never trusted. A client that sends "My position is now (X, Y, Z)" enables instant teleportation hacks and speed cheats.
- **Rule**: Clients send **inputs only** (keystrokes, mouse deltas, timestamp).
- The server runs the authoritative simulation loop (e.g., at 64Hz or 128Hz) and broadcasts ground-truth world snapshots.

---

## 2. Lag Compensation: "Rewind Time"

When Player A shoots Player B who is sprinting across the screen:
- Because of 80ms network latency, Player A aimed at where Player B was on Player A's screen 80ms ago.
- Without compensation, the server would calculate Player B has already moved past that coordinate, resulting in a frustrating missed shot.

```mermaid
graph TD
    Shoot[Player A fires at timestamp t=1000] --> Server[Authoritative Server receives packet at t=1080]
    Server --> Rewind[Lag Compensation: Rewinds world state to t=1000]
    Rewind --> Raycast[Executes bullet raycast against player hitboxes at t=1000]
    Raycast --> Hit{Hit Detected?}
    Hit -->|Yes| Confirm[Confirm Kill / Damage & Fast-Forward World to t=1080]
```

---

## 3. Key Takeaways

- Use authoritative dedicated game servers communicating over custom UDP protocols (not TCP).
- Implement client-side prediction to make local movement feel instantaneous.
- Implement server lag compensation by buffering recent historical hitboxes and rewinding world state upon input arrival.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 16 complete.")
