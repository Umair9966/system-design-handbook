# Section 05: Databases — Practice Exercises

---

### Problem 1: B+Tree vs LSM-Tree Write Amplification
A logging service ingests 100,000 random write events per second (each 500 bytes).
1. Explain why a traditional B+Tree storage engine (like InnoDB) suffers severe write amplification and disk I/O bottlenecks under random write workloads.
2. How does an LSM-tree (Log-Structured Merge Tree) achieve 10x higher write throughput for this specific pattern?
> **Hint**: Consider random 16KB page writes vs sequential append-only logs and MemTables.

---

### Problem 2: SQL Composite Indexing Rules
A table `orders` has columns: `tenant_id`, `created_at`, `status`, `customer_id`.
A frequent query is:
`SELECT * FROM orders WHERE tenant_id = 42 AND status = 'COMPLETED' ORDER BY created_at DESC LIMIT 20;`
1. Propose an optimal composite B+Tree index for this query. Explain the ordering of columns based on equality vs range filtering.
2. What happens if the query adds `AND customer_id = 99`? Does the index still cover it efficiently?
> **Hint**: Place equality columns first, followed by sorting/range columns.

---

### Problem 3: Isolation Levels and Phantom Reads
Transaction A calculates the total sum of balances across all accounts in a branch.
Simultaneously, Transaction B inserts a new account with a balance of $1,000 and commits.
1. Under which standard ANSI isolation levels will Transaction A see the newly inserted row?
2. How does Multi-Version Concurrency Control (MVCC) in PostgreSQL handle this scenario under `REPEATABLE READ`?
> **Hint**: Review Read Committed vs Repeatable Read vs Serializable.

---

### Problem 4: Connection Pool Sizing Math
A backend service runs on 20 Kubernetes pods. Each pod configures a database connection pool with `max_connections = 50`.
The PostgreSQL database server has 8 vCPUs and 32 GB RAM.
1. What is the total potential concurrent connection count hitting PostgreSQL? Why will this degrade rather than improve database throughput?
2. Using the HikariCP recommended formula ($Connections = (CoreCount \times 2) + EffectiveSpindleCount$), what should the total database connection limit be?
> **Hint**: Context switching between hundreds of operating system processes kills database CPU efficiency.

---

### Problem 5: SQL vs NoSQL Selection Matrix
You are designing the storage layer for a healthcare platform with two distinct data requirements:
- Data Subsystem 1: Patient billing, insurance claims, and financial accounting ledgers.
- Data Subsystem 2: High-frequency IoT heart-rate sensor telemetry emitted once every second by 500,000 wearable patient monitors.
Select the optimal database family (Relational, Time-Series, Document, Wide-Column) for each subsystem and justify your decision using ACID and scale requirements.
> **Hint**: Compare transactional correctness against append-heavy time-series throughput.

---

👉 **Solutions**: Check [Section 05 Solutions](05-databases-solutions.md).
