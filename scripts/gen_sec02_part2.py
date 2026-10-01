import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

save("docs/02-networking/05-realtime-protocols-websockets-sse-long-polling.md", """# Real-Time Protocols: WebSockets, Server-Sent Events, and Long Polling

## Overview
Traditional HTTP follows a strict client-initiated request-response lifecycle. For applications requiring instant server-to-client updates, engineers deploy specialized real-time protocols:
- **Short Polling**: Client repeatedly fires standard HTTP requests on a fixed timer (e.g., every 2 seconds).
- **Long Polling**: Server holds the HTTP request open until new data arrives or a timeout occurs.
- **Server-Sent Events (SSE)**: Unidirectional, persistent HTTP connection where the server pushes text events to the client.
- **WebSockets**: Full-duplex, bidirectional, persistent TCP connection established via an initial HTTP upgrade handshake.

```mermaid
sequenceDiagram
    autonumber
    Note over Client, Server: Short Polling (High Waste)
    Client->>Server: GET /status
    Server-->>Client: No update (200 OK)
    Note over Client, Server: Server-Sent Events (Unidirectional Push)
    Client->>Server: GET /stream (Accept: text/event-stream)
    Server-->>Client: event: msg1
    Server-->>Client: event: msg2
    Note over Client, Server: WebSockets (Full Duplex)
    Client->>Server: Upgrade: websocket
    Server-->>Client: 101 Switching Protocols
    Client<<->>Server: Bidirectional Frames (Client <-> Server)
```

## Why It Matters
Holding millions of concurrent persistent connections open consumes substantial server memory and file descriptors. Choosing the wrong protocol can exhaust server connection pools or drain client mobile batteries.

## Core Concepts
- **Full-Duplex vs Half-Duplex vs Simplex**:
  - *Full-Duplex*: Both client and server can transmit data simultaneously over the same connection (WebSockets).
  - *Unidirectional (Simplex)*: Only the server pushes data once the connection is established (SSE).
- **Framing Overhead**: Standard HTTP requests require 500-1,000 bytes of headers. WebSocket binary frames add only **2 to 10 bytes** of framing overhead per message.
- **Proxy & Firewall Traversal**: SSE runs over standard HTTP/2, passing effortlessly through corporate proxies and firewalls. WebSockets require explicit support for the HTTP `101 Switching Protocols` upgrade header.

## Trade-offs
| Protocol | Directionality | Protocol Base | Framing Overhead | Auto-Reconnect |
| :--- | :--- | :--- | :--- | :--- |
| **Short Polling** | Client -> Server | HTTP/1.1 | Massive (new headers every call) | Manual |
| **Long Polling** | Client -> Server | HTTP/1.1 | High (headers on every cycle) | Manual |
| **Server-Sent Events**| Server -> Client | HTTP/2 | Low | **Native in browser (`EventSource`)** |
| **WebSockets** | **Bidirectional** | TCP (custom) | **Minimal (2-10 bytes)** | Manual application logic |

## When to Use / When NOT to Use
### When to Use WebSockets
- Collaborative multi-user editing (Google Docs/Figma), real-time multiplayer gaming, bidirectional chat applications (WhatsApp/Slack), financial crypto order books with user trades.

### When to Use Server-Sent Events (SSE)
- Stock tickers, live sports scores, ChatGPT/LLM streaming responses, notification feeds, build progress logs.

### When to Avoid WebSockets
- Simple notification systems or unidirectional feeds where SSE provides built-in auto-reconnection, multiplexing over HTTP/2, and zero custom firewall configuration.

## Real-World Examples
- **OpenAI ChatGPT**: Uses **Server-Sent Events (SSE)** to stream generated tokens to the browser. Since the user does not send input during text generation, SSE is vastly simpler and more reliable than a WebSocket.
- **Discord**: Uses **WebSockets** for chat and presence tracking, maintaining a shared gateway connection pool multiplexing thousands of servers.

## Common Pitfalls
- **Load Balancer Idle Timeouts**: Intermediary load balancers (e.g., AWS ALB) terminate idle TCP connections after 60 seconds unless application heartbeat/ping-pong frames are implemented.
- **WebSocket Scaling Bottleneck**: Forgetting that WebSocket servers are inherently stateful; broadcasting a message to a room requires a distributed pub/sub backplane (e.g., Redis Pub/Sub) across gateway nodes.

## Key Takeaways
- Use **SSE** for unidirectional server-to-client streaming (simpler, HTTP/2 native, built-in reconnection).
- Use **WebSockets** only when true low-latency bidirectional communication is mandatory.
- Long polling is legacy; avoid it in greenfield systems.

## Common Interview Questions
1. Why did OpenAI choose Server-Sent Events instead of WebSockets for streaming ChatGPT responses?
2. How do you scale a WebSocket server cluster horizontally to 10 million concurrent connections?
3. What happens to a WebSocket connection when an intermediary load balancer restarts?

## Further Reading
- [RFC 6455: The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [HTML Living Standard: Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
""")

