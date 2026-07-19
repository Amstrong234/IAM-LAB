FROM quay.io/keycloak/keycloak:24.0.0

USER root

COPY root-ca.crt /tmp/root-ca.crt
COPY intermediate-ca.crt /tmp/intermediate-ca.crt

RUN keytool -importcert \
  -alias iam-lab-root-ca \
  -file /tmp/root-ca.crt \
  -keystore /usr/lib/jvm/java-17-openjdk-17.0.14.0.7-2.el9.x86_64/lib/security/cacerts \
  -storepass changeit \
  -noprompt

RUN keytool -importcert \
  -alias iam-lab-intermediate-ca \
  -file /tmp/intermediate-ca.crt \
  -keystore /usr/lib/jvm/java-17-openjdk-17.0.14.0.7-2.el9.x86_64/lib/security/cacerts \
  -storepass changeit \
  -noprompt

USER keycloak
