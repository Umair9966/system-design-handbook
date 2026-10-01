import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 05: DATABASES
# =========================================================================

save("docs/05-databases/01-relational-db-acid-and-transactions.md", """# Relational Databases: ACID, Transactions, and the Write-Ahead Log

## Overview
A **Relational Database Management System (RDBMS)** structures data into strictly defined tables consisting of rows and columns, enforcing relationships via foreign keys and mathematical relational algebra. The defining hallmark of enterprise relational databases is support for **ACID transactions**:
- **Atomicity**: All operations in a transaction succeed, or none do ("all or nothing").
- **Consistency**: A transaction transitions the database from one valid state to another, satisfying all schema constraints, checks, and foreign keys.
- **Isolation**: Concurrent transactions execute without interfering with one another.
- **Durability**: Once committed, transaction updates persist permanently, surviving OS crashes or hardware power loss.

```mermaid
sequenceDiagram
    autonumber
    Client->>DB: BEGIN TRANSACTION
    Client->>DB: UPDATE accounts SET bal = bal - 100 WHERE id = 1
    DB->>WAL: 1. Append mutation to Write-Ahead Log (Sequential fsync)
    WAL-->>DB: Disk fsync complete!
    DB->>BufferPool: 2. Modify in-memory 16KB dirty page
    Client->>DB: COMMIT
    DB-->>Client: Success (Guaranteed Durable!)
    Note over DB, Disk: 3. Background Checkpointer flushes dirty page to table disk
```

## Why It Matters
Without ACID guarantees, power cuts during financial transfers cause money to vanish from one account without appearing in the other. Relational databases guarantee financial and operational integrity through battle-tested crash recovery algorithms.

## Core Concepts
- **The Write-Ahead Log (WAL)**: The foundational mechanism ensuring durability and crash recovery. Before any in-memory data page is modified in the database buffer pool, the exact delta mutation must be appended sequentially to the WAL on disk and physically flushed (`fsync`).
- **ARIES Crash Recovery**: Algorithm for Recovery and Isolation Exploiting Semantics. When a crashed database boots up:
  1. *Analysis Pass*: Identifies dirty pages and active in-flight transactions at the time of the crash.
  2. *Redo Pass*: Replays all committed changes in the log forward to bring the database to the exact crash state.
  3. *Undo Pass*: Rolls back all incomplete, uncommitted transactions backward to ensure clean consistency.
- **Checkpointing**: Periodic background flushing of dirty memory pages to disk tables, allowing older segments of the WAL to be safely truncated.

## Trade-offs
| Dimension | Relational ACID Database | Non-ACID / Eventual Store |
| :--- | :--- | :--- |
| **Data Integrity** | **Absolute (zero money lost, zero partial writes)**| Eventual (reconciliation logic needed) |
| **Write Throughput** | Limited by disk `fsync` and lock contention | Massive (appends without coordination) |
| **Schema Flexibility**| Strict (requires migrations) | Dynamic (schemaless JSON / Key-Value) |
| **Horizontal Sharding**| Difficult (cross-shard joins/transactions are slow)| Native (built-in sharding and partitioning) |

## When to Use / When NOT to Use
### When to Use Relational ACID Databases
- Financial accounting, banking ledgers, checkout and payment systems, enterprise ERPs, and identity authentication tables.

### When NOT to Use
- High-volume time-series sensor telemetry, massive clickstream analytics, unstructured document graphs.

## Real-World Examples
- **Stripe & PayPal**: Standardize strictly on relational ACID databases (PostgreSQL, CockroachDB) for their core balance ledgers to ensure zero double-spending.
- **AWS Aurora**: Re-architected MySQL/PostgreSQL for the cloud by offloading the Write-Ahead Log directly to a distributed storage fleet, achieving 5x standard MySQL throughput.

## Common Pitfalls
- **Long-Running Transactions**: Keeping a transaction open while awaiting an external HTTP API response (e.g., Stripe charge), holding row locks open for seconds and causing database connection pool starvation.
- **Premature NoSQL Migration**: Moving from PostgreSQL to NoSQL because "SQL doesn't scale", only to reimplement transactions, joins, and consistency checks badly in application code.

## Key Takeaways
- Relational databases guarantee ACID correctness.
- The **Write-Ahead Log (WAL)** guarantees durability; random disk page flushes happen asynchronously in the background.
- Never make external network calls inside an active database transaction.

## Common Interview Questions
1. How does the Write-Ahead Log (WAL) guarantee durability before data pages are written to disk?
2. What are the three phases of the ARIES crash recovery algorithm?
3. Why are long-running database transactions hazardous to database health?

## Further Reading
- [C. Mohan et al.: ARIES: A Transaction Recovery Method (ACM TODS, 1992)](https://dl.acm.org/doi/10.1145/128765.128770)
- [PostgreSQL Documentation: Chapter 30 - Reliability and the Write-Ahead Log](https://www.postgresql.org/docs/current/wal-intro.html)
""")

