# Design a Travel Search Aggregator (Kayak / Skyscanner)

A distributed travel search engine that aggregates real-time flight, hotel, and car rental prices from hundreds of third-party airline APIs and Global Distribution Systems (GDS: Amadeus, Sabre), handling high supplier latency and volatile pricing.

```mermaid
graph TD
    User[Traveler: NYC to LON on Oct 10] --> API[Search Aggregator Gateway]
    API --> Cache[(Aggregated Flight Price Cache: Redis)]
    
    API --> FanoutWorker[Supplier Fanout Dispatcher]
    
    par Parallel Supplier Queries (with 2-second deadline!)
        FanoutWorker --> Delta[Delta Airlines API]
        FanoutWorker --> United[United Airlines API]
        FanoutWorker --> BA[British Airways API]
        FanoutWorker --> GDS[Sabre / Amadeus GDS]
    end

    Delta --> StreamAgg[Streaming Aggregator / WebSockets]
    United --> StreamAgg
    BA --> StreamAgg
    GDS --> StreamAgg

    StreamAgg --> User
```

---

## 1. Requirements

### Functional Requirements:
1. Search round-trip and one-way flights across hundreds of airlines.
2. Filter and sort by price, duration, stops, and airline.
3. Stream results progressively to user browser as airlines respond.
4. Booking handoff: Redirect user to airline booking portal with verified pricing.

### Non-Functional Requirements:
- **Resilience to Slow Downstreams**: Airline partner APIs take 2-8 seconds to respond. Aggregator must never hang waiting for slow partners.
- **Massive Fanout**: A single user query spawns 50+ external HTTP requests.
- **Price Accuracy**: Prevent showing obsolete cached prices when flights sell out.

---

## 2. Progressive Streaming Search (WebSockets / SSE)

Waiting 8 seconds for all 50 airlines to respond before rendering the page results in high user bounce rates.

### The Progressive Streaming Pattern:
1. Client initiates search: `POST /api/v1/flight-searches`.
2. Gateway immediately opens a **Server-Sent Events (SSE)** or **WebSocket** connection.
3. Instant Response: Deliver cached flight estimates from Redis within **50ms**.
4. As individual airlines respond (at 500ms, 1.2s, 2.5s), stream newly discovered flight fares directly to the browser.
5. Strict Deadline: Cut off slow airline queries at $T = 3.0	ext{ seconds}$ and finalize the search.

---

## 3. Caching Strategy for Volatile Airline Pricing

- Flight prices and seat availability change dynamically based on airline revenue management algorithms.
- **TTL Strategy**:
  - Hot routes (e.g., NYC to LON next week): 5-minute cache TTL.
  - Distant routes (e.g., flight 9 months away): 6-hour cache TTL.
- **Price Verification Step**: Before final redirect to booking, execute a synchronous real-time price check to confirm the fare is still available.

---

## 4. Key Takeaways

- Stream search results progressively using Server-Sent Events (SSE) or WebSockets to display instant results.
- Implement strict client deadlines (timeouts) on external supplier fanout calls.
- Apply dynamic cache TTLs based on departure date proximity and route popularity.
