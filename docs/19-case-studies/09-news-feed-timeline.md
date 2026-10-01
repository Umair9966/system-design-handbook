# Design a Social Media News Feed (Facebook / Instagram)

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
- **Feed Generation Latency**: p99 $< 200	ext{ms}$.
- **Availability**: 99.99%.
- **Scale**: 500M DAU reading feeds 5 times per day.

---

## 2. Capacity & Fanout Sizing

- **DAU**: 500 Million.
- **Feed Views/Day**: $500	ext{M} 	imes 5 = 2.5	ext{ Billion feed loads/day}$.
- **Read QPS**: $rac{2,500,000,000}{86,400} pprox \mathbf{30,000	ext{ QPS}}$ (Peak: $60,000	ext{ QPS}$).
- **Posts/Day**: 100 Million posts/day $\implies \mathbf{1,200	ext{ write QPS}}$.

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
