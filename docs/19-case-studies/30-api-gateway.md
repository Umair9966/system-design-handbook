# Design a High-Performance API Gateway (Kong / Envoy)

A high-throughput L7 API Gateway sitting at the perimeter of a microservices architecture, providing SSL termination, authentication, rate limiting, request transformation, and dynamic routing.

```mermaid
graph TD
    Client[Mobile / Web Clients] --> Edge[Edge Anycast]
    Edge --> GW[Envoy / Kong API Gateway Cluster]
    
    subgraph Gateway Filter Pipeline
        GW --> F1[1. TLS 1.3 Termination & WAF]
        F1 --> F2[2. JWT Authentication & Claims Extraction]
        F2 --> F3[3. Rate Limiter (Redis Token Bucket)]
        F3 --> F4[4. Path Rewriting & Header Injection]
    end

    F4 --> SvcA[Order Microservice]
    F4 --> SvcB[User Microservice]
    F4 --> SvcC[Payment Microservice]
```

---

## 1. Requirements

### Functional Requirements:
1. Dynamic routing based on URI path, headers, and HTTP methods.
2. Centralized Authentication (validate JWTs, verify signatures).
3. Distributed Rate Limiting and quota management.
4. Observability: Generate unified access logs, Prometheus metrics, and distributed trace headers (`traceparent`).

### Non-Functional Requirements:
- **Ultra-High Throughput**: 100,000+ requests per second per node.
- **Minimal Latency Overhead**: Gateway processing overhead $< 2	ext{ms}$.
- **Zero-Downtime Dynamic Configuration**: Reload routes via xDS API without restarting worker processes.

---

## 2. The Envoy Proxy xDS Control Plane

Modern API Gateways (Envoy) decouple the data plane from the control plane using the **xDS protocol**:
- **LDS (Listener Discovery Service)**: Dynamic port and TLS configuration.
- **RDS (Route Discovery Service)**: Dynamic URI routing rules.
- **CDS (Cluster Discovery Service)**: Backend service endpoints and health states.
- **EDS (Endpoint Discovery Service)**: Real-time Kubernetes pod IP updates.

---

## 3. Key Takeaways

- Terminate TLS and authenticate JWTs at the gateway to offload CPU from downstream microservices.
- Inject trusted identity headers (`X-User-Id`, `X-User-Roles`) into internal service requests.
- Use Envoy xDS APIs to dynamically update routes without dropping active TCP connections.
