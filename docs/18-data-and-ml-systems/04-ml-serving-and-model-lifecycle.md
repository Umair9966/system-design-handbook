# ML Serving, Model Registry, and MLOps

Deploying machine learning models to production requires automated CI/CD for models, artifact versioning (MLflow), and low-latency inference runtimes (Triton, TorchServe).

```mermaid
graph LR
    subgraph MLOps Lifecycle
        Train[1. Continuous Training] --> Eval[2. Model Evaluation & Benchmark]
        Eval --> Reg[3. Model Registry (MLflow / Weights & Biases)]
        Reg --> CanaryDeploy[4. Canary Deployment (Shadow / AB Test)]
        CanaryDeploy --> Serving[5. Model Server (Triton / ONNX Runtime)]
        Serving --> Monitor[6. Drift Detection (Evidently AI)]
        Monitor -.->|Data Drift Detected!| Train
    end
```

---

## 1. Model Serving Patterns

| Pattern | Latency | Infrastructure Cost | Scalability | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Real-Time Online RPC** | 10ms - 50ms | High (24/7 GPU/CPU pods) | Autoscaling via KEDA | Fraud detection, live ranking |
| **Batch Offline Scoring** | Hours | Low (Ephemeral batch compute) | Petabytes | Daily recommendation emails |
| **Embedded in Process** | < 1ms | Low (Runs inside app memory) | Scales with app | Lightweight Decision Trees, ONNX models |
| **Edge / Mobile On-Device**| < 5ms | Zero server cost | Infinite | CoreML, TFLite on smartphones |

---

## 2. Detecting Data & Concept Drift

- **Data Drift (Covariate Shift)**: The distribution of incoming input features $P(X)$ changes over time (e.g., user income distribution changes during an inflation spike).
- **Concept Drift**: The statistical relationship between features and target labels $P(Y|X)$ changes (e.g., consumer purchasing patterns shift overnight during a pandemic).
- *Remediation*: Monitor Population Stability Index (PSI) or Kolmogorov-Smirnov statistical tests; trigger automated model retraining when drift exceeds threshold.

---

## 3. Key Takeaways

- Version all model weights, datasets, and hyperparameters using a Model Registry (MLflow).
- Optimize inference models with ONNX Runtime or TensorRT to reduce GPU costs by 3x-5x.
- Continuously monitor for feature drift in production to prevent silent model degradation.
