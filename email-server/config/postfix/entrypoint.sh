#!/bin/bash
set -e

# Substitute environment variables into config files
sed -i "s|mail.example.com|${MAIL_HOSTNAME}|g" /etc/postfix/main.cf
sed -i "s|example.com|${MAIL_DOMAIN}|g" /etc/postfix/main.cf

# Update SQL lookup credentials from environment
for f in /etc/postfix/sql/*.cf; do
    sed -i "s|^hosts = .*|hosts = ${DB_HOST}|" "$f"
    sed -i "s|^dbname = .*|dbname = ${DB_NAME}|" "$f"
    sed -i "s|^user = .*|user = ${DB_USER}|" "$f"
    sed -i "s|^password = .*|password = ${DB_PASSWORD}|" "$f"
done

# Generate self-signed cert if Let's Encrypt not yet available
CERT_DIR="/etc/letsencrypt/live/${MAIL_HOSTNAME}"
if [ ! -f "${CERT_DIR}/fullchain.pem" ]; then
    echo "No TLS cert found — generating self-signed certificate..."
    mkdir -p "${CERT_DIR}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${CERT_DIR}/privkey.pem" \
        -out "${CERT_DIR}/fullchain.pem" \
        -subj "/CN=${MAIL_HOSTNAME}" 2>/dev/null
fi

echo "Starting Postfix..."
exec postfix start-fg
