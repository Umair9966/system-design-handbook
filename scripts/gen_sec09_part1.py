import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 09: API DESIGN
# =========================================================================

save("docs/09-api-design/01-rest-principles-and-resource-modeling.md", """# REST Principles, Resource Modeling, and HTTP Status Codes

## Overview
**REST (Representational State Transfer)** is an architectural style defined by Roy Fielding in 2000 for designing networked distributed hypermedia systems. REST leverages existing standards of the web—primarily HTTP methods, URI identifiers, and status codes—to create stateless, cacheable, uniform client-server interfaces.

```mermaid
graph LR
    Client[Client App] -->|POST /api/v1/orders: 201 Created| API[REST API Gateway]
    Client -->|GET /api/v1/orders/42: 200 OK| API
    Client -->|DELETE /api/v1/orders/42: 204 No Content| API
    API --> Service[Order Microservice]
```

## Why It Matters
Inconsistent API design frustrates frontend engineers, creates security vulnerabilities, and prevents HTTP-level caching. Clean resource modeling ensures APIs are intuitive, self-describing, and maintainable across multi-year enterprise lifecycles.

## Core Concepts & Architectural Constraints
1. **Roy Fielding's 6 Architectural Constraints**:
   - *Client-Server Separation*: Decouples user interface from data storage.
   - *Statelessness*: Every request contains all context needed to process it; server holds zero session memory.
   - *Cacheability*: Responses explicitly declare cache rules (`Cache-Control`).
   - *Uniform Interface*: Identification of resources via URIs, manipulation of resources through representations, and self-descriptive messages.
   - *Layered System*: Client cannot tell whether it is communicating directly with the origin server or an intermediary proxy/CDN.
   - *Code on Demand (Optional)*: Servers can extend client functionality by transferring executable code (e.g., JavaScript).
2. **Resource-Oriented URI Modeling (Nouns vs Verbs)**:
   - **Correct (Nouns & Hierarchies)**:
     - `GET /api/v1/users/42/orders` (Fetch all orders for user 42)
     - `POST /api/v1/users/42/orders` (Create new order for user 42)
     - `DELETE /api/v1/orders/108` (Delete specific order)
   - **Anti-Pattern (Verbs in URIs - RPC Style)**:
     - `POST /api/v1/getUserOrders?id=42`
     - `POST /api/v1/deleteOrder`
3. **HTTP Verb Semantics**:
   - `GET`: Safe, idempotent read. Never mutates server state.
   - `POST`: Non-idempotent resource creation or action execution.
   - `PUT`: Complete resource replacement (idempotent).
   - `PATCH`: Partial resource update (e.g., updating only user email).
   - `DELETE`: Resource removal (idempotent).
4. **HTTP Status Code Selection Standards**:
   - **2xx Success**: `200 OK` (Standard success), `201 Created` (Resource created), `202 Accepted` (Async task queued), `204 No Content` (Deleted successfully, no return body).
   - **3xx Redirection**: `301 Moved Permanently` (SEO canonical redirect), `304 Not Modified` (Cached client ETag match).
   - **4xx Client Error**: `400 Bad Request` (Malformed JSON), `401 Unauthorized` (Missing/invalid auth token), `403 Forbidden` (Authenticated, but lacks RBAC permission), `404 Not Found`, `409 Conflict` (Duplicate unique constraint / race condition), `429 Too Many Requests` (Rate limit exceeded).
   - **5xx Server Error**: `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable` (Server overloaded / maintenance), `504 Gateway Timeout`.

## Trade-offs
| Attribute | Pure RESTful Resource API | RPC / gRPC Style API |
| :--- | :--- | :--- |
| **Ergonomics for CRUD** | **Natural, intuitive, standardized** | Clunky (Requires custom action methods)|
| **Edge Cacheability** | **Maximum (Native HTTP GET caching)** | Poor (POST methods require custom caching) |
| **Complex Multi-Resource Actions**| Awkward (e.g., `/checkout` vs `/orders`)| **Natural (`OrderService.ExecuteCheckout()`)**|

## When to Use / When NOT to Use
### When to Use REST
- Public third-party developer APIs, mobile web backends, CRUD applications, webhooks.

### When to Use RPC / Action Style Instead
- Complex mathematical workflows, financial state machine triggers (e.g., `/api/v1/transfers/42/cancel`), internal microservice RPCs.

## Real-World Examples
- **Stripe REST API**: Universally acknowledged as the premier example of clean RESTful resource modeling. Resources are clean nouns (`/charges`, `/refunds`, `/customers`), utilizing standard HTTP verbs, status codes, and idempotency headers.

## Common Pitfalls
- **Returning HTTP 200 with Error JSON**: Returning `HTTP 200 OK` with payload `{"success": false, "error": "Invalid password"}`, breaking standard HTTP load balancer error tracking, circuit breakers, and monitoring metrics!
- **Using GET for Mutations**: Allowing `GET /users/delete?id=42`, causing search engine web crawlers (Googlebot) to inadvertently delete your entire database by prefetching links!

## Key Takeaways
- Use **plural nouns** for resource paths (`/users`, `/orders`), never verbs.
- Never return `HTTP 200` when an operation failed.
- `GET`, `PUT`, and `DELETE` must be strictly **idempotent**.

## Common Interview Questions
1. What is the difference between `PUT` and `PATCH` in RESTful API design?
2. What is the difference between HTTP `401 Unauthorized` and `403 Forbidden`?
3. Why should APIs never return HTTP 200 OK for failed operations?

## Further Reading
- [Roy Thomas Fielding: Architectural Styles and the Design of Network-based Software Architectures (PhD Dissertation, 2000)](https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm)
- [Stripe API Reference Guide](https://stripe.com/docs/api)
""")

