# Exercises: Messaging and Event Streaming

---

### Exercise 1: Kafka Consumer Lag Spike
A Kafka topic with 12 partitions is consumed by a consumer group of 12 worker pods. Consumer lag suddenly surges to 500,000 messages. You scale the consumer deployment from 12 pods to 24 pods. Does this resolve the lag? Explain why or why not.

### Exercise 2: Outbox Pattern vs Two-Phase Commit
Why do modern microservice architectures strongly prefer the Transactional Outbox pattern with Change Data Capture (CDC) over distributed Two-Phase Commit (2PC) for publishing database state changes to Kafka?
