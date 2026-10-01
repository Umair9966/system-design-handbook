# Section 02: Networking — Practice Exercises

---

### Problem 1: DNS Resolution Latency Breakdown
Trace the full DNS resolution path for a user in Berlin visiting `api.example.com` for the first time (cold cache).
1. Enumerate each server queried in sequence.
2. Explain how DNS caching (TTL) at the browser and local ISP resolver minimizes international network round trips.
> **Hint**: Stub resolver -> Recursive resolver -> Root -> TLD -> Authoritative nameserver.

---

### Problem 2: TCP Handshake Overhead vs HTTP/2 Multiplexing
A web page loads 40 small image assets (10 KB each).
1. Under HTTP/1.1 without pipelining, assuming a browser domain connection limit of 6 TCP sockets and a 50ms RTT, calculate the connection setup delay.
2. How does HTTP/2 binary framing and multiplexing eliminate this latency overhead over a single TCP connection?
> **Hint**: Factor in TCP 3-way handshake (1 RTT) + TLS 1.3 handshake (1 RTT) per socket.

---

### Problem 3: Protocol Selection: WebSockets vs SSE vs Long Polling
You are architecting three distinct real-time features:
- Feature A: A financial crypto exchange live order book ticker (high frequency, server-to-client updates only).
- Feature B: A collaborative multiplayer whiteboard where users continuously draw lines and exchange coordinates.
- Feature C: A parcel tracking delivery status notification (updates occur once every 4 hours).
Select the optimal protocol for each feature and defend your architectural choice based on connection overhead and duplexity.
> **Hint**: Consider unidirectional vs bidirectional needs and idle connection resource costs.

---

### Problem 4: CDN Origin Shield and Cache Stampede
An international sports streaming portal serves 5 million concurrent viewers. Every 10 seconds, a 2-second video segment playlist (`playlist.m3u8`) expires.
1. Without an Origin Shield, what happens to the origin video servers when the playlist expires simultaneously across 150 edge PoPs?
2. Diagram and explain how an Origin Shield mitigates this thunderous load.
> **Hint**: An Origin Shield acts as a centralized caching tier between edge PoPs and the origin.

---

### Problem 5: Layer 4 vs Layer 7 Reverse Proxy Routing
Your company deploys an API Gateway that must handle 200,000 requests per second.
1. Why does an L7 proxy consume significantly more CPU and memory than an L4 proxy when processing the exact same packet throughput?
2. Describe an architecture that combines both L4 and L7 proxies to achieve high throughput alongside sophisticated routing.
> **Hint**: Consider TLS termination and HTTP header parsing cost.

---

👉 **Solutions**: Check [Section 02 Solutions](02-networking-solutions.md).
