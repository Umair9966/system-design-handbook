import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 08: MESSAGING AND STREAMING
# =========================================================================

save("docs/08-messaging-and-streaming/01-message-queues-vs-pubsub-vs-streaming.md", """# Message Queues vs Pub/Sub vs Distributed Event Streaming

## Overview
Asynchronous communication decouples microservices in time and space, smoothing traffic spikes and enabling resilient data flows. Asynchronous messaging falls into three distinct architectural patterns:
- **Point-to-Point Message Queue**: Messages are delivered to exactly one consumer from a pool of workers; the message is deleted from the queue upon successful acknowledgment (e.g., RabbitMQ, AWS SQS).
- **Publish/Subscribe (Pub/Sub)**: Publishers broadcast messages to a topic; all subscribed consumers receive a distinct copy of every message (e.g., Google Cloud Pub/Sub, Redis Pub/Sub).
- **Distributed Event Streaming (Append-Only Log)**: Messages are appended sequentially to an immutable, partitioned, disk-backed commit log; multiple consumer groups read independently at their own pace and can replay historical events (e.g., Apache Kafka, Apache Pulsar).

```mermaid
graph TD
    subgraph Message Queue [Destructive Read]
        P1[Producer] --> Q[(Queue)]
        Q -->|Worker 1 consumes & DELETES| W1[Worker 1]
        Q -.->|No copy left for Worker 2| W2[Worker 2]
    end
    subgraph Distributed Event Stream [Non-Destructive Replayable Log]
        P2[Producer] --> K[(Partitioned Append-Only Log)]
        K -->|Reads from Offset 0| C1[Analytics Consumer Group]
        K -->|Reads from Offset 42| C2[Billing Consumer Group]
    end
```

## Why It Matters
Using a simple message queue like RabbitMQ for an audit logging pipeline that needs historical replay is disastrous—messages disappear the second they are acknowledged. Conversely, deploying a complex 50-node Apache Kafka cluster for a basic background email delivery queue is massive over-engineering.

## Core Concepts & Architectural Comparison
| Paradigm | Message Lifecycle | Consumer Model | Replayability | Ordering Guarantees |
| :--- | :--- | :--- | :--- | :--- |
| **Point-to-Point Queue** | Deleted after consumer ACK | Competing consumers (1 worker per msg)| **None** | FIFO per queue (optional) |
| **Pub/Sub (Traditional)**| Discarded after fan-out delivery | Independent subscribers | None | Per topic |
| **Event Streaming (Kafka)**| **Retained on disk for days/years** | **Consumer Groups with Offsets** | **Infinite historical replay** | **Strict per-partition ordering** |

## Trade-offs
| Feature | Message Queues (RabbitMQ / SQS) | Event Streams (Apache Kafka) |
| :--- | :--- | :--- |
| **Routing Flexibility** | **Complex routing keys & exchanges (AMQP)**| Simple partition key routing |
| **Message Granularity** | Individual message acknowledgment & retry | Offset-based batch commit |
| **Throughput Capacity** | 10,000 - 50,000 msg/sec | **Millions of msg/sec (Zero-Copy OS sequential disk)**|
| **Operational Overhead**| Low to Moderate | High (Cluster brokers, ZooKeeper/KRaft, rebalancing)|

## When to Use / When NOT to Use
### When to Choose a Message Queue (RabbitMQ / SQS)
- Discrete task dispatching (e.g., "Send this password reset email", "Transcode this PDF").
- Workloads requiring complex individual message routing, priority queues, and individual message dead-letter retries.

### When to Choose Event Streaming (Apache Kafka)
- Real-time clickstream analytics, financial transaction event logs, event sourcing, CDC change feeds, systems requiring multi-consumer historical replay.

## Real-World Examples
- **Stripe Webhook Delivery**: Uses **RabbitMQ / SQS** to manage discrete webhook delivery tasks to external merchant URLs, leveraging visibility timeouts and individual retry backoffs.
- **LinkedIn Activity Stream**: Built **Apache Kafka** to ingest trillions of daily user clicks, pageviews, and search events, streaming them simultaneously into real-time fraud detection engines and Hadoop offline warehouses.

## Common Pitfalls
- **Using Redis Pub/Sub for Critical Messages**: Redis Pub/Sub is fire-and-forget; if a consumer disconnects for 50 milliseconds during a deployment, all messages published during that window are permanently lost with zero buffer.
- **Kafka Queue Anti-Pattern**: Attempting to use Kafka like a task queue where individual tasks take 10 minutes to process; a slow task halts consumption for that entire partition (Head-of-Line blocking).

## Key Takeaways
- Queues are for **tasks** (destructive read); Streams are for **events** (immutable log, replayable).
- Kafka provides high throughput via sequential disk I/O and consumer group offset tracking.
- Traditional queues excel at granular per-message retries and complex routing.

## Common Interview Questions
1. Why does Apache Kafka scale write throughput significantly better than traditional AMQP message brokers like RabbitMQ?
2. What happens to Kafka consumer groups when a new consumer instance joins the group?
3. In what scenarios is a destructive message queue preferred over an append-only event stream?

## Further Reading
- [Jay Kreps: The Log: What every software engineer should know about real-time data's unifying abstraction (2013)](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)
- [RabbitMQ Documentation: Core Concepts and AMQP 0-9-1](https://www.rabbitmq.com/tutorials/amqp-concepts.html)
""")

