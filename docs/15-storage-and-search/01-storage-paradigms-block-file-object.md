# Storage Paradigms: Block vs File vs Object Storage

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
