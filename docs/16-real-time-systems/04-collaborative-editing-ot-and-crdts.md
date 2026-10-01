# Collaborative Editing: Operational Transformation vs CRDTs

Real-time multi-user collaborative editing (Google Docs, Figma, Notion) allows multiple participants to concurrently modify shared documents without conflict or lost edits.

```mermaid
graph TD
    subgraph "Operational Transformation (OT - Google Docs)"
        ClientA[Client A] -->|Sends Operation: Insert(pos=3, 'x')| CentralServer[Central Master Server]
        ClientB[Client B] -->|Sends Operation: Delete(pos=2)| CentralServer
        Note over CentralServer: Server transforms concurrent operations using global order
    end

    subgraph "CRDTs (Conflict-free Replicated Data Types - Figma / Automerge)"
        NodeA[Peer / Client A] <-->|Peer-to-Peer / Local Edit| NodeB[Peer / Client B]
        Note over NodeA, NodeB: Mathematically guaranteed to converge without any central coordinator!
    end
```

---

## 1. Operational Transformation (OT)

Pioneered by Google Docs:
- Edits are treated as operations: $	ext{Insert}(	ext{pos}, 	ext{char})$ or $	ext{Delete}(	ext{pos})$.
- Requires a **centralized server** that acts as the single source of truth for total ordering.
- If two users submit edits concurrently at the same index, the server transforms operation $B$ against operation $A$ so that both intent and layout remain preserved.

---

## 2. Conflict-free Replicated Data Types (CRDTs)

Modern collaborative systems (Figma, Notion, Apple Notes) prefer CRDTs:
- **No Central Coordinator Required**: Nodes can edit completely offline and merge asynchronously.
- **Mathematical Convergence**: The merge operation is mathematically proven to be **Commutative** ($A \cup B = B \cup A$), **Associative** ($(A \cup B) \cup C = A \cup (B \cup C)$), and **Idempotent** ($A \cup A = A$).
- **Unique Character IDs (RGA / Yjs)**: Characters are assigned fractional indices or unique Lamport IDs rather than array offsets, so insertions never alter the coordinates of existing letters.

---

## 3. Comparison Matrix

| Dimension | Operational Transformation (OT) | CRDTs (Yjs, Automerge) |
| :--- | :--- | :--- |
| **Topology** | Centralized client-server mandatory | Decentralized / P2P / Local-first supported |
| **Offline Editing** | Complex conflict resolution | Native and seamless |
| **Memory Overhead** | Minimal (stores only character array) | Higher (stores tombstones and metadata history) |
| **Pioneered By** | Google Wave, Google Docs | Figma, Apple Notes, Linear |

---

## 4. Key Takeaways

- Use CRDTs (such as Yjs or Automerge) for modern collaborative applications requiring offline support and peer-to-peer sync.
- Use Operational Transformation when a centralized server is already mandatory and client memory footprint must be minimized.
- In CRDTs, never delete items destructively—mark them with tombstones to maintain causal history.
