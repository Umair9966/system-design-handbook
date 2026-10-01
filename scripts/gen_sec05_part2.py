import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

save("docs/05-databases/06-normalization-vs-denormalization.md", """# Normalization vs Denormalization

## Overview
Database schema design balances two competing forces:
- **Normalization**: The process of organizing data in a database to reduce redundancy and eliminate update anomalies by decomposing tables into smaller, linked entities adhering to normal forms (1NF, 2NF, 3NF, BCNF).
- **Denormalization**: The deliberate introduction of redundancy into a schema by copying data across tables to eliminate expensive multi-table `JOIN` operations and optimize read performance.

```mermaid
graph TD
    subgraph Normalized Schema [Optimized for Writes & Integrity]
        O1[Orders: id, customer_id, total] --> C1[Customers: id, name, email]
        O1 --> OA1[Addresses: id, street, zip]
    end
    subgraph Denormalized Schema [Optimized for Read Latency]
        O2[Orders: id, customer_id, customer_name, customer_email, street, zip, total]
    end
```

## Why It Matters
In high-scale systems, joining 5 large normalized tables across millions of rows requires extensive memory sorting, hash joins, and random disk page fetches that push query latencies into hundreds of milliseconds. Strategic denormalization trades disk storage for lightning-fast, single-table reads.

## Core Concepts & The Normal Forms
1. **First Normal Form (1NF)**: Each column contains atomic (indivisible) values; no repeating groups or arrays.
2. **Second Normal Form (2NF)**: Meets 1NF, and all non-key attributes are fully functionally dependent on the entire primary key (no partial key dependencies).
3. **Third Normal Form (3NF)**: Meets 2NF, and no non-key attribute depends transitively on the primary key (no transitive dependencies; e.g., storing `zip_code` and `city` in the user table).
4. **Update, Insertion, and Deletion Anomalies**:
   - *Update Anomaly*: Updating a customer's address in a denormalized order table requires updating 10,000 historical rows. If the query fails halfway, customer records become inconsistent.
   - *Deletion Anomaly*: Deleting an order accidentally deletes the only historical record of a customer.

## How It Works: Strategic Denormalization Patterns
1. **Pre-Computed Aggregates**: Storing `comment_count` directly on the `posts` table instead of running `SELECT COUNT(*) FROM comments WHERE post_id = ?` on every page load. Updated via database triggers or transactional code increments.
2. **Read-Heavy Snapshotting**: Copying user address and product price at the time of purchase into the `order_items` table. This serves both performance and business audit compliance (future price changes must not alter historical receipts!).

## Trade-offs
| Architectural Property | Normalized (3NF) | Denormalized |
| :--- | :--- | :--- |
| **Read Performance** | Slower (requires multi-table `JOIN`s) | **Sub-millisecond (single-table lookup)**|
| **Write Performance** | **Fast (single write in one place)** | Slower (must update all redundant copies)|
| **Data Consistency** | **Guaranteed (Single Source of Truth)**| Risk of divergent data / anomalies |
| **Storage Overhead** | Minimal | High (redundant columns duplicated) |

## When to Use / When NOT to Use
### When to Normalize (3NF)
- Write-heavy transactional systems (OLTP), core accounting ledgers, systems where data changes frequently and inconsistency is intolerable.

### When to Denormalize
- Read-heavy workloads ($> 100:1$ read/write ratio), dashboard aggregations, document and wide-column NoSQL databases, data warehouses (OLAP Star/Snowflake schemas).

## Real-World Examples
- **Twitter/X Home Timelines**: Tweets are aggressively denormalized directly into follower in-memory timeline lists. Storing only tweet IDs and executing 800 relational joins on every user refresh would bring Twitter's database fleet to a standstill.
- **Amazon Order History**: Product titles, seller names, and prices are permanently denormalized into the order record at the moment of checkout.

## Common Pitfalls
- **Denormalizing Without Transactions**: Copying data across tables without wrapping the mutations in an atomic transaction, leaving orphan or contradictory records when crashes occur.
- **Premature Denormalization**: Denormalizing tables before hitting performance bottlenecks, creating technical debt and complex multi-table update logic for zero measurable gain.

## Key Takeaways
- **Normalize for writes and integrity; denormalize for read performance.**
- Denormalization is mandatory in NoSQL databases because they do not support relational joins.
- Always use transactions or event-driven reconcilers when updating denormalized data copies.

## Common Interview Questions
1. What is an update anomaly, and how does database normalization prevent it?
2. When is denormalization preferred over adding database indexes?
3. How do you maintain data consistency across redundant denormalized fields?

## Further Reading
- [E. F. Codd: A Relational Model of Data for Large Shared Data Banks (1970)](https://dl.acm.org/doi/10.1145/362384.362685)
- [Designing Data-Intensive Applications: Chapter 3 (Storage and Retrieval)](https://dataintensive.net/)
""")

