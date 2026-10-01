import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 03: LOAD BALANCING AND PROXIES
# =========================================================================

save("docs/03-load-balancing-and-proxies/01-l4-vs-l7-load-balancing.md", """# Layer 4 vs Layer 7 Load Balancing

## Overview
A **load balancer** distributes network and application traffic across a pool of backend servers to prevent overload, maximize throughput, and ensure high availability. Load balancing operates fundamentally at two distinct network layers:
- **Layer 4 (Transport / L4)**: Routes traffic based purely on network and transport protocols (IP addresses and TCP/UDP ports) without inspecting the application data payload.
- **Layer 7 (Application / L7)**: Terminates client connections, inspects the application payload (HTTP headers, cookies, URL paths, JSON bodies), and routes intelligently based on content.

```mermaid
graph TD
    Client[Incoming Client Request] --> L4[Layer 4 Load Balancer: IP + Port Hashing]
    L4 --> L7_1[Layer 7 Load Balancer A: Path /api/users]
    L4 --> L7_2[Layer 7 Load Balancer B: Path /api/checkout]
    L7_1 --> App1[Users Microservice Pool]
    L7_2 --> App2[Checkout Microservice Pool]
```

## Why It Matters
Modern cloud architectures must process hundreds of thousands of requests per second. Using an L7 load balancer for raw high-throughput video streams wastefully exhausts CPU on cryptographic handshakes and HTTP parsing. Conversely, using an L4 load balancer makes intelligent microservice routing, header-based canary deployments, and API authentication impossible.

## Core Concepts
- **Connection Splicing vs Termination**:
  - *L4 (Non-terminating / Splicing)*: Direct Server Return (DSR) or IPVS routing. The load balancer routes TCP packets directly to backends without terminating the TCP handshake.
  - *L7 (Dual Termination)*: The balancer terminates the client's TCP and TLS sessions, parses the HTTP request, and establishes a *separate* internal connection to the backend server.
- **Direct Server Return (DSR)**: High-performance L4 optimization where request packets flow through the load balancer, but large response packets bypass the balancer completely, flowing directly from backends to clients.

## Trade-offs
| Feature | Layer 4 (L4) | Layer 7 (L7) |
| :--- | :--- | :--- |
| **Throughput & Capacity** | **Massive (Millions of PPS)** | Moderate (Tens of thousands RPS) |
| **Latency Added** | Sub-millisecond (< 0.1ms) | 1ms - 5ms (parsing & decryption) |
| **Routing Granularity** | IP address & Port only | URL path, headers, cookies, HTTP verbs |
| **TLS Offloading** | Pass-through (backends handle TLS) | **Terminates TLS at the proxy edge** |
| **Resource Consumption**| Very low CPU/RAM (kernel-space) | High CPU/RAM (user-space parsing) |

## When to Use / When NOT to Use
### When to Deploy Layer 4
- Edge tier ingress handling millions of raw packets, database connection proxying, WebSockets/video streaming, gaming servers.

### When to Deploy Layer 7
- Microservice API Gateways, path-based routing (`/auth` vs `/billing`), canary percentage traffic splitting, gRPC load balancing.

## Real-World Examples
- **Google Maglev**: Google's distributed L4 network load balancer deployed on commodity Linux servers, routing billions of requests across Google services using consistent hashing and kernel-bypass packet forwarding.
- **Envoy & NGINX**: Industry-standard L7 reverse proxies providing advanced HTTP/2 and HTTP/3 multiplexing, circuit breaking, and distributed tracing injection.

## Common Pitfalls
- **Using L4 for gRPC**: In gRPC (HTTP/2), multiple RPC calls are multiplexed across a single long-lived TCP connection. An L4 balancer assigns the entire TCP connection to one backend server, causing massive server load imbalance while other backends sit idle.
- **Memory Exhaustion on Slow Clients**: Exposing L7 balancers without request buffering configurations, allowing slow-client attacks (Slowloris) to pin open worker threads.

## Key Takeaways
- L4 is fast, blind packet forwarding; L7 is intelligent, payload-aware request routing.
- High-scale systems place an L4 balancer at the edge to distribute traffic across a horizontal pool of L7 proxies.
- gRPC requires an L7 load balancer to balance individual multiplexed RPC calls.

## Common Interview Questions
1. Why does gRPC fail to balance load properly behind a Layer 4 load balancer?
2. What is Direct Server Return (DSR), and how does it dramatically improve load balancer throughput?
3. How does TLS termination at Layer 7 simplify backend microservice architecture?

## Further Reading
- [Google Research: Maglev: A Fast and Reliable Software Network Load Balancer (2016)](https://research.google/pubs/pub44824/)
- [Envoy Proxy: Layer 4 vs Layer 7 Architecture](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/arch_overview)
""")