save("docs/08-messaging-and-streaming/02-apache-kafka-architecture.md", """# Apache Kafka Architecture Deep Dive

## Overview
**Apache Kafka** is a distributed, partitioned, replicated, commit-log service engineered for high-throughput, fault-tolerant event streaming. Originally developed at LinkedIn, Kafka processes trillions of events daily across global technology companies.

```mermaid
graph TD
    subgraph Kafka Cluster
        subgraph Broker 1
            P0_Leader[Topic A - Partition 0: LEADER]
            P1_Follower[Topic A - Partition 1: FOLLOWER]
        end
        subgraph Broker 2
            P0_Follower[Topic A - Partition 0: FOLLOWER]
            P1_Leader[Topic A - Partition 1: LEADER]
        end
    end
    Prod[Kafka Producer] -->|Hash Key: Partition 0| P0_Leader
    Prod -->|Hash Key: Partition 1| P1_Leader
    P0_Leader -->|Sync Replication| P0_Follower
    P1_Leader -->|Sync Replication| P1_Follower
    P0_Leader -->|Consume Offset 104| CG1_W1[Consumer Group 1 - Worker 1]
    P1_Leader -->|Consume Offset 208| CG1_W2[Consumer Group 1 - Worker 2]
```

## Why It Matters
Kafka achieves throughput rates that leave traditional message brokers in the dust—routinely handling **millions of messages per second per broker**. It achieves this not through mysterious magic, but through brilliant hardware-aligned mechanical sympathy: **Sequential Disk I/O**, **Page Cache Utilization**, and **OS Zero-Copy Network Splicing**.

## Core Concepts & Architectural Primitives
1. **Topics & Partitions**:
   - A **Topic** is a logical stream of messages.
   - Topics are horizontally divided into **Partitions**.
   - The **Partition is the fundamental unit of parallelism and scale in Kafka**.
   - Messages within a partition are strictly ordered by sequential 64-bit integer **Offsets**.
   - *Ordering Guarantee*: Messages are strictly ordered **within a partition**, NOT across the entire topic!
2. **Producers & Partition Keys**:
   - Producers hash the message key (`hash(key) % num_partitions`) to assign it to a partition. Messages with the identical key (e.g., `user_id = 42`) are guaranteed to land on the same partition, preserving causal ordering.
3. **Consumer Groups & Offset Management**:
   - Multiple consumers form a **Consumer Group**.
   - Each partition is consumed by **exactly one consumer worker** within a group.
   - Consumers track their position by committing their current **Offset** (stored in an internal Kafka topic: `__consumer_offsets`).
4. **In-Sync Replicas (ISR) & ACKs**:
   - Each partition has 1 Leader and $N-1$ Followers.
   - **ISR (In-Sync Replicas)**: The subset of replicas caught up with the leader.
   - `acks=0`: Producer fire-and-forget (zero wait).
   - `acks=1`: Leader writes to local log and acknowledges.
   - `acks=all` (or `-1`): Leader waits for all In-Sync Replicas to acknowledge (**Guarantees zero data loss**).

## Why Kafka is Blazing Fast: Mechanical Sympathy
- **Sequential Disk Appends**: Kafka writes exclusively to append-only log segments. Sequential disk access on modern drives is as fast as random RAM access (~600 MB/s).
- **Page Cache Exploitation**: Rather than managing complex JVM heap caches (which cause massive GC pauses), Kafka relies entirely on the Linux OS Page Cache.
- **Zero-Copy Network Transfers (`sendfile` syscall)**:
  Data moves directly from OS Page Cache to the Network Interface Card (NIC) buffer via DMA (Direct Memory Access), **completely bypassing user-space CPU memory copying**.

## Trade-offs
| Feature | Advantage | Trade-off / Cost |
| :--- | :--- | :--- |
| **Partition Parallelism** | Massive linear read/write throughput | Adding partitions changes hash key mapping; high partition counts add file descriptor overhead |
| **Disk Retention** | Replayable history for days/months | Disk storage capacity management required |
| **Consumer Group Scale** | Effortless horizontal scale-out | Max consumers in a group is capped by partition count! |

## When to Use / When NOT to Use
### When to Choose Apache Kafka
- Large-scale event-driven architectures, real-time analytics pipelines, event sourcing, activity tracking, Change Data Capture (CDC).

### When NOT to Choose Kafka
- Small teams needing a simple task queue with individual message acknowledgments and immediate dead-letter handling (use RabbitMQ or SQS).

## Real-World Examples
- **LinkedIn**: Operates over 100 Kafka clusters with 4,000+ brokers, ingesting over **7 trillion messages per day**.
- **Netflix**: Uses Kafka as the central nervous system connecting all microservice telemetry to real-time analytics and alerting platforms.

## Common Pitfalls
- **More Consumers Than Partitions**: Deploying 20 consumer pods for a topic with only 10 partitions; 10 pods will sit completely idle because a partition cannot be shared within the same group!
- **Consumer Rebalance Storms**: A consumer taking too long to process a batch of records exceeds `max.poll.interval.ms`. The Kafka coordinator assumes the consumer died, kicks it out of the group, and triggers a massive stop-the-world **Consumer Rebalance** across all workers.

## Key Takeaways
- The **Partition** is the unit of scalability, parallelism, and ordering in Kafka.
- Kafka achieves millions of messages per second using **Sequential Disk Appends**, **Linux Page Cache**, and **Zero-Copy `sendfile`**.
- Consumer count in a group cannot exceed the number of partitions.

## Common Interview Questions
1. How does Apache Kafka achieve extreme throughput using OS zero-copy data transfer?
2. What happens during a Kafka consumer rebalance, and what triggers it?
3. How do partition keys guarantee message ordering for specific business entities?

## Further Reading
- [Neha Narkhede et al.: Kafka: The Definitive Guide (O'Reilly)](https://www.oreilly.com/library/view/kafka-the-definitive/9781491936153/)
- [Apache Kafka Documentation: Design and Implementation](https://kafka.apache.org/documentation/#design)
""")

