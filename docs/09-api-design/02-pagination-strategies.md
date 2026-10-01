# API Pagination Strategies: Offset, Keyset, and Cursor Pagination

## Overview
When an API endpoint returns collections containing thousands or millions of records (e.g., `/users`, `/comments`), returning the entire dataset in a single payload crashes client mobile memory, exhausts database connection buffers, and saturates network bandwidth.

APIs manage collection retrieval through **Pagination**, implemented primarily via three distinct patterns:
- **Offset Pagination**: Traditional page and limit offsets (`LIMIT 20 OFFSET 1000`).
- **Keyset Pagination**: Filtering against an indexed unique ordering column (`WHERE id > 1000 LIMIT 20`).
- **Cursor Pagination**: Opaque, tamper-proof encoded tokens pointing to the exact boundary of the next page.

```mermaid
graph TD
    subgraph Offset Pagination [Deep Scan Hazard]
        O1[OFFSET 1,000,000 LIMIT 20] -->|DB reads 1,000,020 rows from disk, discards 1,000,000!| DB1[(PostgreSQL: 15 Seconds!)]
    end
    subgraph Cursor Pagination [Constant Time O(1)]
        C1[cursor = eyJpZCI6IDEwMDB9] -->|Decodes: WHERE id > 1000 LIMIT 20| DB2[(PostgreSQL: Index Seek: 1ms!)]
    end
```

## Why It Matters
Offset pagination is notorious for the **Deep Page Collapse**: requesting page 50,000 (`OFFSET 1,000,000`) forces the database to read 1,000,020 rows sequentially from the B+Tree leaf nodes into memory, only to discard the first 1,000,000 rows and return the last 20, driving database query latency from 2ms to **15+ seconds**.

## Core Concepts & Mechanical Implementation

### 1. Offset Pagination (`page` and `limit`)
- URL: `GET /api/v1/items?limit=20&page=5`
- SQL: `SELECT * FROM items ORDER BY id LIMIT 20 OFFSET 80;`
- *Pros*: Simple to implement; supports jumping directly to arbitrary pages (e.g., "Jump to Page 42").
- *Cons*: Catastrophic performance on deep pages ($O(N)$); vulnerable to **Duplicate/Missing Records** when items are inserted or deleted while a user is browsing.

### 2. Keyset Pagination (`seek` pagination)
- URL: `GET /api/v1/items?limit=20&since_id=1084`
- SQL: `SELECT * FROM items WHERE id > 1084 ORDER BY id ASC LIMIT 20;`
- *Pros*: Blazing fast $O(1)$ B+Tree index seek; unaffected by real-time insertions or deletions.
- *Cons*: Cannot jump to arbitrary pages; requires natural sortable columns.

### 3. Cursor-Based Pagination (The Modern Standard)
- URL: `GET /api/v1/items?limit=20&cursor=eyJpZCI6MTA4NCwiY3JlYXRlZF9hdCI6MTY3MjU4ODgwMH0=`
- The cursor is an opaque, Base64-encoded JSON string containing the exact values of the sorting columns from the last item of the previous page:
  ```json
  {"id": 1084, "created_at": 1672588800}
  ```
- SQL executed behind the scenes:
  ```sql
  SELECT * FROM items 
  WHERE (created_at, id) < ('2026-01-01 12:00:00', 1084)
  ORDER BY created_at DESC, id DESC 
  LIMIT 21; -- Fetch 1 extra to determine 'has_next_page'
  ```

## Trade-offs
| Strategy | Implementation Complexity | Performance on Deep Pages | Resistance to Data Shifts | Arbitrary Page Jumps |
| :--- | :--- | :--- | :--- | :--- |
| **Offset** | **Trivial** | **Terrible ($O(N)$ disk scan)**| Poor (Duplicates / Skips) | **Yes (Jump to Page 50)** |
| **Keyset** | Moderate | **Exceptional ($O(1)$ index seek)**| **High (Zero duplicates)** | No (Sequential only) |
| **Cursor** | Moderate to High | **Exceptional ($O(1)$ index seek)**| **High (Zero duplicates)** | No (Infinite scroll only) |

## When to Use / When NOT to Use
### When to Use Cursor Pagination
- Infinite scroll social feeds (Twitter/Instagram), real-time messaging history (Slack), public high-volume developer APIs (Stripe, GitHub), datasets exceeding 100,000 rows.

### When to Use Offset Pagination
- Back-office enterprise admin portals with small tables (< 5,000 rows) where users explicitly demand page number pagination buttons (`[1] [2] [3]...[Next]`).

## Real-World Examples
- **Stripe & Slack APIs**: Enforce cursor-based pagination across all collection endpoints. Stripe returns an opaque cursor ID (`starting_after: "ch_12345"`) and a boolean `has_more: true`.
- **Twitter/X Timeline API**: Uses Tweet IDs as natural 64-bit snowflake cursors (`max_id` and `since_id`) to fetch previous or subsequent tweets smoothly without duplicates.

## Common Pitfalls
- **Exposing Internal Database Primary Keys Directly**: Using raw auto-incrementing integer IDs as cursors instead of encoded opaque tokens, leaking sensitive internal business metrics (e.g., an attacker seeing total order count).
- **Pagination Without Deterministic Tie-Breaking**: Sorting by a non-unique column (e.g., `ORDER BY created_at DESC`); if 10 items share the exact same timestamp, database engine non-determinism causes items to be duplicated or skipped across pages. (Always append unique primary key as tie-breaker: `ORDER BY created_at DESC, id DESC`!).

## Key Takeaways
- Offset pagination fails on large datasets because the database must read and discard all preceding offset rows.
- **Cursor pagination** provides stable $O(1)$ B+Tree index lookups for infinite scroll feeds.
- Always include a unique column (Primary Key ID) as the secondary sort tie-breaker.

## Common Interview Questions
1. Why does `OFFSET 1000000 LIMIT 20` perform poorly in relational databases?
2. How do real-time record insertions cause items to be skipped or duplicated during offset pagination?
3. How do you design an opaque cursor token supporting multi-column sorting (e.g., sorting by rating and creation date)?

## Further Reading
- [Slack Engineering: Evolving API Pagination at Slack](https://slack.engineering/evolving-api-pagination-at-slack/)
- [Use The Index, Luke! No Offset: Paging Through Results](https://use-the-index-luke.com/no-offset)
