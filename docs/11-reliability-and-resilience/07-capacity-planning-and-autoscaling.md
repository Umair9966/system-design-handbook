# Capacity Planning and Autoscaling

Capacity planning ensures a system has sufficient compute, memory, storage, and network bandwidth to meet expected load with acceptable latency while minimizing infrastructure costs.

```mermaid
graph TD
    Metrics[System Metrics: CPU, Memory, Queue Depth, Req/sec] --> MetricsServer[Kubernetes Metrics Server / Prometheus]
    MetricsServer --> HPA[Horizontal Pod Autoscaler (HPA)]
    HPA -->|Pod Replicas: Scales 10 -> 80| Deploy[Application Deployment]
    Deploy --> CA[Cluster Autoscaler / Karpenter]
    CA -->|Provisions New Cloud VM Nodes| Cloud[AWS EC2 / GCP Compute]
```

---

## 1. Vertical vs Horizontal Autoscaling

- **HPA (Horizontal Pod Autoscaler)**: Increases or decreases the number of pod or container replicas based on real-time load.
- **VPA (Vertical Pod Autoscaler)**: Dynamically adjusts CPU and memory resource requests/limits of existing containers.
- **Cluster Autoscaler (Karpenter)**: Adds physical or virtual cloud worker nodes to the Kubernetes cluster when pending pods cannot be scheduled due to insufficient node resources.

---

## 2. Autoscaling Metrics: Choosing the Right Trigger

| Metric | Scaling Speed | Pitfalls / Gotchas | Best For |
| :--- | :--- | :--- | :--- |
| **CPU Utilization** | Moderate | CPU is a lagging indicator; spike arrives before CPU registers | General compute workloads |
| **Memory Utilization** | Very Slow | Garbage collected languages (Java, Go) retain memory; won't trigger scale down | Memory leaks, cache nodes |
| **Queue Depth (SQS / Kafka Lag)**| Fast & Predictive | If consumers crash, queue expands and spawns infinite pods | Asynchronous worker pipelines |
| **Request Rate (RPS)** | Instant | Requires custom metrics via Prometheus adapter | Public HTTP API gateways |

---

## 3. The Autoscaling Thrashing Problem (Flapping)

Rapid oscillation between scaling up and scaling down due to short bursts:

```mermaid
graph TD
    Spike[Sudden 30s Spike] --> ScaleUp[Scale Up to 100 Pods]
    SpikeEnd[Spike Clears] --> ScaleDown[Scale Down to 10 Pods]
    Spike2[Another Burst] --> ScaleUp2[Scale Up Again!]
    Note over ScaleUp,ScaleUp2: Causes continuous container cold starts and waste
```

### Prevention:
- **Cooldown / Stabilization Windows**: Require a metric to remain low for at least 5 minutes before initiating a scale-down.
- **Scale-Up Aggressive, Scale-Down Conservative**: Scale up instantly (e.g., +100% capacity), scale down slowly (e.g., -10% every 5 minutes).

---

## 4. Key Takeaways

- Scale horizontally on request rate or queue depth rather than lagging CPU metrics whenever possible.
- Configure aggressive scale-up policies paired with conservative scale-down cooldown windows to prevent thrashing.
- Align container autoscaling (HPA) with node autoscaling (Karpenter) to avoid scheduling deadlocks.
