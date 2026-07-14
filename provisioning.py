import csv
import logging
from datetime import datetime
from ldap3 import Server, Connection, ALL, SIMPLE, MODIFY_ADD, Tls
import ssl

# Configuration
AD_SERVER = "localhost"
AD_PORT = 636
AD_USER = "CN=Administrator,CN=Users,DC=iam,DC=lab"
AD_PASSWORD = "Admin1234!"
USERS_OU = "OU=Users,DC=iam,DC=lab"
GROUPS = {
    "admin": "CN=GRP_Admins,CN=Users,DC=iam,DC=lab",
    "user": "CN=GRP_Users,CN=Users,DC=iam,DC=lab"
}

# Logging
logging.basicConfig(
    filename=f"logs/provisioning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def connect_ad():
    tls = Tls(
        validate=ssl.CERT_NONE
    )
    server = Server(AD_SERVER, port=AD_PORT, use_ssl=True, tls=tls, get_info=ALL)
    conn = Connection(
        server,
        user=AD_USER,
        password=AD_PASSWORD,
        authentication=SIMPLE,
        auto_bind=True
    )
    logging.info("Connexion LDAPS établie")
    print("[OK] Connexion LDAPS établie")
    return conn

def create_user(conn, firstname, lastname, email, role):
    username = f"{firstname.lower()}.{lastname.lower()}"
    user_dn = f"CN={firstname} {lastname},{USERS_OU}"

    attributes = {
        "objectClass": ["top", "person", "organizationalPerson", "user"],
        "cn": f"{firstname} {lastname}",
        "sAMAccountName": username,
        "userPrincipalName": f"{username}@iam.lab",
        "givenName": firstname,
        "sn": lastname,
        "mail": email,
        "userAccountControl": 512
    }

    success = conn.add(user_dn, attributes=attributes)

    if success:
        logging.info(f"Utilisateur créé : {username} ({role})")
        print(f"[OK] Utilisateur créé : {username}")
        assign_group(conn, username, role, user_dn)
    else:
        logging.error(f"Echec création {username} : {conn.result}")
        print(f"[ERREUR] {username} : {conn.result['description']}")

def assign_group(conn, username, role, user_dn):
    group_dn = GROUPS.get(role)
    if not group_dn:
        logging.warning(f"Rôle inconnu : {role}")
        return

    conn.modify(group_dn, {"member": [(MODIFY_ADD, [user_dn])]})

    if conn.result["result"] == 0:
        logging.info(f"{username} ajouté au groupe {role}")
        print(f"[OK] {username} → groupe {role}")
    else:
        logging.error(f"Echec ajout groupe {username} : {conn.result}")
        print(f"[ERREUR] groupe {username} : {conn.result['description']}")

def main():
    print("=== Démarrage provisioning IAM ===")
    logging.info("=== Démarrage provisioning ===")

    conn = connect_ad()

    with open("users.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            create_user(
                conn,
                row["firstname"],
                row["lastname"],
                row["email"],
                row["role"]
            )

    conn.unbind()
    logging.info("=== Provisioning terminé ===")
    print("=== Provisioning terminé ===")

if __name__ == "__main__":
    main()
