import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\18-data-and-ml-systems"

files = {
    "01-data-pipelines-etl-vs-elt.md": """# Data Pipelines: ETL vs ELT

Data integration pipelines extract raw data from operational databases, transform it into business models, and load it into analytical engines.

```mermaid
graph TD
    subgraph "ETL (Extract, Transform, Load - Legacy On-Prem)"
        Sources1[OLTP DBs & Logs] --> Extract1[Extract Raw Data]
        Extract1 --> Transform1[Compute Engine / Spark: Transform & Clean]
        Transform1 --> Load1[Load Structured Tables into Data Warehouse]
    end

    subgraph "ELT (Extract, Load, Transform - Modern Cloud)"
        Sources2[OLTP DBs & Logs] --> Extract2[Extract Raw Data (Fivetran / Airbyte)]
        Extract2 --> Load2[Load RAW Data directly into Cloud Warehouse (Snowflake / BigQuery)]
        Load2 --> Transform2[Transform inside Warehouse using SQL & dbt (Scalable Compute!)]
    end
```

---

## 1. Comparing ETL and ELT

| Dimension | ETL (Extract, Transform, Load) | ELT (Extract, Load, Transform) |
| :--- | :--- | :--- |
| **Compute Engine** | Dedicated external cluster (Apache Spark, Databricks) | Cloud Data Warehouse (Snowflake, BigQuery, Redshift) |
| **Raw Data Retention**| Raw data often discarded after transformation | Raw data preserved indefinitely in raw warehouse schemas |
| **Pipeline Flexibility**| Low: Schema changes require altering pipeline code | High: Re-run SQL models with dbt on preserved raw data |
| **Transformation Tool**| Python, Scala, Java Spark jobs | Declarative SQL models via dbt |
| **Ingestion Speed** | Slower (bottlenecked by transformation stage) | Blazing fast (dump raw files directly) |

---

## 2. Modern ELT with dbt (data build tool)

In modern data stacks, **dbt** manages transformations inside the cloud data warehouse:
- Declarative SQL `SELECT` statements compiled into database tables or views.
- Automated lineage Directed Acyclic Graphs (DAGs).
- Native schema tests (`unique`, `not_null`, foreign key assertions).

```mermaid
graph LR
    Raw[Raw Table: raw_stripe.charges] --> Model1[stg_stripe__payments.sql]
    Model1 --> Fact[fct_orders.sql (Clean Dimension/Fact)]
    Fact --> Mart[mart_finance_revenue.sql]
```

---

## 3. Key Takeaways

- Default to ELT using Cloud Data Warehouses and dbt for analytical pipelines.
- Reserve ETL for real-time streaming transformations or when strict compliance prohibits storing raw PII data in warehouses.
- Version control all SQL transformations and enforce automated data tests in CI.
""",

    "02-data-lakes-warehouses-and-lakehouses.md": """# Data Lakes, Warehouses, and the Lakehouse Architecture

Modern analytical architectures have converged from siloed data warehouses and unstructured data lakes into unified **Lakehouse** platforms (Delta Lake, Apache Iceberg, Apache Hudi).

```mermaid
graph TD
    subgraph "Evolution of Data Architectures"
        DW[1. Data Warehouse: Fast SQL, Structured only, High Cost]
        DL[2. Data Lake: Cheap S3 Storage, All Formats, No ACID, 'Data Swamp']
        LH[3. Lakehouse: ACID Transactions + Parquet Open Formats + S3 Pricing]
    end
```

---

## 1. The Lakehouse Revolution (Apache Iceberg & Delta Lake)

```mermaid
graph TD
    subgraph "Lakehouse Architecture"
        Engines[Query Engines: Spark, Trino, Presto, DuckDB, Snowflake]
        TableFormat[Table Format Layer: Apache Iceberg / Delta Lake<br/>Metadata Files, Snapshots, Manifest Lists]
        FileFormat[Columnar Data Files: Apache Parquet (Zstd)]
        Storage[Cloud Object Storage: AWS S3 / Google Cloud Storage]

        Engines --> TableFormat
        TableFormat --> FileFormat
        FileFormat --> Storage
    end
```

### Superpowers of the Lakehouse:
1. **ACID Transactions on Object Storage**: Serializable snapshot isolation on top of cloud object storage (S3).
2. **Time Travel & Rollbacks**: Query historical snapshots (`SELECT * FROM table TIMESTAMP AS OF '2026-09-01'`).
3. **Partition Evolution**: Modify partition schemes without rewriting billions of underlying Parquet files.
4. **Zero Vendor Lock-in**: Parquet data files on S3 can be queried simultaneously by Snowflake, Trino, Databricks, and Python.

---

## 2. Key Takeaways

- Adopt open table formats (**Apache Iceberg** or Delta Lake) to combine S3 economics with database ACID reliability.
- Use columnar formats (**Apache Parquet**) with Zstd compression for analytical query performance.
- Decouple compute from storage to scale query clusters and storage capacity independently.
""",

    "03-feature-stores.md": """# Feature Stores: Feast and Hopsworks

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
""",

    "04-ml-serving-and-model-lifecycle.md": """# ML Serving, Model Registry, and MLOps

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
""",

    "05-recommendation-systems-architecture.md": """# Recommendation Systems Architecture (Two-Stage Retrieval & Ranking)

Modern recommendation systems (YouTube, Netflix, TikTok, Instagram) recommend items from catalogs of billions of items within 50ms using the **Two-Stage Candidate Retrieval and Ranking** pattern.

```mermaid
graph TD
    UserReq[User Opens App: 1 Billion Items in Catalog] --> Step1[1. Candidate Generation / Retrieval<br/>Reduces 1 Billion -> 1,000 Candidates<br/>Latency: 10ms | Light Vector Search (Two-Tower / HNSW)]
    Step1 --> Step2[2. Scoring & Heavy Ranking<br/>Reduces 1,000 -> 50 Items<br/>Latency: 25ms | Deep Neural Network / GBDT]
    Step2 --> Step3[3. Re-Ranking & Diversity Filtering<br/>Reduces 50 -> 10 Final Display Items<br/>Latency: 5ms | Business rules, deduplication, sponsored ads]
    Step3 --> Output[User Screen: Top 10 Personalized Carousel]
```

---

## 1. The Two-Stage Architecture Deep Dive

### Stage 1: Candidate Generation (Retrieval)
- **Goal**: Coarsely filter millions/billions of items down to ~1,000 candidates.
- **Technology**: **Two-Tower Neural Networks** (User Tower + Item Tower) outputting 128-dimensional dense vector embeddings.
- **Serving**: Approximate Nearest Neighbor (ANN) search using Faiss or Milvus over HNSW graphs ($O(\log N)$ latency).

### Stage 2: Heavy Ranking
- **Goal**: Accurately predict Click-Through Rate ($pCTR$) and Watch Time for the 1,000 candidates.
- **Technology**: Multi-task Deep Learning models (DLRM, Transformer-based rankers) incorporating hundreds of real-time features (user history, device, time of day).

### Stage 3: Re-Ranking and Business Logic
- Deduplicates recently watched items.
- Enforces topic diversity (don't show 10 cooking videos in a row).
- Injects sponsored promotional content.

---

## 2. Key Takeaways

- Never evaluate a heavy ranking model over the entire catalog; always use a lightweight retrieval stage first.
- Precompute item embeddings offline; compute user embeddings online using real-time interaction signals.
- Include a final re-ranking phase for diversity, fairness, and business constraints.
""",

    "06-rag-and-vector-search-systems.md": """# Retrieval-Augmented Generation (RAG) and Vector Search Systems

Retrieval-Augmented Generation (RAG) grounds Large Language Models (LLMs) with dynamic, proprietary, or private external knowledge, eliminating hallucinations and enabling real-time factual accuracy without expensive fine-tuning.

```mermaid
sequenceDiagram
    autonumber
    participant User as End User
    participant App as Orchestrator / LangChain
    participant Embed as Embedding Model (Text-Embedding-3)
    participant VectorDB as Vector DB (Pinecone / Milvus / Qdrant)
    participant LLM as Frontier LLM (Gemini 1.5 / Claude)

    User->>App: "What is our company's refund policy for damaged goods?"
    App->>Embed: Embed query string into 1536-dim vector
    Embed-->>App: Returns query vector [0.023, -0.412, ...]
    App->>VectorDB: ANN Search(query_vector, Top_K=3, Cosine Similarity)
    VectorDB-->>App: Returns relevant policy chunk documents
    Note over App: Constructs Augmented Prompt:<br/>"Context: {chunks}<br/>Question: {query}<br/>Answer strictly based on Context."
    App->>LLM: Generates grounded response
    LLM-->>App: Factual, hallucination-free answer with citations
    App-->>User: Delivers response
```

---

## 1. Document Ingestion Pipeline

```mermaid
graph LR
    Docs[Raw PDFs / Wiki / Confluence] --> Chunk[Document Chunker: 500 tokens + 50 overlap]
    Chunk --> Embed[Embedding Model]
    Embed --> Store[(Vector DB: HNSW Index)]
```

### Chunking Strategies:
- **Fixed Size with Overlap**: 500 tokens with 50-token overlap preserves context across boundaries.
- **Semantic / Document Structure**: Chunk by Markdown headers (`#`, `##`) or sentence boundaries.

---

## 2. Advanced RAG Techniques

1. **Hybrid Search (Dense + Sparse)**: Combines dense vector semantic similarity with traditional sparse keyword BM25 search via Reciprocal Rank Fusion (RRF).
2. **Re-Ranking (Cross-Encoder)**: Run top-20 retrieved chunks through a Cohere/BGE cross-encoder model to score relevance before sending the top 5 to the LLM.
3. **Hypothetical Document Embeddings (HyDE)**: The LLM generates a hypothetical answer to the query first; that hypothetical answer is embedded to find real matching documents.

---

## 3. Key Takeaways

- Chunk documents intelligently with semantic boundaries and overlaps.
- Combine vector search with BM25 keyword search (Hybrid Search) to ensure exact keyword and part-number matches.
- Use cross-encoder re-rankers to maximize context relevance while minimizing expensive LLM prompt token costs.
""",

    "07-data-quality-and-governance.md": """# Data Quality, Lineage, and Governance

Data governance ensures data assets are trustworthy, traceable, compliant with privacy regulations, and accessible across the enterprise.

```mermaid
graph LR
    Source[Raw Data Ingestion] --> Contracts[1. Data Contracts: Schema & SLA Enforcement]
    Contracts --> Tests[2. Great Expectations / dbt Tests: Data Quality Checks]
    Tests --> Lineage[3. OpenLineage / Marquez: Automated Data Lineage DAG]
    Lineage --> Catalog[4. Data Catalog / DataHub: Search & Metadata]
```

---

## 1. Data Contracts

A data contract is an explicit agreement between data producers (software engineering teams) and data consumers (data analysts, ML engineers) defining schema, semantic meaning, SLA freshness, and quality guarantees:

```yaml
# Example Data Contract: orders_contract.yaml
dataset: orders
version: 2.1.0
owner: checkout-team
sla:
  freshness_minutes: 15
schema:
  - name: order_id
    type: string
    tests: [unique, not_null]
  - name: total_amount
    type: decimal(10,2)
    tests: [not_null, "total_amount > 0"]
```

---

## 2. Automated Data Lineage (OpenLineage)

When a critical financial dashboard shows incorrect numbers, data lineage tracks the upstream provenance of every row and column back to the originating database tables, Kafka topics, and dbt models.

---

## 3. Key Takeaways

- Implement Data Contracts at the boundary between software services and the data warehouse.
- Automate data quality testing using dbt assertions or Great Expectations.
- Track end-to-end data lineage to rapidly debug data corruption and evaluate upstream change impacts.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 18 complete.")
