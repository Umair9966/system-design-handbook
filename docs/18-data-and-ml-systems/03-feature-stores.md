# Feature Stores: Feast and Hopsworks

A Feature Store is a centralized data management layer for machine learning that bridges the gap between batch feature engineering (training) and low-latency feature serving (inference).

```mermaid
graph TD
    subgraph Feature Ingestion
        BatchSource[Batch: Snowflake / S3] --> Feast[Feature Store / Feast Engine]
        StreamSource[Stream: Kafka / Flink] --> Feast
    end

    subgraph Feature Storage
        Feast --> Offline[(Offline Store: S3 / Snowflake Parquet)<br/>Stores Years of History for Training]
        Feast --> Online[(Online Store: Redis / DynamoDB)<br/>Stores Latest Feature Vector: <10ms for Inference]
    end

    subgraph ML Consumers
        Offline --> Train[Model Training: Point-in-time Joins]
        Online --> Serve[Real-time Inference: Model Server]
    end
```

---

## 1. The Dual-Store Problem

Machine Learning models require features in two fundamentally different environments:
- **Offline (Training)**: Needs terabytes of historical point-in-time data to train weights without data leakage. High throughput, batch-oriented.
- **Online (Inference)**: Needs the latest feature values for a specific user ID within 5ms during an API call. Low latency, point lookups.

Without a Feature Store, data science teams re-implement features twice (once in Python for training, once in Java/Go for production), causing **Training-Serving Skew**.

---

## 2. Preventing Data Leakage with Point-in-Time Joins

When training an ML model to predict whether a loan defaults at timestamp $T$, the training pipeline must strictly exclude any features created *after* $T$ (e.g., late payments that occurred 6 months later). Feature stores automate point-in-time historical joins ("as-of joins").

---

## 3. Key Takeaways

- Feature stores eliminate Training-Serving skew by defining feature logic once for both batch and real-time.
- Use Redis or DynamoDB for the low-latency Online Store and S3/Snowflake for the high-capacity Offline Store.
- Enforce point-in-time correctness to prevent future data leakage into training sets.