save("docs/09-api-design/02-pagination-strategies.md", """# API Pagination Strategies: Offset, Keyset, and Cursor Pagination

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
""")

save("docs/09-api-design/03-idempotency-keys-and-etags.md", """# Idempotency Keys and ETags for Safe API Operations

## Overview
In production web systems, network disruptions between clients and servers are inevitable. Designing safe, resilient APIs requires two standard architectural primitives:
- **Idempotency Keys**: Request headers (`Idempotency-Key: <uuid>`) allowing clients to safely retry mutating operations (POST) without creating duplicate payments or orders.
- **ETags (Entity Tags) & Conditional Headers**: Cache validators and optimistic concurrency control mechanisms (`If-Match`, `If-None-Match`) preventing lost updates and bandwidth waste.

```mermaid
sequenceDiagram
    autonumber
    actor Alice
    actor Bob
    participant API as API Gateway / DB

    Alice->>API: GET /articles/42
    API-->>Alice: 200 OK (ETag: "hash-v1", Text: "Hello")
    Bob->>API: GET /articles/42
    API-->>Bob: 200 OK (ETag: "hash-v1", Text: "Hello")
    Note over Alice, API: Alice updates article first!
    Alice->>API: PUT /articles/42 (If-Match: "hash-v1", Text: "Hello World!")
    API-->>Alice: 200 OK (New ETag: "hash-v2")
    Note over Bob, API: Bob attempts update with stale ETag!
    Bob->>API: PUT /articles/42 (If-Match: "hash-v1", Text: "Hello Universe!")
    API-->>Bob: 412 Precondition Failed! (Lost Update Prevented!)
```

## Why It Matters
Without idempotency keys, an unacknowledged timeout causes an e-commerce customer to tap "Checkout" three times, creating three separate credit card charges. Without ETags, two customer service agents editing a user's address concurrently will trigger a **Lost Update Bug**, where the last write silently overwrites and destroys the first write.

## Core Concepts & Mechanical Implementation

### 1. The Idempotency Key Pattern (RFC 9440)
- Client attaches header: `Idempotency-Key: 7b34b6b1-4c72-4e4b-a912-32a5e95a1234`.
- Server wraps processing in an atomic database lock:
  1. Checks `idempotency_records` table.
  2. If record is found with status `COMPLETED`, server returns the cached response body immediately.
  3. If found with status `IN_PROGRESS`, server returns `HTTP 409 Conflict`.
  4. If not found, server inserts key, processes transaction, stores response, and commits.

### 2. ETags & Conditional Requests (RFC 9110)
- **ETag**: An HTTP response header containing an opaque fingerprint (typically a SHA-256 hash or version number) representing the exact state of a resource representation:
  `ETag: "686897696a7c876b7e"`
- **Conditional Cache Validation (`If-None-Match`)**:
  Client sends: `GET /avatar.png` with `If-None-Match: "686897696a7c876b7e"`.
  If the avatar hasn't changed, the server returns **`304 Not Modified` with zero response body**, saving megabytes of bandwidth.
- **Optimistic Concurrency Control (`If-Match`)**:
  Client sends: `PUT /products/42` with `If-Match: "v1-hash"`.
  The server verifies that the database's current version hash matches `"v1-hash"`. If another user modified the product in the interim, the server rejects the write with **`412 Precondition Failed`**, completely preventing lost updates.

## Trade-offs
| Mechanism | Primary Benefit | Operational Cost |
| :--- | :--- | :--- |
| **Idempotency Keys** | **Zero accidental duplicate charges or records** | Requires dedicated database storage and TTL pruning |
| **ETags (Cache Validation)** | Eliminates redundant network bandwidth transfers | Slight CPU cost to compute content hashes on server |
| **ETags (Optimistic Locking)**| **Zero database row locks; eliminates lost updates** | Client must implement retry-and-rebase logic on 412 |

## When to Use / When NOT to Use
### When Idempotency Keys are Mandatory
- Financial payments, subscription billing, flight seat reservations, order submissions.

### When ETags are Mandatory
- Document editing platforms, content management systems, collaborative configurations, and public REST APIs serving static or semi-static assets.

## Real-World Examples
- **Stripe API**: Caches idempotency responses for 24 hours. Retrying an identical POST with the same key returns the exact original charge receipt without hitting Visa or Mastercard payment networks twice.
- **GitHub REST API**: Uses ETags on all repository endpoints. Client tools query GitHub with `If-None-Match`; responses return `304 Not Modified` and do not consume GitHub API rate limit quotas!

## Common Pitfalls
- **Weak vs Strong ETags**: Confusing weak ETags (`W/"v1"`, semantically equivalent) with strong ETags (`"v1"`, byte-for-byte identical). Only strong ETags can be used for byte-range resume downloads.
- **Failing to Expire Idempotency Keys**: Retaining idempotency keys indefinitely in an unpartitioned database table, eventually slowing down index scans (always enforce a 24 to 72-hour TTL).

## Key Takeaways
- Use **Idempotency Keys** to make mutating `POST` endpoints safely retryable.
- Use **ETags with `If-None-Match`** to save bandwidth via `304 Not Modified`.
- Use **ETags with `If-Match`** to implement optimistic concurrency control and eliminate lost update race conditions.

## Common Interview Questions
1. How does an API Gateway implement idempotency key tracking across distributed microservices?
2. What is the Lost Update problem, and how do ETags with `If-Match` prevent it?
3. How do ETags save API consumers from exhausting rate limit quotas?

## Further Reading
- [IETF RFC 9440: The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/html/rfc9440)
- [RFC 9110: HTTP Semantics (Conditional Requests and Preconditions)](https://datatracker.ietf.org/doc/html/rfc9110#section-13)
""")

