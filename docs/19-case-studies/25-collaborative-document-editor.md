# Design a Real-Time Collaborative Document Editor (Google Docs / Notion)

A real-time rich-text document editing platform allowing multiple concurrent users to edit the same document simultaneously with offline synchronization, presence cursors, and conflict-free text merging.

```mermaid
graph TD
    ClientA[User A (Browser)] <-->|WebSocket: Local CRDT Edits| WS_GW[WebSocket Gateway]
    ClientB[User B (Browser)] <-->|WebSocket: Local CRDT Edits| WS_GW

    WS_GW --> DocSvc[Document Session Coordinator]
    DocSvc <--> Redis[(Redis: Ephemeral State & Presence)]
    DocSvc --> SnapshotWorker[Document Snapshot Worker]
    SnapshotWorker --> DocDB[(Document Store: MongoDB / S3)]
```

---

## 1. Requirements

### Functional Requirements:
1. Multi-user concurrent text and block editing.
2. Character-by-character real-time synchronization.
3. Show live user cursors and text selections.
4. Offline editing with automatic conflict resolution upon reconnect.

### Non-Functional Requirements:
- **Low Latency**: Peer edit synchronization $< 50	ext{ms}$.
- **Consistency**: All concurrent users eventually converge on the exact identical document text.
- **Fault Tolerance**: No lost keystrokes during network drops.

---

## 2. CRDTs: Yjs / Automerge vs Operational Transformation

```mermaid
graph TD
    subgraph "CRDT Character Model (Fractional Indexing)"
        Char1["'H' (Pos: 0.5)"]
        Char2["'e' (Pos: 0.75)"]
        Char3["'l' (Pos: 0.875)"]
        Char4["'o' (Pos: 0.9375)"]
        Note over Char2,Char3: User inserts 'l' between 'e' and 'l':<br/>Assigned Pos: 0.8125! Zero index shifts!
    end
```

### Why Modern Systems Prefer CRDTs:
- Characters receive immutable fractional identifiers rather than array indices.
- Inserting a letter in the middle of a paragraph does not alter the coordinate IDs of subsequent characters.
- Merges are commutative and associative; clients can sync peer-to-peer without waiting for a central master server.

---

## 3. Key Takeaways

- Adopt CRDTs (such as Yjs or Automerge) for modern offline-first real-time collaboration.
- Track real-time presence (cursor position, selection) as ephemeral volatile state in Redis.
- Persist periodic document snapshots to object storage (S3) to avoid replaying millions of granular keystroke operations on load.
