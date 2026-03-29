# Containerized Email Server

A full-featured, containerized email server with a web-based administration panel. Supports up to 150+ users with individual mailboxes, DKIM/SPF/DMARC email security, and auto-discovery for Outlook, Thunderbird, and Apple Mail.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Nginx (reverse proxy, TLS, autodiscover)           │
│  Ports: 80, 443                                     │
├─────────────────────────────────────────────────────┤
│  Postfix (SMTP)         │  Dovecot (IMAP/POP3)      │
│  Ports: 25, 587         │  Ports: 993, 995, 4190     │
├─────────────────────────────────────────────────────┤
│  Rspamd (spam/DKIM)     │  ClamAV (antivirus)        │
├─────────────────────────────────────────────────────┤
│  Web Admin (FastAPI)    │  PostgreSQL  │  Redis       │
└─────────────────────────────────────────────────────┘
```

## Features

- **SMTP** (Postfix) — sending and receiving email
- **IMAP/POP3** (Dovecot) — mailbox access with quotas and sieve filtering
- **Spam filtering** (Rspamd) — Bayesian learning, greylisting, score-based actions
- **Antivirus** (ClamAV) — attachment scanning
- **DKIM signing** — per-domain key management via web UI
- **SPF / DMARC** — DNS record guidance in admin panel
- **TLS everywhere** — Let's Encrypt or self-signed certificates
- **Autodiscover** — Microsoft Outlook (POX), Mozilla Thunderbird, Apple Mail
- **Web admin panel** — manage domains, users, aliases, DKIM keys, and server settings
- **PostgreSQL-backed** virtual mailboxes — no system user accounts needed

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your domain and passwords
```

### 2. Start the stack

```bash
docker compose up -d
```

### 3. Access the admin panel

Open `https://<your-server-ip>` in a browser (accept the self-signed cert warning).

Default login:
- **Email:** `admin@<your-domain>`
- **Password:** `admin`

**Change this password immediately** after first login.

### 4. Configure DNS

Go to the **DNS Records** page in the admin panel. Add all listed records to your domain's DNS:

- **MX** record pointing to your mail server
- **A** record for `mail.yourdomain.com`
- **SPF** TXT record
- **DMARC** TXT record
- **DKIM** TXT record (generate via the DKIM Keys page)
- **PTR** reverse DNS (set via your hosting provider)
- **SRV** records for autodiscover

### 5. Set up TLS (production)

```bash
# After DNS is pointing to your server:
bash scripts/setup-certs.sh
```

### 6. Configure email clients

**Outlook / Thunderbird / Apple Mail:** Enter the user's email and password — autodiscover handles the rest.

**Manual settings:**
| Protocol | Server | Port | Security |
|----------|--------|------|----------|
| IMAP     | mail.yourdomain.com | 993 | SSL/TLS |
| POP3     | mail.yourdomain.com | 995 | SSL/TLS |
| SMTP     | mail.yourdomain.com | 587 | STARTTLS |

## Admin Panel Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | Overview stats — domains, users, aliases |
| **Domains** | Add/remove/enable/disable mail domains |
| **Users** | Create mailbox accounts, set quotas, reset passwords |
| **Aliases** | Email forwarding rules |
| **DKIM Keys** | Generate and manage DKIM signing keys per domain |
| **DNS Records** | Shows all required DNS records for copy/paste |
| **Settings** | Server-wide settings (message size, spam threshold, etc.) |

## Ports

| Port | Service | Purpose |
|------|---------|---------|
| 25   | SMTP    | Server-to-server mail delivery |
| 587  | SMTP    | Client mail submission (authenticated) |
| 993  | IMAPS   | Secure IMAP mailbox access |
| 995  | POP3S   | Secure POP3 mailbox access |
| 80   | HTTP    | Redirect to HTTPS / ACME challenges |
| 443  | HTTPS   | Admin panel, autodiscover endpoints |
| 4190 | Sieve   | Mail filter management |

## Security Checklist

- [ ] Change default admin password
- [ ] Set strong `DB_PASSWORD` and `ADMIN_SECRET_KEY` in `.env`
- [ ] Configure DNS: MX, A, SPF, DKIM, DMARC, PTR
- [ ] Obtain TLS certificate via Let's Encrypt
- [ ] Set up PTR (reverse DNS) with your hosting provider
- [ ] Test deliverability with [mail-tester.com](https://www.mail-tester.com)
- [ ] Enable firewall rules for required ports only

## File Structure

```
email-server/
├── docker-compose.yml          # Container orchestration
├── .env.example                # Environment variable template
├── admin/                      # Web admin panel (FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   ├── config.py           # Settings from environment
│   │   ├── database.py         # SQLAlchemy async setup
│   │   ├── models.py           # ORM models
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   ├── auth.py             # JWT auth + password hashing
│   │   ├── dkim.py             # DKIM key generation utilities
│   │   └── routes/             # API endpoints
│   │       ├── auth_routes.py
│   │       ├── domain_routes.py
│   │       ├── user_routes.py
│   │       ├── alias_routes.py
│   │       ├── dkim_routes.py
│   │       ├── settings_routes.py
│   │       └── autodiscover_routes.py
│   ├── static/                 # CSS + JS
│   └── templates/              # HTML templates
├── config/
│   ├── postfix/                # SMTP server config
│   ├── dovecot/                # IMAP/POP3 server config
│   ├── rspamd/                 # Spam filter + DKIM signing config
│   └── nginx/                  # Reverse proxy config
├── db/
│   └── init.sql                # Database schema
└── scripts/
    └── setup-certs.sh          # Let's Encrypt helper
```
