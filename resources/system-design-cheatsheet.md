# System Design Quick Reference Cheatsheet 📑

Essential formulas, mental anchors, latency benchmarks, and architectural heuristics for fast on-the-job and interview reference.

---

## ⚡ Latency Numbers Every Systems Engineer Must Know

| Operation | Latency | Real-World Human Analogy |
| :--- | :--- | :--- |
| **L1 CPU Cache Reference** | 0.5 - 1 ns | 1 Heartbeat (1 sec) |
| **L2 CPU Cache Reference** | 3 - 5 ns | 5 Seconds |
| **L3 CPU Cache Reference** | 10 - 20 ns | 20 Seconds |
| **Main Memory (RAM) Access** | 50 - 100 ns | 1.5 Minutes |
| **NVMe SSD Random Read** | 10 - 50 µs | 1.5 Days |
| **SATA SSD Random Read** | 100 - 200 µs | 3.5 Days |
| **Standard HDD Seek** | 5 - 10 ms | 4 Months |
| **Intra-Datacenter Round Trip (LAN)** | 0.5 ms | 5 Days |
| **Cross-Continental Round Trip (SF to NY)** | 40 - 70 ms | 1.5 Years |
| **Cross-Atlantic Round Trip (SF to London)** | 100 - 150 ms | 3.5 Years |

---

## 🔢 Powers of Two & Storage Conversions

| Power of 2 | Exact Bytes | Approximate Storage |
| :--- | :--- | :--- |
| $2^{10}$ | 1,024 B | **1 KB** (Kilobyte) |
| $2^{20}$ | 1,048,576 B | **1 MB** (Megabyte) |
| $2^{30}$ | 1,073,741,824 B | **1 GB** (Gigabyte) |
| $2^{40}$ | 1,099,511,627,776 B | **1 TB** (Terabyte) |
| $2^{50}$ | 1,125,899,906,842,624 B | **1 PB** (Petabyte) |
| $2^{60}$ | 1,152,921,504,606,846,976 B | **1 EB** (Exabyte) |

---

## ⏱️ Availability & "The Nines" Downtime Cheat Sheet

| Availability | Downtime per Day | Downtime per Month | Downtime per Year |
| :--- | :--- | :--- | :--- |
| **99% (Two Nines)** | 14.4 minutes | 7.2 hours | 3.65 days |
| **99.9% (Three Nines)** | 1.44 minutes | 43.2 minutes | 8.76 hours |
| **99.95%** | 43.2 seconds | 21.6 minutes | 4.38 hours |
| **99.99% (Four Nines)** | 8.64 seconds | 4.32 minutes | 52.56 minutes |
| **99.999% (Five Nines)** | 0.86 seconds | 25.9 seconds | 5.26 minutes |

---

## 🧮 Fast Calculation Rules of Thumb

1. **Seconds in a Day**: $\approx 86,400\text{ seconds} \approx 100,000\text{ (10}^5\text{) seconds}$ for rapid estimates.
2. **QPS from Daily Requests**:
   $$\text{Average QPS} = \frac{\text{Daily Requests}}{86,400} \approx \frac{\text{Daily Requests}}{10^5}$$
   *Example: 100 Million daily requests $\approx 1,000$ QPS (Peak $\approx 2,000 - 3,000$ QPS).*
3. **Bandwidth Conversion**:
   $$\text{Throughput in Bytes/sec} \times 8 = \text{Bandwidth in Bits/sec (bps)}$$
   *Example: 125 MB/sec = 1 Gbps network saturation.*
4. **Cache Sizing (80/20 Rule)**:
   $$\text{RAM Sizing} = 20\% \text{ of Daily Read Working Set}$$
