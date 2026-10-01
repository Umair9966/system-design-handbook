# Secrets Management and Password Hashing

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
