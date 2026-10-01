# Transaction Isolation Levels, Locking, and MVCC

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