save("docs/05-databases/02-isolation-levels-and-concurrency-control.md", """# Transaction Isolation Levels, Locking, and MVCC

## Overview
When hundreds of concurrent transactions read and write to the same database tables simultaneously, the database must enforce concurrency control to prevent data corruption. The ANSI SQL standard defines four hierarchical **isolation levels**, balancing performance against read anomalies.

```mermaid
graph TD
    subgraph Isolation Hierarchy: Increasing Safety, Decreasing Throughput
        L1[Read Uncommitted: Lowest Isolation, High Concurrency]
        L2[Read Committed: Default in Postgres/Oracle]
        L3[Repeatable Read: Default in MySQL InnoDB]
        L4[Serializable: Highest Isolation, Pure Safety]
    end
    L1 --> L2 --> L3 --> L4
```

## Why It Matters
Setting an isolation level too low allows race conditions, phantom rows, and lost updates that silently corrupt financial statements. Setting isolation to `SERIALIZABLE` globally introduces massive lock contention, aborts, and serialization failures under high load.

## Core Concepts & Read Anomalies
1. **Dirty Read**: Transaction A reads uncommitted modifications made by Transaction B. If Transaction B rolls back, Transaction A acted on data that never officially existed.
2. **Non-Repeatable Read**: Transaction A reads row 1. Transaction B updates row 1 and commits. Transaction A reads row 1 again and sees different values within the same transaction.
3. **Phantom Read**: Transaction A queries a range of rows (`WHERE age > 30`). Transaction B inserts a new user with age 35 and commits. Transaction A runs the range query again and discovers a new "phantom" row.
4. **Write Skew**: Two concurrent transactions read overlapping data sets, satisfy separate constraints, and make disjoint updates that together violate a global business invariant (e.g., doctors on call).

### The ANSI SQL Isolation Matrix
| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Concurrency Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Read Uncommitted** | **Allowed** | Allowed | Allowed | No read locks |
| **Read Committed** | Prevented | Allowed | Allowed | Read snapshot per statement |
| **Repeatable Read** | Prevented | Prevented | Prevented in modern MVCC | Read snapshot per transaction |
| **Serializable** | Prevented | Prevented | Prevented | 2PL or SSI (Serialization Graph) |

## How It Works: Concurrency Control Mechanisms
1. **Two-Phase Locking (2PL - Pessimistic)**:
   - *Growing Phase*: Transaction acquires Shared locks (`S`) for reads and Exclusive locks (`X`) for writes.
   - *Shrinking Phase*: Locks are released only at the end of the transaction.
   - *Result*: Guarantees serializability, but readers block writers and writers block readers.
2. **Multi-Version Concurrency Control (MVCC - Optimistic)**:
   - Used by modern PostgreSQL and MySQL InnoDB.
   - **Readers never block writers, and writers never block readers**.
   - Every row update creates a new immutable version of the row tagged with transaction IDs (`xmin`/`xmax`).
   - A reader only sees row versions that were committed before the reader's transaction snapshot timestamp. Dead old versions are cleaned up asynchronously (Postgres `VACUUM` / InnoDB Undo Logs).

## Trade-offs
| Mechanism | Read Throughput | Write Throughput | Abort / Deadlock Rate |
| :--- | :--- | :--- | :--- |
| **2PL (Pessimistic Locking)** | Low (readers lock out writers) | Low (heavy lock contention) | High deadlocks |
| **MVCC (Optimistic Snapshots)**| **Exceptional (zero read locks)**| High (row-level write locks) | Low |
| **Serializable Snapshot (SSI)** | High | Moderate | High abort rate under contention |

## When to Use / When NOT to Use
### When to Use Read Committed (Default)
- 95% of standard web applications, user profile lookups, content management systems.

### When to Use Repeatable Read / Serializable
- Financial reconciliations, end-of-month accounting audits, stock exchange matching engines.

## Real-World Examples
- **PostgreSQL**: Defaults to **Read Committed**. Under `REPEATABLE READ`, Postgres takes a single snapshot at the start of the transaction, completely eliminating both non-repeatable reads and phantom reads via MVCC without locking tables.
- **MySQL InnoDB**: Defaults to **Repeatable Read**, using **Next-Key Locking** (combining index-row locks with gap locks) to physically prevent phantom insertions into indexed gaps.

## Common Pitfalls
- **Deadlocks from Inconsistent Lock Ordering**: Transaction 1 locks Row A then Row B; Transaction 2 locks Row B then Row A. Both transactions freeze forever waiting for each other until the database deadlock detector kills one.
- **Postgres Table Bloat**: Leaving an uncommitted read-only transaction open for hours, preventing `VACUUM` from cleaning up millions of dead row versions, inflating table size and degrading query performance.

## Key Takeaways
- MVCC ensures that **readers do not block writers, and writers do not block readers**.
- Always order lock acquisition consistently across codebase endpoints to eliminate deadlocks.
- Read Committed is the sensible production default for most web systems.

## Common Interview Questions
1. How does Multi-Version Concurrency Control (MVCC) allow concurrent reads and writes without locking?
2. What is the difference between a Non-Repeatable Read and a Phantom Read?
3. What is Write Skew, and why does Repeatable Read fail to prevent it?

## Further Reading
- [PostgreSQL Documentation: Chapter 13 - Concurrency Control](https://www.postgresql.org/docs/current/mvcc.html)
- [Michael Cahill et al.: Serializable Snapshot Isolation in PostgreSQL (VLDB 2011)](https://dl.acm.org/doi/10.14778/3402707.3402737)
""")

