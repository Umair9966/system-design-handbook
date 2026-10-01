# Distributed File Systems (HDFS, Ceph, and GlusterFS)

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
