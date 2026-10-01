import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\15-storage-and-search"

files = {
    "01-storage-paradigms-block-file-object.md": """# Storage Paradigms: Block vs File vs Object Storage

Storage architectures are divided into three primary paradigms, each optimized for different access patterns, latency constraints, and scalability characteristics.

```mermaid
graph TD
    subgraph "1. Block Storage (EBS / SAN)"
        OS1[Operating System] -->|Raw Sectors / Blocks (SCSI / NVMe)| RawDisk[Unformatted 4KB Blocks]
        Note over RawDisk: Ultra-low sub-millisecond latency. Single VM attach.
    end

    subgraph "2. File Storage (NFS / EFS)"
        OS2[Client A] -->|POSIX Hierarchy (/mnt/shared)| NAS[File Server (NFS / SMB)]
        OS3[Client B] -->|POSIX Hierarchy (/mnt/shared)| NAS
        Note over NAS: Multi-instance shared directories with file locking.
    end

    subgraph "3. Object Storage (S3 / GCS)"
        ClientApp[Any Application] -->|HTTP REST: GET /bucket/key| S3[Global Object Store]
        Note over S3: Infinite horizontal scale. Immutable flat namespace with metadata.
    end
```

---

## 1. Comprehensive Paradigm Comparison

| Dimension | Block Storage (AWS EBS, SAN) | File Storage (AWS EFS, NFS) | Object Storage (AWS S3, MinIO) |
| :--- | :--- | :--- | :--- |
| **Data Format** | Raw byte blocks (no metadata) | Hierarchical directory tree | Flat key-value store + rich metadata |
| **Interface** | Low-level protocols (NVMe, iSCSI, Fibre Channel) | POSIX filesystem API (`open`, `read`, `seek`) | HTTP REST API (`GET`, `PUT`, `DELETE`) |
| **Access Latency** | Sub-millisecond (0.1ms - 1ms) | 2ms - 10ms | 20ms - 100ms |
| **Concurrent Access**| Typically 1 instance at a time | Hundreds of instances concurrently | Millions of concurrent clients globally |
| **Modifications** | In-place random read/write byte mutations | Partial updates, append, file locking | Immutable: Modifying 1 byte requires re-uploading entire object |
| **Scalability** | Terabytes per volume | Petabytes | Virtually infinite (Exabytes) |
| **Cost** | High ($0.08 - $0.12 / GB-month) | High ($0.30 / GB-month) | Very Low ($0.02 / GB-month) |
| **Best For** | Relational databases (PostgreSQL data directory), OS boot disks | Shared legacy home dirs, CMS media roots | Backups, video files, ML datasets, data lakes |

---

## 2. Key Takeaways

- Use **Block Storage** for high-IOPS transactional databases requiring random in-place updates.
- Use **File Storage** when multiple legacy applications or Kubernetes pods must mount a shared POSIX filesystem.
- Use **Object Storage** as the primary storage layer for distributed applications, backups, static media, and Big Data lakes.
""",

    "02-distributed-file-systems.md": """# Distributed File Systems (HDFS, Ceph, and GlusterFS)

Distributed file systems pool physical storage across hundreds or thousands of networked commodity servers, presenting a unified, fault-tolerant namespace.

```mermaid
graph TD
    subgraph "HDFS Architecture (Master-Worker)"
        Client[HDFS Client]
        NameNode[NameNode (Master: Metadata & Block Map)]
        DataNode1[DataNode 1 (Block A, B)]
        DataNode2[DataNode 2 (Block A, C)]
        DataNode3[DataNode 3 (Block B, C)]

        Client -->|1. Request block locations| NameNode
        NameNode -.->|Returns DataNode IPs| Client
        Client -->|2. Parallel stream read| DataNode1
        Client -->|2. Parallel stream read| DataNode2
    end
```

---

## 1. Hadoop Distributed File System (HDFS) Architecture

HDFS was designed for batch streaming workloads (MapReduce, Spark) with large sequential files:
- **Large Block Size**: Default 128MB or 256MB blocks (minimizes metadata overhead on the NameNode).
- **Single Master (NameNode)**: Holds all directory metadata and block mapping in memory. Highly performant, but historical single-point-of-failure and memory capacity bottleneck.
- **Write-Once-Read-Many (WORM)**: Files cannot be modified in-place; only sequential appends are allowed.
- **Replication**: Default 3x rack-aware replication (2 copies in local rack, 1 copy in a remote rack).

---

## 2. Ceph: Decentralized CRUSH Algorithm

Ceph eliminates the centralized metadata lookup bottleneck entirely using the **CRUSH** (Controlled Replication Under Scalable Hashing) algorithm.

```mermaid
graph LR
    Client[Ceph Client] -->|Calculates mathematically:<br/>CRUSH(Object_ID, Cluster_Map)| OSD[Direct Target: Storage Daemon (OSD)]
    Note over Client: Zero lookup queries to a central metadata server!
```

Clients compute the exact storage node (OSD) mathematically on the fly, allowing Ceph clusters to scale to tens of thousands of nodes without metadata server saturation.

---

## 3. Key Takeaways

- HDFS is optimized for high-throughput batch processing of massive sequential files.
- Ceph eliminates centralized metadata bottlenecks using deterministic mathematical mapping (CRUSH).
- Cloud object storage (S3) has largely replaced on-premises HDFS for modern cloud-native analytics.
""",

    "03-blob-storage-and-large-file-transfers.md": """# Blob Storage and Large File Transfers

Uploading and serving massive files (gigabytes to terabytes, such as 4K videos or database backups) requires specialized streaming, multipart chunking, and presigned security patterns.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Browser / Mobile
    participant API as Backend API Server
    participant S3 as AWS S3 / Object Store

    Client->>API: POST /upload/initiate { filename: "movie.mp4", size: 5GB }
    API->>S3: InitiateMultipartUpload
    S3-->>API: Returns UploadID
    API->>S3: GeneratePresignedUploadURLs(UploadID, Chunks: 1000)
    API-->>Client: Returns Presigned S3 URLs for each 5MB chunk
    
    par Parallel Direct Chunk Upload (Bypasses Backend API!)
        Client->>S3: PUT chunk_1 to Presigned URL 1
        Client->>S3: PUT chunk_2 to Presigned URL 2
        Client->>S3: PUT chunk_N to Presigned URL N
    end
    
    Client->>API: POST /upload/complete { UploadID, ETags: [...] }
    API->>S3: CompleteMultipartUpload(UploadID, ETags)
    S3-->>API: 200 OK (Object Assembled)
    API-->>Client: Upload Successful!
```

---

## 1. Direct-to-Storage with Presigned URLs

### The Anti-Pattern:
Uploading files through your application backend servers saturates backend network bandwidth, exhausts worker threads, and risks connection timeouts on slow mobile networks.

### The Best Practice:
Generate short-lived (15-minute) **Presigned URLs** with cryptographic signatures. The client uploads data **directly to object storage (S3)**, completely bypassing your application servers.

---

## 2. Multipart Upload Mechanics

For files larger than 100MB, multipart uploads are mandatory:
1. **Parallelism**: Chunks (typically 5MB - 20MB) upload in parallel across multiple TCP sockets, saturating client bandwidth.
2. **Resumability**: If chunk 47 fails due to network drop, only chunk 47 is retried—not the entire 5GB file.
3. **Pipelining**: Uploading can begin while the file is still being generated or recorded on the client device.

---

## 3. Key Takeaways

- Never stream large file uploads or downloads through application backend memory; always use direct-to-storage Presigned URLs.
- Always use Multipart Uploads for files $> 100\text{MB}$ to support parallel chunking and granular retry.
- Front public blob downloads with a Content Delivery Network (CDN) to cache static media close to users.
""",

    "04-full-text-search-and-inverted-indexes.md": """# Full-Text Search and Inverted Indexes

Relational databases use B+Tree indexes, which fail on text search queries containing wildcard substrings (`WHERE text LIKE '%system%'`) because they require full sequential table scans. Search engines (Elasticsearch, OpenSearch) solve this using **Inverted Indexes**.

```mermaid
graph TD
    Doc1["Doc 1: 'Distributed systems are scalable'"]
    Doc2["Doc 2: 'Scalable systems require monitoring'"]

    subgraph Text Analysis Pipeline
        Tokenize[Tokenizer: Lowercase & Split words]
        Filter[Filter: Remove Stop Words ('are')]
        Stem[Stemming: 'scalable' -> 'scale']
    end

    Doc1 --> Tokenize
    Doc2 --> Tokenize
    Tokenize --> Filter --> Stem --> InvertedIndex

    subgraph "Inverted Index (Posting Lists)"
        Term1["'distribut' -> [Doc 1]"]
        Term2["'scale'      -> [Doc 1, Doc 2]"]
        Term3["'system'     -> [Doc 1, Doc 2]"]
        Term4["'monitor'    -> [Doc 2]"]
    end
```

---

## 1. Anatomy of an Inverted Index

An Inverted Index maps every unique word (term) to a sorted list of document IDs where it appears (the **Posting List**):

### Fast Boolean Queries:
To execute: `scale AND monitor`:
1. Fetch posting list for `scale`: `[Doc 1, Doc 2]`
2. Fetch posting list for `monitor`: `[Doc 2]`
3. Compute intersection using two-pointer scan: $\implies \mathbf{[Doc 2]}$ (Sub-millisecond execution over millions of docs!).

---

## 2. Relevance Scoring: TF-IDF vs BM25

Modern search engines rank documents using **BM25 (Best Matching 25)**:
- **Term Frequency (TF)**: How often does the word appear in this document? (With saturation to prevent keyword stuffing).
- **Inverse Document Frequency (IDF)**: How rare is this word across all documents? Rare words ("Kubernetes") carry vastly more weight than common words ("computer").
- **Document Length Normalization**: Shorter documents matching the term receive higher ranking than long documents.

---

## 3. Elasticsearch Distributed Architecture

```mermaid
graph TD
    Index[Index: 'products' - 3 Shards, 1 Replica]
    Index --> P0[Primary Shard 0]
    Index --> P1[Primary Shard 1]
    Index --> P2[Primary Shard 2]
    P0 -.->|Replicated| R0[Replica Shard 0]
    P1 -.->|Replicated| R1[Replica Shard 1]
    P2 -.->|Replicated| R2[Replica Shard 2]
```

- **Query Phase**: The coordinating node broadcasts the search query to all shards (primary or replica). Each shard computes local BM25 top-K results.
- **Fetch Phase**: Coordinating node merges priority queues, requests full document sources for the top $K$, and returns to client.

---

## 4. Key Takeaways

- Inverted indexes turn text search from an $O(N)$ full table scan into an $O(1)$ dictionary lookup and posting list intersection.
- Use BM25 scoring for human-like relevance ranking.
- Synchronize search engines with relational databases asynchronously using CDC (Debezium) to prevent dual-write inconsistencies.
""",

    "05-geospatial-indexing.md": """# Geospatial Indexing: Geohash, Quadtree, and Uber H3

Querying physical locations ("Find the 10 closest drivers within 3 km of latitude 37.77, longitude -122.41") requires specialized 2D geospatial indexing structures.

```mermaid
graph TD
    subgraph "Spatial Indexing Approaches"
        GH[Geohash: 1D Z-Order Curve Hashing]
        QT[Quadtree: Recursive 2D Box Subdivisions]
        H3[Uber H3: Hexagonal Hierarchical Spatial Index]
    end

    subgraph "Uber H3 Hexagonal Grid"
        Hex[Hexagon Cell: Every neighbor is equidistant!]
    end
```

---

## 1. The 2D B-Tree Problem

Relational B+Tree indexes are 1-dimensional. An index on `(latitude, longitude)` can efficiently filter by `latitude`, but must scan all matching rows to filter by `longitude`. Querying bounding boxes becomes slow and inefficient.

---

## 2. Geospatial Indexing Strategies

### 1. Geohash
- Interleaves bits of latitude and longitude into a Base32 string (e.g., `9q8yy`).
- **Prefix Matching**: Shared prefix means spatial proximity. All points in `9q8yy` are inside the same $\approx 5\text{km} \times 5\text{km}$ box.
- *Edge Case*: Boundary discontinuity at the Prime Meridian and Equator.

### 2. Quadtree
- Recursively divides a 2D bounding space into 4 quadrants (NW, NE, SW, SE) when point density exceeds a threshold (e.g., 100 drivers per node).
- Dynamically adapts to density: downtown Manhattan has deep quadtree branches; rural deserts have shallow nodes.

```mermaid
graph TD
    Root[Global World Node] --> NW[North-West]
    Root --> NE[North-East]
    Root --> SW[South-West]
    Root --> SE[South-East: High Density!]
    SE --> SE1[Sub-NW]
    SE --> SE2[Sub-NE]
    SE --> SE3[Sub-SW]
    SE --> SE4[Sub-SE]
```

### 3. Uber H3 (Hexagonal Grid)
- Partitions the globe into hexagonal cells across 16 hierarchical resolutions.
- **Why Hexagons?** Unlike squares where diagonal neighbors are $\sqrt{2} \times$ farther than adjacent neighbors, **every neighbor in a hexagonal grid is exactly equidistant**. This property makes radius searches and routing algorithms drastically simpler.

---

## 3. Key Takeaways

- Use **Uber H3** for ride-sharing, food delivery, and spatial dispatch due to equidistant hexagonal neighbor math.
- Use **Geohashes** in relational or KV stores (Redis `GEOADD`) for simple prefix-based radius lookups.
- Use **Quadtrees** in-memory when managing highly dynamic, non-uniform spatial point density.
""",

    "06-data-compression-deduplication-and-tiering.md": """# Data Compression, Deduplication, and Lifecycle Tiering

Managing petabyte-scale storage economically requires combining byte-level data compression, block-level deduplication, and automated lifecycle storage tiering.

```mermaid
graph LR
    Hot[Hot Tier: NVMe SSD / S3 Standard<br/>$0.023/GB | Sub-10ms Access]
    Warm[Warm Tier: HDD / S3 Infrequent Access<br/>$0.0125/GB | 50ms Access]
    Cold[Cold Tier: S3 Glacier Flexible<br/>$0.0036/GB | 3-5 Hours Retrieval]
    Archive[Deep Archive: S3 Glacier Deep<br/>$0.00099/GB | 12 Hours Retrieval]

    Hot -->|After 30 Days of Zero Reads| Warm
    Warm -->|After 90 Days| Cold
    Cold -->|After 365 Days| Archive
```

---

## 1. Modern Compression Algorithms

| Algorithm | Compression Ratio | Compression Speed | Decompression Speed | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Zstandard (Zstd)** | Very High | Fast (Tunable levels 1-22) | Ultra-Fast (~1.2 GB/s) | Modern general default, Kafka topics, Parquet |
| **Snappy / LZ4** | Moderate | Blazing Fast (~500 MB/s) | Blazing Fast (~2 GB/s) | Real-time RPC payloads, LSM-tree block stores |
| **Gzip (DEFLATE)** | High | Slow | Moderate | Legacy HTTP assets, static web content |

---

## 2. Block-Level Data Deduplication

Backup systems and storage arrays (Pure Storage, NetApp) eliminate duplicate blocks:
1. Divide incoming streams into chunks (e.g., variable-length Rabin fingerprinting).
2. Hash chunk content: $\text{Hash} = \text{SHA-256}(\text{Chunk})$.
3. Check index: If hash exists, increment reference pointer and discard duplicate bytes.
4. Typical deduplication ratio in enterprise backup systems: **10:1 to 30:1** storage savings!

---

## 3. Key Takeaways

- Standardize on **Zstandard (Zstd)** for high compression ratios with sub-millisecond decompression speed.
- Implement automated S3 Lifecycle policies to push cold data to Glacier Deep Archive, slashing storage bills by up to 95%.
- Employ variable-length chunk deduplication for disk backup and volume snapshot systems.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 15 complete.")