save("docs/05-databases/03-database-indexing-deep-dive.md", """# Database Indexing Deep Dive: B-Trees, Hash, and Composite Indexes

## Overview
A database **index** is an auxiliary data structure that improves the speed of data retrieval operations on a database table at the cost of additional storage space and slower write operations. Without an index, the database engine must execute a **Full Table Scan ($O(N)$)**, reading every single disk page sequentially from disk.

```mermaid
graph TD
    subgraph B+Tree Index Structure
        Root[Root Node] --> I1[Internal Node: Keys 10, 50]
        Root --> I2[Internal Node: Keys 90, 150]
        I1 --> L1[Leaf Node: 1..9 -> Row Pointers]
        I1 --> L2[Leaf Node: 10..49 -> Row Pointers]
        L1 <-->|Bidirectional Linked List| L2
    end
```

## Why It Matters
On a table with 50 million rows, a query without an index can take **30 to 60 seconds** as it reads gigabytes of raw data from disk. With an appropriate B+Tree index, the database executes a binary tree traversal requiring **3 to 4 disk page reads**, answering the query in **sub-2 milliseconds**.

## Core Concepts & Index Types
1. **B+Tree Index (The Industry Standard)**:
   - Self-balancing, multi-way search tree with high fan-out (typically 100 to 500 children per node).
   - *Key Property*: Internal nodes store only routing keys; **all actual data pointers reside exclusively in leaf nodes**.
   - Leaf nodes are linked sequentially via a **bidirectional linked list**, making range scans (`WHERE age BETWEEN 20 AND 30`) exceptionally fast.
2. **Hash Index**:
   - $O(1)$ lookups based on an in-memory hash table.
   - *Limitation*: Only supports exact equality matches (`=`). **Useless for range queries or sorting** (`<`, `>`, `ORDER BY`).
3. **Composite Index (Multi-Column)**:
   - An index spanning multiple columns: `CREATE INDEX idx ON orders (tenant_id, status, created_at)`.
   - **The Leftmost Prefix Rule**: The query must filter on the leftmost indexed column (`tenant_id`) to leverage the index. A query filtering only on `created_at` cannot use this index.
4. **Covering Index (Index-Only Scan)**:
   - An index that contains all columns requested by a `SELECT` statement:
     `SELECT user_id, email FROM users WHERE user_id = 42;`
   - If the index stores `(user_id, email)`, the database retrieves the result directly from the B+Tree leaf without ever visiting the main table heap on disk.
5. **Index Selectivity**:
   - The ratio of distinct values to total rows:
     $$\\text{Selectivity} = \\frac{\\text{Count Distinct}(column)}{\\text{Total Rows}}$$
   - Columns with high selectivity (UUIDs, email addresses) benefit tremendously from indexes. Columns with low selectivity (boolean flags, gender) should rarely be indexed alone.

## Trade-offs
| Index Factor | Benefit | Cost / Trade-off |
| :--- | :--- | :--- |
| **Adding a B+Tree Index** | $O(\\log N)$ read lookups and fast range scans | Adds write latency (every `INSERT`/`UPDATE` must balance the tree)|
| **Covering Index** | Eliminates expensive table heap lookups | Consumes additional disk space and buffer pool RAM |
| **Composite Index** | Optimizes complex multi-column queries | Useless if queries do not match leftmost prefix order |

## When to Use / When NOT to Use
### When to Index
- Primary keys and foreign key join columns.
- Columns appearing frequently in `WHERE`, `ORDER BY`, and `GROUP BY` clauses with high selectivity.

### When NOT to Index
- Small tables (< 1,000 rows); a full table scan in RAM is faster than traversing an index tree.
- Low-cardinality columns (e.g., `is_active: boolean`).
- Extremely write-heavy append-only tables where read queries are rare.

## Real-World Examples
- **Composite Index Ordering in E-Commerce**:
  `WHERE tenant_id = 42 AND status = 'SHIPPED' ORDER BY created_at DESC LIMIT 20`
  Creating an index on `(tenant_id, status, created_at)` allows the database to locate the exact range for `tenant_id` and `status` and traverse the leaf nodes in reverse order, executing in **1ms with zero in-memory sorting**.

## Common Pitfalls
- **Over-Indexing**: Creating 20 indexes on a single table, causing every `INSERT` statement to execute 21 distinct disk writes and severely degrading batch ingestion performance.
- **Function Calls Invalidating Indexes**: Writing `WHERE YEAR(created_at) = 2026`, preventing the database from using an index on `created_at` (must write `WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01'`).

## Key Takeaways
- B+Trees are the default database index because their high fan-out minimizes tree height (3-4 levels) and leaf-node linked lists enable lightning-fast range queries.
- Follow the **Leftmost Prefix Rule** for composite indexes: Equality columns first, followed by sorting/range columns.
- **Covering indexes** eliminate table lookups completely.

## Common Interview Questions
1. Why do databases use B+Trees rather than standard Binary Search Trees (BST) or Red-Black trees?
2. What is the Leftmost Prefix Rule in composite indexes, and how does column order matter?
3. What is an Index-Only Scan (Covering Index), and why is it so much faster than a standard index lookup?

## Further Reading
- [Use The Index, Luke! A Guide to Database Performance](https://use-the-index-luke.com/)
- [Database Internals: Part 1 - Storage Engines (Alex Petrov)](https://www.databass.dev/)
""")

