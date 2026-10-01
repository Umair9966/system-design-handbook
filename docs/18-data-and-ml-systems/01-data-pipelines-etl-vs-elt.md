# Data Pipelines: ETL vs ELT

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
