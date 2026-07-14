# IAM Lab — Project 2: PKI Infrastructure with OpenSSL

## Context

Project 1 established an Active Directory and automated user provisioning 
over LDAPS, but used ssl.CERT_NONE — meaning the TLS certificate was never 
verified. This is a man-in-the-middle vulnerability: anyone could intercept 
the connection by presenting a fake certificate.

Project 2 builds a proper PKI infrastructure to fix this. The LDAPS 
connection now uses ssl.CERT_REQUIRED, validating the full certificate chain 
from dc1.iam.lab up to our Root CA.

---

## What was built

- A Root CA (4096-bit RSA, valid 10 years)
- An Intermediate CA signed by the Root CA (2048-bit RSA, valid 5 years)
- A server certificate for dc1.iam.lab signed by the Intermediate CA
- A full certificate chain file used by Python for LDAPS verification

---

## Architecture
Root CA (offline in production)
└── signs
Intermediate CA (operational CA)
└── signs
dc1.iam.lab (server certificate)
└── used by
Samba AD LDAPS (port 636)
└── verified by
Python provisioning script (ssl.CERT_REQUIRED)
---

## Technical choices and why

**Two-tier CA hierarchy instead of one**
A single Root CA signing everything directly is simpler but riskier. 
If the Root CA key is compromised, every certificate ever issued must 
be revoked. With an Intermediate CA, the Root CA stays offline — only 
the Intermediate CA is operational. If the Intermediate CA is compromised, 
we revoke it and create a new one without touching the Root CA.
This is how all public CAs operate (DigiCert, Let's Encrypt).

**4096-bit Root CA, 2048-bit Intermediate and server certs**
The Root CA uses 4096-bit RSA because it has a 10-year validity — 
longer validity requires stronger keys. Intermediate and server certs 
use 2048-bit because they have short validity periods (1-5 years) 
and need to be reissued regularly anyway.

**Subject Alternative Names (SAN) on the server certificate**
Modern TLS requires the server hostname to appear in the SAN extension,
not just the Common Name. We included both DNS.1=dc1.iam.lab and 
IP.1=127.0.0.1 — which is why Python connects via 127.0.0.1 
rather than localhost.

---

## Problems encountered

**Samba ignoring /etc/samba/tls/ certificates**
Samba on this Docker image stores its TLS certificates in 
/var/lib/samba/private/tls/ — not /etc/samba/tls/ as documented. 
The smb.conf tls parameters were being ignored because Samba was 
reading from its private directory directly.
Fix: copy certificates directly to /var/lib/samba/private/tls/

**Certificate ownership causing LDAP failure**
After copying the private key into the container, Samba refused to start
with: "invalid ownership of file key.pem: owned by uid 1000, should be 0"
This is a known security check (CVE-2013-4476) — Samba refuses to load
a private key not owned by root to prevent privilege escalation.
Fix: chown root:root + chmod 600 on the key file inside the container.

**hostname mismatch: localhost vs 127.0.0.1**
Python's ssl library matched the server address against the certificate SAN.
The certificate listed 127.0.0.1 (IP SAN) but Python was connecting to 
"localhost" (hostname) — these are not equivalent in TLS validation.
Fix: set AD_SERVER = "127.0.0.1" in provisioning.py.

---

## Certificate chain validation

```bash
openssl verify -CAfile certs/fullchain.crt certs/dc1.iam.lab.crt
# certs/dc1.iam.lab.crt: OK
```

---

## What is NOT committed to GitHub

Private keys (.key files) are never committed to version control.
In production, private keys would be stored in a HSM 
(Hardware Security Module) or a secrets manager like HashiCorp Vault
— which will be explored in Project 5.

---

## Next step — Project 4: Active Directory Audit with PowerShell

With a working AD and a secure LDAPS connection, the next step is to 
audit what we built — detecting excessive permissions, inactive accounts,
and misconfigured groups. This connects the technical infrastructure 
back to governance and compliance, bridging the GRC background with 
hands-on IAM engineering.
