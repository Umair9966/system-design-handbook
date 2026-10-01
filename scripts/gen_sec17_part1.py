import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\17-low-level-design"

files = {
    "01-solid-principles-with-code-examples.md": """# SOLID Principles with Production Code Examples

The SOLID principles, introduced by Robert C. Martin (Uncle Bob), provide the foundation for writing maintainable, extensible, and understandable object-oriented code.

```mermaid
graph TD
    S[S: Single Responsibility Principle]
    O[O: Open/Closed Principle]
    L[L: Liskov Substitution Principle]
    I[I: Interface Segregation Principle]
    D[D: Dependency Inversion Principle]

    S --> Clean[Maintainable & Testable Codebase]
    O --> Clean
    L --> Clean
    I --> Clean
    D --> Clean
```

---

## 1. Single Responsibility Principle (SRP)
> *"A class should have one, and only one, reason to change."*

### Anti-Pattern:
A class that handles business calculations, database persistence, and HTML formatting:
```python
# VIOLATION of SRP
class Invoice:
    def __init__(self, amount):
        self.amount = amount

    def calculate_total(self):
        return self.amount * 1.20 # Tax

    def save_to_database(self):
        db.execute("INSERT INTO invoices VALUES (?)", self.amount)

    def print_html_report(self):
        return f"<div>Invoice: ${self.amount}</div>"
```

### Refactored (Adhering to SRP):
```python
class Invoice:
    def __init__(self, amount: float):
        self.amount = amount

    def calculate_total(self) -> float:
        return self.amount * 1.20

class InvoiceRepository:
    def save(self, invoice: Invoice):
        db.execute("INSERT INTO invoices VALUES (?)", invoice.amount)

class InvoiceHtmlFormatter:
    def format(self, invoice: Invoice) -> str:
        return f"<div>Invoice: ${invoice.amount}</div>"
```

---

## 2. Open/Closed Principle (OCP)
> *"Software entities should be open for extension, but closed for modification."*

Add new behavior by writing new classes, not by modifying and adding `if/else` ladders to existing tested classes.

```python
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float):
        pass

class StripePaymentProcessor(PaymentProcessor):
    def pay(self, amount: float):
        stripe_api.charge(amount)

class PayPalPaymentProcessor(PaymentProcessor):
    def pay(self, amount: float):
        paypal_api.charge(amount)

# To add ApplePay: create ApplePayProcessor class WITHOUT altering PaymentProcessor!
```

---

## 3. Liskov Substitution Principle (LSP)
> *"Subtypes must be substitutable for their base types without altering program correctness."*

### Classic Violation: Square Inheriting from Rectangle
```python
class Rectangle:
    def set_width(self, w): self.width = w
    def set_height(self, h): self.height = h
    def area(self): return self.width * self.height

class Square(Rectangle):
    def set_width(self, w):
        self.width = self.height = w # Mutates height unexpectedly!
```
*Fix*: Make `Shape` the base interface with an `area()` method; do not inherit Square from Rectangle.

---

## 4. Interface Segregation Principle (ISP)
> *"Clients should not be forced to depend upon interfaces that they do not use."*

Favor many small, client-specific role interfaces over one bloated general-purpose interface.

```go
// GOOD: Small, segregated interfaces
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type ReadWriter interface {
    Reader
    Writer
}
```

---

## 5. Dependency Inversion Principle (DIP)
> *"High-level modules should not depend on low-level modules. Both should depend on abstractions."*

High-level business use cases must not directly instantiate SQL database connections or third-party SDKs; inject interfaces via constructors.

---

## 6. Key Takeaways

- Apply SRP to keep classes focused and testable.
- Use polymorphism and Strategy patterns to uphold OCP.
- Avoid inheritance traps that violate LSP; prefer composition over inheritance.
- Design narrow interfaces (ISP) and inject abstractions (DIP).
""",

    "02-gang-of-four-design-patterns.md": """# Gang of Four (GoF) Design Patterns

The 23 classic software design patterns documented by the "Gang of Four" (Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides) are divided into Creational, Structural, and Behavioral categories.

```mermaid
graph TD
    GoF[GoF Design Patterns]
    GoF --> Creational[Creational: Object Instantiation]
    GoF --> Structural[Structural: Object Composition]
    GoF --> Behavioral[Behavioral: Object Communication]

    Creational --> Factory[Factory Method & Abstract Factory]
    Creational --> Singleton[Singleton / Double-Checked Locking]
    Creational --> Builder[Builder Pattern]

    Structural --> Adapter[Adapter Pattern]
    Structural --> Decorator[Decorator Pattern]
    Structural --> Proxy[Proxy Pattern]

    Behavioral --> Strategy[Strategy Pattern]
    Behavioral --> Observer[Observer Pattern]
    Behavioral --> State[State Pattern]
```

---

## 1. Top Patterns in System Design

### 1. Strategy Pattern (Behavioral)
Defines a family of interchangeable algorithms at runtime:
```python
from abc import ABC, abstractmethod

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float) -> float:
        pass

class RegularPricing(PricingStrategy):
    def calculate_price(self, base_price: float) -> float:
        return base_price

class SurgePricing(PricingStrategy):
    def calculate_price(self, base_price: float) -> float:
        return base_price * 1.5

class RideFareCalculator:
    def __init__(self, strategy: PricingStrategy):
        self.strategy = strategy

    def get_fare(self, distance: float) -> float:
        base = distance * 2.0
        return self.strategy.calculate_price(base)
```

---

### 2. Observer Pattern (Behavioral)
Publish/subscribe mechanism for in-memory event notifications:
```mermaid
graph LR
    Subject[Subject: StockPriceTracker] -->|Notify change| Obs1[Observer: MobileAppAlert]
    Subject -->|Notify change| Obs2[Observer: TradingBot]
    Subject -->|Notify change| Obs3[Observer: AuditLogger]
```

---

### 3. Decorator Pattern (Structural)
Attaches additional responsibilities dynamically without modifying underlying classes:
```python
class Coffee(ABC):
    @abstractmethod
    def cost(self) -> float: pass

class SimpleCoffee(Coffee):
    def cost(self) -> float: return 2.0

class MilkDecorator(Coffee):
    def __init__(self, coffee: Coffee):
        self._coffee = coffee
    def cost(self) -> float:
        return self._coffee.cost() + 0.5
```

---

## 2. Key Takeaways

- Use **Strategy** to swap business rules dynamically (discounts, route calculation, compression).
- Use **Decorator** to wrap cross-cutting behavior (rate limiting, logging, retry wrappers).
- Use **Observer** for decoupled in-memory event handling.
""",

    "03-uml-diagrams-class-and-sequence.md": """# UML Diagrams: Class and Sequence Diagrams

Unified Modeling Language (UML) provides standard visual notations for modeling software structure and runtime interaction workflows.

```mermaid
classDiagram
    class User {
        -String id
        -String email
        +login() bool
    }
    class Order {
        -String orderId
        -Double total
        +addItem(Item item) void
    }
    class Item {
        -String sku
        -Double price
    }
    User "1" --> "*" Order : places
    Order "1" *-- "*" Item : contains
```

---

## 1. Class Diagram Relationships

| Notation | Relationship | Meaning | Example |
| :--- | :--- | :--- | :--- |
| `-->` | **Association** | One class uses or references another | `User` uses `PaymentService` |
| `--*` | **Composition** | Strong "part-of" whole; lifetime bound | `Order` owns `LineItems` (if order dies, items die) |
| `--o` | **Aggregation** | Weak "has-a" relationship; independent life | `Department` has `Employees` (employees survive) |
| `..|>` | **Realization** | Class implements an interface | `PostgresRepo` implements `Repository` |
| `--|>` | **Inheritance** | Class extends a parent class | `CreditCard` extends `PaymentMethod` |

---

## 2. Sequence Diagrams: Runtime Interactions

Sequence diagrams depict object lifecycles, method invocations, and synchronous vs asynchronous message passing:

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant CheckoutCtrl as CheckoutController
    participant OrderSvc as OrderService
    participant PayGateway as PaymentGateway

    Customer->>CheckoutCtrl: POST /checkout (Items, Card)
    activate CheckoutCtrl
    CheckoutCtrl->>OrderSvc: CreateOrder(Items)
    activate OrderSvc
    OrderSvc-->>CheckoutCtrl: Order(id="123", status=PENDING)
    deactivate OrderSvc
    
    CheckoutCtrl->>PayGateway: Charge(Card, Total)
    activate PayGateway
    PayGateway-->>CheckoutCtrl: ChargeResult(SUCCESS)
    deactivate PayGateway

    CheckoutCtrl-->>Customer: 200 OK (Order Confirmed)
    deactivate CheckoutCtrl
```

---

## 3. Key Takeaways

- Class diagrams visualize static system structure and dependency coupling.
- Sequence diagrams capture runtime execution flow, call hierarchy, and message ordering.
- Use Composition over Aggregation when the child entity cannot exist without the parent container.
""",

    "04-worked-lld-parking-lot.md": """# Worked LLD: Parking Lot System

A complete Low-Level Design for a multi-floor parking lot supporting different vehicle types, dynamic spot allocation, and payment calculation.

```mermaid
classDiagram
    class VehicleType {
        <<enumeration>>
        MOTORCYCLE
        COMPACT
        LARGE
    }
    class Vehicle {
        <<abstract>>
        -String licensePlate
        -VehicleType type
        +getType() VehicleType
    }
    class ParkingSpot {
        -int spotNumber
        -int floor
        -VehicleType supportedType
        -boolean isFree
        -Vehicle currentVehicle
        +assignVehicle(Vehicle v) bool
        +vacate() void
    }
    class ParkingLot {
        -List~ParkingFloor~ floors
        -ParkingStrategy strategy
        +parkVehicle(Vehicle v) Ticket
        +unparkVehicle(Ticket t) Receipt
    }
    class Ticket {
        -String ticketId
        -Vehicle vehicle
        -ParkingSpot spot
        -Instant entryTime
    }

    Vehicle <|-- Car
    Vehicle <|-- Motorcycle
    Vehicle <|-- Truck
    ParkingLot "1" *-- "*" ParkingSpot
    ParkingLot --> Ticket
```

---

## 1. Functional Requirements

1. Multiple floors, with each floor having multiple parking spots.
2. Support distinct vehicle types: Motorcycle, Car (Compact), Truck (Large).
3. Assign closest available spot to entrance.
4. Issue timestamped ticket on entry.
5. Calculate dynamic hourly parking fees on exit based on vehicle type.
6. Thread-safe concurrent entry/exit.

---

## 2. Production Code Implementation (Python)

```python
from enum import Enum
from datetime import datetime
import threading
from typing import Dict, Optional, List

class VehicleType(Enum):
    MOTORCYCLE = 1
    CAR = 2
    TRUCK = 3

class Vehicle:
    def __init__(self, license_plate: str, vehicle_type: VehicleType):
        self.license_plate = license_plate
        self.vehicle_type = vehicle_type

class ParkingSpot:
    def __init__(self, spot_id: int, floor: int, spot_type: VehicleType):
        self.spot_id = spot_id
        self.floor = floor
        self.spot_type = spot_type
        self.is_occupied = False
        self.vehicle: Optional[Vehicle] = None
        self._lock = threading.Lock()

    def assign(self, vehicle: Vehicle) -> bool:
        with self._lock:
            if not self.is_occupied and self.spot_type == vehicle.vehicle_type:
                self.is_occupied = True
                self.vehicle = vehicle
                return True
            return False

    def vacate(self):
        with self._lock:
            self.is_occupied = False
            self.vehicle = None

class Ticket:
    def __init__(self, ticket_id: str, vehicle: Vehicle, spot: ParkingSpot):
        self.ticket_id = ticket_id
        self.vehicle = vehicle
        self.spot = spot
        self.entry_time = datetime.utcnow()

class FeeCalculator:
    RATES = {
        VehicleType.MOTORCYCLE: 1.0,
        VehicleType.CAR: 2.5,
        VehicleType.TRUCK: 5.0
    }

    @classmethod
    def calculate_fee(cls, ticket: Ticket, exit_time: datetime) -> float:
        duration_hours = max(1, int((exit_time - ticket.entry_time).total_seconds() / 3600))
        return duration_hours * cls.RATES[ticket.vehicle.vehicle_type]

class ParkingLot:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_parking_lot()
            return cls._instance

    def _init_parking_lot(self):
        self.spots: List[ParkingSpot] = []
        self.active_tickets: Dict[str, Ticket] = {}
        self.lot_lock = threading.Lock()

    def add_spot(self, spot: ParkingSpot):
        self.spots.append(spot)

    def park(self, vehicle: Vehicle) -> Optional[Ticket]:
        with self.lot_lock:
            for spot in self.spots:
                if spot.assign(vehicle):
                    ticket_id = f"TICK-{vehicle.license_plate}-{int(datetime.utcnow().timestamp())}"
                    ticket = Ticket(ticket_id, vehicle, spot)
                    self.active_tickets[ticket_id] = ticket
                    return ticket
            return None # Lot Full

    def unpark(self, ticket_id: str) -> Optional[float]:
        with self.lot_lock:
            ticket = self.active_tickets.pop(ticket_id, None)
            if not ticket:
                return None
            ticket.spot.vacate()
            return FeeCalculator.calculate_fee(ticket, datetime.utcnow())
```

---

## 3. Thread-Safety and Edge Cases

- **Locking Granularity**: Dual locking ensures thread safety. A coarse lot lock protects ticket dictionaries; fine-grained spot locks prevent race conditions where two cars claim the same spot simultaneously.
- **Lost Ticket Handling**: System allows looking up tickets by license plate in the active ticket hash map.
""",

    "05-worked-lld-elevator-system.md": """# Worked LLD: Elevator System (Dispatch Controller)

A complete Low-Level Design for a multi-car elevator control system optimizing passenger wait time using the LOOK (SCAN) elevator dispatching algorithm.

```mermaid
classDiagram
    class Direction {
        <<enumeration>>
        UP
        DOWN
        IDLE
    }
    class ElevatorState {
        <<enumeration>>
        MOVING
        STOPPED
        MAINTENANCE
    }
    class ElevatorCar {
        -int id
        -int currentFloor
        -Direction direction
        -ElevatorState state
        -TreeSet~int~ upStops
        -TreeSet~int~ downStops
        +addStop(int floor)
        +step()
    }
    class Dispatcher {
        -List~ElevatorCar~ elevators
        +requestElevator(int floor, Direction dir)
    }

    Dispatcher --> ElevatorCar
```

---

## 1. Requirements and Dispatch Strategy

- Multiple elevator cars serving $N$ floors.
- Hall calls from floors (Up / Down buttons).
- Internal car destination requests (floor buttons inside car).
- **Dispatch Algorithm**: SCAN / LOOK algorithm (serves all requests in current direction until no more remain, then reverses).

---

## 2. Production Code Implementation (Python)

```python
from enum import Enum
import threading
import time
from typing import List, Set

class Direction(Enum):
    UP = 1
    DOWN = -1
    IDLE = 0

class ElevatorCar:
    def __init__(self, car_id: int):
        self.car_id = car_id
        self.current_floor = 1
        self.direction = Direction.IDLE
        self.up_stops: Set[int] = set()
        self.down_stops: Set[int] = set()
        self._lock = threading.Lock()

    def add_destination(self, floor: int):
        with self._lock:
            if floor > self.current_floor:
                self.up_stops.add(floor)
                if self.direction == Direction.IDLE:
                    self.direction = Direction.UP
            elif floor < self.current_floor:
                self.down_stops.add(floor)
                if self.direction == Direction.IDLE:
                    self.direction = Direction.DOWN

    def step(self):
        with self._lock:
            if self.direction == Direction.UP:
                self.current_floor += 1
                if self.current_floor in self.up_stops:
                    self.up_stops.remove(self.current_floor)
                    self._open_doors()
                if not self.up_stops:
                    self.direction = Direction.DOWN if self.down_stops else Direction.IDLE

            elif self.direction == Direction.DOWN:
                self.current_floor -= 1
                if self.current_floor in self.down_stops:
                    self.down_stops.remove(self.current_floor)
                    self._open_doors()
                if not self.down_stops:
                    self.direction = Direction.UP if self.up_stops else Direction.IDLE

    def _open_doors(self):
        # Open doors for passenger boarding
        pass

class ElevatorDispatcher:
    def __init__(self, elevators: List[ElevatorCar]):
        self.elevators = elevators

    def select_best_elevator(self, floor: int, direction: Direction) -> ElevatorCar:
        # P2C / Proximity Scoring heuristic
        best_car = None
        min_distance = float('inf')

        for car in self.elevators:
            distance = abs(car.current_floor - floor)
            # Bonus score if car is moving toward the floor in same direction
            if car.direction == direction and ((direction == Direction.UP and car.current_floor <= floor) or 
                                               (direction == Direction.DOWN and car.current_floor >= floor)):
                distance -= 2
            elif car.direction == Direction.IDLE:
                distance -= 1

            if distance < min_distance:
                min_distance = distance
                best_car = car

        return best_car or self.elevators[0]

    def press_hall_button(self, floor: int, direction: Direction):
        car = self.select_best_elevator(floor, direction)
        car.add_destination(floor)
```

---

## 3. Key Takeaways

- Separate the Dispatcher (global routing controller) from individual Elevator Cars (local state machines).
- Use sorted sets or bitsets to store stops for the LOOK / SCAN elevator movement algorithm.
- Ensure state transitions are protected with mutexes to prevent concurrent movement corruption.
""",

    "06-worked-lld-library-management-system.md": """# Worked LLD: Library Management System

A complete Low-Level Design for a Library Management System supporting catalog search, book lending, overdue fines, and member reservations.

```mermaid
classDiagram
    class BookItem {
        -String barcode
        -String title
        -String author
        -String isbn
        -BookStatus status
        -Instant dueDate
    }
    class Member {
        -String memberId
        -String name
        -int booksCheckedOut
        +checkoutBook(BookItem item)
        +returnBook(BookItem item)
    }
    class BookLending {
        -String transactionId
        -BookItem item
        -Member member
        -Instant checkoutDate
        -Instant returnDate
        -double fineAmount
    }
    Member "1" --> "*" BookLending
    BookLending --> BookItem
```

---

## 1. Functional Requirements

1. Catalog search by Title, Author, or ISBN.
2. Members can check out at most 5 books at a time.
3. Maximum checkout period is 14 days.
4. Automated overdue fine calculation ($0.50/day overdue).
5. Thread-safe book reservation and checkout.

---

## 2. Production Code Implementation (Python)

```python
from datetime import datetime, timedelta
import threading
from typing import Dict, List, Optional

class BookStatus:
    AVAILABLE = "AVAILABLE"
    LOANED = "LOANED"
    RESERVED = "RESERVED"

class BookItem:
    def __init__(self, barcode: str, isbn: str, title: str, author: str):
        self.barcode = barcode
        self.isbn = isbn
        self.title = title
        self.author = author
        self.status = BookStatus.AVAILABLE
        self.due_date: Optional[datetime] = None
        self._lock = threading.Lock()

class Member:
    MAX_BOOKS = 5

    def __init__(self, member_id: str, name: str):
        self.member_id = member_id
        self.name = name
        self.borrowed_books: Dict[str, BookItem] = {}

    def can_borrow(self) -> bool:
        return len(self.borrowed_books) < self.MAX_BOOKS

class LibraryService:
    DAILY_FINE = 0.50

    def __init__(self):
        self.catalog_by_barcode: Dict[str, BookItem] = {}
        self.catalog_by_title: Dict[str, List[BookItem]] = {}
        self.members: Dict[str, Member] = {}
        self._sys_lock = threading.Lock()

    def checkout_book(self, member_id: str, barcode: str) -> bool:
        with self._sys_lock:
            member = self.members.get(member_id)
            book = self.catalog_by_barcode.get(barcode)

            if not member or not book:
                return False
            if not member.can_borrow():
                return False

            with book._lock:
                if book.status != BookStatus.AVAILABLE:
                    return False
                book.status = BookStatus.LOANED
                book.due_date = datetime.utcnow() + timedelta(days=14)
                member.borrowed_books[barcode] = book
                return True

    def return_book(self, member_id: str, barcode: str) -> float:
        with self._sys_lock:
            member = self.members.get(member_id)
            if not member or barcode not in member.borrowed_books:
                return 0.0

            book = member.borrowed_books.pop(barcode)
            with book._lock:
                fine = 0.0
                if book.due_date and datetime.utcnow() > book.due_date:
                    days_overdue = (datetime.utcnow() - book.due_date).days
                    fine = max(0, days_overdue) * self.DAILY_FINE
                
                book.status = BookStatus.AVAILABLE
                book.due_date = None
                return fine
```

---

## 3. Key Takeaways

- Encapsulate book state transitions within synchronized blocks on the specific book item.
- Enforce business invariants (max 5 books, overdue fines) prior to state modification.
- Maintain separate indices by barcode, title, and author to support multi-attribute search.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 17 Part 1 complete.")
