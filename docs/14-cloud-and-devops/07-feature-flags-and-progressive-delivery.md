# Feature Flags and Progressive Delivery

Progressive Delivery decouples code deployment from feature release. Deploying code to production is an engineering event; releasing functionality to users is a business decision.

```mermaid
graph LR
    Deploy[Deploy Code to Production (Flags Off)] --> Internal[1. Internal Employees (Dogfooding)]
    Internal --> Beta[2. Beta Testers (1%)]
    Beta --> Canary[3. Canary Percentage Rollout (10% -> 50%)]
    Canary --> GA[4. General Availability (100%)]
    Canary -.->|Anomaly Detected!| KillSwitch[Emergency Kill Switch: 0% Instantly]
```

---

## 1. Feature Flag Architecture

Feature flag evaluations must happen in-memory in microseconds without making a remote network call per evaluation:

```mermaid
graph TD
    Dashboard[LaunchDarkly / Unleash Admin Dashboard] --> FlagStream[SSE / WebSocket Config Stream]
    FlagStream --> LocalCache[In-Memory Flag Cache inside App SDK]
    AppCode[Incoming User Request] --> Eval[SDK.evaluate('new-ui', userContext)]
    Eval --> LocalCache
    LocalCache -->|0.001ms In-Memory Hash| Decision{Flag Enabled?}
```

---

## 2. Contextual Targeting and Gradual Rollouts

Feature flags use deterministic hashing (e.g., MurmurHash3) to ensure a user consistently receives the same feature experience:

$$	ext{Bucket} = 	ext{MurmurHash3}(	ext{user\_id} + "	ext{new\_checkout}") \pmod{100}$$

If the rollout percentage is set to 25%, any user whose hash bucket is $< 25$ receives the new feature. As the slider increases to 50%, previously enabled users remain enabled without state synchronization.

---

## 3. Managing Technical Debt of Stale Flags

Feature flags are short-term loans. If not removed, they turn codebases into tangled spaghetti:
1. **Flag Expiration / TTLs**: Assign every flag an owner and an expiration date (e.g., 30 days after 100% rollout).
2. **Automated Flag Cleanup**: Use static analysis tools (e.g., Uber's Piranha) to automatically generate pull requests that delete obsolete feature flag if/else statements.

---

## 4. Key Takeaways

- Decouple deployment from release using feature flags to minimize deployment risk.
- Evaluate flags locally in memory; never make synchronous HTTP calls to feature flag servers in the request path.
- Treat feature flags as technical debt and schedule automated pruning after general release.