save("docs/03-load-balancing-and-proxies/02-load-balancing-algorithms.md", """# Load Balancing Algorithms

## Overview
Load balancing algorithms dictate the mathematical distribution of incoming requests across a cluster of healthy upstream servers. Choosing the right algorithm directly affects server utilization, tail latency, and cache efficiency.

```mermaid
graph TD
    LB{Load Balancing Engine}
    LB -->|Predictable Uniform Tasks| RR[Round Robin / Weighted RR]
    LB -->|Variable Execution Durations| LC[Least Connections / P2C]
    LB -->|Session & Cache Locality| CH[Consistent Hashing with Vnodes]
    RR --> Pool1[Standard Web Pool]
    LC --> Pool2[Long-Running DB / AI Jobs]
    CH --> Pool3[Distributed Cache / Storage Nodes]
```

## Why It Matters
Deploying an algorithm unsuited to your workload profile leads to severe cluster degradation. For example, using Round Robin when request processing times vary between 10ms and 10 seconds causes small worker instances to quickly saturate their thread pools and crash, while neighboring nodes remain idle.

## Core Concepts & Algorithms
1. **Round Robin**: Sequentially routes each incoming request to the next server in the list. Assumes identical server capacity and uniform request execution times.
2. **Weighted Round Robin**: Assigns integer weights proportional to physical server hardware capacity (e.g., Server A has weight 3, Server B has weight 1).
3. **Least Connections**: Dispatches traffic to the server currently processing the fewest active concurrent connections. Highly effective for long-lived database connections or streaming.
4. **Weighted Least Connections**: Normalizes active connections against server weight capacity:
   $$\\text{Load Factor} = \\frac{\\text{Active Connections}}{\\text{Weight}}$$
   Routes to the server with the lowest load factor.
5. **Power of Two Random Choices (P2C)**: Picks two servers at random and chooses the one with fewer active connections. Mathematically proven to eliminate the herd effect in large distributed clusters while operating in $O(1)$ time.
6. **Consistent Hashing**: Hashes request keys (e.g., `user_id`) to a circular hash ring, guaranteeing that identical keys land on the same physical backend server with minimal remapping when nodes fail.

## Trade-offs
| Algorithm | CPU Overhead | Load Uniformity | Cache Locality |
| :--- | :--- | :--- | :--- |
| **Round Robin** | Zero ($O(1)$) | High for uniform requests, Poor for variable tasks | None |
| **Least Connections**| Low ($O(1)$ with heap) | **Exceptional for variable duration workloads**| None |
| **Consistent Hashing**| Low ($O(\\log N)$ binary search)| Good (with virtual nodes) | **Maximum (keeps caches hot)** |
| **Power of Two (P2C)** | Minimal ($O(1)$) | Excellent (avoids stampedes) | None |

## When to Use / When NOT to Use
### When to Use Least Connections / P2C
- Heavy computation endpoints, video transcoding tasks, SQL query pools, long-lived WebSocket sessions.

### When to Use Consistent Hashing
- In-memory cache tiers (Redis/Memcached), stateful game servers, rate limiters, session stores where cache hits are critical.

### When to Avoid Simple Round Robin
- Heterogeneous server fleets (mixing small and large VMs) or workloads with high execution variance.

## Real-World Examples
- **NGINX & Envoy P2C**: Envoy uses the **Power of Two Choices (P2C)** algorithm as its default load balancer for high-throughput microservices to avoid centralized connection tracking bottlenecks.
- **Memcached Client Libraries**: Implement consistent hashing rings across client SDKs to ensure cache keys consistently route to the correct cache node without a central broker.

## Common Pitfalls
- **The Herd Effect with Global Least Connections**: In large clusters with distributed load balancers, multiple balancers simultaneously detect Server X as having the fewest connections, overwhelming Server X with a sudden flood of traffic.
- **Consistent Hashing without Virtual Nodes**: Failing to configure virtual nodes leads to severe key clustering, overloading individual servers by 200-300%.

## Key Takeaways
- Use **Weighted Least Connections** or **P2C** for web APIs with variable processing times.
- Use **Consistent Hashing** whenever maintaining backend cache locality is required.
- Round Robin should only be used for homogeneous servers processing identical, instantaneous tasks.

## Common Interview Questions
1. How does the Power of Two Random Choices algorithm outperform Round Robin and global Least Connections?
2. What happens to key distribution in consistent hashing when a physical server crashes?
3. How does Weighted Least Connections calculate the target server?

## Further Reading
- [Michael Mitzenmacher: The Power of Two Choices in Randomized Load Balancing (1996)](https://www.eecs.harvard.edu/~michaelm/postscripts/tpds2001.pdf)
- [Envoy Documentation: Load Balancing Algorithms](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers)
""")