save("docs/08-messaging-and-streaming/03-rabbitmq-and-sqs-architecture.md", """# RabbitMQ and AWS SQS Architecture

## Overview
For asynchronous task execution, background worker coordination, and complex message routing, dedicated message queue brokers remain the industry standard:
- **RabbitMQ**: An open-source, highly versatile message broker implementing the **AMQP 0-9-1 (Advanced Message Queuing Protocol)** standard, featuring programmable exchanges, bindings, and flexible routing.
- **AWS SQS (Simple Queue Service)**: A fully managed, serverless, infinitely scalable distributed message queue offering Standard (at-least-once, best-effort ordering) and FIFO (exactly-once, strict ordering) queues.

```mermaid
graph LR
    subgraph RabbitMQ AMQP Topology
        P1[Producer] --> Ex{Topic Exchange}
        Ex -->|Binding: order.*| Q1[(Queue: All Orders)]
        Ex -->|Binding: order.critical| Q2[(Queue: Critical Orders)]
        Q1 --> W1[Worker Pool]
        Q2 --> W2[Priority Worker Pool]
    end
    subgraph AWS SQS Distributed Buffer
        P2[Producer] --> SQS[(AWS SQS Distributed Buffer)]
        SQS -->|Pull / Visibility Timeout| W3[Worker 3]
    end
```

## Why It Matters
Unlike distributed streaming logs (Kafka), RabbitMQ and SQS are **pure task queues**. They provide granular per-message acknowledgments, individual message redelivery delays, message prioritization, and automatic dead-letter queueing without requiring complex partition management.

## Core Concepts & Architectural Comparison

### 1. RabbitMQ AMQP Mechanics
- Producers **never publish directly to a queue**; they publish to an **Exchange**.
- Exchanges inspect message metadata and route copies to bound queues:
  - **Direct Exchange**: Routes messages based on exact matching of routing keys (`error` -> Error Queue).
  - **Fanout Exchange**: Broadcasts every message to 100% of bound queues (Pub/Sub pattern).
  - **Topic Exchange**: Sophisticated wildcard routing (e.g., `usa.sports.*` or `*.critical.#`).
  - **Headers Exchange**: Routes based on arbitrary HTTP-like header attributes.
- **Consumer Prefetch (QoS)**: Limits how many unacknowledged messages a worker can hold simultaneously, preventing fast workers from starving and slow workers from drowning.

### 2. AWS SQS Serverless Mechanics
- **Push vs Pull**: Consumers continuously poll SQS using long polling (`WaitTimeSeconds = 20`).
- **Visibility Timeout**: When Worker A pulls a message, the message is **NOT deleted**; it is made invisible to other workers for a configured duration (e.g., 30 seconds).
  - If Worker A processes the task and calls `DeleteMessage`, the message is permanently removed.
  - If Worker A crashes or times out, the visibility timeout expires, and the message automatically reappears in the queue for another worker to process.
- **SQS Standard vs FIFO**:
  - *Standard*: Unlimited throughput, at-least-once delivery, best-effort ordering.
  - *FIFO*: Capped at 3,000 msgs/sec (with batching), strictly ordered within Message Group IDs, deduplication within 5-minute windows.

## Trade-offs
| Dimension | RabbitMQ | AWS SQS |
| :--- | :--- | :--- |
| **Routing Capability** | **Unmatched (Direct, Topic, Fanout, Headers)**| Primitive (Queue-only, requires SNS for fan-out)|
| **Management Overhead** | High (Requires managing Erlang VM clusters) | **Zero (100% Fully Managed Serverless)** |
| **Scaling Model** | Vertical node scaling / Quorum queues | **Virtually infinite automated elasticity** |
| **Protocol Support** | AMQP, MQTT, STOMP, WebSockets | Proprietary AWS HTTP API |

## When to Use / When NOT to Use
### When to Choose RabbitMQ
- On-premise or multi-cloud enterprise deployments requiring sophisticated topic/header routing rules, sub-millisecond local LAN latency, and priority queuing.

### When to Choose AWS SQS
- Cloud-native applications on AWS, serverless architectures (triggering AWS Lambda), variable bursty workloads where zero maintenance is required.

## Real-World Examples
- **Stripe Asynchronous Jobs**: Leverages distributed queues with custom visibility timeouts to schedule payment webhooks and API retry notifications with exponential backoff.
- **E-Commerce Order Processing (RabbitMQ)**: Orders are published to a Topic Exchange with routing key `order.created`. The exchange routes the message simultaneously to an `inventory-queue`, a `shipping-queue`, and an `email-queue` in parallel.

## Common Pitfalls
- **RabbitMQ Queue Backlog RAM Collapse**: Letting millions of messages accumulate in a traditional RabbitMQ queue; unread messages spill from Erlang memory to disk, severely degrading broker throughput (mitigated by using **Quorum Queues**).
- **Short SQS Visibility Timeouts**: Setting a 10-second visibility timeout on a job that takes 15 seconds to execute; the message reappears while Worker A is still working, causing duplicate concurrent processing by Worker B!

## Key Takeaways
- RabbitMQ excels at **complex in-broker routing** via AMQP exchanges and bindings.
- SQS is **fully managed and infinitely elastic**, utilizing **visibility timeouts** for fault-tolerant worker processing.
- Set consumer prefetch in RabbitMQ and long polling in SQS to maximize processing efficiency.

## Common Interview Questions
1. How does the AWS SQS Visibility Timeout mechanism guarantee fault-tolerant task execution?
2. Explain the difference between a Direct Exchange, a Fanout Exchange, and a Topic Exchange in RabbitMQ.
3. What is Consumer Prefetch in RabbitMQ, and why is it critical for balancing worker loads?

## Further Reading
- [RabbitMQ: Official AMQP 0-9-1 Specification Guide](https://www.rabbitmq.com/tutorials/amqp-concepts.html)
- [AWS Documentation: How Amazon SQS Queues Work](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html)
""")

