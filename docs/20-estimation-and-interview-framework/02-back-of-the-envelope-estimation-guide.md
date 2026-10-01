# Back-of-the-Envelope Estimation Guide

Back-of-the-envelope estimation allows system designers to quantitatively evaluate architectural choices, storage requirements, network bandwidth, and server counts within 5 minutes.

```mermaid
graph TD
    DAU[Daily Active Users (DAU)] --> RPS[Read & Write Queries Per Second (QPS)]
    RPS --> Bandwidth[Ingress & Egress Bandwidth]
    RPS --> Storage[Daily & 5-Year Storage Capacity]
    RPS --> Memory[Cache Sizing (80/20 Pareto Rule)]
    RPS --> Servers[Server Instance Estimation]
```

---

## 1. The 5 Core Estimation Equations

### 1. Queries Per Second (QPS)
$$	ext{Average QPS} = rac{	ext{Total Daily Requests}}{86,400} pprox rac{	ext{Requests}}{10^5}$$
$$	ext{Peak QPS} = 	ext{Average QPS} 	imes 2 \quad (	ext{or } 	imes 5 	ext{ for spiky traffic})$$

### 2. Storage Estimation
$$	ext{Daily Storage} = 	ext{Daily Writes} 	imes 	ext{Average Payload Size}$$
$$	ext{5-Year Storage} = 	ext{Daily Storage} 	imes 365 	imes 5 pprox 	ext{Daily Storage} 	imes 2,000$$

### 3. Network Bandwidth
$$	ext{Ingress Bandwidth} = 	ext{Write QPS} 	imes 	ext{Average Request Size}$$
$$	ext{Egress Bandwidth} = 	ext{Read QPS} 	imes 	ext{Average Response Size}$$

### 4. Memory / Cache Sizing (The 80/20 Rule)
According to the Pareto Principle, 20% of content generates 80% of read traffic.
$$	ext{Cache Size} = 	ext{Daily Read Data Volume} 	imes 0.20$$

---

## 2. Worked Example: Twitter / X Architecture Estimation

### Assumptions:
- **DAU**: 300 Million Daily Active Users.
- **Write Ratio**: Each user tweets twice per day on average.
- **Read Ratio**: Each user views 50 tweets per day on average.
- **Tweet Payload**: 300 bytes text + metadata. 1 in 5 tweets includes a 200KB image.

### Step 1: QPS Calculation
$$	ext{Total Daily Tweets} = 300	ext{M} 	imes 2 = 600	ext{ Million tweets/day}$$
$$	ext{Average Write QPS} = rac{600,000,000}{86,400} pprox \mathbf{7,000	ext{ writes/sec}}$$
$$	ext{Peak Write QPS} = 7,000 	imes 2 = \mathbf{14,000	ext{ writes/sec}}$$

$$	ext{Total Daily Reads} = 300	ext{M} 	imes 50 = 15	ext{ Billion reads/day}$$
$$	ext{Average Read QPS} = rac{15,000,000,000}{86,400} pprox \mathbf{175,000	ext{ reads/sec}}$$
$$	ext{Peak Read QPS} = 175,000 	imes 2 = \mathbf{350,000	ext{ reads/sec}}$$

### Step 2: Storage Sizing (5 Years)
$$	ext{Daily Text Storage} = 600	ext{M} 	imes 300	ext{B} = 180	ext{ GB/day}$$
$$	ext{Daily Media Storage} = (600	ext{M} 	imes 0.20) 	imes 200	ext{KB} = 120	ext{M} 	imes 200	ext{KB} = 24	ext{ TB/day}$$
$$	ext{Total Daily Storage} pprox 24.2	ext{ TB/day}$$
$$	ext{5-Year Storage} = 24.2	ext{ TB} 	imes 365 	imes 5 pprox \mathbf{44.1	ext{ Petabytes}}$$

### Step 3: Cache Sizing (Memory)
$$	ext{Daily Active Working Set (Text)} = 180	ext{ GB}$$
$$	ext{Redis Cache (20% of Daily Reads)} = 180	ext{ GB} 	imes 0.20 = \mathbf{36	ext{ GB of RAM}}$$

---

## 3. Key Takeaways

- Round numbers to 1 or 2 significant digits during interviews ($86,400 	o 100,000$).
- Always separate Read QPS from Write QPS to identify read-heavy vs write-heavy architectures.
- Size cache RAM on 20% of daily read volume.
