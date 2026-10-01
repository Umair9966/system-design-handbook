# Design an Ultra-Low-Latency Stock Exchange Matching Engine (LMAX / NASDAQ)

An ultra-low-latency financial order matching engine capable of executing limit orders, market orders, and cancellations with sub-microsecond determinism, zero garbage collection pauses, and strict FIFO price-time priority.

```mermaid
graph TD
    Trader[High-Frequency Trading Firms] -->|FIX Protocol / TCP Direct| Gateway[FIX Gateway (Kernel Bypass / Solarflare EF_VI)]
    Gateway --> Sequencer[Deterministic Sequencer (Raft / Hardware FPGA)]
    Sequencer --> Disruptor[LMAX Disruptor In-Memory Ring Buffer]
    Disruptor --> Engine[Order Book Matching Engine (Single Thread Core)]
    Engine --> MarketData[Market Data Multicast Feed: UDP ITCH]
    Engine --> Clearing[Clearing & Settlement Ledger]
```

---

## 1. Requirements

### Functional Requirements:
1. Submit, cancel, and modify Limit and Market orders.
2. Maintain Order Book with Price-Time Priority (FIFO at same price level).
3. Execute trades when bid price $\ge$ ask price.
4. Broadcast market data updates (level 2 order book) in real time.

### Non-Functional Requirements:
- **Ultra-Low Latency**: Sub-microsecond matching ($< 5\mu	ext{s}$).
- **Determinism**: 100% reproducible execution sequence.
- **Zero Garbage Collection Pauses**: Mechanical sympathy and off-heap memory.

---

## 2. Architectural Secret: The Single-Threaded Core Pattern (LMAX Disruptor)

Traditional multi-threaded concurrent programming relies on mutex locks and context switching, introducing jitter and 10-50 microsecond delays.

### The LMAX Disruptor Architecture:
```mermaid
graph LR
    subgraph "Single-Threaded Pinned CPU Core"
        Ring[Disruptor Lock-Free Circular Ring Buffer] --> Matcher[Single-Threaded Matching Engine]
        Matcher --> Book[(In-Memory Doubly Linked Order Book)]
    end
    Note over Matcher: Pinned to exclusive CPU core with CPU cacheline padding.<br/>ZERO thread contention! ZERO lock overhead! 6 Million ops/sec!
```

- **Order Book Data Structure**:
  - **Limit Prices**: B+Tree or Red-Black Tree mapping Price $	o$ FIFO Queue.
  - **Order Queue**: Doubly linked list of orders at each price level.
  - Inserting an order: $O(1)$ at price tail; executing trade: $O(1)$ at opposite head.

---

## 3. Deterministic Sequencing and Journaling

Before entering the matching engine, every order passes through a **Deterministic Sequencer** that assigns an incrementing monotonic sequence number (`seq_id`). The input stream is written sequentially to NVMe storage. In the event of a catastrophic server reboot, replaying the sequence stream from disk produces the exact identical order book state.

---

## 4. Key Takeaways

- Use a single-threaded matching core pinned to a dedicated CPU core to eliminate lock contention.
- Implement the LMAX Disruptor circular lock-free ring buffer for inter-thread communication.
- Enforce strict Price-Time Priority (FIFO) using tree-indexed doubly linked lists.
