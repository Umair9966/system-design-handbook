import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\14-cloud-and-devops"

files = {
    "01-cloud-computing-models.md": """# Cloud Computing Models: IaaS, PaaS, SaaS, and Hybrid Cloud

Cloud computing delivers on-demand computing services over the internet on a pay-as-you-go pricing model. Understanding the shared responsibility model across cloud service tiers is fundamental to modern system design.

```mermaid
graph TD
    subgraph "Shared Responsibility Spectrum"
        OnPrem[On-Premises: You Manage 100%]
        IaaS[IaaS: AWS EC2 / Azure VMs]
        PaaS[PaaS: Heroku / AWS Elastic Beanstalk]
        Serverless[Serverless / FaaS: AWS Lambda]
        SaaS[SaaS: Snowflake / Auth0 / Datadog]
    end

    OnPrem -->|Cloud handles Data Center & Power| IaaS
    IaaS -->|Cloud handles OS, Virtualization & Patching| PaaS
    PaaS -->|Cloud handles Scaling & Runtime Execution| Serverless
    Serverless -->|Cloud handles Full Application Software| SaaS
```

---

## 1. Comparing Cloud Service Models

| Model | What You Manage | What Provider Manages | Control Level | Operational Overhead |
| :--- | :--- | :--- | :--- | :--- |
| **IaaS** | OS, Runtime, Middleware, Data, App | Physical hardware, networking, hypervisor | Maximum | High |
| **PaaS** | Application code, Data, Configurations | OS, Runtime, Auto-patching, Hardware | Medium | Low |
| **Serverless** | Function code, Event triggers | Runtime, Instant scaling, Infrastructure | Focused | Near Zero |
| **SaaS** | User accounts, Access policies | Entire application, Storage, Security | Minimal | Zero |

---

## 2. Multi-Cloud vs Hybrid Cloud Strategies

```mermaid
graph TD
    subgraph "Hybrid Cloud"
        HQ[On-Premises Private Data Center: Legacy Core] <-->|AWS Direct Connect (Dedicated 10Gbps Fiber)| Cloud1[AWS Public Cloud VPC]
    end

    subgraph "Multi-Cloud (Best-of-Breed vs Reality)"
        App[Application Workload]
        App --> AWS[AWS for S3 / EKS]
        App --> GCP[GCP for BigQuery / TPU AI]
        Note over AWS,GCP: Risk: Egress data transfer fees ($0.09/GB) create massive cost traps!
    end
```

### The Multi-Cloud Reality:
While multi-cloud promises vendor independence, abstracting across AWS, GCP, and Azure often forces architectures to the "lowest common denominator," sacrificing managed cloud-native superpowers. Best practice: Choose one primary cloud provider and utilize specialized secondary clouds only for distinctive advantages (e.g., GCP for BigQuery/ML).

---

## 3. Key Takeaways

- Balance operational overhead against architectural control: default to managed PaaS/Serverless unless scale dictates IaaS.
- Beware of cloud egress costs when architecting multi-cloud data flows.
- Enforce the Shared Responsibility Model to ensure your security controls cover what the cloud provider does not.
""",

    "02-containers-and-kubernetes-concepts.md": """# Containers and Kubernetes Architecture

Containerization packages application code with all dependencies, libraries, and runtime binaries into an immutable container image. Kubernetes (K8s) automates the deployment, scaling, and operational management of containerized workloads.

```mermaid
graph TD
    subgraph "Kubernetes Control Plane (Master Nodes)"
        API[kube-apiserver] <--> etcd[(etcd: Consensus State Store)]
        API --> Sched[kube-scheduler: Assigns Pods to Nodes]
        API --> CM[kube-controller-manager]
    end

    subgraph "Kubernetes Worker Node 1"
        Kubelet1[kubelet] <--> API
        KubeProxy1[kube-proxy]
        CRI1[Containerd Runtime]
        Pod1[Pod: App Container + Envoy Sidecar]
    end

    subgraph "Kubernetes Worker Node 2"
        Kubelet2[kubelet] <--> API
        KubeProxy2[kube-proxy]
        CRI2[Containerd Runtime]
        Pod2[Pod: App Container]
    end
```

---

## 1. Core Kubernetes Building Blocks

- **Pod**: The smallest deployable computing unit. Pods encapsulate one or more containers that share storage (volumes), network IP, and localhost namespace.
- **Deployment**: Declarative specification managing replica sets, rolling updates, and rollbacks.
- **Service**: Abstraction defining a logical set of Pods and a policy to access them (ClusterIP, NodePort, LoadBalancer).
- **Ingress**: Manages external HTTP/HTTPS routing into services (e.g., NGINX Ingress, Traefik).

---

## 2. Pod Lifecycle and Scheduling Mechanics

```mermaid
sequenceDiagram
    autonumber
    participant Dev as kubectl apply
    participant API as kube-apiserver
    participant Sched as kube-scheduler
    participant Kubelet as Worker Kubelet
    participant CRI as Container Runtime

    Dev->>API: Submits Deployment manifest
    API->>API: Validates and saves to etcd
    Sched->>API: Detects unscheduled pod
    Sched->>Sched: Filters & Ranks nodes (Affinity, Taints, Resource limits)
    Sched->>API: Binds pod to Worker Node 1
    Kubelet->>API: Watches pod bound to its node
    Kubelet->>CRI: Pulls image & starts containers
    Kubelet->>API: Reports pod status: Running
```

---

## 3. Key Takeaways

- Use Deployments for stateless services and StatefulSets for databases requiring persistent identity and storage.
- Always define CPU and Memory `requests` and `limits` to prevent noisy neighbors from triggering kernel OOM kills.
- Use `readinessProbes` and `livenessProbes` to enable zero-downtime rolling updates.
""",

    "03-ci-cd-pipelines.md": """# CI/CD Pipelines and Automated Delivery

Continuous Integration (CI) and Continuous Delivery (CD) automate the journey of software from code commit through automated testing, security scanning, container packaging, and production rollout.

```mermaid
graph LR
    subgraph Continuous Integration (CI)
        Commit[Git Push / PR] --> Lint[Lint & Static Analysis]
        Lint --> Unit[Unit & Integration Tests]
        Unit --> Security[SAST & Dependency Scan]
        Security --> Build[Docker Build & Push to Registry]
    end

    subgraph Continuous Delivery / Deployment (CD)
        Build --> Staging[Deploy to Staging]
        Staging --> E2E[End-to-End Automated Tests]
        E2E --> Canary[Canary Release to Production (5%)]
        Canary --> Full[Promote to 100% Production]
    end
```

---

## 1. GitOps: The Modern CD Paradigm (ArgoCD & Flux)

GitOps treats Git repositories as the single source of truth for declared infrastructure and application state.

```mermaid
graph LR
    Dev[Developer] -->|git commit| GitRepo[Git Repository (Manifests / Helm)]
    subgraph Kubernetes Cluster
        Argo[ArgoCD Controller] -->|Watches Git| GitRepo
        Argo -->|Compares Desired vs Live State| K8s[Live Cluster Resources]
        Argo -->|Auto-Syncs Discrepancies / Reverts Drift| K8s
    end
```

### Core Tenets of GitOps:
1. **Declarative State**: The entire system is described declaratively in Git (YAML / Helm / Kustomize).
2. **Automated Pull Reconciliation**: The in-cluster agent pulls changes from Git rather than external CI pushing credentials into the cluster.
3. **Drift Detection**: Any manual `kubectl edit` in production is automatically overwritten and reverted back to the Git state.

---

## 2. Key Takeaways

- Shift security left by integrating static analysis (SAST) and container vulnerability scanning into pull request CI checks.
- Adopt GitOps (ArgoCD) to eliminate giving CI systems broad administrative cluster credentials.
- Automate canary rollouts with metric verification to catch regressions before full deployment.
""",

    "04-infrastructure-as-code.md": """# Infrastructure as Code (IaC): Terraform and GitOps

Infrastructure as Code (IaC) is the practice of provisioning and managing computing infrastructure using declarative configuration definitions rather than manual console clicks.

```mermaid
graph TD
    Code[Terraform / OpenTofu HCL Code] --> Plan[terraform plan: Calculates Execution Graph]
    Plan --> StateLock[Locks Remote State in S3 + DynamoDB]
    StateLock --> Apply[terraform apply: Makes Cloud API Calls]
    Apply --> Cloud[Provisions AWS VPC, RDS, EKS, IAM]
    Apply --> StateUpdate[Updates terraform.tfstate]
```

---

## 1. Declarative vs Imperative IaC

| Dimension | Declarative (Terraform, Pulumi, CloudFormation) | Imperative (Bash, AWS CLI, Python SDK) |
| :--- | :--- | :--- |
| **Paradigm** | You declare **what** the final state should look like | You write step-by-step instructions on **how** to create it |
| **Idempotency** | Native ($N$ executions yield identical state) | Requires manual checks and scripting logic |
| **Drift Detection** | Automatic comparison of live cloud state vs code | Difficult / Manual |
| **Dependency Graph**| Computes DAG automatically for parallel provisioning | Developer must order execution manually |

---

## 2. State Management and Race Conditions

Terraform relies on a state file (`terraform.tfstate`) to map real-world cloud resources to code.
- **Remote State**: Store state in remote object storage (AWS S3, GCS) with encryption at rest.
- **State Locking**: Use a distributed lock (DynamoDB, Consul) to prevent two engineers or CI pipelines from running `apply` concurrently, which corrupts infrastructure state.

---

## 3. Key Takeaways

- Never click manually in cloud provider consoles for production resources; everything must be in IaC.
- Keep Terraform modules small and decoupled to reduce blast radius and state-locking contention.
- Store sensitive variables in secret vaults rather than plain text in Terraform repositories.
""",

    "05-regions-zones-and-edge.md": """# Regions, Availability Zones, and Edge Locations

Cloud physical architecture is organized hierarchically into Regions, Availability Zones, and Edge Points of Presence (PoPs) to balance latency, redundancy, and disaster recovery.

```mermaid
graph TD
    subgraph "Global Cloud Topology"
        Edge[Edge PoP / Cloudflare CDN: 300+ Cities]
        Edge -->|AWS Backbone WAN| Reg[Cloud Region: us-east-1]
        
        subgraph "Region us-east-1"
            AZ1[Availability Zone A: DC 1 & 2]
            AZ2[Availability Zone B: DC 3 & 4]
            AZ3[Availability Zone C: DC 5 & 6]
            AZ1 <-->|< 1ms Ultra-Low Latency Dark Fiber| AZ2
            AZ2 <-->|< 1ms Ultra-Low Latency Dark Fiber| AZ3
        end
    end
```

---

## 1. Physical Infrastructure Definitions

- **Edge PoP**: Lightweight cache and routing nodes located in major metropolitan areas close to end users. Handles TLS termination, static asset caching, and DDoS mitigation.
- **Availability Zone (AZ)**: One or more discrete physical data centers with redundant power, networking, and cooling. Separated by meaningful physical distance (miles) to protect against localized disasters, but close enough (< 1ms) for synchronous replication.
- **Region**: A geographic area containing 3 or more isolated AZs connected via dedicated low-latency fiber networks.

---

## 2. Intra-Region vs Cross-Region Latency & Cost

| Traffic Type | Latency | Data Transfer Cost | Typical Usage |
| :--- | :--- | :--- | :--- |
| **Intra-AZ** | < 0.1ms | Free | Communication within same subnet |
| **Cross-AZ (Same Region)** | ~1ms | $0.01 / GB | Synchronous DB replication, High Availability |
| **Cross-Region (WAN)** | 30ms - 150ms | $0.02 - $0.09 / GB | Disaster recovery, Global data replication |

---

## 3. Key Takeaways

- Deploy workloads across a minimum of 3 Availability Zones to survive data center-level hardware disasters.
- Understand cross-AZ data transfer costs; high-throughput chatty microservices can generate massive bills if placed across AZs unnecessarily.
- Terminate TLS and serve static assets at Edge PoPs to cut end-user perceived latency by 70%+.
""",

    "06-cloud-cost-optimization.md": """# Cloud Cost Optimization (FinOps)

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
""",

    "07-feature-flags-and-progressive-delivery.md": """# Feature Flags and Progressive Delivery

Progressive Delivery decouples code deployment from feature release. Deploying code to production is an engineering event; releasing functionality to users is a business decision.

```mermaid
graph LR
    Deploy[Deploy Code to Production (Flags Off)] --> Internal[1. Internal Employees (Dogfooding)]
    Internal --> Beta[2. Beta Testers (1%)]
    Beta --> Canary[3. Canary Percentage Rollout (10% -> 50%)]
    Canary --> GA[4. General Availability (100%)]
    Canary -.->|Anomaly Detected!| KillSwitch[Emergency Kill Switch: 0% Instantly]
```

---

## 1. Feature Flag Architecture

Feature flag evaluations must happen in-memory in microseconds without making a remote network call per evaluation:

```mermaid
graph TD
    Dashboard[LaunchDarkly / Unleash Admin Dashboard] --> FlagStream[SSE / WebSocket Config Stream]
    FlagStream --> LocalCache[In-Memory Flag Cache inside App SDK]
    AppCode[Incoming User Request] --> Eval[SDK.evaluate('new-ui', userContext)]
    Eval --> LocalCache
    LocalCache -->|0.001ms In-Memory Hash| Decision{Flag Enabled?}
```

---

## 2. Contextual Targeting and Gradual Rollouts

Feature flags use deterministic hashing (e.g., MurmurHash3) to ensure a user consistently receives the same feature experience:

$$\text{Bucket} = \text{MurmurHash3}(\text{user\_id} + "\text{new\_checkout}") \pmod{100}$$

If the rollout percentage is set to 25%, any user whose hash bucket is $< 25$ receives the new feature. As the slider increases to 50%, previously enabled users remain enabled without state synchronization.

---

## 3. Managing Technical Debt of Stale Flags

Feature flags are short-term loans. If not removed, they turn codebases into tangled spaghetti:
1. **Flag Expiration / TTLs**: Assign every flag an owner and an expiration date (e.g., 30 days after 100% rollout).
2. **Automated Flag Cleanup**: Use static analysis tools (e.g., Uber's Piranha) to automatically generate pull requests that delete obsolete feature flag if/else statements.

---

## 4. Key Takeaways

- Decouple deployment from release using feature flags to minimize deployment risk.
- Evaluate flags locally in memory; never make synchronous HTTP calls to feature flag servers in the request path.
- Treat feature flags as technical debt and schedule automated pruning after general release.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 14 complete.")
