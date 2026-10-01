# Worked LLD: Thread-Safe LRU Cache

A complete Low-Level Design and production implementation of an $O(1)$ Least Recently Used (LRU) Cache using a Hash Map and a Doubly Linked List with Read-Write concurrency locks.

```mermaid
graph LR
    subgraph "Hash Map: O(1) Key Lookup"
        HM["'key1' -> Node(key1, val1)<br/>'key2' -> Node(key2, val2)"]
    end

    subgraph "Doubly Linked List: O(1) Eviction & Promotion"
        Head[Head (Dummy)] <--> N1[Node 1: Most Recent] <--> N2[Node 2] <--> Tail[Tail (Dummy: Least Recent)]
    end
```

---

## 1. Requirements

1. $O(1)$ time complexity for `get(key)` and `put(key, value)`.
2. Fixed maximum capacity $C$.
3. When capacity is exceeded, evict the least recently used element.
4. **Thread-Safe**: Concurrent reads and writes supported with high throughput.

---

## 2. Production Code Implementation (Python)

```python
import threading
from typing import Optional, Dict

class Node:
    def __init__(self, key: int = 0, val: int = 0):
        self.key = key
        self.val = val
        self.prev: Optional['Node'] = None
        self.next: Optional['Node'] = None

class ThreadSafeLRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.map: Dict[int, Node] = {}
        
        # Sentinel dummy head and tail nodes
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        
        self.lock = threading.RLock()

    def _remove(self, node: Node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node: Node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        with self.lock:
            if key not in self.map:
                return -1
            node = self.map[key]
            self._remove(node)
            self._add_to_front(node)
            return node.val

    def put(self, key: int, value: int):
        with self.lock:
            if key in self.map:
                node = self.map[key]
                node.val = value
                self._remove(node)
                self._add_to_front(node)
            else:
                if len(self.map) >= self.capacity:
                    lru = self.tail.prev
                    self._remove(lru)
                    del self.map[lru.key]

                new_node = Node(key, value)
                self.map[key] = new_node
                self._add_to_front(new_node)
```

---

## 3. Key Takeaways

- Sentinel head and tail dummy nodes eliminate edge case checks for empty lists or single-element lists.
- Combining a Hash Map and Doubly Linked List achieves guaranteed $O(1)$ operations.
- Use Read-Write locks (`sync.RWMutex` in Go, `ReentrantReadWriteLock` in Java) for high read concurrency.
