# System Design Interview Evaluation Rubric (FAANG Standards)

How interviewers evaluate candidates across Staff and Principal engineering dimensions.

```mermaid
radar
    title Candidate Competency Dimensions
    "Requirements & Scoping" : 4
    "High-Level Architecture" : 5
    "Distributed Deep Dive" : 4
    "Trade-off Articulation" : 5
    "Fault Tolerance & Scale" : 4
    "Communication & Leadership" : 5
```

---

## The 4 Competency Levels

| Dimension | Junior / Mid (L4) | Senior (L5) | Staff / Principal (L6+) |
| :--- | :--- | :--- | :--- |
| **Scoping** | Waits for requirements to be handed down | Identifies key use cases and non-functional requirements | Clarifies business trade-offs, identifies ambiguous edge cases |
| **Architecture** | Simple 3-tier app (Client -> API -> DB) | Microservices, caching, read replicas, messaging queues | Elegant distributed topologies, handles partitioning and consensus |
| **Data Design** | Basic SQL table schema | Appropriate SQL vs NoSQL selection, indexing strategy | Sharding key selection, replication models, data consistency guarantees |
| **Resilience** | Mentions backups | Circuit breakers, health checks, multi-AZ deployment | Active-Active multi-region, split-brain mitigation, chaos engineering |
| **Communication**| Hesitant, needs prompting | Clear, drives standard framework | Inspiring, drives consensus, explains complex trade-offs simply |

---

## Scoring Grid

1. **Strong No Hire**: Silent, unable to handle scale, suggests single MySQL instance for 100M QPS, defends broken designs.
2. **No Hire**: Implements generic textbook architecture, unable to explain internals of proposed technologies, misses major failure modes.
3. **Hire**: Follows 6-step framework cleanly, makes justifiable tech choices, calculates accurate numbers, handles failure scenarios gracefully.
4. **Strong Hire**: Drives the session masterfully, proactively points out subtle distributed bugs (cache stampedes, clock skew, split-brain), evaluates trade-offs with mathematical rigor.