save("docs/08-messaging-and-streaming/04-delivery-guarantees-and-deduplication.md", """# Message Delivery Guarantees, Ordering, and Deduplication

## Overview
Building reliable asynchronous event architectures requires rigorous handling of the three universal networking hazards: **message loss**, **message duplication**, and **out-of-order delivery**.

Production architectures guarantee data integrity through the union of **Idempotent Producers**, **Partition-Level Sequence Ordering**, and **Consumer Deduplication Stores**.

```mermaid
sequenceDiagram
    autonumber
    participant Producer as Idempotent Producer
    participant Broker as Kafka Broker (Partition 0)
    participant Consumer as Idempotent Consumer
    participant DedupDB as Deduplication Store (Redis / DB)

    Producer->>Broker: Send Msg (ProducerID: 42, Seq: 101, Order: Paid)
    Broker->>Broker: Commit offset 500
    Broker-->>Producer: ACK Success
    Producer->>Broker: Network glitch causes duplicate send! (PID: 42, Seq: 101)
    Broker->>Broker: Sequence 101 already committed! DISCARD DUPLICATE!
    Broker-->>Producer: ACK (Deduplicated at Broker!)
    Broker->>Consumer: Deliver Msg (Seq: 101)
    Consumer->>DedupDB: INSERT INTO processed_events VALUES ('evt-101') ON CONFLICT DO NOTHING
    Consumer->>Consumer: Execute Business Logic
```

## Why It Matters
Network timeouts make duplicates inevitable. If a producer transmits a message and the network drops the broker's acknowledgment packet, the producer *must* retry. If consumers do not deduplicate, customers will be billed twice, inventory will decrement twice, and data integrity will be corrupted.

## Core Concepts & Mechanical Implementation

### 1. Delivery Guarantees Matrix
- **At-Most-Once**: Consumer commits offset *before* processing the message. If the consumer crashes during processing, the message is lost forever.
- **At-Least-Once**: Consumer processes the message and commits offset *after* completing database writes. If the consumer crashes right before committing, the next worker re-processes the message (guarantees zero data loss, but introduces duplicates).
- **Effectively-Once**: Combines At-Least-Once delivery with **Consumer Deduplication**.

### 2. Message Ordering Guarantees
- In distributed streaming (Kafka/Pulsar), **ordering is only guaranteed within a single partition**, never globally across topics!
- *Partition Key Selection*: To preserve strict causal ordering for an entity, all events related to that entity must share the same partition key:
  $$\\text{Partition} = \\text{MurmurHash3}(\\text{account\\_id}) \\pmod{\\text{NumPartitions}}$$
  All transactions for `account_id = 99` flow sequentially through Partition 3, guaranteeing in-order FIFO processing.

### 3. Consumer-Side Deduplication Strategies
- **Deduplication Table (Unique Constraint)**:
  Every message contains a globally unique `event_id` (UUID). The consumer writes to the database inside a transaction:
  ```sql
  BEGIN;
  INSERT INTO processed_events (event_id, processed_at) VALUES ('evt-uuid-123', NOW());
  -- If unique constraint fails, abort transaction! Duplicate detected!
  UPDATE accounts SET balance = balance + 100 WHERE id = 42;
  COMMIT;
  ```
- **Redis TTL Bitmaps / Sets**: For high-throughput streams, check event existence in an in-memory Redis key with a 48-hour expiration (`SET event:123 1 NX EX 172800`).

## Trade-offs
| Architecture Strategy | Processing Throughput | Consistency Guarantee | Operational Cost |
| :--- | :--- | :--- | :--- |
| **At-Most-Once** | Blazing Fast | Zero (Tolerates message loss) | Lowest |
| **At-Least-Once (Naive)**| High | Risky (Duplicates will corrupt state)| Low |
| **Effectively-Once (Dedup)**| Moderate | **Absolute Mathematical Correctness** | Moderate (Requires dedup storage) |

## When to Use / When NOT to Use
### When Effectively-Once (Deduplication) is Mandatory
- Financial ledgers, payment processing, billing counters, inventory deduction, order fulfillment.

### When At-Least-Once without Deduplication Suffices
- Idempotent state synchronization where messages represent full state overwrites (e.g., `SET user:name = "Alice"`).

## Real-World Examples
- **Apache Flink Exactly-Once State Processing**: Uses the **Chandy-Lamport distributed snapshotting algorithm**, injecting checkpoint barriers into data streams to periodically record consistent state snapshots across all operators and Kafka offsets.
- **Kafka Transactions (`read_committed`)**: Coordinates atomic multi-partition writes, ensuring consumer groups only read events from producers whose transactions officially committed.

## Common Pitfalls
- **Changing Partition Counts with Keyed Data**: Increasing the partition count of a live Kafka topic changes the output of `hash(key) % N`, causing subsequent events for `account_id = 99` to route to a different partition, immediately breaking sequential ordering!
- **Committing Offsets Before Storage Writes**: A consumer pulling 100 messages, committing the offset immediately, and crashing while writing to PostgreSQL, permanently losing all 100 messages.

## Key Takeaways
- Never promise "Exactly-Once" without implementing **idempotent consumers** and **deduplication stores**.
- Message ordering in Kafka is guaranteed **only within a single partition**.
- Always commit offsets *after* business logic transactions complete successfully.

## Common Interview Questions
1. How does an idempotent Kafka producer eliminate network duplicate writes at the broker layer?
2. Why does changing the partition count of an existing Kafka topic break ordering guarantees for keyed messages?
3. How do you implement consumer-side deduplication using a relational database unique constraint?

## Further Reading
- [Apache Kafka Documentation: Exactly-Once Semantics in Apache Kafka](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)
- [K. Mani Chandy and Leslie Lamport: Distributed Snapshots: Determining Global States of Distributed Systems (ACM TOCS 1985)](https://lamport.azurewebsites.net/pubs/chandy.pdf)
""")

print("Section 08 Part 1 complete.")
