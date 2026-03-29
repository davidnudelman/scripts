#!/bin/bash
# =====================================================
# Let's Encrypt Certificate Setup
# Run this on the host AFTER DNS is configured.
# =====================================================
set -e

HOSTNAME="${MAIL_HOSTNAME:-mail.example.com}"
EMAIL="${LETSENCRYPT_EMAIL:-admin@example.com}"

echo "Requesting Let's Encrypt certificate for ${HOSTNAME}..."

docker compose run --rm nginx certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    -d "${HOSTNAME}"

echo "Certificate obtained. Restarting services..."
docker compose restart nginx postfix dovecot

echo "Done. Certificate will auto-renew via cron."
echo ""
echo "Add this to your crontab for auto-renewal:"
echo "0 3 * * * cd $(pwd) && docker compose run --rm nginx certbot renew --quiet && docker compose restart nginx postfix dovecot"
