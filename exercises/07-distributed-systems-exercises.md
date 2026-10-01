# Exercises: Distributed Systems Theory

Test your comprehension of consensus, CAP/PACELC, clocks, and distributed transactions.

---

### Exercise 1: PACELC Analysis
A financial ledger requires zero lost balance updates and strong consistency, even during WAN network partitions. How would you classify this system under PACELC? What are the latency consequences?

### Exercise 2: Raft Split-Vote Simulation
In a 5-node Raft cluster, Node 1 (leader) disconnects. Nodes 2 and 3 both simultaneously time out and increment their term to 2, voting for themselves. How does Raft resolve this split-vote scenario without deadlocking?

### Exercise 3: Lamport Clock vs Vector Clock
Explain a concrete scenario where Lamport timestamps indicate that Event A happened before Event B ($L(A) < L(B)$), but where Event A did NOT causally precede Event B ($A 
ot	o B$).
