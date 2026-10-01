# BFF, Sidecar, and Ambassador Patterns

Modern distributed architectures decouple peripheral cross-cutting concerns (transport security, logging, client formatting) from core application business logic using helper patterns.

```mermaid
graph TD
    subgraph "Backend-For-Frontend (BFF)"
        WebClient[Web Browser] --> BFF_Web[Web BFF (SSR / Rich Desktop Data)]
        MobileClient[Mobile App] --> BFF_Mobile[Mobile BFF (Aggregated / Compact Data)]
        BFF_Web --> Svc1[Microservice A]
        BFF_Web --> Svc2[Microservice B]
        BFF_Mobile --> Svc1
        BFF_Mobile --> Svc2
    end

    subgraph "Sidecar Pattern (Pod / Container Colocation)"
        subgraph Kubernetes Pod
            App[App Container (Node.js)] <-->|localhost / IPC| Sidecar[Envoy Proxy Sidecar]
        end
        Sidecar -->|mTLS, Tracing, Metrics| Mesh[Service Mesh Network]
    end
```

---

## 1. Backend-For-Frontend (BFF) Pattern

### The Problem:
A single generic API Gateway serving desktop web, iOS, Android, and smart watches forces compromises:
- Mobile needs tiny payloads and aggregated calls to conserve cellular battery and bandwidth.
- Desktop web needs rich relational data and server-side rendering (SSR).

### The BFF Solution:
Each frontend platform owns and maintains its dedicated backend service:
- **Mobile BFF**: Aggregates 5 internal microservices into one compact payload; strips unused fields.
- **Web BFF**: Handles cookie-based auth, Next.js server actions, and desktop-specific features.

---

## 2. Sidecar Pattern

A sidecar attaches an independent helper process to an application without altering application code. In Kubernetes, both containers run inside the same Pod, sharing the same network namespace (`localhost`) and filesystem volumes.

```mermaid
graph LR
    subgraph Kubernetes Pod
        Main[Main Application (Business Logic)]
        SC1[Sidecar: Envoy Proxy (mTLS & Routing)]
        SC2[Sidecar: Fluentbit (Log Forwarding)]
        Main <-->|localhost:15001| SC1
        Main -->|Writes /var/log/app.log| SC2
    end
    SC1 -->|External Traffic| Remote[Downstream Service]
    SC2 -->|Ship Logs| Elastic[(Elasticsearch)]
```

### Common Sidecar Use Cases:
1. **Service Mesh Proxies (Istio / Linkerd)**: Transparently intercepts all outbound/inbound traffic to handle mTLS encryption, circuit breaking, and telemetry.
2. **Log Collectors**: Fluentbit or Filebeat tails local log files and streams them to central aggregators.
3. **Secret Injectors**: HashiCorp Vault Agent sidecar periodically fetches dynamic database credentials and mounts them into a shared memory volume.

---

## 3. Ambassador Pattern

An Ambassador is a specialized out-of-process proxy that offloads network routing, retries, and protocol translation on behalf of an application.

```mermaid
graph LR
    App[Legacy Application] -->|Plain HTTP localhost:8080| Ambassador[Ambassador Proxy]
    Ambassador -->|gRPC + TLS + Retry with Jitter| RemoteSvc[Cloud Microservice]
```

- Application makes simple local HTTP calls.
- Ambassador manages complex transport: circuit breaking, timeouts, connection pooling, and credential refreshing.

---

## 4. Key Takeaways

- Use BFFs to allow frontend teams to iterate independently without bloating shared backend APIs.
- Use Sidecars to keep business logic pure while standardizing logging, metrics, and security.
- Ambassador proxies allow legacy applications to communicate with modern cloud services without modifying legacy source code.
