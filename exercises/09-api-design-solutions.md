# Solutions: API Design and Rate Limiting

---

### Solution 1: Cursor vs Offset Pagination
- **Problem with Offset**: The SQL database must scan, sort, and materialize all 5,000,020 rows, then discard the first 5,000,000 rows. This is an $O(N)$ full index scan that consumes high I/O and causes latency to degrade linearly as the page number increases.
- **Cursor Solution**:
  ```sql
  SELECT id, title, created_at
  FROM posts
  WHERE (created_at, id) < (:last_seen_created_at, :last_seen_id)
  ORDER BY created_at DESC, id DESC
  LIMIT 20;
  ```
  - Leverages a composite index on `(created_at, id)` to seek directly to the target record in $O(\log N)$ time, skipping past millions of rows instantly.

---

### Solution 2: Rate Limiting Race Condition
- **Naive Race Condition**: Two concurrent requests from the same user arrive at Pod A and Pod B simultaneously. Both read `GET tokens` (e.g., returns 1). Both evaluate $1 \ge 1$, allow the request, decrement to 0, and write `SET tokens 0`. Both requests were allowed even though only 1 token was available!
- **Lua Script Fix**: Redis executes Lua scripts as a single atomic operation on the main execution thread. No other command or script can run concurrently between reading and updating the token count.
