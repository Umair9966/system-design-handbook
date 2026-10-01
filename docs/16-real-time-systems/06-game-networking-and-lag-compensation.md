# Multiplayer Game Networking: Client Prediction and Lag Compensation

Real-time multiplayer games (FPS, battle royale) operate under stringent physics budgets where network round-trip times (50ms - 150ms) are intolerable without deterministic prediction and server reconciliation.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Local Player Client
    participant Server as Authoritative Game Server
    participant Remote as Remote Opponent

    Client->>Client: 1. Press W -> Predict Move Instantly (Local render: 0ms lag!)
    Client->>Server: 2. Send Input: {InputID: 101, Cmd: MOVE_FORWARD, Timestamp: t=100}
    Note over Server: Server simulates physics at tick rate (64 Hz)
    Server->>Server: Validates movement against collision map
    Server-->>Client: 3. Authoritative State: {AckInputID: 101, Pos: (10, 0, 5)}
    Server-->>Remote: Broadcast Position: (10, 0, 5)
    Note over Client: If client prediction matched server: Smooth playback!<br/>If mismatch (desync): Reconcile & Snap to server position
```

---

## 1. The Authoritative Server Model

Clients are never trusted. A client that sends "My position is now (X, Y, Z)" enables instant teleportation hacks and speed cheats.
- **Rule**: Clients send **inputs only** (keystrokes, mouse deltas, timestamp).
- The server runs the authoritative simulation loop (e.g., at 64Hz or 128Hz) and broadcasts ground-truth world snapshots.

---

## 2. Lag Compensation: "Rewind Time"

When Player A shoots Player B who is sprinting across the screen:
- Because of 80ms network latency, Player A aimed at where Player B was on Player A's screen 80ms ago.
- Without compensation, the server would calculate Player B has already moved past that coordinate, resulting in a frustrating missed shot.

```mermaid
graph TD
    Shoot[Player A fires at timestamp t=1000] --> Server[Authoritative Server receives packet at t=1080]
    Server --> Rewind[Lag Compensation: Rewinds world state to t=1000]
    Rewind --> Raycast[Executes bullet raycast against player hitboxes at t=1000]
    Raycast --> Hit{Hit Detected?}
    Hit -->|Yes| Confirm[Confirm Kill / Damage & Fast-Forward World to t=1080]
```

---

## 3. Key Takeaways

- Use authoritative dedicated game servers communicating over custom UDP protocols (not TCP).
- Implement client-side prediction to make local movement feel instantaneous.
- Implement server lag compensation by buffering recent historical hitboxes and rewinding world state upon input arrival.
