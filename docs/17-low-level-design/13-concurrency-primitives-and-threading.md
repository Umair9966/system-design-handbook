# Concurrency Primitives: Mutexes, Semaphores, and Thread Pools

Concurrency primitives prevent race conditions, memory corruption, and deadlocks in multi-threaded environments.

```mermaid
graph TD
    subgraph "Concurrency Primitives"
        Mutex[Mutex / Lock: Mutual Exclusion (1 Thread)]
        RWMutex[RWMutex: Multiple Readers, 1 Writer]
        Semaphore[Semaphore: Permit Counter (N Threads)]
        Condition[Condition Variable: Signal / Wait]
        Atomic[Atomic CPU CAS: Lock-Free Operations]
    end
```

---

## 1. Comparing Concurrency Primitives

| Primitive | Mechanism | Primary Use Case |
| :--- | :--- | :--- |
| **Mutex (Lock)** | Only 1 thread holds lock; others block | Protecting shared mutable in-memory state |
| **RWLock (Shared Lock)**| Multiple concurrent readers OR single exclusive writer | Read-heavy data structures (e.g., caches) |
| **Counting Semaphore** | Maintains $K$ permits (`acquire()` / `release()`) | Limiting concurrent DB connections or worker pools |
| **Atomic (CAS)** | Hardware CPU instruction (`CMPXCHG`) | Lock-free counters and flags with zero thread sleep |

---

## 2. The Four Coffman Deadlock Conditions

A system deadlock occurs if and only if **all four** conditions hold simultaneously:
1. **Mutual Exclusion**: Resources cannot be shared.
2. **Hold and Wait**: Threads hold resources while waiting for others.
3. **No Preemption**: Resources cannot be forcibly taken away.
4. **Circular Wait**: Thread A waits for B, and B waits for A.

### Prevention:
Break condition 4 (**Circular Wait**) by enforcing a **strict global lock acquisition order** everywhere in code:
```python
# PREVENTS DEADLOCK: Always lock in ascending order of resource ID!
def transfer(acc1, acc2, amount):
    first, second = (acc1, acc2) if acc1.id < acc2.id else (acc2, acc1)
    with first.lock:
        with second.lock:
            acc1.balance -= amount
            acc2.balance += amount
```

---

## 3. Key Takeaways

- Prefer RWMutex for read-heavy workloads to prevent readers from blocking other readers.
- Prevent deadlocks by enforcing consistent lock acquisition ordering across the codebase.
- Use atomics (`AtomicInteger`) for counters to avoid mutex context-switch overhead.
