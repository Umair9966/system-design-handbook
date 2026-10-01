# Design a Distributed 64-Bit Unique ID Generator (Snowflake)

> **System Scope**: Generates globally unique, roughly time-sortable 64-bit integer IDs at scale without centralized database locks.
> Implements Twitter Snowflake layout: timestamp bits, datacenter ID, worker ID, sequence counter, and clock drift defense.

---

## 1. Problem Statement
<!-- Case study content to be fully implemented in Phase 3 -->
High-level architectural problem statement for a distributed 64-bit unique id generator (snowflake) supporting millions of active users.

## 2. Requirements
### Functional
- Core user operations and business workflows for a distributed 64-bit unique id generator (snowflake).
- High-priority interactive and asynchronous features.

### Non-Functional
- **Scale**: Target QPS, daily active users (DAU), and peak traffic multipliers.
- **Latency**: P99 response time targets.
- **Availability**: 99.99% availability with zero single points of failure.
- **Consistency**: Consistency vs availability trade-offs (PACELC).

### Out of Scope
- Secondary enterprise admin tooling and auxiliary back-office features.

## 3. Capacity Estimation
- Read QPS, Write QPS, Storage capacity over 5 years, Ingress/Egress bandwidth, and Cache RAM sizing.

## 4. API Design
```http
POST /api/v1/a-distributed-64-bit-unique-id-generator-(snowflake)
Content-Type: application/json
Idempotency-Key: <uuid>

{
  "request_payload": "value"
}
```

## 5. Data Model and Storage Choice
- Data persistence strategy, relational vs NoSQL selection criteria, and indexing schema.

## 6. High-Level Architecture
```mermaid
graph TD
    Client([Client App]) --> CDN[CDN / Edge]
    CDN --> LB[L7 Load Balancer]
    LB --> Gateway[API Gateway]
    Gateway --> Service[a Distributed 64-Bit Unique ID Generator (Snowflake) Core Service]
    Service --> Cache[(Distributed Cache)]
    Service --> PrimaryDB[(Primary Database)]
    Service --> MessageQueue[(Event Queue / Kafka)]
```

## 7. Deep Dives
- **Bottleneck 1**: Algorithmic optimizations and concurrency control.
- **Bottleneck 2**: Data replication, partitioning, and consistency boundaries.

## 8. Scaling Strategy
- Multi-tier caching, consistent hashing ring partitioning, and read replica topologies.

## 9. Reliability and Failure Scenarios
- Component failure mitigation, circuit breakers, dead-letter queues, and cross-region disaster recovery.

## 10. Security and Abuse Considerations
- Authentication, authorization (RBAC), rate limiting, DDoS mitigation, and audit logging.

## 11. Monitoring and Metrics
- RED and USE metrics, distributed tracing spans, and SLO error budget alerting.

## 12. Trade-offs and Alternatives Considered
- Evaluation of competing architectural paradigms and rationale for selected design.

## 13. Possible Extensions
- Future capabilities and multi-region active-active deployments.

## 14. Interview Follow-Up Questions
1. How does the architecture handle a sudden 10x viral traffic spike?
2. What happens if the distributed cache crashes simultaneously across all zones?
3. How do you guarantee data consistency during network partitioning?
