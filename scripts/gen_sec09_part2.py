import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\09-api-design"

files = {
    "05-grpc-and-protocol-buffers.md": """# gRPC and Protocol Buffers

gRPC is an open-source, high-performance Remote Procedure Call (RPC) framework developed by Google. It operates over HTTP/2 transport and uses Protocol Buffers (Protobuf) as its Interface Definition Language (IDL) and binary serialization format.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Application
    participant Stub as Client Stub (Generated)
    participant Channel as HTTP/2 Channel
    participant Skeleton as Server Skeleton
    participant Service as Backend Service

    Client->>Stub: OrderResponse = PlaceOrder(OrderRequest)
    Note over Stub: Serializes request into binary Protobuf
    Stub->>Channel: HTTP/2 POST /OrderService/PlaceOrder (binary payload)
    Channel->>Skeleton: Frames multiplexed over single TCP socket
    Skeleton->>Service: Unmarshals binary to struct & invokes method
    Service-->>Skeleton: Returns OrderResponse object
    Skeleton-->>Channel: Binary serialized response + Status Headers
    Channel-->>Stub: Multiplexed frames returned
    Stub-->>Client: Typed native object returned
```

---

## 1. What It Is & Why It Exists

In distributed microservices, REST over JSON introduces high serialization overhead, bulky textual payloads, lack of compile-time contract enforcement, and HTTP/1.1 head-of-line blocking. 

gRPC was designed to solve these bottlenecks:
- **Binary Protocol Buffers**: Compact serialization (3x-10x smaller than JSON) and ultra-fast marshalling/unmarshalling.
- **Strict Typed Contracts**: `.proto` files define service contracts. Code generators (`protoc`) emit strongly-typed stubs in Go, Java, Python, C++, Rust, and TypeScript.
- **HTTP/2 Transport**: Native header compression (HPACK), bidirectional multiplexing over a single persistent TCP connection, and flow control.
- **Streaming Primitives**: Unary, Client-streaming, Server-streaming, and Bidirectional streaming.

---

## 2. Protocol Buffers Internals: Varints and Wire Types

Protobuf uses tag-value encoding instead of field names. Each field in a `.proto` file has a unique number:

```protobuf
syntax = "proto3";

package commerce.v1;

service OrderService {
  rpc PlaceOrder (PlaceOrderRequest) returns (PlaceOrderResponse);
  rpc StreamOrderStatus (OrderStatusRequest) returns (stream OrderStatusUpdate);
}

message PlaceOrderRequest {
  string order_id = 1;
  int64 user_id = 2;
  double total_amount = 3;
  repeated string item_skus = 4;
}

message PlaceOrderResponse {
  string order_id = 1;
  enum Status {
    PENDING = 0;
    CONFIRMED = 1;
    FAILED = 2;
  }
  Status status = 2;
  int64 created_at = 3;
}
```

### Key Encoding Mechanics:
1. **Field Tag**: `(field_number << 3) | wire_type`.
2. **Varints**: Integers use variable-length bytes (MSB indicates if more bytes follow). An integer `1` takes 1 byte instead of 4 or 8 bytes.
3. **No Field Names on the Wire**: JSON transmits keys repeatedly (`"total_amount": 199.99`); Protobuf only transmits tag `(3 << 3) | 1` (1 byte) followed by the 8-byte double.

---

## 3. The Four gRPC Communication Patterns

```mermaid
graph TD
    subgraph "1. Unary RPC"
        U_C[Client] -->|Single Request| U_S[Server]
        U_S -->|Single Response| U_C
    end

    subgraph "2. Server Streaming"
        SS_C[Client] -->|Single Request| SS_S[Server]
        SS_S -->|Stream: Chunk 1, 2, 3...| SS_C
    end

    subgraph "3. Client Streaming"
        CS_C[Client] -->|Stream: Chunk 1, 2, 3...| CS_S[Server]
        CS_S -->|Single Response| CS_C
    end

    subgraph "4. Bidirectional Streaming"
        BD_C[Client] <-->|Independent Full-Duplex Streams| BD_S[Server]
    end
```

---

## 4. Trade-offs: gRPC vs REST vs GraphQL

| Dimension | gRPC | REST (JSON) | GraphQL |
| :--- | :--- | :--- | :--- |
| **Data Format** | Binary (Protobuf) | Text (JSON, XML) | Text (JSON) |
| **Transport** | HTTP/2 (requires end-to-end) | HTTP/1.1, HTTP/2, HTTP/3 | HTTP/1.1, HTTP/2 |
| **Payload Size** | Extremely Small | Moderate to Large | Minimal (client-selected fields) |
| **Browser Support** | Requires gRPC-Web proxy (Envoy) | Native in all browsers | Native in all browsers |
| **Load Balancing** | Complex (L7 connection pooling) | Simple (L4/L7 load balancers) | Simple (L7 load balancers) |
| **Contract Enforcement**| Strict compile-time `.proto` | Optional (OpenAPI / JSON Schema) | Strict Schema Definition (SDL) |
| **Best Used For** | Service-to-service internal RPC | Public APIs, Browser clients | Mobile BFFs, complex graph data |

---

## 5. gRPC Load Balancing Gotcha

Because gRPC uses long-lived HTTP/2 multiplexed TCP connections, standard L4 load balancers (like AWS NLB or round-robin TCP proxies) will route the initial TCP connection to one backend pod, and **all subsequent RPCs over that connection stay on that pod**.

```mermaid
graph LR
    subgraph Problem: L4 Load Balancing
        C1[Client 1] -->|Single Persistent TCP Connection| LB4[L4 Load Balancer]
        LB4 -->|All 10,000 RPCs| S1[Backend Pod 1 - 100% CPU]
        LB4 -.->|Idle Connection| S2[Backend Pod 2 - 0% CPU]
    end
```

### Solutions:
1. **L7 Proxy Load Balancing**: Envoy or NGINX parses HTTP/2 frames and balances individual requests across backends.
2. **Client-Side Load Balancing**: The gRPC client queries DNS or a control plane (xDS / Consul) to resolve all backend IPs and manages a pool of sub-channels with round-robin or P2C.

---

## 6. Real-World Case Studies

1. **Netflix**: Migrated internal IPC from REST/JSON to gRPC. Reduced CPU usage on microservices by 25% and reduced p99 internal tail latency by 40ms.
2. **Uber**: Uses Protobuf schemas stored in a monorepo with automated breaking-change detection during CI linting.
3. **CockroachDB & Kubernetes**: Native gRPC for consensus communication (Raft transport) and API controller interactions.

---

## 7. Common Pitfalls

- **Forgetting Deadlines / Timeouts**: Without client deadlines, slow downstreams will cause requests to cascade and hang client goroutines/threads forever.
- **Breaking Schema Changes**: Changing field numbers or field types breaks binary backwards compatibility. Only add new fields or deprecate existing ones.
- **Attempting gRPC from Browsers Directly**: Browsers cannot access raw HTTP/2 frames; you must use `grpc-web` with an Envoy translation proxy.

---

## 8. Key Takeaways

- gRPC delivers unmatched throughput and lower resource usage for internal microservices.
- Protobuf tags ensure fast serialization without sending repeated string field names.
- Always implement L7 or client-side load balancing to avoid connection pinning.
- Always propagate `context` with deadlines and cancellation tokens across RPC hops.

---

## 9. Interview Questions

1. *How does gRPC achieve higher performance compared to REST over JSON?*
2. *Why does L4 load balancing fail with gRPC, and how do you resolve it?*
3. *How do you version and evolve a Protocol Buffer schema without breaking existing consumers?*
""",

    "06-graphql-design-and-tradeoffs.md": """# GraphQL Schema, Resolvers, and DataLoader

GraphQL is an open-source query language for APIs and a runtime for fulfilling those queries with existing data. Developed by Meta in 2012 and open-sourced in 2015, GraphQL enables clients to define the exact structure of data required.

```mermaid
sequenceDiagram
    autonumber
    participant Mobile as Mobile Client
    participant GQL as GraphQL Gateway
    participant UserSvc as User Service
    participant OrderSvc as Order Service
    participant ReviewSvc as Review Service

    Mobile->>GQL: POST /graphql { user(id: "u1") { name, orders { id, total }, reviews { rating } } }
    par Fetch User
        GQL->>UserSvc: GET /users/u1
    and Fetch Orders
        GQL->>OrderSvc: GET /orders?userId=u1
    and Fetch Reviews
        GQL->>ReviewSvc: GET /reviews?userId=u1
    end
    Note over GQL: Aggregates & shapes JSON response matching query
    GQL-->>Mobile: { "data": { "user": { "name": "Alice", "orders": [...], "reviews": [...] } } }
```

---

## 1. Core Concepts: Schema, Queries, and Mutations

A GraphQL API is defined by a strongly typed schema:

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  orders(limit: Int = 10): [Order!]!
}

type Order {
  id: ID!
  total: Float!
  createdAt: String!
  items: [OrderItem!]!
}

type Query {
  user(id: ID!): User
}

type Mutation {
  createOrder(userId: ID!, items: [OrderItemInput!]!): Order!
}
```

---

## 2. The N+1 Problem and DataLoader

In naive GraphQL implementations, each nested resolver executes an independent database query. 

```mermaid
graph TD
    Q[Query: 10 Users + their Orders] --> U[1 Query: SELECT * FROM users LIMIT 10]
    U --> O1[Query 1: SELECT * FROM orders WHERE user_id = 1]
    U --> O2[Query 2: SELECT * FROM orders WHERE user_id = 2]
    U --> O3[Query 3: SELECT * FROM orders WHERE user_id = 3]
    U --> ON[... Query 10: SELECT * FROM orders WHERE user_id = 10]
```
*Result*: 1 query for users + 10 queries for orders = 11 queries ($N+1$). For 1,000 users, 1,001 database queries will saturate the database pool.

### Solution: DataLoader (Batching and Caching)

DataLoader collects all individual IDs requested during a single tick of the event loop and issues a single batch query:

```mermaid
graph TD
    DL[DataLoader Batching Window] -->|Collects IDs: 1, 2, 3... 10| DB[(Database)]
    DB -->|Single Query: SELECT * FROM orders WHERE user_id IN (1,2,3...10)| DL
    DL -->|Distributes arrays back to respective resolvers| Resolvers[User Resolvers]
```

```javascript
const orderLoader = new DataLoader(async (userIds) => {
  const orders = await db.query(
    'SELECT * FROM orders WHERE user_id = ANY($1)',
    [userIds]
  );
  // Group orders by userId and return in the exact order of userIds
  const orderMap = groupBy(orders, 'userId');
  return userIds.map(id => orderMap[id] || []);
});

// Inside GraphQL Resolver:
const resolvers = {
  User: {
    orders: (parent, args, context) => context.orderLoader.load(parent.id)
  }
};
```

---

## 3. Trade-offs: GraphQL vs REST

| Dimension | GraphQL | REST |
| :--- | :--- | :--- |
| **Over/Under-Fetching** | Zero over-fetching (client requests exact fields) | Frequent over-fetching or multiple round-trips |
| **HTTP Caching** | Hard (most queries are `POST /graphql` with body) | Trivial (URL-based `GET /users/123` cached by CDNs) |
| **Attack Surface** | High (nested queries can cause recursive DoS) | Low (fixed endpoints with predictable resource costs) |
| **Client Flexibility** | Maximum flexibility | Rigid endpoints |
| **API Versioning** | Field deprecation (`@deprecated`) | URL path `/v1`, headers, or query params |
| **Monitoring** | Complex (need field-level execution metrics) | Simple (HTTP status codes, URI path metrics) |

---

## 4. Mitigating GraphQL Security & DoS Risks

Because clients define queries, malicious or poorly written queries can take down backends:

```graphql
# Malicious recursive query
query MaliciousBomb {
  user(id: "1") {
    orders {
      user {
        orders {
          user {
            orders { ... }
          }
        }
      }
    }
  }
}
```

### Production Protections:
1. **Query Depth Limiting**: Reject any query exceeding a maximum AST depth (e.g., maximum depth of 6).
2. **Query Complexity Analysis**: Assign cost points to each field (e.g., scalar = 1 pt, list = 10 pts). Reject queries exceeding 500 total points.
3. **Persisted Queries (Automatic Persisted Queries - APQ)**: Clients do not send arbitrary query strings in production. Instead, build systems hash approved queries, and clients send `POST /graphql?hash=a1b2c3d4`. This restores CDN caching and prevents arbitrary AST execution!

---

## 5. Real-World Case Studies

1. **GitHub**: Migrated its v4 API to GraphQL, enabling developers to fetch complex relationships (repos, pull requests, reviewers, comments) in a single round-trip.
2. **Shopify**: Exposes its Storefront and Admin APIs via GraphQL to allow headless storefronts to fetch only required product details.
3. **Twitter / X**: Uses GraphQL for mobile client feeds, cutting mobile payload sizes by 40%.

---

## 6. Key Takeaways

- GraphQL shines as a Backend-For-Frontend (BFF) layer aggregating disparate microservices for mobile and web clients.
- Always use DataLoader in resolvers to eliminate the $N+1$ query disaster.
- Implement Query Depth and Complexity limiting or Persisted Queries before exposing GraphQL to public untrusted clients.
""",

    "07-webhooks-and-async-apis.md": """# Webhooks and Asynchronous APIs

A webhook (reverse API) is an architectural pattern where a server notifies external clients of events by making an asynchronous HTTP POST request to a client-configured URL.

```mermaid
sequenceDiagram
    autonumber
    participant Customer as Customer
    participant Merchant as Merchant App (Client)
    participant Stripe as Payment Gateway (Server)

    Customer->>Stripe: Submits Credit Card Payment
    Stripe-->>Customer: Payment processing started...
    Note over Stripe: 3 seconds later, bank confirms charge
    Stripe->>Merchant: POST https://merchant.com/webhooks/stripe<br/>Header: Stripe-Signature<br/>Body: {"event": "charge.succeeded", "amount": 5000}
    Merchant-->>Stripe: 200 OK (Processed)
    Merchant->>Customer: Send Confirmation Email & Activate Account
```

---

## 1. Webhooks vs Polling vs WebSockets

| Method | Communication Direction | Efficiency | Latency | Infrastructure Overhead |
| :--- | :--- | :--- | :--- | :--- |
| **Short Polling** | Client -> Server (`GET` every 5s) | Extremely Low (99% empty responses) | 0 - 5 seconds | High server load |
| **WebSockets** | Bidirectional persistent TCP | High for browser-to-server real-time | < 50ms | High connection state on server |
| **Webhooks** | Server -> Client (`POST` on event) | Optimal (triggered only on events) | < 1 second | Stateless event delivery pipeline |

---

## 2. Production Webhook Delivery Architecture

Delivering webhooks reliably at scale requires handling client timeouts, downstream failures, network partitions, and malicious consumer URLs.

```mermaid
graph TD
    Event[Business Event Occurs] --> Queue[Kafka / SQS Outbox]
    Queue --> Worker[Webhook Dispatch Worker Pool]
    Worker --> Sign[HMAC-SHA256 Signer]
    Sign --> ClientEndpoint[Client HTTPS URL]
    ClientEndpoint -->|200 OK| Success[Mark Delivered]
    ClientEndpoint -->|500 / Timeout| RetryQueue[Retry Queue with Exponential Backoff]
    RetryQueue --> Worker
    RetryQueue -->|Exceeded 10 Attempts| DLQ[Dead Letter Queue & Alert Merchant]
```

### Essential Reliability Guarantees:
1. **Exponential Backoff with Jitter**: If client returns non-2xx or times out, retry at $t = 2^n + \text{random\_jitter}$ (e.g., 5s, 15s, 1m, 5m, 1h, 6h, 24h).
2. **Strict Timeouts**: Limit outgoing HTTP requests to 5-10 seconds. Never allow a slow client endpoint to exhaust your worker threads.
3. **Circuit Breaking**: If an external endpoint fails 100% of requests over 1 hour, pause delivery and notify the developer via dashboard/email.

---

## 3. Security: Signatures, Replay Attacks, and SSRF

### 1. Cryptographic Signatures (HMAC-SHA256)
The sending server signs the payload with a shared secret:
```
Header: X-Signature: t=1696156800,v1=9c84b1e56b464a7c8c8...
```
Verification on client side:
$$\text{Expected} = \text{HMAC-SHA256}(K_{\text{secret}}, \text{timestamp} + "." + \text{payload})$$

### 2. Preventing Replay Attacks
Include a Unix timestamp in the signature header. The client rejects any webhook where $|T_{\text{current}} - T_{\text{header}}| > 300\text{ seconds}$.

### 3. Server-Side Request Forgery (SSRF) Protection
Prevent malicious users from registering internal IPs (e.g., `http://169.254.169.254` AWS metadata or `http://localhost:8080/admin`) as their webhook URL:
- Resolve DNS and block private IP ranges (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, link-local `169.254.0.0/16`).
- Disallow HTTP redirects (`301`/`302`) to prevent DNS rebinding attacks.

---

## 4. Consumer Best Practices: Asynchronous Processing

A webhook endpoint on the receiving side should **never** perform synchronous business logic before responding.

```mermaid
sequenceDiagram
    participant S as Stripe
    participant API as Merchant Webhook Receiver
    participant Q as Internal Redis Queue
    participant W as Async Background Worker

    S->>API: POST /webhooks/stripe
    Note over API: 1. Verify HMAC Signature<br/>2. Push payload to internal queue
    API->>Q: LPUSH "webhook:events" payload
    API-->>S: 200 OK (Within 50ms)
    Q->>W: Pops event
    W->>W: Process billing, credit wallet, send invoice
```

---

## 5. Real-World Case Studies

1. **Stripe**: Sends millions of webhooks daily with signature verification, automated retries over 3 days, and a local CLI (`stripe listen`) that tunnels webhooks to localhost for local testing.
2. **GitHub**: Triggers webhooks on git push, pull request, and deployment events to automate CI/CD runners (Jenkins, GitHub Actions).
3. **Slack**: Uses event subscriptions to send bot interactions and mention events to app servers.

---

## 6. Key Takeaways

- Always sign webhooks using HMAC-SHA256 and include timestamps to prevent replay attacks.
- Senders must implement exponential backoff with jitter and a Dead-Letter Queue.
- Receivers must verify signatures, enqueue payloads immediately, return HTTP 200 within milliseconds, and process idempotently.
""",

    "08-api-security-and-auth.md": """# API Security and Authentication

Securing distributed APIs requires multi-layered defense covering authentication (AuthN), authorization (AuthZ), transport security, token handling, and traffic protection.

```mermaid
graph LR
    subgraph Edge / Gateway
        Client[Client App] -->|HTTPS + TLS 1.3| GW[API Gateway / Envoy]
        GW -->|1. Validate WAF & Rate Limits| WAF[WAF]
        GW -->|2. Verify JWT Signature / Introspect| IdP[(Identity Provider / OAuth2)]
    end

    subgraph Internal Network
        GW -->|3. Forward Request + Injected Claims| S1[Service A]
        S1 -->|mTLS + Spiffe Identity| S2[Service B]
    end
```

---

## 1. Authentication Mechanisms: API Keys, OAuth2, and JWTs

### 1. API Keys
- Simple string passed in headers (`X-API-Key: abc123xyz`).
- **Use Case**: Server-to-server integration for machine identification.
- **Limitation**: Cannot represent user delegation; vulnerable if leaked in client-side code.

### 2. OAuth 2.0 & OpenID Connect (OIDC)
- OAuth 2.0 handles **delegated authorization** (e.g., "Allow app X to read my Google Drive files").
- OIDC adds an **identity layer** on top of OAuth 2.0 (`id_token`) for authentication.
- **Grant Types**:
  - *Authorization Code + PKCE*: Standard for single-page apps (SPAs) and mobile devices.
  - *Client Credentials*: Server-to-server machine communication.

### 3. JSON Web Tokens (JWT) vs Opaque Tokens

```mermaid
graph TD
    subgraph "Stateless JWT"
        J_GW[Gateway] -->|Decodes Signature with Public Key (RS256)| J_OK[Verified Locally (0 DB lookups)]
        J_Revoke[Revocation Challenge: Hard until expiry]
    end

    subgraph "Opaque Token"
        O_GW[Gateway] -->|Queries Session Store / Redis| O_DB[(Token Cache)]
        O_Revoke[Instant Revocation: Delete from Redis]
    end
```

| Feature | JWT (Stateless) | Opaque Token (Stateful) |
| :--- | :--- | :--- |
| **Verification** | In-memory via public key (asymmetric RS256/ES256) | Database or Redis lookup |
| **Latency** | Sub-millisecond | 1-5ms network round-trip |
| **Payload Size** | ~500B - 2KB (Base64 encoded headers, claims, signature) | 32-64 bytes random string |
| **Instant Revocation** | Difficult (requires token blacklist / short expiration) | Trivial (delete key from Redis) |
| **Best Practice** | Short-lived Access Token (15m) + Long-lived Refresh Token (7d) | Enterprise session management |

---

## 2. Authorization: RBAC vs ABAC

```mermaid
graph TD
    subgraph "Role-Based Access Control (RBAC)"
        User[User] --> Role[Role: Admin / Editor / Viewer]
        Role --> Perm[Permissions: read, write, delete]
    end

    subgraph "Attribute-Based Access Control (ABAC)"
        Req[Context: User, Resource, Time, Location] --> Engine{Policy Engine (OPA)}
        Engine -->|User.dept == Resource.dept AND Time in 9-5| Allow[Allow Access]
    end
```

- **RBAC**: Map permissions to roles, and roles to users. Simple to implement, but suffers from "role explosion" when fine-grained rules emerge.
- **ABAC**: Evaluates attributes (Subject, Resource, Action, Environment). Implemented via engines like Open Policy Agent (OPA) with Rego policies.

---

## 3. Mutual TLS (mTLS) for Service-to-Service Security

In zero-trust microservice architectures, edge authentication is not enough. Services must authenticate each other over internal networks.

```mermaid
sequenceDiagram
    participant SvcA as Service A (Client)
    participant SvcB as Service B (Server)

    Note over SvcA, SvcB: Standard TLS Handshake
    SvcB-->>SvcA: Sends Server Certificate
    SvcA->>SvcA: Validates Server Certificate against Root CA
    Note over SvcA, SvcB: mTLS Client Verification
    SvcB->>SvcA: Requests Client Certificate
    SvcA-->>SvcB: Sends Client Certificate
    SvcB->>SvcB: Validates Client SAN (SPIFFE ID) against CA
    Note over SvcA, SvcB: Both parties authenticated -> Encrypted Channel
```

---

## 4. OWASP API Security Top 10 (Critical Defenses)

1. **BOLA (Broken Object Level Authorization)**: A user changes `GET /api/v1/orders/100` to `/orders/101` and sees another user's order.
   - *Fix*: Always verify ownership: `WHERE order_id = :id AND user_id = :authenticated_user_id`.
2. **Broken Authentication**: Weak JWT signing algorithms (e.g., accepting `alg: "none"` or using symmetric HMAC with a guessable secret).
   - *Fix*: Enforce asymmetric RS256/ES256; validate `iss`, `aud`, and `exp`.
3. **Mass Assignment**: Client sends extra fields in JSON payload (`{"name": "Alice", "is_admin": true}`).
   - *Fix*: Use strict Data Transfer Objects (DTOs) with allow-listed fields.
4. **Lack of Rate Limiting**: Brute-force attacks against login and OTP endpoints.
   - *Fix*: IP and user-level rate limiting at the API Gateway.

---

## 5. Key Takeaways

- Never roll custom cryptography or authentication protocols. Use established standards (OAuth 2.0, OIDC, PKCE).
- Keep JWT lifetimes short (10-15 minutes) and issue refresh tokens stored in HTTP-only, Secure, SameSite cookies.
- Defend against BOLA at every data access layer by scoping queries to the authenticated tenant/user.
- Implement mTLS between microservices to enforce Zero Trust security.
""",

    "09-api-documentation-and-contracts.md": """# API Documentation, Versioning, and Contracts

In microservice ecosystems, APIs are binding public contracts between teams and organizations. Effective versioning, backward compatibility, and automated schema contracts prevent outages and developer friction.

```mermaid
graph LR
    Spec[OpenAPI / Protobuf Spec in Git] --> Lint[Spectral / Buf Linting]
    Lint --> CI[Breaking Change Detection CI]
    CI --> CodeGen[SDK & Stub Generation]
    CI --> Mock[Mock Servers (Prism)]
    CI --> Docs[Interactive Docs (Swagger / Redoc)]
```

---

## 1. API Versioning Strategies

When breaking changes cannot be avoided, versioning ensures existing consumers continue operating without interruption.

```mermaid
graph TD
    V1[API Versioning Strategies]
    V1 --> URI[1. URI Path Versioning<br/>/v1/users, /v2/users]
    V1 --> Header[2. Custom Header Versioning<br/>X-API-Version: 2026-10-01]
    V1 --> Content[3. Content Negotiation / Accept Header<br/>Accept: application/vnd.company.v2+json]
    V1 --> Query[4. Query Parameter<br/>/users?version=2]
```

### Comparative Analysis:

| Strategy | Example | Pros | Cons | Used By |
| :--- | :--- | :--- | :--- | :--- |
| **URI Path** | `https://api.example.com/v1/orders` | Clear, cache-friendly on CDNs, easy browser testing | Can lead to code duplication across controllers | Google, Twitter, Stripe (for major) |
| **Custom Header** | `X-API-Version: 2026-10-01` | Clean URLs, allows granular date-based rolling versions | Cannot be tested directly in a browser URL bar | Stripe, Twilio |
| **Accept Header** | `Accept: application/vnd.myapi.v2+json` | Follows pure REST HATEOAS standards | Hard to inspect, complicated client configurations | GitHub |

---

## 2. Backward Compatibility Rules

A breaking change forces consumers to modify their client code. Follow Postel's Law: *"Be conservative in what you send, be liberal in what you accept."*

```mermaid
graph TD
    subgraph "Safe (Non-Breaking) Changes"
        N1[Add new optional query parameter]
        N2[Add new field in response JSON]
        N3[Add a completely new endpoint]
    end

    subgraph "Breaking Changes (Requires New Version)"
        B1[Rename or delete an existing field]
        B2[Change data type: int -> string]
        B3[Add a new mandatory request parameter]
        B4[Alter HTTP status code: 200 -> 204]
    end
```

---

## 3. Contract-First vs Code-First Development

```mermaid
graph LR
    subgraph "Contract-First (Recommended)"
        C_Spec[1. Write OpenAPI 3.1 YAML] --> C_Review[2. Review Contract with Consumers]
        C_Review --> C_Gen[3. Generate Server Stubs & Client SDKs]
        C_Review --> C_Mock[4. Spin up Mock API Server]
    end

    subgraph "Code-First"
        CF_Code[1. Write Backend Code] --> CF_Export[2. Extract Docs via Annotations]
        CF_Export --> CF_Break[Risk: Accidental Breaking Changes]
    end
```

---

## 4. Consumer-Driven Contract Testing (Pact)

Consumer-Driven Contract (CDC) testing validates that microservices adhere to expected contracts without running slow, flaky end-to-end integration environments.

```mermaid
sequenceDiagram
    participant Consumer as Mobile / Frontend Team
    participant PactBroker as Pact Contract Broker
    participant Provider as Backend Team CI

    Consumer->>Consumer: Run unit tests with Mock Provider
    Consumer->>PactBroker: Publish pact contract (expected requests/responses)
    Note over Provider: Backend CI pipeline runs
    Provider->>PactBroker: Fetches latest consumer contracts
    Provider->>Provider: Replays consumer requests against real backend controllers
    Provider-->>PactBroker: Confirms contract verified (can-i-deploy: SUCCESS)
```

---

## 5. Key Takeaways

- Prefer Contract-First development with OpenAPI 3.1 or Protocol Buffers.
- Use URI path versioning for major overhauls and date-based headers for rolling updates (Stripe model).
- Treat response fields as additive-only. Never rename or delete fields without multi-month deprecation cycles.
- Integrate automated breaking-change detectors (`openapi-diff` or `buf breaking`) directly into CI pull-request checks.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 09 Part 2 complete.")
