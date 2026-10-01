# Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC)

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
| **Logic** | User $	o$ Role $	o$ Permission | Policy evaluates attributes dynamically |
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
