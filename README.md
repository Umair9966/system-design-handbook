# System Design Handbook 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Status: In Active Development](https://img.shields.io/badge/Status-Phase%201%20Skeleton-orange.svg)](ROADMAP.md)

> A production-grade, open-source guide to distributed systems architecture, low-level design, and real-world system design interview preparation.

---

## 📖 Overview

The **System Design Handbook** is designed to bridge the gap between abstract academic distributed systems theory and production engineering reality. Whether you are a beginner building your first client-server application, an experienced software engineer preparing for senior or staff-level design interviews, or a tech lead architecting mission-critical production backends, this repository provides deep, structured, and practical insights.

Every concept in this handbook is structured around **what it is, why it exists, how it works, trade-offs, when to use it, and when NOT to use it**, backed by real-world numbers, architectural diagrams, and concrete failure modes.

---

## 🎯 Target Audience

- **Aspiring Software Engineers & Students**: Build a rock-solid mental model of distributed systems, networking, databases, and microservices.
- **Mid & Senior Software Engineers**: Prepare effectively for FAANG/tier-1 technical interviews with structured frameworks, capacity estimation templates, and 35 deep-dive case studies.
- **Architects & Tech Leads**: Utilize this handbook as an on-the-job reference for architectural decision records (ADRs), resiliency patterns, and trade-off matrices.

---

## 🗺️ Repository Structure & Table of Contents

```
system-design-handbook/
├── README.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── LICENSE
├── docs/
│   ├── 00-how-to-use-this-repo.md
│   ├── 01-fundamentals/
│   ├── 02-networking/
│   ├── 03-load-balancing-and-proxies/
│   ├── 04-caching/
│   ├── 05-databases/
│   ├── 06-data-partitioning-and-replication/
│   ├── 07-distributed-systems-theory/
│   ├── 08-messaging-and-streaming/
│   ├── 09-api-design/
│   ├── 10-architecture-patterns/
│   ├── 11-reliability-and-resilience/
│   ├── 12-security/
│   ├── 13-observability/
│   ├── 14-cloud-and-devops/
│   ├── 15-storage-and-search/
│   ├── 16-real-time-systems/
│   ├── 17-low-level-design/
│   ├── 18-data-and-ml-systems/
│   ├── 19-case-studies/
│   ├── 20-estimation-and-interview-framework/
│   └── 21-glossary.md
├── diagrams/
├── templates/
│   ├── topic-template.md
│   ├── case-study-template.md
│   └── adr-template.md
├── exercises/
└── resources/
```

### 📚 Sections Overview

| Section | Topic | Core Focus |
| :--- | :--- | :--- |
| [**00**](docs/00-how-to-use-this-repo.md) | **How to Use This Repo** | Recommended reading tracks, navigation strategies, and mindset |
| [**01**](docs/01-fundamentals/) | **Fundamentals** | Scalability, latency vs throughput, availability nines, SPOF, statelessness |
| [**02**](docs/02-networking/) | **Networking** | TCP/IP, DNS, HTTP/1-2-3, WebSockets, gRPC, CDN edge caching, NAT & VPN |
| [**03**](docs/03-load-balancing-and-proxies/) | **Load Balancing & Proxies** | L4 vs L7, consistent hashing, GSLB, Anycast, Envoy, NGINX, API gateways |
| [**04**](docs/04-caching/) | **Caching** | Cache-aside, write-through, LRU/LFU, thundering herd, Redis vs Memcached |
| [**05**](docs/05-databases/) | **Databases** | ACID, B+Tree vs LSM, isolation levels, SQL vs NoSQL, OLTP vs OLAP |
| [**06**](docs/06-data-partitioning-and-replication/) | **Data Partitioning & Replication** | Sharding strategies, consistent hashing, replication lag, quorum reads/writes |
| [**07**](docs/07-distributed-systems-theory/) | **Distributed Systems Theory** | CAP, PACELC, Raft, Paxos, clocks, 2PC, Sagas, idempotency, Bloom filters |
| [**08**](docs/08-messaging-and-streaming/) | **Messaging & Streaming** | Kafka, RabbitMQ, SQS, transactional outbox, CDC, backpressure, CQRS |
| [**09**](docs/09-api-design/) | **API Design** | REST, pagination, idempotency keys, rate limiting algorithms, Protobuf |
| [**10**](docs/10-architecture-patterns/) | **Architecture Patterns** | Modular monoliths, microservices, DDD bounded contexts, Strangler Fig |
| [**11**](docs/11-reliability-and-resilience/) | **Reliability & Resilience** | Circuit breakers, exponential backoff with jitter, load shedding, SLOs/SLIs |
| [**12**](docs/12-security/) | **Security** | OAuth 2.0, OIDC, mTLS, zero trust, KMS envelope encryption, OWASP top 10 |
| [**13**](docs/13-observability/) | **Observability** | Metrics, logs, traces, RED & USE methods, OpenTelemetry, incident runbooks |
| [**14**](docs/14-cloud-and-devops/) | **Cloud & DevOps** | Kubernetes abstractions, CI/CD, Terraform IaC, blue-green, FinOps |
| [**15**](docs/15-storage-and-search/) | **Storage & Search** | Block/file/object storage, distributed file systems, Elasticsearch, Geohash |
| [**16**](docs/16-real-time-systems/) | **Real-Time Systems** | WebSocket gateways, presence tracking, fan-out architectures, CRDTs & OT |
| [**17**](docs/17-low-level-design/) | **Low-Level Design (LLD)** | SOLID principles, GoF design patterns, UML, 10+ worked object-oriented problems |
| [**18**](docs/18-data-and-ml-systems/) | **Data & ML Systems** | Data warehouses, Lakehouses (Iceberg), Feature Stores, RAG vector systems |
| [**19**](docs/19-case-studies/) | **Case Studies** | 35 comprehensive end-to-end architectures (URL shortener to Matching Engine) |
| [**20**](docs/20-estimation-and-interview-framework/) | **Estimation & Interview Framework** | Latency numbers, back-of-the-envelope cheat sheet, 6-step interview rubric |
| [**21**](docs/21-glossary.md) | **Glossary** | Comprehensive alphabetical dictionary of 100+ distributed systems terms |

---

## ⏱️ Recommended Study Tracks

Depending on your timeline and goals, follow one of our curated tracks detailed in [**`ROADMAP.md`**](ROADMAP.md):

1. **4-Week Intensive Interview Sprint**: High-yield fundamentals, estimation, caching, databases, and top 10 case studies.
2. **8-Week Comprehensive Engineering Track**: Complete distributed systems theory, networking, messaging, reliability, and 20 case studies.
3. **12-Week Staff+ Mastery Track**: Deep dives into storage engines, consensus protocols, low-level design patterns, ML systems, and all 35 case studies.

---

## 🤝 Contributing

We welcome contributions! Please review our [Contributing Guide](CONTRIBUTING.md) and adhere to our strict technical standards:
- Clear, plain English definitions before complex jargon.
- Balanced trade-off tables for every architectural decision.
- Mermaid diagrams for flows and topologies.
- Standardized templates for topics, case studies, and ADRs.

---

## 📄 License

This repository is licensed under the [MIT License](LICENSE). You are free to share, study, and adapt this material with appropriate attribution.
