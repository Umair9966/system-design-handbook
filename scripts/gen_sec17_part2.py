import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\17-low-level-design"

files = {
    "07-worked-lld-lru-cache.md": """# Worked LLD: Thread-Safe LRU Cache

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
""",

    "08-worked-lld-rate-limiter.md": """# Worked LLD: In-Memory Rate Limiter (Token Bucket)

A complete Low-Level Design for a thread-safe, high-throughput in-memory Token Bucket rate limiter.

```mermaid
classDiagram
    class TokenBucket {
        -double capacity
        -double refillRate
        -double availableTokens
        -Instant lastRefillTime
        +allowRequest(int tokens) bool
        -refill() void
    }
    class RateLimiterService {
        -ConcurrentHashMap~String, TokenBucket~ buckets
        +isAllowed(String clientKey) bool
    }
    RateLimiterService "1" *-- "*" TokenBucket
```

---

## 1. Requirements

1. Token Bucket algorithm: Smooth traffic bursts up to capacity while enforcing steady-state refill rate.
2. Thread-safe execution under multi-threaded concurrency.
3. Memory leak protection: Automatically expire idle client buckets.

---

## 2. Production Code Implementation (Python)

```python
import time
import threading
from typing import Dict

class TokenBucket:
    def __init__(self, capacity: float, refill_rate_per_sec: float):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = capacity
        self.last_refill_timestamp = time.monotonic()
        self._lock = threading.Lock()

    def allow(self, tokens_needed: int = 1) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill_timestamp
            self.last_refill_timestamp = now

            # Refill tokens proportional to elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True
            return False

class RateLimiterService:
    def __init__(self, capacity: float = 10, refill_rate: float = 2):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.clients: Dict[str, TokenBucket] = {}
        self._global_lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        with self._global_lock:
            if client_id not in self.clients:
                self.clients[client_id] = TokenBucket(self.capacity, self.refill_rate)
            bucket = self.clients[client_id]
        
        return bucket.allow(1)
```

---

## 3. Key Takeaways

- Lazy evaluation (`time.monotonic()` delta) eliminates the need for expensive background refill timer threads.
- Two-level locking prevents thread contention across different clients.
- Handle Clock Skew by using monotonic timers instead of wall-clock epoch time.
""",

    "09-worked-lld-atm-system.md": """# Worked LLD: ATM System (State Pattern)

A complete Low-Level Design for an Automated Teller Machine (ATM) utilizing the **State Pattern** to manage card validation, PIN verification, cash dispensing, and transactions.

```mermaid
stateDiagram-v2
    [*] --> IdleState
    IdleState --> CardInsertedState : insertCard()
    CardInsertedState --> AuthenticatedState : enterPin(valid)
    CardInsertedState --> IdleState : enterPin(invalid 3x) / eject()
    AuthenticatedState --> DispensingCashState : withdrawCash(sufficient funds)
    DispensingCashState --> IdleState : ejectCard() & dispense
```

---

## 1. Requirements

1. User inserts card, enters 4-digit PIN (max 3 attempts).
2. Check balance, withdraw cash, deposit cash.
3. Dispense cash in specific bill denominations ($100, $50, $20) using Chain of Responsibility.
4. Support state transitions: Idle $\to$ CardInserted $\to$ Authenticated $\to$ Dispensing.

---

## 2. Production Code Implementation (Python)

```python
from abc import ABC, abstractmethod

class ATM:
    def __init__(self, initial_cash: int):
        self.cash = initial_cash
        self.card = None
        self.pin_attempts = 0
        self.idle_state = IdleState(self)
        self.card_inserted_state = CardInsertedState(self)
        self.auth_state = AuthenticatedState(self)
        self.state: ATMState = self.idle_state

    def set_state(self, state: 'ATMState'):
        self.state = state

class ATMState(ABC):
    def __init__(self, atm: ATM):
        self.atm = atm

    @abstractmethod
    def insert_card(self, card): pass
    @abstractmethod
    def enter_pin(self, pin: str): pass
    @abstractmethod
    def withdraw_cash(self, amount: int): pass
    @abstractmethod
    def eject_card(self): pass

class IdleState(ATMState):
    def insert_card(self, card):
        self.atm.card = card
        self.atm.pin_attempts = 0
        self.atm.set_state(self.atm.card_inserted_state)
        print("Card inserted. Please enter PIN.")

    def enter_pin(self, pin): print("Insert card first.")
    def withdraw_cash(self, amount): print("Insert card first.")
    def eject_card(self): print("No card inserted.")

class CardInsertedState(ATMState):
    def insert_card(self, card): print("Card already present.")
    def enter_pin(self, pin: str):
        if pin == "1234":
            self.atm.set_state(self.atm.auth_state)
            print("PIN verified. Select transaction.")
        else:
            self.atm.pin_attempts += 1
            if self.atm.pin_attempts >= 3:
                print("Max attempts exceeded. Swallowing card.")
                self.atm.card = None
                self.atm.set_state(self.atm.idle_state)

    def withdraw_cash(self, amount): print("Enter PIN first.")
    def eject_card(self):
        self.atm.card = None
        self.atm.set_state(self.atm.idle_state)
        print("Card ejected.")

class AuthenticatedState(ATMState):
    def insert_card(self, card): print("Transaction in progress.")
    def enter_pin(self, pin): print("Already authenticated.")
    def withdraw_cash(self, amount: int):
        if amount > self.atm.cash:
            print("ATM has insufficient funds.")
            return
        self.atm.cash -= amount
        print(f"Dispensed ${amount}. Thank you.")
        self.eject_card()

    def eject_card(self):
        self.atm.card = None
        self.atm.set_state(self.atm.idle_state)
        print("Card ejected.")
```

---

## 3. Key Takeaways

- The State Pattern encapsulates state-specific behaviors, eliminating messy nested `switch/if` conditionals.
- Combine with the Chain of Responsibility pattern for currency dispensing ($100 $\to$ $50 $\to$ $20).
""",

    "10-worked-lld-chess-game.md": """# Worked LLD: Chess Game

A complete Low-Level Design for a standard two-player Chess game modeling boards, pieces, movement validations, turns, and checkmate detection.

```mermaid
classDiagram
    class PieceColor {
        <<enumeration>>
        WHITE
        BLACK
    }
    class Piece {
        <<abstract>>
        -PieceColor color
        -boolean isKilled
        +canMove(Board b, Spot start, Spot end) bool
    }
    class Spot {
        -int x
        -int y
        -Piece piece
    }
    class Board {
        -Spot[8][8] boxes
        +getSpot(int x, int y) Spot
        +resetBoard()
    }
    class ChessGame {
        -Board board
        -Player[2] players
        -Player currentTurn
        +makeMove(Move move) bool
    }

    Piece <|-- King
    Piece <|-- Queen
    Piece <|-- Rook
    Piece <|-- Bishop
    Piece <|-- Knight
    Piece <|-- Pawn
    Board "1" *-- "64" Spot
    Spot --> Piece
```

---

## 1. Core Classes and Piece Movement (Python)

```python
from enum import Enum
from typing import Optional

class Color(Enum):
    WHITE = 1
    BLACK = 2

class Piece:
    def __init__(self, color: Color):
        self.color = color
        self.is_alive = True

    def can_move(self, board, start, end) -> bool:
        raise NotImplementedError

class Knight(Piece):
    def can_move(self, board, start, end) -> bool:
        # Destination cannot have same color piece
        if end.piece and end.piece.color == self.color:
            return False
        
        dx = abs(start.x - end.x)
        dy = abs(start.y - end.y)
        return (dx * dy) == 2 # 2 and 1 or 1 and 2

class Spot:
    def __init__(self, x: int, y: int, piece: Optional[Piece] = None):
        self.x = x
        self.y = y
        self.piece = piece

class Board:
    def __init__(self):
        self.grid = [[Spot(x, y) for y in range(8)] for x in range(8)]
        self._init_pieces()

    def _init_pieces(self):
        self.grid[0][1].piece = Knight(Color.WHITE)
        self.grid[7][1].piece = Knight(Color.BLACK)

class ChessGame:
    def __init__(self):
        self.board = Board()
        self.turn = Color.WHITE

    def make_move(self, start_x, start_y, end_x, end_y) -> bool:
        start_spot = self.board.grid[start_x][start_y]
        end_spot = self.board.grid[end_x][end_y]
        piece = start_spot.piece

        if not piece or piece.color != self.turn:
            return False

        if not piece.can_move(self.board, start_spot, end_spot):
            return False

        # Execute move
        if end_spot.piece:
            end_spot.piece.is_alive = False

        end_spot.piece = piece
        start_spot.piece = None

        # Toggle turn
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
        return True
```

---

## 2. Key Takeaways

- Encapsulate move validation inside individual Piece subclasses (Polymorphism).
- Represent board coordinates using immutable Spot objects.
- Validate game-level invariants (checks, castling, en-passant) in the coordinating GameController.
""",

    "11-worked-lld-notification-service.md": """# Worked LLD: Notification Service

A complete Low-Level Design for an extensible, multi-channel notification engine (Email, SMS, Push, Slack) supporting user preference filtering, templates, and rate limiting.

```mermaid
classDiagram
    class NotificationChannel {
        <<interface>>
        +send(NotificationMessage msg) bool
    }
    class EmailChannel {
        +send(NotificationMessage msg) bool
    }
    class SMSChannel {
        +send(NotificationMessage msg) bool
    }
    class PushChannel {
        +send(NotificationMessage msg) bool
    }
    class NotificationDispatcher {
        -Map~String, NotificationChannel~ channels
        +dispatch(NotificationMessage msg)
    }

    NotificationChannel <|.. EmailChannel
    NotificationChannel <|.. SMSChannel
    NotificationChannel <|.. PushChannel
    NotificationDispatcher --> NotificationChannel
```

---

## 1. Functional Requirements

1. Support Email, SMS, and Mobile Push channels.
2. Dynamic templating engine.
3. User preferences (e.g., User opt-out of SMS marketing).
4. Extensibility: Add new channels (Slack, WhatsApp) without modifying existing channels (OCP).

---

## 2. Production Code Implementation (Python)

```python
from abc import ABC, abstractmethod
from typing import Dict, List

class NotificationMessage:
    def __init__(self, user_id: str, channel: str, template: str, params: Dict[str, str]):
        self.user_id = user_id
        self.channel = channel
        self.template = template
        self.params = params

class NotificationChannel(ABC):
    @abstractmethod
    def send(self, message: NotificationMessage) -> bool: pass

class EmailChannel(NotificationChannel):
    def send(self, message: NotificationMessage) -> bool:
        print(f"[EMAIL] Sent to {message.user_id}: {message.template}")
        return True

class SMSChannel(NotificationChannel):
    def send(self, message: NotificationMessage) -> bool:
        print(f"[SMS] Sent to {message.user_id}: {message.template}")
        return True

class PushChannel(NotificationChannel):
    def send(self, message: NotificationMessage) -> bool:
        print(f"[PUSH] Sent to {message.user_id}: {message.template}")
        return True

class UserPreferenceService:
    def is_channel_enabled(self, user_id: str, channel: str) -> bool:
        return True # Checked against user settings DB

class NotificationDispatcher:
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.prefs = UserPreferenceService()

    def register_channel(self, name: str, channel: NotificationChannel):
        self.channels[name] = channel

    def dispatch(self, message: NotificationMessage) -> bool:
        if not self.prefs.is_channel_enabled(message.user_id, message.channel):
            return False # Suppressed by user preferences

        channel = self.channels.get(message.channel)
        if not channel:
            raise ValueError(f"Unsupported channel: {message.channel}")

        return channel.send(message)
```

---

## 3. Key Takeaways

- Apply the Strategy Pattern to make communication channels interchangeable.
- Centralize rate limiting and preference checks before invoking expensive downstream provider APIs (Twilio, SendGrid).
""",

    "12-worked-lld-splitwise-expense-sharing.md": """# Worked LLD: Splitwise (Expense Sharing & Debt Simplification)

A complete Low-Level Design for an expense sharing system (Splitwise) supporting Equal, Exact, and Percentage splits, along with the **Greedy Debt Simplification Algorithm**.

```mermaid
graph TD
    subgraph "Debt Simplification Algorithm"
        A[Alice owes Bob $40]
        B[Bob owes Charlie $40]
        Direct[Simplified: Alice pays Charlie $40 directly!]
    end
```

---

## 1. Production Code Implementation (Python)

```python
from typing import Dict, List
import heapq

class SplitType:
    EQUAL = "EQUAL"
    EXACT = "EXACT"

class Expense:
    def __init__(self, payer_id: str, amount: float, splits: Dict[str, float]):
        self.payer_id = payer_id
        self.amount = amount
        self.splits = splits # user_id -> amount owed

class DebtSimplifier:
    @staticmethod
    def simplify_debts(balances: Dict[str, float]) -> List[str]:
        # Positive balance = owed money (creditor)
        # Negative balance = owes money (debtor)
        debtors = [] # max heap (stored as positive)
        creditors = [] # max heap

        for user, bal in balances.items():
            if bal < -0.01:
                heapq.heappush(debtors, (bal, user)) # min heap gives most negative
            elif bal > 0.01:
                heapq.heappush(creditors, (-bal, user)) # max heap

        transactions = []
        while debtors and creditors:
            debt_amt, debtor = heapq.heappop(debtors)
            debt_amt = -debt_amt
            cred_amt, creditor = heapq.heappop(creditors)
            cred_amt = -cred_amt

            settled = min(debt_amt, cred_amt)
            transactions.append(f"{debtor} pays {creditor} ${settled:.2f}")

            if debt_amt > cred_amt:
                heapq.heappush(debtors, (-(debt_amt - settled), debtor))
            elif cred_amt > debt_amt:
                heapq.heappush(creditors, (-(cred_amt - settled), creditor))

        return transactions
```

---

## 2. Key Takeaways

- Calculate net balances per user across all transactions ($O(N)$).
- Use two priority heaps (debtors and creditors) to greedily eliminate debt in at most $N-1$ transactions.
""",

    "13-concurrency-primitives-and-threading.md": """# Concurrency Primitives: Mutexes, Semaphores, and Thread Pools

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
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 17 Part 2 complete.")
