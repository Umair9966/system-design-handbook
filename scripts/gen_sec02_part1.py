import os

BASE_DIR = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook"

def save(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Written: {rel_path}")

# =========================================================================
# SECTION 02: NETWORKING
# =========================================================================

save("docs/02-networking/01-osi-and-tcp-ip-models.md", """# OSI and TCP/IP Models: A Practical Systems Perspective

## Overview
Networking models provide abstract layered frameworks for conceptualizing how data moves across physical mediums into running application processes:
- **The OSI 7-Layer Model**: A theoretical reference model (Physical, Data Link, Network, Transport, Session, Presentation, Application).
- **The TCP/IP 4-Layer Model**: The pragmatic, implemented architecture of the internet (Link, Internet, Transport, Application).

```mermaid
graph LR
    subgraph OSI 7 Layers
        L7[7. Application]
        L6[6. Presentation]
        L5[5. Session]
        L4[4. Transport]
        L3[3. Network]
        L2[2. Data Link]
        L1[1. Physical]
    end
    subgraph TCP/IP Model
        T4[Application: HTTP, gRPC, DNS]
        T3[Transport: TCP, UDP, QUIC]
        T2[Internet: IPv4, IPv6, BGP]
        T1[Network Access: Ethernet, Wi-Fi]
    end
    L7 & L6 & L5 -.-> T4
    L4 -.-> T3
    L3 -.-> T2
    L2 & L1 -.-> T1
```

## Why It Matters
In production system design, backend engineers rarely debug L1 or L2 (fiber optic photons or Ethernet frames). However, deep mastery of **L3 (IP routing / Anycast)**, **L4 (TCP connections, UDP streams, port multiplexing)**, and **L7 (HTTP headers, cookies, TLS termination)** is essential for architecting load balancers, firewalls, and low-latency microservices.

## Core Concepts
- **Encapsulation & Decapsulation**: As data descends the stack, each layer prepends its own header (e.g., Application Data -> TCP Segment -> IP Packet -> Ethernet Frame). Upon arrival, each layer strips its header.
- **Maximum Transmission Unit (MTU)**: The largest packet size that can be transmitted over a network link without fragmentation (standard Ethernet MTU is **1,500 bytes**).
- **Port Multiplexing**: 16-bit identifiers (0-65535) allowing a single IP address to host multiple distinct network services simultaneously (e.g., Port 443 for HTTPS, Port 5432 for PostgreSQL).

## How It Works: Packet Traversal Lifecyle
1. **L7 Application**: User browser creates an HTTP/2 GET request.
2. **L4 Transport**: OS TCP stack wraps the payload in a TCP segment, attaching source/destination ports and sequence numbers.
3. **L3 Internet**: IP stack wraps the segment in an IP packet, attaching source and destination IP addresses.
4. **L2 Link**: Network card resolves the next-hop router via ARP (Address Resolution Protocol) and transmits an Ethernet frame.
5. **Traversing the Web**: Routers inspect only L3 headers to hop across autonomous systems (AS) via BGP.
6. **Arrival**: The destination server decapsulates the headers and delivers the raw byte payload to the socket buffer of the target process.

## Trade-offs
| Layer Focus | Processing Overhead | Routing Intelligence |
| :--- | :--- | :--- |
| **Layer 4 (Transport / TCP)** | Sub-millisecond (kernel-space zero-copy splicing) | Blind to application payload (cannot route by URL path or cookies) |
| **Layer 7 (Application / HTTP)**| Moderate (requires TLS decryption and HTTP parsing) | High (intelligent path-based routing, header auth, rate limiting) |

## When to Use / When NOT to Use
### When to Operate at Layer 4
- Ultra-high throughput raw streaming (gaming, live audio UDP), internal database proxies, and edge DDoS packet scrubbing.

### When to Operate at Layer 7
- Microservice API Gateways, web application routing, authentication middleware, and content-based request caching.

## Real-World Examples
- **AWS Elastic Load Balancing**: Explicitly offers two distinct products reflecting this divide: **AWS Network Load Balancer (NLB - Layer 4)** capable of handling millions of requests per second with ultra-low latency, and **AWS Application Load Balancer (ALB - Layer 7)** for HTTP/HTTPS path-based routing.

## Common Pitfalls
- **Packet Fragmentation Overhead**: Exceeding MTU limits causes routers to split packets into fragments, dramatically increasing packet loss rates and router CPU loads.
- **Ignoring Ephemeral Port Exhaustion**: A server initiating thousands of outbound HTTP connections per second can exhaust the 16-bit ephemeral port range (~65,000 ports) if sockets linger in `TIME_WAIT`.

## Key Takeaways
- System design focuses primarily on Layer 3 (IP), Layer 4 (TCP/UDP), and Layer 7 (HTTP/gRPC).
- L4 routing is fast and blind; L7 routing is intelligent and computationally expensive.
- Encapsulation adds fixed header overhead to every transmitted payload.

## Common Interview Questions
1. How does a Layer 4 load balancer route traffic compared to a Layer 7 load balancer?
2. What is MTU, and what happens when an IP packet exceeds the path MTU?
3. What is the difference between a TCP socket, a port, and an IP address?

## Further Reading
- [W. Richard Stevens: TCP/IP Illustrated, Volume 1 (The Protocols)](https://www.pearson.com/en-us/subject-catalog/p/tcpip-illustrated-volume-1-the-protocols/P200000003504)
- [RFC 1122: Requirements for Internet Hosts -- Communication Layers](https://datatracker.ietf.org/doc/html/rfc1122)
""")

save("docs/02-networking/02-ip-and-dns.md", """# IP Addressing and Domain Name System (DNS)

## Overview
The **Internet Protocol (IP)** provides the universal addressing and routing mechanism across the global internet. The **Domain Name System (DNS)** serves as the decentralized hierarchical phonebook of the internet, mapping human-readable hostnames (e.g., `api.example.com`) to machine-routable IP addresses (e.g., `93.184.216.34` or IPv6 `2606:2800:220:1:248:1893:25c8:1946`).

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant Resolver as Recursive Resolver (ISP/1.1.1.1)
    participant Root as Root Nameserver (.)
    participant TLD as TLD Nameserver (.com)
    participant Auth as Authoritative Nameserver (example.com)

    Client->>Resolver: Resolve api.example.com
    Resolver->>Root: Where is .com?
    Root-->>Resolver: Referral to .com TLD
    Resolver->>TLD: Where is example.com?
    TLD-->>Resolver: Referral to Authoritative Nameserver
    Resolver->>Auth: Query api.example.com (A Record)
    Auth-->>Resolver: Return 93.184.216.34 (TTL: 300s)
    Resolver-->>Client: 93.184.216.34
```

## Why It Matters
DNS is the very first network hop for every web and API transaction. A misconfigured DNS record can take an entire company offline globally within seconds. Furthermore, modern architectures leverage DNS as a powerful global traffic management engine for latency routing, geo-fencing, and disaster recovery.

## Core Concepts
- **Common DNS Record Types**:
  - **A**: Maps hostname to an IPv4 address (32-bit).
  - **AAAA**: Maps hostname to an IPv6 address (128-bit).
  - **CNAME**: Canonical Name alias pointing one hostname to another hostname (cannot be set on the root apex domain `@`).
  - **ALIAS / ANAME**: Virtual synthetic record allowing CNAME-like flattening at the zone apex.
  - **MX**: Mail Exchange record designating destination mail servers.
  - **TXT**: Arbitrary text strings used for domain ownership validation and email security (SPF, DKIM, DMARC).
- **Time to Live (TTL)**: Number of seconds recursive resolvers and client OSs are permitted to cache a DNS response before querying authoritative servers again.
- **GeoDNS & Latency-Based Routing**: Authoritative nameservers inspect the requester's IP (via EDNS Client Subnet) and dynamically respond with the IP address of the topologically closest datacenter.

## How It Works: The 4-Tier Hierarchical Query Flow
1. **Stub Resolver**: Client OS checks local browser cache and OS hosts file.
2. **Recursive Resolver**: Queries are sent to configured public or ISP resolvers (e.g., Cloudflare `1.1.1.1`, Google `8.8.8.8`).
3. **Root Nameservers**: 13 logical root server clusters (`a.root-servers.net` to `m.root-servers.net`) distributed worldwide via Anycast respond with referrals to TLD servers.
4. **TLD Nameservers**: Handle top-level domains (`.com`, `.org`, `.net`) and provide referrals to authoritative servers.
5. **Authoritative Nameservers**: The final authority hosting the actual zone file (e.g., AWS Route 53, Cloudflare).

## Trade-offs
| DNS TTL Strategy | Failover Speed | Cache Efficiency & DNS Query Load |
| :--- | :--- | :--- |
| **Short TTL (30 - 60 seconds)** | Rapid failover (traffic updates in < 1 min) | High DNS query volume, higher latency on cold misses |
| **Long TTL (86,400 seconds / 24 hours)** | Terrible failover (traffic stuck on dead IP for a day) | Maximum cache hit ratio, sub-millisecond DNS lookups |

## When to Use / When NOT to Use
### When to Use DNS for Load Balancing
- Global Server Load Balancing (GSLB) across major continental datacenters (e.g., US-East vs EU-West).

### When NOT to Rely Solely on DNS for Load Balancing
- Rapid failover within a datacenter or distributing load across application containers (local L4/L7 load balancers are required due to client DNS caching disregarding TTLs).

## Real-World Examples
- **Dyn DNS DDoS Attack (2016)**: The Mirai botnet targeted Dyn's authoritative DNS infrastructure with tens of millions of IP lookups per second, effectively taking down Twitter, Netflix, GitHub, and Spotify across North America despite their servers being 100% healthy.
- **AWS Route 53 Health Checks**: Constantly monitors backend web endpoints. If an endpoint fails health checks, Route 53 automatically withdraws its IP address from DNS responses.

## Common Pitfalls
- **Ignoring ISP TTL Disregard**: Some mobile carriers and ISPs cache DNS records for days, ignoring your 60-second TTL during an emergency migration.
- **Apex CNAME Limitation**: Attempting to put a standard CNAME record on the root domain (`example.com`), violating RFC 1034 (must use ALIAS/ANAME instead).

## Key Takeaways
- DNS is a distributed, hierarchical, globally cached database.
- Lower TTLs prior to scheduled data center migrations to allow rapid cutover.
- Never use DNS as your sole local load balancing mechanism.

## Common Interview Questions
1. Walk through the complete lifecycle of a DNS resolution when typing `google.com` into a browser.
2. How does GeoDNS determine the user's geographic location, and what are its limitations?
3. What is the difference between an A record, a CNAME record, and an ALIAS record?

## Further Reading
- [RFC 1034: Domain Names - Concepts and Facilities](https://datatracker.ietf.org/doc/html/rfc1034)
- [Cloudflare: How DNS Works](https://www.cloudflare.com/learning/dns/what-is-dns/)
""")

save("docs/02-networking/03-tcp-vs-udp-and-congestion-control.md", """# TCP vs UDP: Handshakes, Reliability, and Congestion Control

## Overview
The Transport Layer (Layer 4) provides host-to-host communication services for applications, dominated by two fundamentally distinct protocols:
- **TCP (Transmission Control Protocol)**: A connection-oriented, reliable, byte-stream protocol guaranteeing in-order delivery, error detection, flow control, and network congestion control.
- **UDP (User Datagram Protocol)**: A connectionless, lightweight, unreliable datagram protocol providing minimal transport framing with zero delivery, ordering, or congestion guarantees.

```mermaid
sequenceDiagram
    autonumber
    Note over Client, Server: TCP 3-Way Handshake
    Client->>Server: SYN (seq=x)
    Server-->>Client: SYN-ACK (seq=y, ack=x+1)
    Client->>Server: ACK (ack=y+1)
    Note over Client, Server: Data Transmission with ACKs
    Client->>Server: Data Segment (seq=x+1)
    Server-->>Client: ACK (ack=x+len)
```

## Why It Matters
Choosing between TCP and UDP determines whether your application optimizes for **guaranteed reliability** or **ultra-low latency**. Furthermore, understanding TCP congestion control algorithms (like Cubic and BBR) is essential for saturating high-bandwidth transatlantic fiber links.

## Core Concepts
- **TCP 3-Way Handshake**: Connection establishment: `SYN` -> `SYN-ACK` -> `ACK` (incurs 1 full network Round Trip Time - RTT before any application data is sent).
- **TCP 4-Way Teardown**: Connection closure: `FIN` -> `ACK` -> `FIN` -> `ACK` (accompanied by `TIME_WAIT` state to catch lingering delayed packets).
- **Flow Control (Sliding Window)**: Prevents a fast sender from overwhelming a slow receiver's buffer space (advertised via the TCP Receive Window `rwnd`).
- **Congestion Control**: Prevents the sender from overwhelming the intermediate network infrastructure:
  - **Loss-based (TCP Reno / Cubic)**: Interprets packet loss as a congestion signal; ramps up window exponentially, then backs off multiplicatively upon packet drop.
  - **BBR (Bottleneck Bandwidth and RTT - Google)**: Models maximum physical delivery rate and minimum round-trip time, preventing bufferbloat.

## How It Works: The Protocols in Action
1. **TCP Reliability Mechanics**:
   - Every transmitted byte has a sequence number.
   - The receiver sends cumulative ACKs.
   - If an ACK is not received before the Retransmission Timeout (RTO), or if 3 duplicate ACKs arrive (Fast Retransmit), the sender retransmits the missing segment.
   - *Head-of-Line Blocking*: If segment 2 is lost in transit, segments 3, 4, and 5 cannot be delivered to the application until segment 2 is retransmitted and acknowledged.
2. **UDP Datagram Mechanics**:
   - The sender transmits an 8-byte header (Source Port, Destination Port, Length, Checksum) followed by data.
   - No handshake, no state, no retransmissions. If packets drop, they are gone forever.

## Trade-offs
| Feature | TCP | UDP |
| :--- | :--- | :--- |
| **Connection State** | Stateful (requires handshake and memory buffers) | Stateless (zero connection overhead) |
| **Header Size** | 20 - 60 bytes | Exactly 8 bytes |
| **Delivery Guarantee**| 100% Reliable (retransmits dropped packets) | Unreliable (best-effort delivery) |
| **Packet Ordering** | Strictly Guaranteed | None (can arrive out of order) |
| **Latency** | Higher (handshake + retransmission delays) | Minimal (instant transmission) |

## When to Use / When NOT to Use
### When to Choose TCP
- Web browsing (HTTP/1.1, HTTP/2), REST APIs, database queries, file transfers (SSH, SFTP), transactional email (SMTP).

### When to Choose UDP
- Real-time multiplayer video games, VoIP (voice calls), video conferencing (WebRTC media streams), DNS queries, live sports broadcasting.

## Real-World Examples
- **Google BBR**: Developed by Google in 2016 and deployed across YouTube and Google.com. By moving from loss-based congestion control to BBR, Google increased YouTube network throughput by 4% globally and over 14% in developing markets.
- **HTTP/3 (QUIC)**: Replaced TCP entirely with UDP at the transport layer, implementing its own user-space reliability and stream multiplexing to eliminate TCP Head-of-Line blocking.

## Common Pitfalls
- **Head-of-Line Blocking on Lossy Networks**: Using TCP for real-time multiplayer gaming over Wi-Fi/cellular; a single dropped packet freezes the game stream for 200ms while waiting for a retransmission.
- **SYN Flood DDoS**: Attackers send millions of TCP `SYN` packets from spoofed IPs without returning the final `ACK`, exhausting server connection backlogs (mitigated using **SYN Cookies**).

## Key Takeaways
- TCP guarantees reliability and order at the cost of latency and Head-of-Line blocking.
- UDP provides raw speed and zero connection overhead, delegating reliability logic to the application layer if needed.
- BBR congestion control prevents bufferbloat by measuring real physical pipe width rather than relying on packet drops.

## Common Interview Questions
1. Why does HTTP/3 run over UDP instead of TCP?
2. What is TCP Head-of-Line blocking, and why does HTTP/2 still suffer from it?
3. How do SYN cookies defend against SYN flood attacks?

## Further Reading
- [Neal Cardwell et al.: BBR: Congestion-Based Congestion Control (ACM Queue, 2016)](https://queue.acm.org/detail.cfm?id=3022184)
- [RFC 793: Transmission Control Protocol](https://datatracker.ietf.org/doc/html/rfc793)
""")

save("docs/02-networking/04-http-evolution-https-tls.md", """# HTTP Evolution: HTTP/1.1, HTTP/2, HTTP/3 (QUIC), and TLS

## Overview
The **Hypertext Transfer Protocol (HTTP)** is the foundational application-layer protocol of the World Wide Web. Over three decades, HTTP has undergone fundamental architectural rewrites to eliminate transport bottlenecks:
- **HTTP/1.1**: Text-based, keep-alive persistent TCP connections, prone to Head-of-Line blocking.
- **HTTP/2**: Binary framing, single-connection multiplexing, header compression (HPACK), server push.
- **HTTP/3**: Runs over **QUIC (UDP)**, eliminating TCP-level Head-of-Line blocking and enabling connection migration.
- **HTTPS & TLS 1.3**: Cryptographic security layer providing confidentiality, data integrity, and authentication.

```mermaid
graph TD
    subgraph HTTP Evolution
        H1[HTTP/1.1: Text Protocol, Multiple TCP Connections, HoL Blocking]
        H2[HTTP/2: Binary Framing, Single TCP Multiplexing, HPACK]
        H3[HTTP/3: QUIC over UDP, Zero HoL Blocking, 0-RTT Reconnection]
    end
    H1 -->|2015| H2 -->|2022| H3
```

## Why It Matters
Modern web pages load an average of 70+ distinct assets (JavaScript bundles, CSS, images, API payloads). Understanding protocol differences enables architects to optimize asset delivery, configure edge CDN termination, and minimize mobile battery consumption.

## Core Concepts
- **HTTP/1.1 Head-of-Line (HoL) Blocking**: Over a single TCP connection, requests must be processed serially. If request 1 stalls on a slow database query, requests 2, 3, and 4 wait in line. Browsers hacked around this by opening 6 parallel TCP connections per domain.
- **HTTP/2 Binary Framing & Multiplexing**: Breaks requests into independent binary frames tagged with a stream ID. Multiple concurrent requests travel over a **single TCP connection** simultaneously.
- **HPACK Compression**: Compresses repetitive HTTP headers using static and dynamic Huffman encoding tables.
- **QUIC & HTTP/3**: Replaces TCP with UDP. Stream multiplexing happens at the transport layer: if packet loss occurs on Stream 1, **Stream 2 and Stream 3 continue processing without interruption**.
- **TLS 1.3 Handshake**: Reduced from 2 RTTs in TLS 1.2 down to **1 RTT** (and 0-RTT for resumed sessions) using Ephemeral Diffie-Hellman key exchange.

## How It Works: Protocol Feature Comparison
| Protocol Feature | HTTP/1.1 | HTTP/2 | HTTP/3 (QUIC) |
| :--- | :--- | :--- | :--- |
| **Transport Layer** | TCP | TCP | UDP (QUIC) |
| **Data Format** | Plain Text | Binary Framing | Binary Framing |
| **Multiplexing** | No (Serial) | Yes (Application-layer) | Yes (Transport-layer) |
| **Head-of-Line Blocking**| Severe (HTTP level) | Partial (TCP level) | **Zero** |
| **TLS Handshake** | 2 RTTs (TLS 1.2) | 1 RTT (TLS 1.3) | 1 RTT (Combined Crypto + Transport) |
| **Connection Migration**| Broken on IP change | Broken on IP change | **Seamless** (via Connection ID) |

## Trade-offs
| Protocol Choice | Latency & Performance | Infrastructure & Operational Cost |
| :--- | :--- | :--- |
| **HTTP/1.1** | Slowest (connection setup overhead) | Universal compatibility, trivial to debug with `curl` |
| **HTTP/2** | Fast on clean broadband networks | High CPU memory during massive fan-out multiplexing |
| **HTTP/3** | Blazing fast on mobile/lossy Wi-Fi | Higher UDP CPU utilization; corporate firewalls sometimes block UDP:443 |

## When to Use / When NOT to Use
### When to Deploy HTTP/2 and HTTP/3
- Public-facing websites, mobile application APIs, and edge CDN termination where network loss and latency vary widely.

### When HTTP/1.1 or gRPC (over HTTP/2) Suffices
- Internal backend microservice-to-microservice RPCs running inside the pristine LAN of a cloud datacenter.

## Real-World Examples
- **Mobile Handover (HTTP/3)**: A smartphone user on a video call walks out of their house, transitioning from Wi-Fi to 5G cellular. Under HTTP/2 (TCP), the IP address change severs the socket, dropping the call. Under HTTP/3, the **QUIC Connection ID** persists across the network shift with zero packet drop.
- **Cloudflare**: In 2021 reported that HTTP/3 reduced page load times by up to 20% on lossy networks compared to HTTP/2.

## Common Pitfalls
- **Domain Sharding in HTTP/2**: Splitting assets across `cdn1.example.com`, `cdn2.example.com` was an essential HTTP/1.1 hack. In HTTP/2, this is a harmful anti-pattern that forces multiple TCP connections and breaks single-connection multiplexing.
- **Ignoring UDP Blocking**: Some enterprise corporate firewalls arbitrarily block all outbound UDP traffic on port 443, requiring modern web clients to support automatic fallback to HTTP/2.

## Key Takeaways
- HTTP/1.1 was text-based and serial; HTTP/2 introduced binary multiplexing over single TCP sockets.
- HTTP/3 moves to UDP (QUIC) to eradicate TCP-level Head-of-Line blocking and support mobile connection migration.
- TLS 1.3 cuts cryptographic connection setup time in half (1 RTT).

## Common Interview Questions
1. Why does HTTP/2 still suffer from Head-of-Line blocking if it multiplexes requests?
2. How does QUIC handle connection migration when a mobile phone switches from Wi-Fi to cellular?
3. What security improvements did TLS 1.3 introduce over TLS 1.2?

## Further Reading
- [RFC 9114: HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114)
- [RFC 8446: The Transport Layer Security (TLS) Protocol Version 1.3](https://datatracker.ietf.org/doc/html/rfc8446)
""")

print("Section 02 generated part 1.")