save("docs/09-api-design/04-rate-limiting-algorithms.md", """# Rate Limiting Algorithms: Token Bucket, Leaky Bucket, and Sliding Window

## Overview
**Rate limiting** is an essential defensive engineering strategy that controls the rate of incoming or outgoing traffic to a network or API. It protects backend infrastructure from denial-of-service (DDoS) attacks, brute-force credential stuffing, web scraping, and accidental cascading traffic floods.

Production rate limiters implement one of five foundational mathematical algorithms:
1. **Token Bucket**
2. **Leaky Bucket**
3. **Fixed Window Counter**
4. **Sliding Window Log**
5. **Sliding Window Counter (Redis Hybrid)**

```mermaid
graph TD
    subgraph Token Bucket Algorithm
        Refill[Refill: +r tokens/sec] --> Bucket[Bucket: Max Capacity B]
        Request[Incoming Request] --> Check{Token Available?}
        Check -->|Yes: Consume 1 Token| Allow[Allow Request: HTTP 200]
        Check -->|No: Bucket Empty| Reject[Reject Request: HTTP 429 Too Many Requests]
    end
```

## Why It Matters
Without rate limiting, a single runaway client running an infinite loop script can exhaust database connection pools and starve thousands of legitimate users. Rate limiters enforce fair resource sharing across multi-tenant platforms.

## Core Concepts & Algorithm Breakdown

### 1. Token Bucket
- A bucket holds up to $B$ tokens.
- Tokens refill at a constant rate of $r$ tokens per second.
- When a request arrives: if tokens $\ge 1$, consume 1 token and allow request; otherwise, reject with **HTTP 429 Too Many Requests**.
- *Advantage*: **Allows short traffic bursts** up to bucket capacity $B$, while strictly bounding long-term sustained throughput to $r$.

### 2. Leaky Bucket
- A queue of fixed capacity $B$. Requests enter the queue and leak (are processed) at a **constant, smooth rate $r$**.
- If the queue overflows, incoming requests are dropped.
- *Advantage*: Perfectly smooths out bursty traffic into a constant, uniform downstream stream.

### 3. Fixed Window Counter
- Time is divided into fixed windows (e.g., 1 minute: `12:00:00 - 12:00:59`).
- A counter increments per request. If counter $> limit$, reject.
- *Fatal Flaw (Boundary Burst Hazard)*: A user sends 100 requests at 12:00:59 and another 100 requests at 12:01:01. In a 2-second window, **200 requests pass**, doubling the allowed limit!

### 4. Sliding Window Log
- Logs the exact timestamp of every request in a sorted set (Redis ZSET).
- On new request: delete timestamps older than $(\\text{now} - \\text{window})$; count remaining elements.
- *Advantage*: 100% mathematically precise rate limiting.
- *Fatal Flaw*: Massive memory footprint; storing timestamps for high-volume endpoints consumes gigabytes of RAM.

### 5. Sliding Window Counter (Cloudflare / Redis Hybrid)
- Combines the memory efficiency of Fixed Window with the accuracy of Sliding Log:
  $$\\text{Current Count} = \\text{Requests in Current Window} + (\\text{Requests in Previous Window} \\times \\text{Overlap Factor})$$
  *Example*: In a 60-second window, if current time is 15 seconds in (overlap factor = $75\\%$):
  $$\\text{Count} = \\text{Current} + (\\text{Previous} \\times 0.75)$$
- Consumes only 2 integer counters in Redis while bounding boundary bursts within a 5% margin of error.

## Trade-offs
| Algorithm | Memory Overhead | Handles Bursts? | Smoothing Effect | Precision |
| :--- | :--- | :--- | :--- | :--- |
| **Token Bucket** | **Minimal ($O(1)$)** | **Yes (Up to capacity $B$)**| None | High |
| **Leaky Bucket** | Moderate (Queue size) | No (Converts to smooth stream)| **Maximum** | High |
| **Fixed Window** | **Minimal ($O(1)$)** | Vulnerable to 2x boundary bursts| None | Poor |
| **Sliding Window Log** | High ($O(N)$ timestamps)| Yes | None | **100% Precise** |
| **Sliding Window Counter**| **Minimal ($O(1)$)** | Yes | Good | **99% Accurate** |

## When to Use / When NOT to Use
### When to Choose Token Bucket
- General-purpose public web APIs (AWS, Stripe, GitHub). Allows users to burst when loading web pages while bounding sustained usage.

### When to Choose Leaky Bucket
- Egress queues sending traffic to strict third-party partner APIs with rigid concurrency limits.

### When to Choose Sliding Window Counter
- Distributed high-scale API Gateways backed by Redis clusters.

## Real-World Examples
- **Stripe & GitHub APIs**: Implement **Token Bucket** rate limiting. GitHub allows 5,000 requests per hour for authenticated users, returning remaining tokens via response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
- **Cloudflare Edge Rate Limiting**: Uses the **Sliding Window Counter** algorithm implemented in edge NGINX/Lua memory pools to block DDoS attacks with minimal memory.

## Common Pitfalls
- **Distributed Race Conditions in Redis**: Executing `GET count` followed by `SET count` in separate round trips; under high concurrency, 50 requests read the same value, causing rate limits to be exceeded. (Always use **atomic Redis Lua scripts** or `INCR` commands!).
- **Global vs User-Level Limits**: Applying a single global IP rate limit; all 5,000 corporate employees behind a single corporate NAT gateway IP get blocked simultaneously. (Combine IP limiting with API Key / User ID limits).

## Key Takeaways
- **Token Bucket** allows bursts; **Leaky Bucket** enforces smooth constant-rate processing.
- Avoid Fixed Window counters due to the 2x boundary burst vulnerability.
- In distributed environments, implement rate limiting via **atomic Redis Lua scripts**.

## Common Interview Questions
1. How does the Token Bucket algorithm handle bursty traffic compared to the Leaky Bucket algorithm?
2. What is the boundary burst problem in Fixed Window rate limiting, and how does Sliding Window solve it?
3. How do you implement a distributed rate limiter in Redis without race conditions?

## Further Reading
- [Cloudflare: How we built rate limiting capable of scaling through DDoS attacks](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)
- [IETF Draft: RateLimit Header Fields for HTTP](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers)
""")

print("Section 09 Part 1 complete.")
