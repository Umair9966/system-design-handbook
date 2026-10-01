# Fanout Architectures: Push vs Pull (Twitter/X and Instagram)

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
