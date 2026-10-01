# Contributing to System Design Handbook 🤝

Thank you for your interest in contributing to the **System Design Handbook**! Our mission is to build the highest-quality, most accurate, and accessible open-source system design resource on the web.

---

## 📜 Writing Rules & Style Guide

All contributions must strictly adhere to the following 10 standards:

1. **Plain, Clear English**: Define every technical term the first time it appears. Avoid unexplained acronyms.
2. **Mandatory Conceptual Dimensions**: Every architectural concept must clearly detail:
   - **What it is** (concise definition)
   - **Why it exists** (the problem it solves)
   - **How it works** (internal mechanics)
   - **Trade-offs** (structured markdown comparison table)
   - **When to use it**
   - **When NOT to use it**
3. **Realistic Numbers**: Use grounded estimates for latency, throughput, and memory. Mark all approximations clearly (e.g., `"~100 ms estimate"`).
4. **No Hallucinated Benchmarks**: Never invent company statistics or proprietary metrics. State `"varies by implementation"` if an industry benchmark is not publicly verified.
5. **Visual Architecture**: Use Mermaid diagrams (` ```mermaid `) for topologies, state transitions, and sequence flows.
6. **Structured Tables**: Use Markdown tables for comparisons (e.g., SQL vs NoSQL, B-Tree vs LSM-Tree).
7. **Originality**: Write 100% original explanations. Do not copy-paste copyrighted text from blogs, books, or papers. Link original papers in the "Further reading" section.
8. **Consistent File Endings**: Every file must end with:
   - **Key takeaways** (3 to 5 bullet points)
   - **Common interview questions** (3 to 5 questions)
   - **Further reading** (canonical papers, RFCs, engineering blogs)
9. **Focus & Modularity**: Keep each markdown document focused. If a file exceeds ~400 lines, split it logically.
10. **Relative Markdown Links**: Use relative links (`[link text](../04-caching/01-cache.md)`) so links work seamlessly in local repositories, GitHub, and static site generators.

---

## 🛠️ Contribution Workflow

1. **Fork the Repository**: Create your branch from `main`:
   ```bash
   git checkout -b feature/topic-name
   ```
2. **Use the Standard Templates**:
   - For technical topics: [`templates/topic-template.md`](templates/topic-template.md)
   - For case studies: [`templates/case-study-template.md`](templates/case-study-template.md)
   - For architectural decisions: [`templates/adr-template.md`](templates/adr-template.md)
3. **Verify Links & Mermaid Formatting**:
   Ensure all Mermaid diagram blocks render cleanly and relative file links are valid.
4. **Submit a Pull Request**:
   Provide a concise PR description summarizing the changes and referencing any open issues.
