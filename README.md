# IAM Lab — Project 1: Active Directory Provisioning over LDAPS

## Context

This project is part of a personal IAM security lab built to develop hands-on
identity management skills. The goal is to simulate a real enterprise IAM 
environment — from directory setup to automated provisioning, SSO federation, 
and PKI — using open source tools only.

This first module focuses on the foundation of any IAM infrastructure: 
an Active Directory domain and automated user lifecycle management over a 
secure LDAP connection.

---

## What was built

- A Samba Active Directory domain (iam.lab) running in Docker
- Organizational Units: Users, Groups, ServiceAccounts
- A Python script that reads a CSV file and automatically:
  - Creates users in the correct OU
  - Assigns them to the right group based on their role
  - Generates a timestamped audit log of every action
- A secure LDAPS connection (port 636, TLS) between Python and Samba AD

---

## Architecture# IAM-LAB
users.csv → provisioning.py → LDAPS (port 636) → Samba AD (Docker)
|
OU=Users (users)
OU=Groups (GRP_Admins, GRP_Users)
OU=ServiceAccounts (service accounts)
---

## Technical choices and why

**Samba AD over Windows Server**
Using Samba AD in Docker makes the lab fully portable and free. 
The LDAP/LDAPS interface is identical to Microsoft Active Directory 
from a protocol perspective.

**LDAPS over plain LDAP**
Plain LDAP transmits credentials in cleartext — unacceptable even in a lab 
environment. We configured TLS on port 636 from the start.
Note: the current setup uses a self-signed certificate with ssl.CERT_NONE 
for validation. In production, this would use ssl.CERT_REQUIRED with a 
certificate signed by a trusted CA — which will be implemented in Project 2 
(PKI with OpenSSL).

**subprocess approach rejected**
An alternative approach was to call samba-tool via Python subprocess. 
This was rejected because LDAP is the actual protocol used by all 
real IAM platforms (SailPoint, Okta, Keycloak) to communicate with 
Active Directory. Using ldap3 directly is closer to production reality.

---

## Problems encountered

**--userou and --groupou path duplication**
Samba on this Docker image automatically appends DC=iam,DC=lab to 
any path passed via --userou or --groupou, causing a path duplication error.
Fix: pass only the relative OU path (e.g. OU=Users, not OU=Users,DC=iam,DC=lab).

**NTLM authentication rejected**
The ldap3 library with NTLM authentication caused session termination errors.
Fix: switched to SIMPLE authentication over LDAPS (encrypted channel makes 
SIMPLE auth acceptable).

**strongerAuthRequired on plain LDAP**
Samba rejected SIMPLE auth on port 389 with strongerAuthRequired.
Rather than disabling this security requirement (which would be a 
vulnerability), we moved to LDAPS on port 636 — the correct solution.

**Certificate verification failure**
The self-signed certificate could not be verified (unable to get local 
issuer certificate). This is expected since the cert is its own CA.
Current workaround: ssl.CERT_NONE in the lab. 
Proper fix: build a real CA — covered in Project 2.

---

## How to run

```bash
# Start Samba AD
docker run -d --name samba-ad --hostname dc1 --privileged \
  -e DOMAIN=IAM.LAB -e DOMAINPASS=Admin1234! -e DNSFORWARDER=8.8.8.8 \
  -p 389:389 -p 636:636 -p 445:445 -p 53:53/udp \
  nowsci/samba-domain

# Install dependency
pip3 install ldap3 --user

# Edit users.csv with users to provision
# Run the script
python3 provisioning.py
```

---

## Next step — Project 2: PKI with OpenSSL

The current LDAPS connection uses a self-signed certificate with no 
validation. Project 2 will build a proper PKI infrastructure:

- A Root CA
- An Intermediate CA
- A certificate issued for dc1.iam.lab and signed by the Intermediate CA
- LDAPS reconfigured with ssl.CERT_REQUIRED validating against our CA

This will make the LDAPS connection fully production-grade and demonstrate 
end-to-end certificate lifecycle management.