save("docs/03-load-balancing-and-proxies/03-health-checks-and-sticky-sessions.md", """# Health Checks, Flapping Prevention, and Sticky Sessions

## Overview
A load balancer must dynamically track backend server availability to ensure traffic is never routed to failing or overloaded instances:
- **Active Health Checks**: The balancer periodically probes upstream servers (e.g., HTTP `GET /healthz` every 5 seconds) to verify responsiveness.
- **Passive Health Checks**: The balancer monitors real in-flight customer traffic, temporarily ejecting instances that return excessive 5xx errors or connection timeouts.
- **Sticky Sessions (Session Affinity)**: Routing subsequent requests from a specific client to the exact same backend server based on cookies or IP hashes.

```mermaid
graph TD
    LB[Load Balancer Health Engine]
    LB -->|Active Probe: GET /healthz| Node1[Backend 1: Healthy 200 OK]
    LB -->|Active Probe: GET /healthz| Node2[Backend 2: Dead / Timeout]
    LB -->|Passive Anomaly Detection| Node3[Backend 3: 50% 500 Errors]
    style Node2 fill:#ff9999,stroke:#333
    style Node3 fill:#ffcc99,stroke:#333
    LB -.->|Evict from Pool| Node2
    LB -.->|Circuit Break / Eject| Node3
```

## Why It Matters
Naive health checks frequently trigger catastrophic outages: a database timeout can cause all 100 backend servers to fail their deep health check simultaneously, causing the load balancer to declare the entire cluster dead and dropping 100% of customer traffic. Meanwhile, sticky sessions create severe load imbalances that undermine horizontal scaling.

## Core Concepts
- **Shallow vs Deep Health Checks**:
  - *Shallow Health Check*: Verifies local process liveness (e.g., web server running and responding 200 OK). Fast and safe.
  - *Deep Health Check*: Tests downstream dependencies (e.g., executing a query against the primary database and Redis). Vulnerable to cascading failure storms.
- **Flapping Prevention & Hysteresis**: Prevents an unstable server from constantly bouncing in and out of the upstream pool. Requires consecutive successes to mark healthy and consecutive failures to mark unhealthy:
  - *Threshold Unhealthy*: 3 consecutive failures.
  - *Threshold Healthy*: 5 consecutive successes.
- **Outlier Detection (Passive)**: Automatically ejects an instance for 30 seconds if its 5xx error rate exceeds 15% over a 10-second rolling window.

## Trade-offs
| Mechanism | Availability Benefit | Operational Risk |
| :--- | :--- | :--- |
| **Deep Health Check** | Guarantees backend can complete real queries | Risk of cascading cluster-wide self-inflicted blackout |
| **Shallow Health Check**| Reliable cluster stability | Traffic may route to an instance with broken DB access |
| **Sticky Sessions** | Keeps legacy stateful code functioning | Load hotspots, broken autoscaling, session loss on restarts |

## When to Use / When NOT to Use
### When to Use Shallow Checks + Passive Outlier Detection
- Production microservices. Use shallow checks (`/live`) for container orchestrators and passive circuit breaking for upstream dependency failures.

### When to AVOID Sticky Sessions
- All modern stateless web architectures. Offload session state to Redis or use signed JWT tokens instead.

## Real-World Examples
- **Cascading Health Check Blackout**: A major cloud incident occurred when a database slowed down under heavy traffic. Every web server's `/health` endpoint checked the database synchronously, failed the 2-second timeout, and was evicted by the load balancer, taking down the entire service worldwide.

## Common Pitfalls
- **Health Check Storms**: 50 load balancer worker processes independently pinging 200 backend nodes every second, generating $50 \\times 200 = 10,000$ internal health requests per second that saturate backend CPU!
- **Sticky Session Traffic Clustering**: Corporate enterprise offices with 5,000 employees routing through a single NAT gateway IP get pinned to a single server under IP-hash stickiness, crashing that instance while others remain idle.

## Key Takeaways
- Decouple **Liveness** (is the process alive?) from **Readiness** (is it ready to receive traffic?).
- Never include slow or non-critical third-party external APIs inside health check endpoints.
- Avoid sticky sessions—they create traffic skew and destroy cloud autoscaling benefits.

## Common Interview Questions
1. What is the danger of putting downstream database queries inside a load balancer health check?
2. How does hysteresis prevent server flapping in load balancers?
3. How do you transition an application away from sticky sessions to support zero-downtime rolling deployments?

## Further Reading
- [Kubernetes Documentation: Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Envoy Documentation: Outlier Detection (Passive Health Checking)](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier)
""")