save("docs/02-networking/06-grpc-rest-graphql-overview.md", """# API Paradigms: REST, gRPC, and GraphQL Overview

## Overview
Modern distributed architectures connect clients and microservices through three dominant API paradigms:
- **REST (Representational State Transfer)**: Resource-oriented, text-based (JSON over HTTP/1.1 or HTTP/2), stateless, ubiquitous.
- **gRPC (Google Remote Procedure Call)**: Action-oriented RPC, binary serialization (Protocol Buffers over HTTP/2), strictly typed, high performance.
- **GraphQL**: Query-oriented, single-endpoint declarative data fetching (JSON over HTTP), eliminates over-fetching and under-fetching.

```mermaid
graph TD
    Client[Client App]
    subgraph REST
        Client -->|GET /users/123| R1[REST Endpoint: Fixed JSON]
    end
    subgraph GraphQL
        Client -->|POST /graphql: Query specific fields| G1[GraphQL Engine: Exact Shape]
    end
    subgraph gRPC
        Client -->|Binary Protobuf over HTTP/2| P1[gRPC Service: Microsecond RPC]
    end
```

## Why It Matters
Selecting the wrong API paradigm impacts client developer productivity, payload size over mobile networks, and microservice throughput. High-scale architectures routinely deploy **GraphQL or REST at the public edge** and **gRPC for internal east-west microservice communication**.

## Core Concepts
- **Over-Fetching vs Under-Fetching**:
  - *Over-fetching*: Downloading an entire 50-field user object when the UI only displays a username (typical in REST).
  - *Under-fetching*: Firing 4 consecutive REST calls (`/users`, `/orders`, `/products`, `/reviews`) to render a single screen.
- **Interface Definition Language (IDL)**: gRPC uses `.proto` files to define strongly typed service contracts, auto-generating client SDKs in Go, Java, Python, TypeScript, and C++.
- **Binary vs Text Serialization**: Protobuf serializes data into compact binary tags, executing **5x to 10x faster** with 30-50% smaller payloads than JSON serialization.

## Trade-offs
| Feature | REST | gRPC | GraphQL |
| :--- | :--- | :--- | :--- |
| **Data Format** | JSON (Plain Text) | Protocol Buffers (Binary) | JSON (Plain Text) |
| **Protocol** | HTTP/1.1 or HTTP/2 | HTTP/2 (Multiplexed) | HTTP/1.1 or HTTP/2 |
| **Schema Strictness** | Optional (OpenAPI) | **Mandatory & Strictly Typed** | **Mandatory (Schema SDL)** |
| **Client Control** | Low (Server defines response) | Low (Fixed RPC return) | **Absolute (Client requests fields)**|
| **Browser Compatibility**| 100% Native | Requires gRPC-Web proxy | 100% Native |
| **Caching** | Excellent (Native HTTP GET)| Difficult (HTTP POST / RPC) | Challenging (Single POST endpoint) |

## When to Use / When NOT to Use
### When to Use gRPC
- High-throughput internal microservice-to-microservice communication where CPU serialization latency must be minimized.
- Polyglot backend teams needing type-safe, auto-generated SDKs.

### When to Use GraphQL
- Complex mobile and frontend applications aggregating data across dozens of disparate backend microservices.
- Public developer APIs with unpredictable query requirements (e.g., GitHub API v4).

### When to Use REST
- Public third-party partner APIs, CRUD applications, webhooks, and services relying heavily on edge CDN caching.

## Real-World Examples
- **Netflix**: Uses GraphQL as an API Gateway orchestration layer for mobile and smart TV clients, which internally fans out to thousands of microservices via **gRPC**.
- **Uber**: Replaced legacy JSON-over-HTTP internal RPCs with gRPC and Protocol Buffers, dramatically reducing service tail latencies and eliminating interface contract bugs.

## Common Pitfalls
- **The GraphQL N+1 Query Disaster**: Resolving nested relations (e.g., fetching 100 authors and each author's books) triggers 101 separate database queries unless mitigated via **DataLoader** batching.
- **Debugging gRPC Payloads**: Unlike JSON, raw gRPC network frames are unreadable binary streams, requiring specialized tooling (`grpcurl`, Wireshark protobuf dissectors) for debugging.

## Key Takeaways
- Use **GraphQL** or **REST** at the public client-facing boundary; use **gRPC** for internal high-throughput microservice communication.
- Protocol Buffers eliminate type mismatches and reduce CPU serialization overhead.
- GraphQL solves mobile over-fetching but requires defensive query depth limiting and DataLoader batching.

## Common Interview Questions
1. How does gRPC achieve significantly higher throughput and lower latency than REST over JSON?
2. What is the N+1 problem in GraphQL, and how does the DataLoader pattern resolve it?
3. Why is edge caching significantly more difficult with GraphQL compared to REST?

## Further Reading
- [gRPC Official Documentation](https://grpc.io/docs/)
- [GraphQL: A Data Query Language (Facebook, 2015)](https://spec.graphql.org/)
""")

