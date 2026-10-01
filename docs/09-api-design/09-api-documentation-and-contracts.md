# API Documentation, Versioning, and Contracts

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