save("docs/05-databases/07-oltp-vs-olap-and-columnar-storage.md", """# OLTP vs OLAP: Row-Oriented vs Columnar Storage

## Overview
Data processing in production architectures splits into two fundamentally divergent paradigms based on query access patterns:
- **OLTP (Online Transaction Processing)**: High-throughput, low-latency, concurrent reads and writes of individual rows (e.g., e-commerce orders, user logins, banking transactions).
- **OLAP (Online Analytical Processing)**: Complex analytical queries scanning millions of rows across a few columns to compute aggregations, trends, and business intelligence reports.

```mermaid
graph TD
    subgraph Row-Oriented Storage [OLTP: PostgreSQL / MySQL]
        R1[Row 1: ID, Name, Age, Salary]
        R2[Row 2: ID, Name, Age, Salary]
    end
    subgraph Columnar Storage [OLAP: ClickHouse / Parquet]
        C1[Column ID: 1, 2, 3...]
        C2[Column Name: Alice, Bob...]
        C3[Column Age: 25, 30...]
        C4[Column Salary: 100k, 120k...]
    end
```

## Why It Matters
Running an analytical query like `SELECT AVG(salary) FROM employees WHERE department = 'Engineering'` on a row-oriented OLTP database forces the disk controller to read every single employee's full row (names, addresses, phone numbers) from disk into RAM, wasting 95% of I/O bandwidth. In a columnar database, the disk controller reads **only the salary and department columns**, executing 100x faster.

## Core Concepts & Architectural Comparison
1. **Row-Oriented Layout (OLTP)**:
   - Data is stored on disk row by row: `[Row1_col1, Row1_col2, ...] [Row2_col1, Row2_col2, ...]`.
   - *Advantage*: Writing a new row or fetching an entire user record by ID requires writing/reading a single contiguous block of disk.
2. **Column-Oriented Layout (OLAP)**:
   - Data is stored on disk column by column: `[Col1_row1, Col1_row2, ...] [Col2_row1, Col2_row2, ...]`.
   - *Advantage*: An analytical query reading 2 columns out of a 100-column table skips 98% of the data on disk.
3. **Columnar Compression**:
   - Because all values in a column share the exact same data type, compression algorithms (Run-Length Encoding, Dictionary Encoding, Bit-Packing) achieve **5x to 10x compression ratios**, allowing petabytes of analytical data to fit in modest disk arrays.
4. **Vectorized Query Execution**:
   - Modern columnar engines (ClickHouse, DuckDB) process blocks of column data using **SIMD (Single Instruction, Multiple Data)** CPU registers, processing millions of rows per CPU cycle.

## Trade-offs
| Dimension | OLTP (Row-Oriented) | OLAP (Columnar) |
| :--- | :--- | :--- |
| **Typical Query** | `SELECT * WHERE id = ?` | `SELECT dept, AVG(salary) GROUP BY dept` |
| **Latency Target** | Sub-10ms (Real-time user facing) | Seconds to minutes (Analytical reports) |
| **Write Pattern** | High-frequency random `INSERT` / `UPDATE` | Bulk batch append (Millions of rows at once) |
| **Update / Delete**| In-place single-row mutations | Extremely expensive (requires rewriting columnar blocks)|
| **Compression** | Poor (mixing strings, ints, dates in a row)| **Phenomenal (5x - 10x compression ratio)** |

## When to Use / When NOT to Use
### When to Choose OLTP (Row-Oriented)
- Primary transactional databases: PostgreSQL, MySQL, CockroachDB. Handling user registration, shopping carts, checkout, auth.

### When to Choose OLAP (Columnar)
- Data warehousing and analytics: ClickHouse, Snowflake, Google BigQuery, Amazon Redshift, Apache Druid, Parquet files on S3.

## Real-World Examples
- **Uber Data Platform**: Separates its online dispatch database (OLTP on MySQL/Schemaless) from its analytical pipeline. CDC streams real-time trip data into **Apache Hudi / ClickHouse** (OLAP) so data scientists can run queries over billions of historical rides.
- **Financial Fraud Detection**: Streams transaction logs into ClickHouse to calculate rolling 30-day user spending averages in 5 milliseconds.

## Common Pitfalls
- **Running Analytical Reports on the Primary OLTP Database**: A marketing manager runs a massive cross-table analytical query during Black Friday, exhausting PostgreSQL buffer pool RAM and crashing the online checkout API. (Always offload analytics to read replicas or a dedicated OLAP warehouse!).
- **Treating OLAP Databases Like OLTP**: Attempting to execute single-row `UPDATE user SET email = ? WHERE id = 1` inside ClickHouse or Snowflake, causing massive table re-compaction and disk thrashing.

## Key Takeaways
- Never run heavy analytical aggregation queries on your primary OLTP production database.
- Row-oriented storage is optimized for writing and reading entire rows.
- Columnar storage is optimized for reading and aggregating a subset of columns across millions of rows.

## Common Interview Questions
1. Why is columnar storage exponentially faster than row-oriented storage for analytical aggregation queries?
2. How does Run-Length Encoding (RLE) achieve high compression on columnar data?
3. How do you stream data from an OLTP transactional database into an OLAP data warehouse in near real-time?

## Further Reading
- [Daniel Abadi et al.: The Design and Implementation of Modern Column-Oriented Database Systems (2013)](https://www.nowpublishers.com/article/Details/DBS-024)
- [ClickHouse Architecture Overview](https://clickHouse.com/docs/en/development/architecture)
""")

