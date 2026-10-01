# Cloud Cost Optimization (FinOps)

FinOps brings financial accountability to cloud infrastructure. Without guardrails, autoscaling and unmonitored resources lead to catastrophic cloud bills.

```mermaid
graph TD
    subgraph "Cloud Cost Reduction Levers"
        Compute[Compute Optimization]
        Storage[Storage Optimization]
        Network[Network Optimization]

        Compute --> C1[Spot / Preemptible Instances: 70-90% Discount]
        Compute --> C2[Savings Plans & Reserved Instances: 40-60% Discount]
        Compute --> C3[Right-Sizing Over-Provisioned Pods]

        Storage --> S1[S3 Lifecycle Policies: Glacier Deep Archive]
        Storage --> S2[Clean up unattached EBS volumes / snapshots]

        Network --> N1[VPC Endpoints to eliminate NAT Gateway egress]
        Network --> N2[Compress payloads with Brotli / Gzip]
    end
```

---

## 1. Compute Savings: Spot vs Reserved vs On-Demand

```mermaid
graph LR
    subgraph "Pricing Models"
        OD[On-Demand: 100% Full Price<br/>Zero Commitment, Instant Launch]
        RI[Reserved / Savings Plans: 50% Price<br/>1-3 Year Commitment]
        Spot[Spot Instances: 10-30% Price<br/>Excess Capacity, Cloud can terminate with 2-min warning]
    end
```

- **Spot Instances**: Perfect for stateless worker pools, CI/CD runners, batch processing, and ML training jobs that tolerate interruption.
- **Reserved Instances / Savings Plans**: Commit to a baseline hourly spend ($/hr) for predictable 24/7 databases and core services.

---

## 2. The NAT Gateway Egress Trap

One of the most common surprise AWS bills:
- Sending traffic from private subnets to AWS S3 through a public NAT Gateway costs **$0.045/GB** for NAT processing plus standard egress fees.
- **Solution**: Provision a free **AWS S3 VPC Gateway Endpoint**. Traffic stays on internal AWS routing at $0.00 cost!

---

## 3. Key Takeaways

- Combine Reserved/Savings Plans for baseline load and Spot instances for elastic batch workloads.
- Enforce lifecycle rules on object storage to transition cold data to Glacier automatically.
- Use VPC Gateway Endpoints for AWS services to eliminate unnecessary NAT Gateway transfer costs.
