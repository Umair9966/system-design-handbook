# Containers and Kubernetes Architecture

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
