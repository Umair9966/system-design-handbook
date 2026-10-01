# Probabilistic Data Structures: Bloom Filters, HyperLogLog, and Count-Min Sketch

## Overview
As datasets scale into billions of items, traditional exact data structures (Hash Sets, Balanced Trees) become prohibitively expensive, consuming hundreds of gigabytes of RAM.

**Probabilistic Data Structures** trade mathematical perfection for exponential reductions in memory consumption and constant $O(1)$ query times by allowing a tiny, configurable margin of error:
- **Bloom Filter**: Tests set membership ("Definitely Not in Set" vs "Possibly in Set").
- **HyperLogLog (HLL)**: Estimates unique count (cardinality) of high-volume datasets.
- **Count-Min Sketch**: Estimates the frequency of events in high-throughput streams.

```mermaid
graph TD
    subgraph Bloom Filter Mechanics
        Item[Item: user_42] --> H1[Hash Function 1] --> Bit3[Bit 3 = 1]
        Item --> H2[Hash Function 2] --> Bit7[Bit 7 = 1]
        Item --> H3[Hash Function 3] --> Bit15[Bit 15 = 1]
    end
    Query[Query: user_99] --> Check{Are bits 3, 7, 15 all 1?}
    Check -->|No: Any bit is 0| Res1[DEFINITELY NOT IN SET (Zero False Negatives!)]
    Check -->|Yes: All bits are 1| Res2[POSSIBLY IN SET (Small False Positive Rate)]
```

## Why It Matters
Calculating the number of unique daily visitors across 1 billion clicks using an exact hash set requires storing 1 billion 64-bit user IDs:
$$1,000,000,000 \times 8\text{ bytes} \approx \mathbf{8\text{ Gigabytes of RAM}}$$
Using **HyperLogLog**, you can estimate the exact same 1 billion unique users with a **1.04% error rate using only 1.5 Kilobytes of RAM**—a **5,000,000x memory reduction**!

## Core Concepts & Mechanics

### 1. Bloom Filter (Set Membership)
- A bit array of $m$ bits, initially all 0, paired with $k$ independent cryptographic hash functions.
- *Insertion*: Hash the item with all $k$ functions and set the corresponding bits to 1.
- *Query*: Hash the query item. If **any** of the $k$ bits is 0, the item is **definitely NOT in the set** (0% False Negative). If all bits are 1, the item is **probably in the set** (small false positive rate $\approx 1\%$).
- *Limitation*: You cannot delete items from a standard Bloom filter (setting a bit to 0 breaks other keys).

### 2. HyperLogLog (Cardinality Estimation)
- Solves: *"How many distinct users visited today?"*
- Hashes each item and counts the number of leading zeros in the binary hash output.
- The probability of seeing $k$ consecutive leading zeros is $2^{-k}$. Observing 20 leading zeros suggests the stream contains roughly $2^{20} \approx 1,000,000$ unique items.
- Averages estimates across thousands of registers using harmonic mean to eliminate outliers.

### 3. Count-Min Sketch (Frequency Estimation)
- A 2D array of counters ($d$ rows, $w$ columns) paired with $d$ hash functions.
- Used to identify "Heavy Hitters" (e.g., top-100 trending hashtags on Twitter, or top IP addresses in a DDoS attack).

## Trade-offs
| Data Structure | Query Capability | Memory Footprint | Accuracy Guarantee |
| :--- | :--- | :--- | :--- |
| **Exact Hash Set** | Exact Membership & Count | Massive ($O(N)$ RAM) | 100% Precise |
| **Bloom Filter** | Set Membership | Minimal ($O(1)$ fixed bits) | **Zero False Negatives; Tunable False Positives** |
| **HyperLogLog** | Distinct Count (Cardinality)| Tiny (1.5 KB in Redis) | **Standard Error $\approx 0.81 / \sqrt{m}$ (1%)** |
| **Count-Min Sketch** | Frequency Estimation | Fixed 2D table | May overestimate frequency (Never underestimates)|

## When to Use / When NOT to Use
### When to Use Probabilistic Data Structures
- Web crawlers checking visited URLs (Bloom Filter).
- Database storage engines checking SSTables before disk seeks (RocksDB/Cassandra Bloom filters).
- Analytics platforms tracking Monthly Active Users (Redis HyperLogLog `PFADD` / `PFCOUNT`).
- CDN DDoS mitigations tracking top IP request frequencies (Count-Min Sketch).

### When NOT to Use
- Financial transactions, security password verification, medical records where even a 0.01% false positive error is unacceptable.

## Real-World Examples
- **Google Chrome**: Originally used a Bloom filter to check whether a URL typed by a user was a known malicious phishing site before querying Google servers.
- **Redis HyperLogLog**: Commands `PFADD` and `PFCOUNT` consume exactly **12 KB of memory** per key, capable of estimating up to $2^{64}$ unique elements with a standard error of 0.81%.

## Common Pitfalls
- **Attempting Deletions in Standard Bloom Filters**: Deleting an item by setting bits to 0, which inadvertently deletes bits shared by dozens of other valid items (use a **Counting Bloom Filter** if deletions are required).
- **Under-sizing Bloom Filter Bit Arrays**: Under-allocating bits for anticipated capacity, causing the bit array to become saturated with 1s and driving the false positive rate up to 100%.

## Key Takeaways
- Use **Bloom Filters** to eliminate expensive disk seeks and database lookups for missing keys.
- Use **HyperLogLog** for massive unique count aggregations in fixed memory (1.5 KB - 12 KB).
- Bloom filters guarantee **zero false negatives**; false positives are tunable.

## Common Interview Questions
1. How does a Bloom filter guarantee that it will never produce a false negative?
2. How does HyperLogLog estimate 1 billion unique users using only 12 KB of memory?
3. How does RocksDB use Bloom filters to optimize read performance in LSM-trees?

## Further Reading
- [Burton H. Bloom: Space/Time Trade-offs in Hash Coding with Allowable Errors (1970)](https://dl.acm.org/doi/10.1145/362686.362692)
- [Flajolet et al.: HyperLogLog: The Analysis of a Near-Optimal Cardinality Estimation Algorithm (2007)](https://hal.archives-ouvertes.fr/hal-00406166/document)
