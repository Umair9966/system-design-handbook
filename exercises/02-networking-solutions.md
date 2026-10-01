# Section 02: Networking — Solutions

### Solution 1: DNS Resolution Path
1. **Resolution Steps**:
   - User OS checks local browser DNS cache and OS hosts cache.
   - OS queries the configured Recursive DNS Resolver (typically ISP or public DNS like 1.1.1.1 or 8.8.8.8).
   - Recursive resolver checks its cache; on a cold miss, queries the **Root Nameserver** (`.`).
   - Root nameserver responds with the referral to the **`.com` TLD Nameserver**.
   - Recursive resolver queries the `.com` TLD nameserver, which referrals to the **Authoritative Nameserver** for `example.com`.
   - Recursive resolver queries the authoritative nameserver for `api.example.com`, which returns the final IP address (A/AAAA record).
   - Recursive resolver caches the record according to its TTL and returns the IP to the client OS.
2. **TTL Economics**: Subsequent requests from any user on that ISP are answered in < 1ms directly from the recursive resolver's RAM, avoiding repeated cross-continental lookups.

---

### Solution 2: TCP Handshake Overhead vs HTTP/2
1. **HTTP/1.1 Delay**:
   - 6 connections each require: 1 RTT (TCP SYN/ACK) + 1 RTT (TLS 1.3) = 2 RTTs = $2 \times 50\text{ ms} = 100\text{ ms}$ per socket.
   - 40 images across 6 parallel connections require $\lceil 40 / 6 \rceil = 7$ serial batches.
   - Total network transfer and handshake delay will easily exceed 450-600ms due to Head-of-Line (HoL) blocking at the HTTP application layer.
2. **HTTP/2 Advantage**:
   - Establishes exactly **1 TCP socket** (handshake overhead incurred only once: 100ms).
   - Binary framing divides requests into independent streams multiplexed concurrently over the single connection. All 40 images are requested in parallel without waiting for prior responses.

---

### Solution 3: Protocol Selection
- **Feature A (Crypto Ticker)**: **Server-Sent Events (SSE)**. Unidirectional server-to-client streaming, native browser reconnection (`EventSource`), built over standard HTTP/2, traverses corporate firewalls easily without WebSocket upgrade overhead.
- **Feature B (Collaborative Whiteboard)**: **WebSockets**. Full-duplex bidirectional streaming with minimal framing overhead (2-10 bytes) is essential for sub-50ms coordinate synchronization.
- **Feature C (Parcel Tracking)**: **Short Polling or Push Notifications / Webhooks**. Persistent connections held open for hours for an event firing once every 4 hours waste server file descriptors and mobile battery.

---

### Solution 4: CDN Origin Shield
1. **The Problem**: 150 edge PoPs missing their cache simultaneously generate 150 simultaneous origin requests for the identical small file, overwhelming origin transcoding servers.
2. **Origin Shield**:
   ```mermaid
   graph TD
       A[150 CDN Edge PoPs] --> B[Central Origin Shield CDN]
       B --> C[Origin Media Server]
   ```
   Edge PoPs route their misses to the Origin Shield. The shield coalesces identical requests (request collapsing) and performs only **1 request** to the origin media server, protecting it from collapse.

---

### Solution 5: L4 vs L7 Reverse Proxy Routing
1. **Resource Difference**:
   - L4 proxies only inspect IP headers and TCP ports without terminating TLS or parsing HTTP payloads. Data is forwarded via fast kernel-space zero-copy splicing.
   - L7 proxies must terminate the TLS session (expensive symmetric crypto), buffer TCP packets, reassemble HTTP headers/cookies, parse URI paths, and run routing regexes.
2. **Hybrid Architecture**:
   Deploy an L4 load balancer (AWS NLB, Maglev, or IPVS) at the edge to distribute raw TCP streams across a pool of horizontally scaled L7 proxies (Envoy/NGINX) that perform SSL termination, auth, and intelligent path-based microservice routing.