save("docs/02-networking/07-cdn-edge-caching.md", """# Content Delivery Networks (CDN) and Edge Caching

## Overview
A **Content Delivery Network (CDN)** is a geographically distributed network of proxy servers (Points of Presence - PoPs) deployed close to end users. CDNs cache static assets (images, videos, JavaScript, CSS) and accelerate dynamic API requests to reduce origin server load and minimize physical network propagation latency.

```mermaid
graph TD
    UserEurope[User in Europe] -->|20ms| CDNEurope[CDN Edge PoP: Frankfurt]
    UserAsia[User in Asia] -->|15ms| CDNAsia[CDN Edge PoP: Tokyo]
    CDNEurope -->|Cache Miss: Transatlantic Fiber| Origin[Origin Datacenter: US-East]
    CDNAsia -->|Cache Miss: Transpacific Fiber| Origin
```

## Why It Matters
Without a CDN, a user in Sydney requesting a 2MB webpage from an origin server in Virginia, USA must cross 15,000 km of undersea fiber cables, incurring 200ms+ of physical latency per round trip. With a CDN, the request is terminated in Sydney within **10ms**, reducing origin server bandwidth costs by up to 90%.

## Core Concepts
- **Edge Point of Presence (PoP)**: Datacenter facilities placed near major internet exchange points (IXPs) worldwide.
- **Push vs Pull CDN**:
  - *Pull CDN*: The CDN automatically fetches (pulls) the asset from the origin on the first cache miss and caches it for future requests (ideal for high-traffic web assets).
  - *Push CDN*: Content is explicitly uploaded (pushed) to the CDN before users request it (ideal for large software releases and game patches).
- **Dynamic Site Acceleration (DSA)**: Accelerates non-cacheable API calls by maintaining pre-warmed persistent TCP/TLS connections from the edge PoP to the origin across optimized private backbone networks.
- **Origin Shield**: A centralized caching tier positioned between edge PoPs and the origin server to prevent cache miss storms.

## How It Works: Cache Invalidation Strategies
1. **Time to Live (TTL)**: Headers (`Cache-Control: max-age=3600`) dictate how long an asset lives at the edge before revalidation.
2. **Purge by URL / Tag**: Explicitly invalidating cached keys via API when content changes (e.g., purging `/products/123` on price change).
3. **Asset Fingerprinting / Cache Busting**: Appending unique content hashes to static asset URLs (`app.a8f9c2.js`). When code changes, the URL changes, rendering stale caches irrelevant and allowing infinite TTLs (`max-age=31536000, immutable`).

## Trade-offs
| Dimension | Benefit | Risk / Trade-off |
| :--- | :--- | :--- |
| **Edge Caching** | Sub-15ms global latency, 90%+ origin offload | Serving stale content during rapid inventory/price shifts |
| **Purge-on-Update** | Immediate content freshness | High purge API overhead, potential origin stampede |
| **Edge Compute (Workers)**| Personalization and auth at the edge | Limited execution runtime memory, vendor lock-in |

## When to Use / When NOT to Use
### When to Use a CDN
- Public websites, media streaming, global mobile apps, e-commerce storefronts, software distribution.

### When NOT to Rely on Caching at the Edge
- Highly personalized, sensitive user banking portals, real-time private messaging payloads (though DSA can still accelerate routing).

## Real-World Examples
- **Fastly & Cloudflare**: Provide programmable edge compute (V8 isolates and WebAssembly) allowing authentication validation, A/B testing, and image resizing to execute in under 5ms directly at the edge.
- **Super Bowl Live Streams**: Akamai and AWS CloudFront distribute live video segments to tens of millions of concurrent viewers, absorbing tens of terabits per second of outbound traffic that would instantly incinerate origin media encoders.

## Common Pitfalls
- **Accidental Caching of Private Data**: Misconfiguring `Cache-Control: public` on user profile endpoints, causing CDN edges to serve User A's private personal info to User B.
- **Cache Invalidation Delays**: Relying on manual purges during breaking UI deploys, resulting in HTML files referencing old, deleted JavaScript bundle chunks.

## Key Takeaways
- Use **asset fingerprinting** with immutable 1-year cache headers for static frontend assets.
- Deploy an **Origin Shield** to prevent hundreds of edge PoPs from stampeding the origin on cache misses.
- Never cache authenticated endpoints without explicit `Cache-Control: private, no-store` headers.

## Common Interview Questions
1. How does a CDN accelerate dynamic, uncacheable API requests?
2. What is the difference between a Push CDN and a Pull CDN?
3. How do you guarantee that users immediately receive updated frontend code without waiting for CDN TTLs to expire?

## Further Reading
- [Cloudflare: How CDNs Work](https://www.cloudflare.com/learning/cdn/what-is-a-cdn/)
- [RFC 9111: HTTP Caching](https://datatracker.ietf.org/doc/html/rfc9111)
""")