save("docs/05-databases/08-storage-engines-btree-vs-lsm-tree.md", """# Storage Engines: B+Trees vs Log-Structured Merge (LSM) Trees

## Overview
A database **storage engine** is the low-level software component responsible for reading, writing, and organizing data pages on physical storage (SSD/NVMe). Modern databases are divided between two dominant storage architectures:
- **B+Tree Storage Engines**: Read-optimized, in-place update structures operating on fixed-size pages (e.g., 16KB pages in MySQL InnoDB and PostgreSQL).
- **LSM-Tree (Log-Structured Merge-Tree) Storage Engines**: Write-optimized, append-only structures appending writes to an in-memory buffer before flushing immutable sequential sorted files to disk (e.g., RocksDB, Cassandra, ScyllaDB).

```mermaid
graph TD
    subgraph LSM-Tree Write Path
        Write[Incoming Write] --> WAL[Append to WAL on Disk]
        Write --> MemTable[Write to In-Memory MemTable: SkipList]
        MemTable -->|Buffer Full: Flush to Disk| L0[SSTable Level 0]
        L0 -->|Background Compaction| L1[SSTable Level 1]
    end
```

## Why It Matters
Storage hardware has a physical reality: **sequential writes are orders of magnitude faster than random writes**, even on modern NVMe SSDs. B+Trees require random in-place page updates that cause severe write amplification. LSM-Trees convert random writes into sequential disk streams, achieving extraordinary write throughput.

## Core Concepts & Architectural Comparison
1. **B+Tree In-Place Updates**:
   - Modifying a single 50-byte record requires updating the corresponding 16KB page in the buffer pool.
   - When the page is flushed to disk, 16,384 bytes are written to disk for a 50-byte change (**High Write Amplification**).
   - *Advantage*: Point lookups and range scans find data in a fixed, known tree location with minimal read amplification.
2. **LSM-Tree Structure & Mechanics**:
   - **MemTable**: In-memory sorted data structure (typically a SkipList or Red-Black Tree) accepting concurrent writes.
   - **Write-Ahead Log (WAL)**: Sequential disk log guaranteeing crash recovery for the MemTable.
   - **SSTable (Sorted String Table)**: Immutable, sorted disk files. Once written, an SSTable is never modified.
   - **Compaction**: Background merge-sort process that reads multiple older SSTables, discards overwritten/deleted keys (tombstones), and writes a newly consolidated, sorted SSTable to the next level.
   - **Bloom Filters**: Stored in RAM for each SSTable to verify key non-existence, eliminating unnecessary disk seeks on reads.

## Trade-offs
| Metric | B+Tree (InnoDB, Postgres) | LSM-Tree (RocksDB, Cassandra) |
| :--- | :--- | :--- |
| **Write Throughput** | Moderate (bound by random I/O) | **Exceptional (sequential appends)** |
| **Write Amplification**| High (16KB dirty page flushes) | Moderate to High (due to Compaction) |
| **Read Amplification** | **Lowest (single deterministic lookup)**| Higher (must search MemTable + SSTables)|
| **Space Amplification**| Moderate (page internal fragmentation)| Low (sequential packed SSTables) |
| **Latency Stability** | Predictable | Periodic latency spikes during heavy Compaction|

## When to Use / When NOT to Use
### When to Choose B+Tree Engines
- General-purpose workloads with balanced read-write ratios or read-heavy applications where predictable, low read latency is paramount (e.g., user authentication, billing).

### When to Choose LSM-Tree Engines
- High-velocity write-heavy workloads (e.g., logging pipelines, financial market tick data, time-series metrics, distributed messaging logs).

## Real-World Examples
- **RocksDB**: Highly optimized embedded LSM-tree engine developed by Meta, used as the underlying storage foundation for CockroachDB, TiKV, Kafka Streams, and MySQL (MyRocks).
- **Apache Cassandra**: Employs an LSM-tree architecture to sustain millions of writes per second across commodity servers without locking tables.

## Common Pitfalls
- **Compaction Storms in LSM-Trees**: If write ingestion outpaces background compaction bandwidth, uncompacted SSTables accumulate (Level 0 file explosion). Read latency collapses as queries must search 50 separate SSTable files on disk.
- **Tombstone Pollution in Cassandra**: Deleting millions of rows creates "tombstones" (deletion markers). Subsequent range queries must scan thousands of tombstones, causing query timeouts.

## Key Takeaways
- B+Trees optimize for **fast, predictable reads** at the cost of random write I/O.
- LSM-Trees optimize for **massive write throughput** by turning random writes into sequential disk streams.
- LSM-Trees rely on **Bloom Filters** and background **Compaction** to maintain acceptable read latency.

## Common Interview Questions
1. Why are sequential disk writes so much faster than random writes, even on solid-state NVMe drives?
2. What is the role of an SSTable and a MemTable in an LSM-tree storage engine?
3. How do Bloom filters mitigate high read amplification in LSM-tree databases?

## Further Reading
- [Patrick O'Neil et al.: The Log-Structured Merge-Tree (LSM-Tree) (1996)](https://www.cs.umb.edu/~poneil/lsmtree.pdf)
- [RocksDB Architecture Overview](https://github.com/facebook/rocksdb/wiki/RocksDB-Basics)
""")

