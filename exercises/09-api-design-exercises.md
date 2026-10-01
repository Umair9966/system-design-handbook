# Exercises: API Design and Rate Limiting

---

### Exercise 1: Cursor vs Offset Pagination at Scale
Explain why `GET /api/v1/posts?offset=5000000&limit=20` causes severe database performance degradation, and rewrite the query using Cursor-based pagination.

### Exercise 2: Rate Limiting Race Condition
Explain the race condition that occurs when implementing a Token Bucket rate limiter in Redis using naive `GET` and `SET` commands. How does a Lua script eliminate this?
