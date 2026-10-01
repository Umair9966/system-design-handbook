# Recommendation Systems Architecture (Two-Stage Retrieval & Ranking)

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