save("docs/05-databases/09-connection-pooling.md", """# Database Connection Pooling and Resource Management

## Overview
Establishing a connection to a database server is an expensive operation requiring a TCP 3-way handshake, TLS cryptographic negotiation, authentication validation, and backend process memory allocation. A **database connection pool** maintains a pre-warmed cache of active database connections that application threads borrow, execute queries on, and return to the pool.

```mermaid
graph LR
    subgraph Application Tier [100 Web Worker Threads]
        T1[Thread 1] --> CP{Connection Pool: Size 10}
        T2[Thread 2] --> CP
        T3[Thread 100] --> CP
    end
    CP -->|Multiplexed Over 10 Warm Sockets| DB[(PostgreSQL Server: 8 vCPUs)]
```

## Why It Matters
Without connection pooling, an API receiving 5,000 requests per second will attempt to open 5,000 simultaneous TCP connections to PostgreSQL. In PostgreSQL, each client connection spawns a dedicated operating system process consuming **10MB to 20MB of RAM**. Opening 5,000 connections instantly consumes 50 GB of RAM, triggering CPU context-switching thrashing and crashing the database via the Linux Out-Of-Memory (OOM) killer.

## Core Concepts
- **Connection Lifecycle**:
  - *Borrow*: Application thread requests a connection; if all are in use, the thread blocks for up to `connectionTimeout` (e.g., 5 seconds).
  - *Execute*: Thread runs query.
  - *Return*: Thread closes connection object, returning the active socket back to the pool (never actually closing the underlying TCP socket).
- **The HikariCP Pool Sizing Formula**:
  Contrary to intuition, **fewer connections yield higher throughput**. Sizing pools to hundreds of connections degrades performance due to disk queue contention and CPU context switching.
  $$\\text{Optimal Pool Size} = (\\text{CPU Cores} \\times 2) + \\text{Effective Spindle Count}$$
  *Example*: For a database server with 8 CPU cores and an SSD (spindle count = 1):
  $$\\text{Connections} = (8 \\times 2) + 1 = 17\\text{ connections!}$$
- **Connection Leak**: A catastrophic bug where an application thread acquires a connection but fails to return it (e.g., due to an unhandled exception without a `finally` or `try-with-resources` block), permanently starving the pool until all application requests hang.

## Trade-offs
| Pool Strategy | Benefit | Risk / Trade-off |
| :--- | :--- | :--- |
| **Small Dedicated Pool (~20 connections)** | Maximum DB CPU cache efficiency, zero thrashing | High-load traffic spikes queue at the pool |
| **Large Pool (~500 connections)** | Lower thread queueing delay under brief bursts | Destroys database performance; risk of DB OOM |
| **External Proxy Pooler (PgBouncer)** | Scales to 10,000+ client app connections | Incompatible with session-level SQL features (`LISTEN`/`NOTIFY`)|

## When to Use / When NOT to Use
### When Connection Pooling is Mandatory
- 100% of all production relational database applications (PostgreSQL, MySQL, Oracle).

### When to Deploy an External Connection Pooler (PgBouncer)
- In serverless architectures (AWS Lambda) or microservice clusters running hundreds of Kubernetes pods, where total pod count multiplied by local pool size exceeds maximum database connection limits.

## Real-World Examples
- **AWS Aurora Serverless & RDS Proxy**: AWS built **Amazon RDS Proxy** specifically to solve connection exhaustion caused by serverless AWS Lambda functions scaling to 10,000 concurrent containers.
- **HikariCP**: The fastest Java connection pool, engineered using byte-code instrumentation and lock-free concurrency to process millions of connection checkouts per second with zero overhead.

## Common Pitfalls
- **Setting Connection Pool Size = Number of Web Threads**: Configuring a pool of 200 connections on 50 Kubernetes pods, sending $50 \\times 200 = 10,000$ simultaneous connections to a 16-core database server.
- **Connection Leaks on Exception Paths**: Omitting proper cleanup blocks, leaking one connection per failed query until the pool is 100% exhausted.

## Key Takeaways
- Establishing database connections is expensive; connection pools keep a small set of warm sockets alive.
- **Fewer connections mean higher throughput**; follow the HikariCP sizing formula ($\text{Cores} \times 2 + \text{Disk}$).
- Deploy an external pooler (PgBouncer / RDS Proxy) when scaling serverless or microservice containers.

## Common Interview Questions
1. Why does increasing a database connection pool from 20 to 500 often reduce total system throughput?
2. What is a connection leak, and how do connection pool libraries detect it?
3. How does transaction-level pooling in PgBouncer differ from session-level pooling?

## Further Reading
- [HikariCP: About Pool Sizing (Brett Wooldridge)](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- [PostgreSQL Documentation: PgBouncer Connection Pooler](https://www.pgbouncer.org/)
""")

