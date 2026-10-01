# Solutions: Messaging and Event Streaming

---

### Solution 1: Kafka Consumer Lag Spike
- **Outcome**: **No, scaling to 24 pods will NOT resolve the lag.**
- **Reason**: In Kafka, each partition within a consumer group can be consumed by at most **one** consumer thread/pod at any time. With 12 partitions and 24 consumer pods, 12 pods will actively consume while the remaining 12 pods will sit completely **idle**.
- **Correct Solution**:
  1. Increase partition count of the topic to 24 (if ordering key constraints allow).
  2. Or, within each consumer pod, use a thread pool / worker queue to process independent message keys in parallel.
  3. Optimize the consumer processing logic to increase throughput per partition.

---

### Solution 2: Outbox Pattern vs 2PC
- **Drawbacks of 2PC**:
  - Blocking protocol: Locks database rows and broker resources across network round-trips.
  - Fragile: If the coordinator or broker network drops mid-commit, locks remain held, causing cascading connection pool exhaustion.
  - Unsupported: Modern message brokers (Kafka, SQS) do not support XA/2PC transactions with relational databases.
- **Advantages of Transactional Outbox + CDC**:
  - Pure local ACID transaction: The business entity and the outbox message are committed in the same local database transaction.
  - Asynchronous & Non-blocking: CDC tools (Debezium) tail the database Write-Ahead Log (WAL) to publish to Kafka with zero impact on database transaction latency.
