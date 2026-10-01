import os

base_dir = r"C:\Users\Ateeb\.gemini\antigravity-ide\scratch\system-design-handbook\docs\12-security"

files = {
    "01-authentication-and-authorization.md": """# Authentication and Authorization

Authentication (AuthN) and Authorization (AuthZ) are the foundational identity and access pillars of modern distributed systems.

```mermaid
graph LR
    subgraph "Authentication (AuthN)"
        User[User / Client] -->|Credentials: Password / MFA / Cert| AuthN[Who are you?]
        AuthN -->|Verifies identity| Identity[Verified Identity: User 42]
    end

    subgraph "Authorization (AuthZ)"
        Identity --> AuthZ[What are you allowed to do?]
        AuthZ -->|Evaluates policies| Access{Permitted to DELETE /orders/99?}
        Access -->|Allow| Svc[Resource Service]
        Access -->|Deny| 403[HTTP 403 Forbidden]
    end
```

---

## 1. AuthN vs AuthZ: The Critical Distinction

| Dimension | Authentication (AuthN) | Authorization (AuthZ) |
| :--- | :--- | :--- |
| **Core Question** | "Who are you?" | "What are you permitted to do?" |
| **Mechanisms** | Passwords, Passkeys (WebAuthn), TOTP MFA, X.509 client certs | RBAC, ABAC, ACLs, OAuth scopes |
| **Failure Code** | `HTTP 401 Unauthorized` | `HTTP 403 Forbidden` |
| **Transmission** | `Authorization: Bearer <token>` or mTLS cert | JWT claims, Policy Engine (OPA), Database ACL |
| **Execution Point**| Edge Gateway / Identity Provider | Application Service / Resource Layer |

---

## 2. Stateless Tokens (JWT) vs Stateful Sessions (Redis)

```mermaid
graph TD
    subgraph "Stateful Session Model"
        C1[Client] -->|Cookie: session_id=xyz| G1[Server]
        G1 -->|Network Roundtrip: 2ms| R1[(Redis Session Store)]
        R1 --> G1
        Note over R1: Instant Revocation: Delete 'xyz'
    end

    subgraph "Stateless JWT Model"
        C2[Client] -->|Header: Bearer eyJhbGci...| G2[Server / Gateway]
        G2 -->|In-Memory Cryptographic Signature Check: <0.1ms| G2
        Note over G2: Zero Database Lookups! Hard to revoke before expiry.
    end
```

---

## 3. Best Practices in Modern Architectures

1. **Short-Lived Access Tokens**: Keep JWT lifetimes to 10-15 minutes to minimize exposure if stolen.
2. **Refresh Token Rotation**: Store refresh tokens in HTTP-only, Secure, SameSite cookies. Invalidate the entire refresh token family if a revoked token is reused.
3. **Decentralized Validation**: Edge API Gateways verify JWT signatures and extract claims, injecting trusted headers (`X-User-Id`, `X-User-Roles`) into downstream microservices.

---

## 4. Key Takeaways

- Authentication establishes identity; Authorization governs permissions.
- Return `401 Unauthorized` when identity is missing or unverified, and `403 Forbidden` when the authenticated identity lacks permissions.
- Combine short-lived stateless JWTs with stateful refresh tokens for the optimal balance of performance and security control.
""",

    "02-oauth2-and-oidc.md": """# OAuth 2.0 and OpenID Connect (OIDC)

OAuth 2.0 is the industry-standard protocol for delegated authorization. OpenID Connect (OIDC) is an identity layer built directly on top of OAuth 2.0 to provide single sign-on (SSO) and user authentication.

```mermaid
sequenceDiagram
    autonumber
    participant User as End User (Browser)
    participant Client as Client Application (SPA / Mobile)
    participant AuthServer as Authorization Server (IdP / Okta)
    participant API as Resource Server (Backend API)

    User->>Client: Clicks "Login with Google"
    Client->>Client: Generates PKCE code_verifier & code_challenge
    Client->>AuthServer: Redirects: /authorize?response_type=code&client_id=...&code_challenge=...
    User->>AuthServer: Authenticates & Approves Scopes
    AuthServer-->>Client: Redirects back with Authorization Code
    Client->>AuthServer: POST /token (Code + code_verifier)
    AuthServer->>AuthServer: Verifies code & hashes verifier against challenge
    AuthServer-->>Client: Returns ID Token (OIDC) + Access Token + Refresh Token
    Client->>API: GET /api/profile (Header: Bearer <access_token>)
    API-->>Client: 200 OK (User Data)
```

---

## 1. OAuth 2.0 Tokens: ID Token vs Access Token

- **ID Token (OIDC)**: A JWT formatted for the **Client Application**. Contains user profile claims (`sub`, `email`, `name`, `iss`, `exp`). Verifies *who logged in*.
- **Access Token (OAuth 2.0)**: A credential (JWT or opaque) formatted for the **Resource Server (API)**. Authorizes access to specific scopes (`read:orders`, `write:payments`).
- *Golden Rule*: The backend API must **never** accept an ID Token to authorize API requests!

---

## 2. Authorization Code Flow with PKCE (Proof Key for Code Exchange)

PKCE (RFC 7636) prevents authorization code interception attacks on public clients (mobile apps, single-page apps) that cannot safely store a client secret.

### PKCE Mechanics:
1. Client creates random secret: `code_verifier` (43-128 chars).
2. Client hashes it: `code_challenge = BASE64URL(SHA256(code_verifier))`.
3. Client sends `code_challenge` in authorization request.
4. Client trades code for tokens by sending the raw `code_verifier`.
5. IdP verifies that `SHA256(code_verifier) == code_challenge`. Stolen authorization codes are useless without the raw verifier.

---

## 3. Key Takeaways

- Use Authorization Code Flow with PKCE for all web, mobile, and desktop applications.
- Use Client Credentials Flow strictly for machine-to-machine server communication.
- ID Tokens authenticate the user to the frontend; Access Tokens authorize API calls to backends.
""",

    "03-rbac-and-abac.md": """# Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC)

Access control models dictate how systems grant or deny requests to resources based on identities, roles, and contextual attributes.

```mermaid
graph TD
    subgraph "RBAC (Role-Based)"
        User[User: Alice] --> Role[Role: Billing Admin]
        Role --> P1[Perm: read:invoices]
        Role --> P2[Perm: refund:invoices]
    end

    subgraph "ABAC (Attribute-Based Policy Engine)"
        Context[Context: User, Resource, Time, Location] --> Engine{Policy Engine (OPA / Cedar)}
        Engine -->|Rule: User.dept == Resource.dept AND Time between 9-17| Decision[ALLOW / DENY]
    end
```

---

## 1. RBAC vs ABAC Comparison

| Dimension | RBAC (Role-Based) | ABAC (Attribute-Based) |
| :--- | :--- | :--- |
| **Logic** | User $\to$ Role $\to$ Permission | Policy evaluates attributes dynamically |
| **Complexity** | Simple, easy to model in relational tables | Complex, requires dedicated policy engine |
| **Granularity** | Coarse-grained | Extremely fine-grained |
| **Role Explosion** | High (e.g. `US_Billing_Editor_Weekend`) | Zero (attributes handle conditional rules) |
| **Evaluation Performance**| Ultra-fast bitmask / lookup ($O(1)$) | Requires policy evaluation engine ($O(N)$) |

---

## 2. Open Policy Agent (OPA) and Rego

Modern cloud-native systems decouple authorization logic from application code using OPA:

```rego
package authz

default allow = false

# Allow if user is an admin
allow {
    input.user.role == "admin"
}

# Allow doctors to view patient records in their own department during business hours
allow {
    input.user.role == "doctor"
    input.action == "read"
    input.resource.type == "medical_record"
    input.user.department == input.resource.department
    input.request_time.hour >= 8
    input.request_time.hour <= 18
}
```

---

## 3. Key Takeaways

- Start with RBAC for early-stage and standard enterprise applications.
- Graduate to ABAC or Policy-as-Code (OPA / AWS Cedar) when fine-grained, contextual, or multi-tenant attributes govern permissions.
- Never hardcode permission checks into frontend code; backends must unconditionally validate every action.
""",

    "04-encryption-at-rest-and-in-transit.md": """# Encryption at Rest and in Transit

Data security requires end-to-end protection against eavesdropping, physical theft, man-in-the-middle (MitM) attacks, and unauthorized database access.

```mermaid
graph LR
    Client[Client Browser] -->|TLS 1.3 (In-Transit)| Edge[Cloudflare / Cloud WAF]
    Edge -->|mTLS (In-Transit)| App[Application Service]
    App -->|Envelope Encryption: AES-256-GCM| KMS[KMS / Vault]
    App -->|Encrypted Ciphertext| DB[(Encrypted Database at Rest)]
```

---

## 1. Encryption in Transit: Modern TLS 1.3

- **TLS 1.3**: Reduces handshake latency from 2 round-trips to **1-RTT** (or 0-RTT resumption), and completely removes vulnerable legacy ciphers (RC4, 3DES, CBC mode).
- **Forward Secrecy (PFS)**: Uses ephemeral Diffie-Hellman keys (`ECDHE`). Even if the server's private master key is compromised in the future, past recorded encrypted traffic cannot be decrypted.

---

## 2. Encryption at Rest & Envelope Encryption

Directly storing master encryption keys alongside encrypted data is fatal. Production architectures use **Envelope Encryption**:

```mermaid
sequenceDiagram
    autonumber
    participant App as Application Service
    participant KMS as AWS KMS / Vault
    participant DB as Database / S3 Storage

    App->>KMS: GenerateDataKey(MasterKeyId)
    KMS-->>App: Plaintext Data Key + Ciphertext Data Key (Encrypted under Root KMS Key)
    Note over App: 1. Encrypts user data with Plaintext Data Key (AES-256-GCM)
    Note over App: 2. Erases Plaintext Data Key from RAM memory immediately!
    App->>DB: Stores Encrypted Data + Ciphertext Data Key
    
    Note over App,DB: Decryption Flow:
    App->>KMS: Decrypt(Ciphertext Data Key)
    KMS-->>App: Plaintext Data Key
    Note over App: Decrypts data, then wipes key from RAM!
```

---

## 3. Key Takeaways

- Enforce TLS 1.3 with Perfect Forward Secrecy for all external and internal network communication.
- Use Envelope Encryption (KMS) so root master keys never leave dedicated Hardware Security Modules (HSMs).
- Secure sensitive columns (SSNs, credit cards) with Application-Layer Encryption before persisting to disk.
""",

    "05-secrets-management-and-password-hashing.md": """# Secrets Management and Password Hashing

Hardcoded API keys, exposed database passwords, and obsolete password hashing algorithms (MD5, SHA1) are leading causes of severe data breaches.

```mermaid
graph TD
    subgraph "Dangerous Anti-Pattern"
        Code[Git Repo / Source Code] --> Hardcoded[Hardcoded API Key / DB Password]
        Hardcoded --> Leak[Committed to Public GitHub -> Compromised in Seconds!]
    end

    subgraph "Production Secrets Management"
        Pod[App Container] --> Agent[Vault / AWS Secrets Manager Agent]
        Agent --> DynamicCreds[Short-Lived Ephemeral Database Credentials (1h TTL)]
        DynamicCreds --> DB[(PostgreSQL)]
        Agent --> AutoRotate[Automated Credential Rotation every 30 days]
    end
```

---

## 1. Password Hashing: Argon2id, bcrypt, and PBKDF2

General cryptographic hash functions (SHA-256, SHA-512) are designed to be extremely fast. On modern GPUs, attackers can calculate billions of SHA-256 hashes per second, cracking passwords via brute-force within hours.

### Password Hashes Must Be Slow and Memory-Hard:
1. **Argon2id (Winner of Password Hashing Competition)**: The gold standard. Resists both GPU and ASIC parallel cracking by requiring significant RAM allocation per hash.
2. **bcrypt**: Battle-tested industry standard with adjustable work factor (cost). Recommended cost $\ge 12$.
3. **Always Use Unique Salts**: Random 16-byte salt per user prevents Rainbow Table attacks.

---

## 2. Secrets Management Best Practices

- **Never Commit Secrets to Git**: Use pre-commit hooks (`gitleaks`, `trufflehog`) to block secrets from reaching repositories.
- **Dynamic Ephemeral Credentials**: HashiCorp Vault generates temporary database credentials with 1-hour TTLs; compromised credentials expire automatically.
- **Secrets Injection**: Inject secrets into memory via environment variables or in-memory mounted volumes (`/dev/shm`), never writing them to persistent container disks.

---

## 3. Key Takeaways

- Always hash passwords with Argon2id or bcrypt (cost $\ge 12$) with a unique cryptographic salt.
- Never store secrets in source code, Docker images, or unencrypted config files.
- Automate secrets rotation and use short-lived ephemeral credentials.
""",

    "06-owasp-top-risks-for-system-design.md": """# OWASP Top Risks for System Architecture

Security must be designed into distributed architectures from inception rather than bolted on after deployment.

```mermaid
graph TD
    OWASP[Critical Architectural Vulnerabilities]
    OWASP --> BOLA[1. BOLA / IDOR: Broken Object Level Authorization]
    OWASP --> Inj[2. Injection: SQL, NoSQL, Command Injection]
    OWASP --> SSRF[3. SSRF: Server-Side Request Forgery]
    OWASP --> BrokenAuth[4. Broken Authentication & Session Hijacking]
    OWASP --> Misconfig[5. Security Misconfiguration & Default Passwords]
```

---

## 1. Broken Object Level Authorization (BOLA / IDOR)

The #1 vulnerability in modern APIs. An attacker manipulates an ID in an API request to view or modify someone else's data:

```http
GET /api/v1/accounts/10042/statements HTTP/1.1
Authorization: Bearer <AttackerToken (Account 9999)>
```

### Architectural Defense:
Enforce tenant and user ownership checks at the data layer or via ORM middleware:
```sql
SELECT * FROM statements 
WHERE id = :statement_id 
  AND user_id = :authenticated_user_id; -- MUST BE ENFORCED!
```

---

## 2. Server-Side Request Forgery (SSRF)

An attacker tricks a backend server into making requests to internal infrastructure (e.g., AWS metadata endpoint `169.254.169.254` or internal microservices):

```mermaid
graph LR
    Attacker[Attacker] -->|POST /convert-pdf?url=http://169.254.169.254/latest/meta-data/| WebApp[Vulnerable Web App]
    WebApp -->|Internal Request| AWSMeta[AWS Instance Metadata Service]
    AWSMeta -->>WebApp: Returns IAM Secret Keys!
    WebApp -->>Attacker: Leaks Cloud Admin Credentials!
```

### Defenses:
- Use AWS IMDSv2 (requires session token header, blocking simple SSRF).
- Resolve DNS and block private RFC-1918 IP addresses (`10.0.0.0/8`, `127.0.0.1`, `172.16.0.0/12`, `192.168.0.0/16`).

---

## 3. Key Takeaways

- BOLA is mitigated by strictly binding all database queries to the authenticated session context.
- Prevent SSRF by validating destination URLs against a strict allowlist and blocking private IP routing.
- Use parameterized queries and prepared statements exclusively to eliminate SQL injection.
""",

    "07-ddos-mitigation-and-waf.md": """# DDoS Mitigation and Web Application Firewalls (WAF)

Distributed Denial of Service (DDoS) attacks attempt to exhaust network bandwidth, connection state tables, or application compute capacity.

```mermaid
graph TD
    Attackers[Botnet / Attack Traffic] --> Edge[Anycast Edge Network: Cloudflare / CloudFront]
    Edge --> L34[Layer 3/4 Scrubbing: SYN Flood, UDP Amplification]
    L34 --> WAF[Layer 7 WAF: Rate Limiting, Bot Detection, Managed Rules]
    WAF --> CleanTraffic[Clean Traffic]
    CleanTraffic --> Origin[Origin Application Servers]
```

---

## 1. Layers of DDoS Attacks

- **Layer 3 / 4 (Network & Transport)**:
  - *SYN Flood*: Floods server with TCP SYN packets without completing the 3-way handshake, exhausting kernel backlog connection queues.
  - *UDP Amplification*: Spoofs victim IP and sends requests to vulnerable open DNS/NTP servers, generating 50x amplified response floods.
  - *Mitigation*: Anycast BGP routing distributes floods across hundreds of global PoPs; SYN cookies absorb incomplete handshakes.
- **Layer 7 (Application Layer)**:
  - *HTTP Flood*: High-volume legitimate-looking `GET` or `POST` requests targeting heavy database search queries.
  - *Slowloris*: Sends HTTP headers extremely slowly (1 byte every 10 seconds), keeping server worker sockets open indefinitely until thread pools exhaust.
  - *Mitigation*: Web Application Firewalls (WAF), CAPTCHA challenges, strict socket read timeouts, and IP reputation scores.

---

## 2. Web Application Firewall (WAF) Architecture

WAFs inspect incoming HTTP traffic before it reaches origin servers:
1. **Signature-Based Inspection**: Blocks known SQL injection patterns (`UNION SELECT`) and cross-site scripting (`<script>`).
2. **Rate Limiting Rules**: Automatically block or challenge IPs exceeding 100 requests per minute to sensitive endpoints (`/login`, `/checkout`).
3. **Geo-Blocking & ASN Filtering**: Blocks traffic originating from unauthorized countries or suspicious data center ASNs.

---

## 3. Key Takeaways

- Absorb Layer 3 and 4 floods at the edge using Anycast and cloud scrubbing networks.
- Protect expensive Layer 7 endpoints with WAF rate limiting and managed rulesets.
- Enforce strict connection and read timeouts on reverse proxies to neutralize Slowloris attacks.
""",

    "08-zero-trust-and-mtls.md": """# Zero Trust Architecture and Mutual TLS (mTLS)

Traditional perimeter security ("Castle and Moat") assumes that anything inside the internal corporate or cloud network is trusted. Zero Trust replaces this with: **"Never trust, always verify."**

```mermaid
graph TD
    subgraph "Legacy Castle-and-Moat (Vulnerable)"
        Hacker[Attacker breaches VPN / Perimeter] --> Net[Internal Flat Network]
        Net --> S1[Service A: Unencrypted HTTP]
        Net --> S2[Service B: Unauthenticated DB]
        Note over Net: Attacker moves laterally across all systems!
    end

    subgraph "Zero Trust Architecture"
        Client1[Service A] -->|mTLS + SPIFFE Identity Check| Srv1[Service B]
        Note over Srv1: Every single packet is encrypted and mutually authenticated!
    end
```

---

## 1. The Core Tenets of Zero Trust

1. **Verify Explicitly**: Authenticate and authorize based on all available data points (identity, location, device health, service credentials).
2. **Least Privilege Access**: Grant access with Just-In-Time (JIT) and Just-Enough-Access (JEA) policies.
3. **Assume Breach**: Minimize blast radius by segmenting networks, encrypting all traffic internally, and continuously monitoring telemetry.

---

## 2. Mutual TLS (mTLS) Deep Dive

In standard HTTPS, only the server proves its identity with an X.509 certificate. In **Mutual TLS (mTLS)**, both the client and server present and verify certificates:

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Microservice (Envoy)
    participant CA as Internal CA (Vault / Istio Citadel)
    participant Server as Server Microservice (Envoy)

    Client->>CA: Requests short-lived cert with SPIFFE ID: spiffe://cluster/ns/prod/sa/order-service
    Server->>CA: Requests short-lived cert with SPIFFE ID: spiffe://cluster/ns/prod/sa/payment-service
    
    Client->>Server: ClientHello
    Server-->>Client: ServerHello + Server Certificate
    Client->>Client: Verifies Server Cert against Root CA
    Server->>Client: CertificateRequest
    Client-->>Server: Client Certificate
    Server->>Server: Verifies Client Cert + Checks SPIFFE ID in authorization policy
    Note over Client,Server: Mutual Trust Established -> Encrypted TLS 1.3 Channel
```

---

## 3. Key Takeaways

- Perimeter-only security is obsolete; internal networks must be assumed compromised.
- Implement mTLS via service meshes (Istio, Linkerd) to automate certificate rotation and encryption without touching application code.
- Enforce authorization policies based on cryptographic identities (SPIFFE/SPIRE).
""",

    "09-privacy-compliance-and-abuse-prevention.md": """# Privacy, Compliance, and Abuse Prevention

Modern architectures must comply with global data privacy regulations (GDPR, CCPA, HIPAA) and proactively detect fraudulent abuse.

```mermaid
graph TD
    UserReq[User Request: GDPR "Right to be Forgotten"] --> PrivacySvc[Privacy Orchestration Service]
    PrivacySvc --> UserDB[(User Relational DB: Delete / Anonymize)]
    PrivacySvc --> Logs[(Elasticsearch Logs: Scrub PII)]
    PrivacySvc --> S3[(Backups / S3 Data Lake: Crypto-Shredding)]
```

---

## 1. GDPR & CCPA Compliance Architecture

- **Right to Access (SAR)**: System must export all stored user data in a portable machine-readable format (JSON/CSV).
- **Right to be Forgotten (Erasure)**: Deleting user data across distributed shards, event streams, and immutable backups.

### The Crypto-Shredding Pattern for Immutable Storage:
Deleting individual user rows from append-only immutable backups (S3 Glacier, Kafka logs) is virtually impossible.
- **Solution**: Encrypt each user's personally identifiable information (PII) with a **dedicated per-user encryption key**.
- When the user exercises their right to be forgotten: **Destroy the user's encryption key**.
- The encrypted data in backups and Kafka logs becomes mathematically unrecoverable gibberish, fulfilling GDPR erasure requirements!

---

## 2. Abuse Prevention and Fraud Detection

```mermaid
graph LR
    Action[User Action: Login / Post / Checkout] --> Engine[Fraud & Risk Engine]
    Engine --> Check1[Device Fingerprinting]
    Engine --> Check2[Velocity Check: 10 orders/sec?]
    Engine --> Check3[IP Reputation / VPN Detection]
    Engine --> Decision{Risk Score}
    Decision -->|Low (<20)| Allow[Allow Action]
    Decision -->|Medium (20-70)| Challenge[Step-Up MFA / CAPTCHA]
    Decision -->|High (>70)| Block[Block & Flag Account]
```

### Abuse Mitigation Vectors:
1. **Velocity Limits**: Detect bot account creation or coupon abuse using Redis sliding-window counters.
2. **Device Fingerprinting**: Canvas hash, audio context, and browser hardware signatures identify multi-account fraudsters.
3. **Graph Analysis**: Detect botnets and payment fraud rings using graph databases (Neo4j) to uncover shared credit cards and IP addresses across thousands of accounts.

---

## 3. Key Takeaways

- Implement Crypto-Shredding to achieve GDPR erasure compliance on immutable logs and backups.
- Store sensitive PII in dedicated, isolated databases with audited access logs.
- Defend against automated abuse with risk-based multi-factor challenges and velocity rate limiters.
"""
}

for fname, content in files.items():
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {fname}")

print("Section 12 complete.")
