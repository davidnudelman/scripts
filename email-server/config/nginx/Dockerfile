FROM nginx:stable-alpine

RUN mkdir -p /var/www/certbot /srv/admin/static

# Generate self-signed cert for initial startup
RUN apk add --no-cache openssl && \
    mkdir -p /etc/letsencrypt/live/mail.example.com && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/letsencrypt/live/mail.example.com/privkey.pem \
        -out /etc/letsencrypt/live/mail.example.com/fullchain.pem \
        -subj "/CN=mail.example.com" 2>/dev/null

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

EXPOSE 80 443