save("docs/05-databases/10-search-and-vector-databases.md", """# Search and Vector Databases Overview

## Overview
Modern architectures require specialized storage engines to handle search problems that relational and traditional NoSQL databases are fundamentally incapable of executing efficiently:
- **Full-Text Search Engines**: Inverted index databases optimized for unstructured text matching, fuzzy search, tokenization, and BM25 relevance ranking (Elasticsearch, OpenSearch).
- **Vector Databases**: High-dimensional vector stores optimized for semantic similarity search, artificial intelligence embeddings, and Retrieval-Augmented Generation - RAG (Pinecone, Milvus, Qdrant, pgvector).

```mermaid
graph LR
    subgraph Full-Text Search [Elasticsearch]
        Doc[Text: The quick brown fox] --> Lexer[Tokenization / Stemming]
        Lexer --> InvIdx[Inverted Index: fox -> Doc1, Doc5]
    end
    subgraph Vector Database [Pinecone / Milvus]
        Text[Text / Image] --> EmbeddingModel[LLM / Embedding Model]
        EmbeddingModel --> Vector[1536-Dimensional Float Array]
        Vector --> ANN[ANN Search: HNSW Graph / Cosine Distance]
    end
```

## Why It Matters
A relational `LIKE '%search_term%'` query forces a brutal full table scan across millions of disk pages. An **Inverted Index** resolves keyword queries in milliseconds. Meanwhile, traditional search cannot understand concepts: searching for *"affordable commute vehicle"* will miss an article titled *"cheap city bicycle"* because zero words overlap. **Vector databases** solve semantic meaning search using mathematical vector space embeddings.

## Core Concepts & Architectural Comparison
1. **Full-Text Search (Inverted Index)**:
   - Maps individual tokens/words to the list of document IDs where they occur.
   - Text processing pipeline: Character Filtering -> Tokenization -> Lowercasing -> Stemming (converting `running` to `run`) -> Stop Word Removal.
   - **BM25 Scoring**: Algorithms evaluating Term Frequency (TF) and Inverse Document Frequency (IDF) to score document relevance.
2. **Vector Databases & Embeddings**:
   - Machine learning models (OpenAI `text-embedding-3`, BERT) convert text, audio, or images into high-dimensional vectors (arrays of 768 or 1536 floating-point numbers).
   - Semantic similarity is calculated using geometric distance metrics:
     - **Cosine Similarity**: Measures the angle between two vectors (independent of magnitude).
     - **Euclidean Distance (L2)**: Measures straight-line distance.
     - **Dot Product**: Measures angle and magnitude.
3. **Approximate Nearest Neighbor (ANN) Search**:
   - Comparing a query vector against 100 million vectors sequentially ($O(N)$) is too slow.
   - **HNSW (Hierarchical Navigable Small World)**: Builds a multi-layer graph of vectors, achieving $O(\\log N)$ search latency similar to a skip list.
   - **IVFFlat (Inverted File Index)**: Clusters vectors into Voronoi cells, searching only within the closest cluster centroids.

## Trade-offs
| Search Engine Type | Query Mechanism | Strengths | Weaknesses |
| :--- | :--- | :--- | :--- |
| **Full-Text (Elasticsearch)**| Inverted Index (BM25) | Exact keyword matching, typos (fuzzy), filters | Zero semantic understanding |
| **Vector DB (Milvus/Pinecone)**| ANN Index (HNSW / Cosine)| Conceptual understanding, multimodal search | High RAM consumption; poor exact keyword filtering|
| **Hybrid Search** | Reciprocal Rank Fusion (RRF)| **Best of both worlds (Exact words + Semantic meaning)**| Requires syncing two indexes |

## When to Use / When NOT to Use
### When to Choose Full-Text Search (Elasticsearch)
- E-commerce product search with exact SKU matching, legal document discovery, log aggregation and analysis (ELK Stack).

### When to Choose Vector Databases
- LLM Retrieval-Augmented Generation (RAG), semantic question answering, reverse image search, facial recognition, personalized recommendation systems.

## Real-World Examples
- **Pinterest Visual Search**: Uses vector embeddings to allow users to photograph a piece of furniture and find visually identical items across billions of catalog images using ANN search.
- **Notion AI**: Stores document chunks as vector embeddings in vector databases, retrieving relevant knowledge snippets in under 30ms to inject into LLM prompt contexts.

## Common Pitfalls
- **High Memory Footprint of HNSW Indexes**: HNSW vector graphs must reside entirely in RAM for fast traversal; storing 50 million 1536-dimensional vectors in memory can require 300+ GB of RAM, causing massive cloud costs.
- **Ignoring Hybrid Search**: Relying purely on vector search for product catalogs; a user searching for exact part number `GTX-4080` will receive semantically related graphics cards rather than the exact product they want to buy.

## Key Takeaways
- Inverted indexes power keyword search; Vector databases power semantic meaning search.
- Exact vector distance search ($O(N)$) does not scale; production systems use **Approximate Nearest Neighbor (ANN)** algorithms like HNSW.
- The state of the art in production is **Hybrid Search**: combining BM25 keyword matching with dense vector similarity.

## Common Interview Questions
1. How does an inverted index work, and why does it outperform SQL `LIKE` queries?
2. What is Approximate Nearest Neighbor (ANN) search, and how does the HNSW graph algorithm work?
3. How do you implement a Retrieval-Augmented Generation (RAG) system using vector databases?

## Further Reading
- [Malkov & Yashunin: Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs (IEEE TPAMI 2018)](https://arxiv.org/abs/1603.09320)
- [Elasticsearch: The Definitive Guide](https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html)
""")

print("Section 05 complete.")
