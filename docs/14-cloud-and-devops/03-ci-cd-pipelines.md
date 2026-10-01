# CI/CD Pipelines and Automated Delivery

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