save("docs/03-load-balancing-and-proxies/04-global-load-balancing-anycast-georouting.md", """# Global Server Load Balancing (GSLB), Anycast, and Geo-Routing

## Overview
High-scale applications operate multiple geographically dispersed datacenters across continents. Directing global users to the optimal regional facility requires **Global Server Load Balancing (GSLB)**, executed primarily through two distinct routing mechanisms:
- **GeoDNS (DNS-Based GSLB)**: Authoritative DNS servers dynamically return different regional IP addresses based on the requester's geographic location.
- **BGP Anycast**: Multiple physical datacenters announce the **identical IP address** via Border Gateway Protocol (BGP). The global internet routing mesh automatically steers packets to the topologically closest datacenter.

```mermaid
graph TD
    ClientAsia[Client in Singapore] -->|BGP Shortest AS Path| PopAsia[Anycast PoP: Singapore: IP 1.1.1.1]
    ClientUS[Client in New York] -->|BGP Shortest AS Path| PopUS[Anycast PoP: New York: IP 1.1.1.1]
    ClientEU[Client in Paris] -->|BGP Shortest AS Path| PopEU[Anycast PoP: Frankfurt: IP 1.1.1.1]
```

## Why It Matters
Global routing cuts hundreds of milliseconds of transatlantic and transpacific latency off initial user connections. Crucially, BGP Anycast provides instant, automated DDoS mitigation and disaster failover at the internet routing layer without waiting for DNS TTL expirations.

## Core Concepts
- **BGP Anycast Mechanics**:
  - Autonomous Systems (AS) advertise the exact same IP prefix (e.g., `/24`) from hundreds of edge locations worldwide.
  - Internet routers evaluate the shortest AS-Path and route client packets to the nearest Point of Presence (PoP).
  - If a PoP fails, BGP withdraws the route, and internet routers automatically redirect subsequent packets to the next closest healthy PoP in seconds.
- **GeoDNS Mechanics**:
  - Uses the client's IP (or EDNS Client Subnet) to look up country/continent in a GeoIP database (MaxMind).
  - Responds with the specific regional VIP (e.g., returning `198.51.100.1` for US users and `203.0.113.1` for European users).
- **Failover Capabilities**:
  - Anycast failover occurs at the **network layer** in seconds.
  - GeoDNS failover depends on **DNS caching TTLs**, often taking minutes or hours to propagate fully.

## Trade-offs
| Dimension | BGP Anycast | GeoDNS |
| :--- | :--- | :--- |
| **Failover Speed** | **Near instantaneous (seconds via BGP withdraw)**| Slow (bounded by DNS TTLs: 1-15 mins) |
| **TCP State Stability** | Risk of route flapping breaking long TCP sessions | High (IP address remains constant) |
| **Implementation Complexity**| Extreme (requires owning BGP AS and IP space) | Low (configured via cloud DNS providers) |
| **DDoS Absorption** | **Superior (distributes attack across global PoPs)**| Weak (attack targets resolved regional IP) |

## When to Use / When NOT to Use
### When to Use BGP Anycast
- Edge CDN termination (Cloudflare, Fastly), public DNS resolvers (1.1.1.1, 8.8.8.8), DDoS mitigation scrubbing layers.

### When to Use GeoDNS
- Compliance boundaries (e.g., forcing European patient data to remain in EU datacenters), long-running persistent TCP connections sensitive to route shifts.

## Real-World Examples
- **Cloudflare & AWS Route 53 Anycast**: Operate global Anycast networks. When an attacker launches a 1 Tbps volumetric DDoS attack, the traffic is naturally diluted and absorbed across hundreds of worldwide edge PoPs simultaneously, preventing origin saturation.
- **Netflix Open Connect**: Directs video streaming traffic via GeoDNS and local ISP appliances to ensure 4K video streams pull from the closest physical storage cache inside the user's local internet provider.

## Common Pitfalls
- **BGP Route Flapping and TCP Resets**: In unstable network conditions, BGP routes can oscillate between two datacenters mid-connection. Because TCP connection state is not shared between datacenters, the client receives a `TCP RST` and the connection drops.
- **GeoIP Misattribution**: Assuming GeoIP databases are 100% accurate; IP blocks frequently get reassigned across countries, misrouting users to distant continents.

## Key Takeaways
- BGP Anycast shares a single IP globally; internet routing directs packets to the closest PoP.
- Anycast absorbs DDoS attacks naturally and fails over in seconds.
- Use GeoDNS when legal data residency rules dictate strict geographic boundaries.

## Common Interview Questions
1. How does BGP Anycast route a user to the nearest datacenter?
2. What causes TCP connection resets in an Anycast architecture during network instability?
3. How does Anycast mitigate massive volumetric DDoS attacks?

## Further Reading
- [Cloudflare: What is Anycast?](https://www.cloudflare.com/learning/cdn/glossary/anycast-network/)
- [RFC 4786: Operation of Anycast Services](https://datatracker.ietf.org/doc/html/rfc4786)
""")

