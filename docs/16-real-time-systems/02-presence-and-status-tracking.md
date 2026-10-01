# Presence and Status Tracking at Scale (Online / Offline)

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