save("docs/02-networking/08-proxies-forward-and-reverse.md", """# Proxies: Forward Proxies vs Reverse Proxies

## Overview
A **proxy server** acts as an intermediary for requests between clients and destination servers:
- **Forward Proxy**: Sits in front of a group of **clients**, intercepting outbound requests to the internet. Destination web servers only see the IP address of the forward proxy.
- **Reverse Proxy**: Sits in front of a group of **backend servers**, intercepting inbound requests from the internet. Clients only see the IP address of the reverse proxy.

```mermaid
graph LR
    subgraph Forward Proxy [Protects Clients]
        C1[Client 1] --> FP[Forward Proxy]
        C2[Client 2] --> FP
        FP --> Internet1((Public Internet))
    end
    subgraph Reverse Proxy [Protects Servers]
        Internet2((Public Internet)) --> RP[Reverse Proxy / NGINX]
        RP --> S1[App Server 1]
        RP --> S2[App Server 2]
    end
```

## Why It Matters
Understanding proxy orientation is essential for security architecture. Forward proxies govern internal enterprise network egress, compliance, and privacy. Reverse proxies are the foundational building block of backend infrastructure, providing load balancing, SSL termination, and DDoS shielding.

## Core Concepts
- **Forward Proxy Capabilities**:
  - *Client Anonymity*: Masks internal corporate IP addresses.
  - *Content Filtering*: Blocks access to malicious or unauthorized domains.
  - *Egress Caching*: Caches popular external downloads, conserving enterprise corporate WAN bandwidth.
- **Reverse Proxy Capabilities**:
  - *Load Balancing*: Distributes incoming requests across backend pools.
  - *SSL/TLS Termination*: Decrypts HTTPS traffic at the edge, freeing backend application servers from CPU-heavy cryptographic handshakes.
  - *Security & Obfuscation*: Hides backend server IP addresses, operating systems, and network topologies from attackers.
  - *Compression & Caching*: Gzips responses and serves cached static content.

## Trade-offs
| Proxy Type | Position | Primary Beneficiary | Primary Risk / Bottleneck |
| :--- | :--- | :--- | :--- |
| **Forward Proxy** | Client-side egress | The Client (privacy, control) | Single bottleneck for corporate outbound traffic |
| **Reverse Proxy** | Server-side ingress | The Server (scalability, security)| Single point of failure if proxy pool crashes |

## When to Use / When NOT to Use
### When to Deploy a Reverse Proxy
- Mandatory in front of all production web applications (e.g., placing NGINX, HAProxy, or Envoy in front of Node.js, Python, or Go processes).

### When to Deploy a Forward Proxy
- Corporate enterprise security, egress filtering for compliance (preventing data exfiltration), developer VPN environments.

## Real-World Examples
- **NGINX / Envoy Reverse Proxy**: Used in front of web services worldwide. Directing public internet traffic directly into an application server (e.g., Python Gunicorn or Node.js Express) leaves the application vulnerable to slow-client HTTP attacks and CPU starvation.
- **Corporate Squid Forward Proxy**: Deployed in enterprise offices to monitor corporate laptops, enforce DLP (Data Loss Prevention) rules, and inspect outbound traffic for malware.

## Common Pitfalls
- **Exposing Backend Instances Directly**: Allowing public internet traffic to bypass the reverse proxy directly to backend EC2 instances, exposing them to port scans and direct attacks.
- **Misconfiguring `X-Forwarded-For`**: Failing to properly configure the reverse proxy to append client IP addresses, causing backend analytics and security rate limiters to see 100% of traffic coming from `127.0.0.1`.

## Key Takeaways
- Forward proxies protect and control **clients**; Reverse proxies protect and scale **servers**.
- Always terminate TLS and enforce rate limiting at the reverse proxy layer.
- Ensure backend services trust the `X-Forwarded-For` header only from verified internal reverse proxies.

## Common Interview Questions
1. What is the fundamental difference between a forward proxy and a reverse proxy?
2. Why is it considered an architectural anti-pattern to expose application runtimes (like Node.js or Flask) directly to the internet without a reverse proxy?
3. How does SSL termination at a reverse proxy affect internal network security?

## Further Reading
- [NGINX: Understanding NGINX HTTP Proxying and Reverse Proxying](https://www.digitalocean.com/community/tutorials/understanding-nginx-http-proxying-load-balancing-buffering-and-caching)
- [Envoy Proxy Architecture Overview](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/arch_overview)
""")