save("docs/03-load-balancing-and-proxies/05-api-gateway-and-service-mesh.md", """# API Gateways and Service Mesh Architecture

## Overview
Modern cloud-native architectures manage traffic across two distinct planes:
- **North-South Traffic**: Traffic entering the cluster from external clients (handled by an **API Gateway**).
- **East-West Traffic**: Internal service-to-service communication between microservices within the cluster (handled by a **Service Mesh**).

```mermaid
graph TD
    Client([External Client]) -->|North-South Traffic| AGW[API Gateway / Ingress]
    subgraph Service Mesh Internal Cluster [East-West Traffic]
        AGW --> S1[Order Service]
        S1 -.->|Envoy Sidecar| P1[Proxy 1]
        P1 ==>|mTLS & OTel Tracing| P2[Proxy 2]
        P2 -.-> S2[Payment Service]
        P1 ==>|mTLS & OTel Tracing| P3[Proxy 3]
        P3 -.-> S3[Inventory Service]
    end
```

## Why It Matters
Allowing every individual microservice to implement its own public authentication, rate limiting, and SSL termination creates massive duplication and security vulnerabilities. Conversely, attempting to route internal service-to-service calls back out through an API Gateway adds unnecessary latency hops and central bottlenecks.

## Core Concepts
- **API Gateway Responsibilities (North-South)**:
  - *Edge Authentication & Authorization*: Validating JWTs, API keys, and OAuth tokens before requests reach microservices.
  - *Rate Limiting & Quota Management*: Protecting downstream backends from abuse.
  - *Request Routing & Transformation*: Path routing, protocol translation (HTTP to gRPC), and header enrichment.
  - *Cross-Origin Resource Sharing (CORS)*: Centralized header configuration.
- **Service Mesh Responsibilities (East-West)**:
  - *Sidecar Pattern*: Deploying a lightweight proxy (Envoy) alongside every application container sharing the same network namespace.
  - *Mutual TLS (mTLS)*: Cryptographically verifying and encrypting all internal service-to-service traffic automatically.
  - *Traffic Shifting*: Canary releases, A/B testing, and fault injection without modifying application code.
  - *Observability*: Standardized distributed tracing and metrics injection across all polyglot microservices.

## Trade-offs
| Architecture Component | Primary Role | Operational Overhead | Latency Added |
| :--- | :--- | :--- | :--- |
| **API Gateway** (Kong, Apigee, AWS API GW) | Public edge entry, auth, billing | Low to Moderate | 2ms - 10ms |
| **Service Mesh** (Istio, Linkerd, Consul) | Internal security, mTLS, traffic management | **High (complex control plane & proxy sidecars)**| 1ms - 3ms per internal hop |

## When to Use / When NOT to Use
### When to Deploy an API Gateway
- Almost universally necessary when exposing backend microservices to public web and mobile clients.

### When to Deploy a Service Mesh
- Large organizations managing hundreds of microservices where automated zero-trust security (mTLS) and standardized distributed tracing are mandatory.

### When to AVOID a Service Mesh
- Small to mid-sized teams with fewer than 20 microservices; the operational cognitive load of managing an Istio control plane far outweighs the benefits.

## Real-World Examples
- **Lyft**: Created **Envoy Proxy** to solve internal microservice observability and resilience, establishing the modern blueprint for service mesh architectures.
- **Netflix Zuul**: Serves as the primary public API Gateway for Netflix streaming traffic, managing billions of requests daily with dynamic routing filters and edge security.

## Common Pitfalls
- **Adopting a Service Mesh for Small Teams**: Introducing Istio into a 5-microservice architecture, resulting in days lost debugging Kubernetes sidecar injection and certificate rotation issues.
- **Fat API Gateways**: Writing heavy business logic inside API Gateway Lua/JavaScript plugins, turning the gateway into an unmaintainable monolithic bottleneck.

## Key Takeaways
- API Gateways manage **North-South** public ingress; Service Meshes manage **East-West** internal communication.
- The Sidecar proxy pattern intercepts network traffic transparently without code changes.
- Never write core business domain logic inside the API Gateway layer.

## Common Interview Questions
1. What is the difference between North-South and East-West traffic in microservice architectures?
2. How does a Service Mesh implement mutual TLS (mTLS) transparently without changing application code?
3. When is a Service Mesh an anti-pattern or unnecessary operational overhead?

## Further Reading
- [Matt Klein: Service Mesh Data Plane vs Control Plane](https://medium.com/@mattklein123/service-mesh-data-plane-vs-control-plane-2774e720fa94)
- [Istio Architecture Overview](https://istio.io/latest/docs/ops/deployment/architecture/)
""")

