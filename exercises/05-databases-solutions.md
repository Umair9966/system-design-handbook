# Section 05: Databases — Solutions

### Solution 1: B+Tree vs LSM-Tree Write Amplification
1. **B+Tree Write Bottleneck**:
   - In a B+Tree, random writes update records located in arbitrary 16KB disk pages. To write a 500-byte update, the database must write the WAL *plus* flush the entire 16KB dirty page to disk.
   - Result: Heavy random I/O and high write amplification ($16,384 / 500 \approx 32\times$ write amplification).
2. **LSM-Tree Throughput**:
   - An LSM-Tree appends every incoming write sequentially to an in-memory `MemTable` and a sequential append-only WAL.
   - No random disk writes occur on the write path. When the MemTable fills up, it flushes sequentially to disk as an immutable SSTable. Sequential disk writes utilize 100% of physical storage bandwidth.

---

### Solution 2: SQL Composite Indexing Rules
1. **Optimal Index**: `(tenant_id, status, created_at)`.
   - **Reasoning**:
     - `tenant_id = 42`: Exact match equality filter.
     - `status = 'COMPLETED'`: Exact match equality filter.
     - `created_at DESC`: Ordered range/sort filter.
     - Placing equality columns first narrows the B+Tree search space to a continuous leaf range where rows are pre-sorted by `created_at`, completely eliminating an in-memory `filesort`.
2. **Adding `customer_id`**: If `customer_id` is queried frequently, appending it to the end or creating `(tenant_id, status, customer_id, created_at)` will be required.

---

### Solution 3: Isolation Levels and Phantom Reads
1. **Visibility**:
   - Under **Read Committed**, Transaction A will see the phantom row if it executes another query after Transaction B commits.
   - Under **Repeatable Read** and **Serializable**, Transaction A will NOT see the newly inserted row.
2. **PostgreSQL MVCC**: Under `REPEATABLE READ`, PostgreSQL takes a snapshot of the transaction status at the start of Transaction A. Any row inserted by a transaction that committed after this snapshot timestamp is invisible to Transaction A.

---

### Solution 4: Connection Pool Sizing Math
1. **Connection Overload**:
   - Total connections = $20 \text{ pods} \times 50 = 1,000\text{ connections}$.
   - An 8-core CPU can only physically execute 8 threads simultaneously. Having 1,000 active database connections causes massive CPU thrashing, context switching, memory consumption for connection buffers, and disk I/O queue lockups.
2. **HikariCP Sizing**:
   - Optimal pool size $\approx (8 \times 2) + 1 = 17\text{ to } 25\text{ connections total}$ across the entire database!
   - Deploy an external connection pooler like **PgBouncer** between the 20 pods and the database to multiplex 1,000 application connections onto ~25 real PostgreSQL server backends.

---

### Solution 5: SQL vs NoSQL Selection Matrix
- **Subsystem 1 (Billing & Claims)**: **Relational Database (PostgreSQL / CockroachDB)**. Strict ACID guarantees, multi-table transactions, referential integrity (foreign keys), and structured schema prevent financial ledger corruption or double-billing.
- **Subsystem 2 (Sensor Telemetry)**: **Time-Series / Wide-Column Database (TimescaleDB / Cassandra / InfluxDB)**. 500,000 writes/sec requires high sequential append throughput, automatic time-based partitioning (chunking), columnar compression, and automated TTL rollups for downsampling old data.
