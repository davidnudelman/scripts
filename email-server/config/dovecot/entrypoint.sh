#!/bin/bash
set -e

# Substitute hostname in config
sed -i "s|mail.example.com|${MAIL_HOSTNAME}|g" /etc/dovecot/dovecot.conf

# Update SQL credentials from environment
SQL_CONF="/etc/dovecot/sql/dovecot-sql.conf"
sed -i "s|host=postgres|host=${DB_HOST}|" "$SQL_CONF"
sed -i "s|dbname=mailserver|dbname=${DB_NAME}|" "$SQL_CONF"
sed -i "s|user=mailuser|user=${DB_USER}|" "$SQL_CONF"
sed -i "s|password=changeme|password=${DB_PASSWORD}|" "$SQL_CONF"

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

# Ensure mailbox directory exists and has correct ownership
mkdir -p /var/mail/vhosts
chown -R vmail:vmail /var/mail/vhosts

echo "Starting Dovecot..."
exec dovecot -F