save("docs/03-load-balancing-and-proxies/06-reverse-proxies-nginx-haproxy-envoy.md", """# Production Reverse Proxies: NGINX, HAProxy, and Envoy

## Overview
High-performance reverse proxies form the backbone of modern web infrastructure. Three battle-tested technologies dominate production deployments:
- **NGINX**: Event-driven, asynchronous worker architecture; legendary for static content caching, web serving, and HTTP reverse proxying.
- **HAProxy**: High-performance, event-driven, single-threaded/multithreaded pure TCP and HTTP proxy; renowned for stability, queueing, and metrics.
- **Envoy Proxy**: Modern, cloud-native C++ proxy designed for dynamic microservices, advanced Layer 7 routing, and service mesh architectures.

```mermaid
graph TD
    subgraph NGINX [Master-Worker Architecture]
        M1[Master Process] --> W1[Worker Process 1: Event Loop]
        M1 --> W2[Worker Process 2: Event Loop]
    end
    subgraph Envoy [Thread-Per-Core Asynchronous]
        E1[Main Thread: Dynamic xDS API] --> WT1[Worker Thread: Libevent Loop]
        E1 --> WT2[Worker Thread: Libevent Loop]
    end
```

## Why It Matters
Understanding the internal event loops, concurrency models, and configuration paradigms of these proxies allows architects to deploy the right tool for the job—whether maximizing raw TCP socket throughput, serving gigabytes of cached media, or dynamically managing microservice discovery.

## Core Concepts & Architectural Comparison
1. **NGINX Architecture**:
   - Single master process spawns unprivileged worker processes (typically 1 worker per CPU core).
   - Uses non-blocking I/O multiplexing (`epoll` on Linux, `kqueue` on BSD).
   - Static configuration files (`nginx.conf`) requiring a process reload (`nginx -s reload`) to apply changes.
2. **HAProxy Architecture**:
   - Highly optimized event loop designed for deterministic sub-millisecond packet forwarding.
   - World-class TCP connection queueing and health-check state engines.
   - Comprehensive runtime statistical socket API for live metric inspection.
3. **Envoy Proxy Architecture**:
   - Fully dynamic, API-driven configuration via **xDS management APIs** (LDS, RDS, CDS, EDS), updating routing and clusters with **zero process restarts**.
   - First-class support for HTTP/3, gRPC, and bidirectional streaming.
   - Built-in distributed tracing, access logging, and rate limiting integration.

## Trade-offs
| Dimension | NGINX | HAProxy | Envoy Proxy |
| :--- | :--- | :--- | :--- |
| **Core Strength** | Static file serving & web caching | Pure TCP/HTTP throughput & stability | Dynamic cloud-native microservice routing |
| **Dynamic Reconfiguration** | Requires config reload / NGINX Plus | Runtime CLI socket / Dataplane API | **Native Dynamic xDS gRPC APIs** |
| **gRPC & HTTP/3** | Supported | Supported | **Industry Standard First-Class Support** |
| **Memory Footprint** | Extremely low (few MBs) | Minimal (very light) | Moderate (higher due to C++ abstractions) |
| **Scripting / Extensibility**| Lua, JavaScript (njs) | Lua | C++, WebAssembly (WASM), Lua |

## When to Use / When NOT to Use
### When to Choose Envoy
- Cloud-native Kubernetes environments, microservices requiring dynamic service discovery without restarts, Istio service mesh deployments.

### When to Choose NGINX
- Public-facing edge web servers, SSL termination combined with static file caching, WordPress/PHP frontends.

### When to Choose HAProxy
- Extreme high-throughput TCP load balancing, dedicated database proxying (PostgreSQL/MySQL), scenarios requiring deterministic queueing.

## Real-World Examples
- **GitHub**: Uses **HAProxy** as its front-tier load balancing layer, handling tens of billions of requests daily with sub-millisecond queueing precision.
- **Netflix & Airbnb**: Standardized entirely on **Envoy** for internal and external edge routing due to Envoy's dynamic discovery APIs and deep observability.

## Common Pitfalls
- **Frequent NGINX Reloads in Kubernetes**: Reloading NGINX every time a pod scales up or down in an elastic cluster leaks worker processes and drops idle keep-alive connections (Envoy's xDS eliminates this).
- **Misconfigured Buffer Sizes**: Setting proxy buffer sizes too low forces large HTTP responses to spill to local disk, destroying reverse proxy throughput.

## Key Takeaways
- NGINX excels at static caching and edge web serving.
- HAProxy delivers the most robust and predictable pure load balancing and queueing performance.
- Envoy is the undisputed standard for modern dynamic microservices and cloud-native Kubernetes environments.

## Common Interview Questions
1. How does Envoy's dynamic xDS API differ from traditional configuration reloads in NGINX?
2. How do event-driven proxies handle tens of thousands of concurrent connections on a single CPU core?
3. What are the trade-offs of using Envoy as a Kubernetes Ingress Controller compared to NGINX?

## Further Reading
- [Envoy Proxy Architecture Overview](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/arch_overview)
- [HAProxy Architecture Guide](https://www.haproxy.com/documentation/hapee/latest/get-started/architecture/)
""")

print("Section 03 complete.")