save("docs/05-databases/04-nosql-database-types.md", """# NoSQL Database Types: Key-Value, Document, Wide-Column, Graph, and Time-Series

## Overview
**NoSQL ("Not Only SQL")** databases emerged to handle massive horizontal scalability, high write velocities, flexible schemas, and specialized data structures that traditional relational databases struggle to accommodate. NoSQL spans five distinct architectural families:
1. **Key-Value Stores**: Simplest data model; maps unique keys to arbitrary binary payloads (Redis, DynamoDB).
2. **Document Databases**: Stores semi-structured hierarchical JSON/BSON documents (MongoDB, Couchbase).
3. **Wide-Column Stores**: Multi-dimensional sparse matrices indexed by row, column family, and timestamp (Cassandra, ScyllaDB, HBase).
4. **Graph Databases**: Stores nodes, edges, and properties optimized for relationship traversal (Neo4j, Amazon Neptune).
5. **Time-Series Databases**: Optimized for sequential timestamped append-only telemetry (TimescaleDB, InfluxDB).

```mermaid
graph TD
    NoSQL[NoSQL Taxonomy]
    NoSQL --> KV[1. Key-Value: Redis / DynamoDB]
    NoSQL --> Doc[2. Document: MongoDB]
    NoSQL --> WC[3. Wide-Column: Cassandra / ScyllaDB]
    NoSQL --> Graph[4. Graph: Neo4j / Neptune]
    NoSQL --> TS[5. Time-Series: TimescaleDB / InfluxDB]
```

## Why It Matters
Attempting to query 6 degrees of social network relationships in a relational database requires dozens of self-joins that crash the query planner. Conversely, using a graph database for financial accounting ledgers is an operational disaster. Matching data access patterns to the correct storage model is a staff-level engineering skill.

## Detailed Comparison Across the 5 Families
| Family | Representative Tech | Data Model | Primary Query Pattern | Scaling Model |
| :--- | :--- | :--- | :--- | :--- |
| **Key-Value** | Redis, DynamoDB | `Key -> Blob` | Lookup by primary key ($O(1)$) | Consistent hashing |
| **Document** | MongoDB, Couchbase | JSON / BSON | Nested attribute filters, secondary indexes | Sharded clusters |
| **Wide-Column**| Cassandra, ScyllaDB | `Row -> ColFamily -> Value`| Partition key + clustering key range scans | Masterless peer-to-peer ring |
| **Graph** | Neo4j, Neptune | Nodes & Directed Edges | Pointer chasing ($O(1)$ graph traversal)| Typically single-master / read replicas |
| **Time-Series**| TimescaleDB, InfluxDB | Timestamp + Metrics + Tags | Time-window aggregations (rollups) | Time-based chunk partitioning |

## Trade-offs
| Database Family | Strengths | Weaknesses |
| :--- | :--- | :--- |
| **Wide-Column (Cassandra)** | Linear write scaling, zero single point of failure | No joins, queries must be designed upfront per table |
| **Document (MongoDB)** | Developer ergonomics, flexible evolving schemas | Cross-document transactions are slow; memory-heavy |
| **Graph (Neo4j)** | Million-hop relationship queries in milliseconds | Difficult to shard horizontally across machines |
| **Key-Value (Redis)** | Sub-millisecond latency, extreme simplicity | Cannot query by internal value attributes |

## When to Use / When NOT to Use
### When to Choose Wide-Column (Cassandra)
- Massive write-heavy workloads (e.g., messaging message history, IoT metrics, Discord message storage) requiring petabyte scale across hundreds of nodes.

### When to Choose Graph (Neo4j)
- Social network friend recommendations, fraud detection rings, identity and access management (IAM) permission trees.

### When to Choose Document (MongoDB)
- User catalogs, content management platforms, rapid prototyping where object schemas change weekly.

## Real-World Examples
- **Discord Message Storage**: Migrated billions of chat messages from MongoDB to **Apache Cassandra**, and subsequently to **ScyllaDB**, utilizing wide-column storage to sustain billions of daily message writes without locks.
- **Uber Knowledge Graph**: Utilizes graph data modeling to map physical road networks, traffic constraints, and driver-rider proximity relationships.

## Common Pitfalls
- **Using Cassandra Like a Relational DB**: Attempting to run ad-hoc queries with `ALLOW FILTERING` in Cassandra, scanning entire distributed clusters and causing massive CPU timeouts.
- **Unbounded Document Growth in MongoDB**: Embedding unbounded arrays (e.g., embedding all comments inside a single blog post document), hitting MongoDB's 16MB document size limit and forcing expensive disk reallocations.

## Key Takeaways
- NoSQL is not a single technology; it is a suite of specialized data models.
- **Cassandra** is king for massive, linearly scalable write throughput.
- **Graph databases** solve relationship traversal via index-free adjacency.

## Common Interview Questions
1. Why does Cassandra scale writes horizontally better than traditional relational databases?
2. What is "index-free adjacency" in graph databases, and why does it make relationship queries so fast?
3. How does wide-column storage differ from traditional relational row storage?

## Further Reading
- [Avinash Lakshman and Prashant Malik: Cassandra - A Decentralized Structured Storage System (ACM SIGOPS, 2010)](https://www.cs.cornell.edu/projects/ladis2009/papers/lakshman-ladis2009.pdf)
- [Neo4j Graph Database Concepts](https://neo4j.com/docs/getting-started/current/)
""")

