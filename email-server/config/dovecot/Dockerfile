FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    dovecot-core \
    dovecot-imapd \
    dovecot-pop3d \
    dovecot-lmtpd \
    dovecot-pgsql \
    dovecot-sieve \
    dovecot-managesieved \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Create vmail user for mailbox ownership
RUN groupadd -g 5000 vmail && \
    useradd -u 5000 -g vmail -d /var/mail/vhosts -s /usr/sbin/nologin vmail && \
    mkdir -p /var/mail/vhosts && \
    chown -R vmail:vmail /var/mail/vhosts

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 993 995 24 12345 4190

ENTRYPOINT ["/entrypoint.sh"]
