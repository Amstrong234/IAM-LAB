# IAM Lab — Project 3: Keycloak SSO with Active Directory Federation

## Context

Projects 1 and 2 established a secure Active Directory with automated 
provisioning over LDAPS backed by a full PKI. Project 3 adds the SSO layer — 
a Keycloak Identity Provider that federates with our AD and exposes 
authentication to applications via OIDC and SAML.

This is the core of any enterprise IAM platform: a single authentication 
point that applications delegate to, rather than managing credentials 
themselves.

---

## What was built

- A custom Keycloak Docker image with our PKI Root CA and Intermediate CA 
  imported into the JVM truststore
- A Keycloak realm (IAM-LAB) federated with Samba AD via LDAPS (port 636)
- Group mapping: GRP_Admins and GRP_Users synced from AD into Keycloak
- An OIDC client (app-oidc) with group membership claims in JWT tokens
- A SAML client (app-saml) with IDP metadata exposed

---

## Architecture
Samba AD (alice, bob, charlie, diana, eric)
↓ LDAPS port 636 (PKI from Project 2)
Keycloak IAM-LAB realm
↓ JWT token (OIDC)          ↓ XML assertion (SAML)
app-oidc                     app-saml
groups: [GRP_Admins]         metadata: /protocol/saml/descriptor
---

## Technical choices and why

**Custom Docker image instead of runtime truststore configuration**
Keycloak 24 dropped support for the --spi-truststore-file parameter 
for PEM files and PKCS12 files created with certain tools. The only 
reliable approach was to import our CA certificates directly into the 
JVM cacerts truststore at image build time via keytool. This makes 
the trust configuration immutable and reproducible.

**Both Root CA and Intermediate CA imported**
Java's PKIX path builder requires the full chain to be present in the 
truststore — Root CA alone is not enough. It needs to find each 
intermediate certificate to build the path from the server certificate 
up to the trusted root.

**LDAP group filter: (|(cn=GRP_Admins)(cn=GRP_Users))**
Without filtering, Keycloak tried to sync all AD groups including 
system groups like Domain Admins whose members (Administrator) didn't 
exist yet in Keycloak — causing a GroupTreeResolveException. 
Filtering to only our custom groups solved this.

**Group membership mapper on app-oidc client scope**
Adding groups to the JWT token required a dedicated mapper on the 
client scope, not just on the realm. This is the standard pattern 
for per-application claims in Keycloak.

---

## Problems encountered

**SSLHandshakeFailed despite truststore configuration**
Keycloak ignored multiple truststore configuration approaches 
(--spi-truststore-file, volume mounts, runtime imports) because 
the container was recreated each time, losing changes. 
Fix: build a custom Docker image with keytool import baked in.

**trustAnchors parameter must be non-empty**
Only the Root CA was imported initially — Java could not build 
the certificate chain to dc1.iam.lab because the Intermediate CA 
was missing from the truststore.
Fix: import both Root CA and Intermediate CA in the Dockerfile.

**Group sync failure: GroupTreeResolveException**
Syncing all AD groups caused failures on system groups with 
unresolved member references.
Fix: LDAP filter restricted to GRP_Admins and GRP_Users only.

**Data persistence lost on container restart**
Keycloak's default H2 database is in-memory — realm configuration 
was lost on every container restart.
Fix: mount a persistent volume at /opt/keycloak/data.

---

## JWT token output (alice.martin)

After authentication, alice's JWT contains:
- Identity from AD: name, email, username
- Group membership: GRP_Admins
- Issuer: Keycloak IAM-LAB realm
- Expiry: 5 minutes (access token)

---

## How to run

```bash
# Start Samba AD
docker start samba-ad

# Start Keycloak with persistent data
docker run -d --name keycloak \
  --link samba-ad:dc1.iam.lab \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=Admin1234! \
  -v ~/iam-lab/projet3-keycloak/keycloak-data:/opt/keycloak/data \
  -p 8080:8080 \
  keycloak-iam-lab \
  start-dev
```

---
## Next step — Project 4: Active Directory Audit with PowerShell

With a fully operational IAM infrastructure, Project 4 audits what 
we built — detecting excessive permissions, inactive accounts, and 
misconfigured group memberships. This bridges the technical 
infrastructure with governance and compliance, directly connecting 
to the NIS2 GRC background from the internship.
