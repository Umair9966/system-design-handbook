# Data Compression, Deduplication, and Lifecycle Tiering

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
2. Hash chunk content: $	ext{Hash} = 	ext{SHA-256}(	ext{Chunk})$.
3. Check index: If hash exists, increment reference pointer and discard duplicate bytes.
4. Typical deduplication ratio in enterprise backup systems: **10:1 to 30:1** storage savings!

---

## 3. Key Takeaways

- Standardize on **Zstandard (Zstd)** for high compression ratios with sub-millisecond decompression speed.
- Implement automated S3 Lifecycle policies to push cold data to Glacier Deep Archive, slashing storage bills by up to 95%.
- Employ variable-length chunk deduplication for disk backup and volume snapshot systems.
