# Top 10 System Design Interview Mistakes

Understanding the anti-patterns that cause candidates to fail system design interviews.

```mermaid
graph TD
    Mistakes[Top Interview Pitfalls]
    Mistakes --> M1[1. Starting with Tech Buzzwords ('Let's use Kafka and Blockchain')]
    Mistakes --> M2[2. Silent Drawing without Explaining Thought Process]
    Mistakes --> M3[3. Ignoring Scale Numbers in Architectural Decisions]
    Mistakes --> M4[4. Single Point of Failure (SPOF) Blindness]
    Mistakes --> M5[5. Over-Engineering Simple Requirements]
```

---

## The 10 Deadly Sins:

1. **Premature Technology Naming**: Proposing Kafka or Cassandra before defining functional requirements or traffic scale.
2. **Monologuing without Checking In**: Speaking for 10 minutes continuously without pausing to confirm alignment with the interviewer.
3. **Ignoring Back-of-the-Envelope Math**: Designing an in-memory Redis cluster for a dataset that requires 100 Petabytes of disk storage.
4. **Drawing a "Magic Box"**: Labeling a component "Load Balancer" or "Message Queue" without being able to explain how it works internally under failure.
5. **Treating Databases as Black Boxes**: Ignoring indexing, replication lag, transaction isolation levels, and sharding strategies.
6. **Ignoring Failures**: Designing purely for the happy path and panicking when asked: "What happens if this network link severs?"
7. **Over-Engineering**: Proposing a 50-microservice Kubernetes mesh for a system serving 10 requests per minute.
8. **Neglecting Data Models**: Skipping the database schema and entity relationships.
9. **Rigidity and Defensiveness**: Arguing with the interviewer when they offer hints or challenge assumptions.
10. **Running Out of Time**: Spending 35 minutes on requirements and calculations, leaving 5 minutes for the actual architecture.

---

## Key Takeaways

- Focus on fundamentals: data models, access patterns, and fault tolerance.
- Check in with the interviewer every 3-4 minutes: *"Does this component address your primary concern, or should we dive into the storage engine next?"*
