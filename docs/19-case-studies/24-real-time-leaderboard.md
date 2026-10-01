# Design a Real-Time Gaming Leaderboard (Redis Sorted Sets)

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
- **Ultra-Low Latency**: Rank calculation and updates $< 15	ext{ms}$.
- **Massive Scale**: 25 Million registered players.
- **Real-Time Accuracy**: Zero delay in rank updates.

---

## 2. Data Structure: Redis Sorted Sets (SkipList + Hash Table)

Redis `ZSET` natively solves real-time leaderboards:
- **Hash Table**: Maps `user_id` $	o$ `score` in $O(1)$ time.
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
