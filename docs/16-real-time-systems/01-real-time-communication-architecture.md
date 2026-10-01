# Real-Time Communication Architecture: WebSockets at Scale

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
2. **RAM per Connection**: A kernel TCP socket buffer and TLS state consumes 4KB - 16KB of RAM. 1 million concurrent connections require $pprox 10	ext{GB} - 16	ext{GB}$ of pure memory just to maintain idle sockets.
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