save("docs/05-databases/05-sql-vs-nosql-decision-framework.md", """# SQL vs NoSQL: An Engineering Decision Framework

## Overview
The decision between **Relational (SQL)** and **Non-Relational (NoSQL)** databases is one of the most critical architectural forks in system design. Rather than relying on dogma, staff engineers use a structured decision framework grounded in access patterns, transaction boundaries, schema evolution, and scale requirements.

```mermaid
graph TD
    Start{Does the system require multi-table ACID transactions?}
    Start -->|Yes| SQL[Choose Relational SQL: PostgreSQL / MySQL]
    Start -->|No| Q2{Is the workload predominantly write-heavy with petabyte scale?}
    Q2 -->|Yes| Cassandra[Wide-Column: Cassandra / ScyllaDB]
    Q2 -->|No| Q3{Are you querying complex relationship graphs?}
    Q3 -->|Yes| Graph[Graph DB: Neo4j / Neptune]
    Q3 -->|No| Q4{Do you need ultra-simple key lookups or flexible JSON?}
    Q4 -->|Key Lookups| KV[Key-Value: Redis / DynamoDB]
    Q4 -->|Flexible JSON| Doc[Document: MongoDB / PostgreSQL JSONB]
```

## Why It Matters
Debunking the myth: *"SQL cannot scale, so modern apps must use NoSQL."* Relational databases like PostgreSQL scale comfortably to tens of thousands of QPS and terabytes of data on single instances, and horizontally via Citus or CockroachDB. Choosing NoSQL prematurely forces developers to manually write application-layer joins, integrity checks, and custom transactions.

## The 6-Dimension Decision Matrix
| Evaluation Dimension | Choose Relational (SQL) | Choose NoSQL |
| :--- | :--- | :--- |
| **1. Data Relationships & Joins** | Complex relational queries, foreign keys, many-to-many joins | Data is self-contained or queries can be denormalized |
| **2. Transactional Guarantees** | Strict multi-table ACID transactions required (Banking/Billing) | Eventual consistency or single-row atomic writes suffice |
| **3. Schema Predictability** | Structured, predictable schema requiring strict data typing | Highly dynamic, polymorphous, or evolving JSON schemas |
| **4. Scale Limits (Single Node)** | Reads scale via replicas; writes fit on single node (<20K writes/s)| Write throughput exceeds single physical server capacity |
| **5. Query Flexibility** | Ad-hoc queries, analytical reporting, dynamic filtering | Queries are strictly known upfront and mapped to partition keys|
| **6. Operational Maturity** | Decades of battle-tested backup, recovery, and tooling | Requires specialized cluster tuning (compaction, gossip, vnodes)|

## Detailed Decision Flowchart
1. **Financial & Ledger Systems**: Always choose **SQL (PostgreSQL / CockroachDB)**. Zero tolerance for lost updates or inconsistency.
2. **High-Velocity Messaging History**: Choose **Wide-Column NoSQL (Cassandra / DynamoDB)**. Partitioned by `conversation_id`, sorted by `timestamp`.
3. **User Profiles & Catalogs**: Choose **SQL with JSONB** or **Document NoSQL (MongoDB)**.
4. **Social Follower Connections**: Choose **Graph NoSQL (Neo4j)** or specialized relational adjacency lists.
5. **Real-Time Leaderboards**: Choose **Key-Value NoSQL (Redis Sorted Sets)**.

## Trade-offs
| Architectural Choice | Primary Advantage | Primary Compromise |
| :--- | :--- | :--- |
| **Defaulting to PostgreSQL** | Infinite query flexibility, ACID safety, JSONB support | Horizontal write scaling requires manual sharding or distributed SQL |
| **Defaulting to Cassandra/DynamoDB**| Unbounded horizontal write throughput | Zero joins; changing query patterns requires creating new tables and backfilling |

## When to Use / When NOT to Use
### When SQL is the Superior Choice
- 90% of business applications, SaaS backends, e-commerce checkouts, subscription billing, inventory systems.

### When NoSQL is Mandatory
- Ingesting 200,000 writes/second from globally distributed devices, tracking live delivery driver coordinates, storing trillions of chat logs.

## Real-World Examples
- **Segment (Twilio)**: Migrated from a sprawling microservice MongoDB cluster back to **PostgreSQL**, reporting massive operational simplicity, lower latency, and reduced infrastructure bills.
- **Uber**: Uses a custom layer called **Schemaless** built on top of MySQL instances acting as a wide-column append-only key-value store, combining MySQL's rock-solid storage engine with NoSQL horizontal scaling.

## Common Pitfalls
- **The "NoSQL Means No Work" Trap**: Believing NoSQL eliminates data modeling; in Cassandra, data modeling is far stricter than SQL because queries must be mathematically planned around partition keys before writing tables.
- **Ignoring PostgreSQL JSONB**: Deploying a separate MongoDB cluster purely to store dynamic JSON attributes when modern PostgreSQL natively supports indexed, high-performance binary JSON (`JSONB`).

## Key Takeaways
- Start with **PostgreSQL** by default unless concrete technical metrics prove relational limits have been breached.
- NoSQL trades query flexibility and multi-table ACID transactions for unbounded horizontal write scaling.
- In Cassandra/DynamoDB, you model your tables around your **queries**, not around real-world entities.

## Common Interview Questions
1. In what scenario would you recommend a relational database over NoSQL, even at large scale?
2. How do modern relational databases handle semi-structured data via JSONB?
3. How does data modeling in Cassandra differ fundamentally from data modeling in MySQL?

## Further Reading
- [Martin Kleppmann: Data Models and Query Languages (DDIA Chapter 2)](https://dataintensive.net/)
- [Uber Engineering: Designing Schemaless, Uber's Scalable Datastore](https://www.uber.com/blog/schemaless-sql-database/)
""")

print("Section 05 generated part 1.")