save("docs/02-networking/09-nat-firewalls-vpn.md", """# Network Address Translation (NAT), Firewalls, and VPNs

## Overview
Network security and connectivity at scale depend on three foundational Layer 3 / Layer 4 primitives:
- **NAT (Network Address Translation)**: Remaps one IP address space into another, allowing hundreds of private instances to share a single public IPv4 address.
- **Firewall**: Network security system monitoring and controlling incoming and outgoing traffic based on predetermined rules (Packet Filtering, Stateful, and Web Application Firewalls - WAF).
- **VPN (Virtual Private Network)**: Creates an encrypted point-to-point tunnel across public networks, extending private network boundaries securely.

```mermaid
graph LR
    subgraph Private VPC Subnet
        DB[(Private Database)]
        App[Private Backend Node]
    end
    App -->|Outbound Egress Only| NAT[NAT Gateway]
    NAT -->|Public IP| Internet((Internet / Package Repo))
    Internet -.->|Blocked Inbound| NAT
    Admin[Remote Engineer] -->|Encrypted WireGuard/IPsec Tunnel| VPN[VPN Gateway]
    VPN --> App
```

## Why It Matters
A production cloud environment (AWS VPC, GCP Virtual Private Cloud) places sensitive databases and microservices in **private subnets** with zero public IP addresses. Understanding NAT gateways, stateful security groups, and VPN tunnels is mandatory for securing infrastructure against unauthorized intrusion.

## Core Concepts
- **SNAT (Source NAT)**: Modifies the source IP of outbound packets from private instances so external internet servers can route replies back to the NAT gateway.
- **DNAT (Destination NAT / Port Forwarding)**: Modifies the destination IP of incoming packets, directing public traffic to a specific private internal host.
- **Firewall Generations**:
  - *Packet Filtering (Stateless)*: Inspects individual packets in isolation (Source/Destination IP and Port). Fast, but unaware of connection state.
  - *Stateful Inspection*: Tracks active TCP connection states (`SYN`, `ESTABLISHED`). Automatically allows inbound replies to legitimately established outbound requests.
  - *Web Application Firewall (WAF)*: Operates at Layer 7, inspecting HTTP payloads for SQL injection, cross-site scripting (XSS), and malicious user-agents.
- **VPN Tunneling Protocols**: Encapsulates private packets inside encrypted public envelopes using **IPsec** or **WireGuard** with ChaCha20-Poly1305 cryptography.

## Trade-offs
| Security Appliance | Layer | Operational Overhead | Performance Impact |
| :--- | :--- | :--- | :--- |
| **Stateful Security Group** | Layer 4 | Low (cloud-native rules) | Negligible (sub-millisecond line rate) |
| **NAT Gateway** | Layer 3/4 | Moderate (cost per gigabyte egress) | Minimal (bandwidth limits apply) |
| **Web Application Firewall** | Layer 7 | High (rule tuning and false positive risk) | 2ms - 10ms processing latency |

## When to Use / When NOT to Use
### When to Deploy Private Subnets with NAT
- Mandatory for all production databases, Redis caches, background workers, and internal microservices.

### When to Expose Services to Public Subnets
- Exclusively for ingress load balancers, CDN edge gateways, and public NAT instances.

## Real-World Examples
- **AWS NAT Gateway Outage / Cost Traps**: Cloud engineers frequently encounter massive surprise cloud bills when high-throughput internal analytics jobs accidentally route petabytes of S3 traffic through a NAT Gateway instead of a free **VPC S3 Gateway Endpoint**.
- **WireGuard**: Modern Linux kernel-space VPN protocol providing 4x higher throughput and 80% lower latency than legacy OpenVPN or IPsec tunnels.

## Common Pitfalls
- **Placing Databases in Public Subnets**: Assigning public IPv4 addresses to database servers and relying solely on a password for security, exposing the database to continuous brute-force dictionary attacks.
- **NAT Gateway Bandwidth Saturation**: Exceeding the maximum network throughput of a single NAT gateway instance, resulting in dropped packets across all private subnet egress calls.

## Key Takeaways
- Keep all data tiers and application servers in **private subnets**; use a NAT Gateway for outbound-only internet access (e.g., OS security updates).
- Stateful firewalls automatically allow response traffic for established outbound TCP connections.
- Use VPC Endpoints to route cloud service traffic directly, bypassing expensive NAT bandwidth charges.

## Common Interview Questions
1. How does Source NAT (SNAT) differ from Destination NAT (DNAT)?
2. What is the difference between a stateful security group and a stateless network ACL (NACL)?
3. Why should production databases never have public IP addresses, even if protected by strong passwords?

## Further Reading
- [AWS VPC Documentation: NAT Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [Jason A. Donenfeld: WireGuard: Next Generation Kernel Network Tunnel](https://www.wireguard.com/papers/wireguard.pdf)
""")

print("Section 02 complete.")
