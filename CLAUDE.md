# CLAUDE.md

## Repository Overview

This is a repository maintained by davidnudelman containing technical guides, utility scripts, and a containerized email server project.

## Structure

```
scripts/
├── README.md              # Repository introduction
├── CLAUDE.md              # This file - AI assistant guidance
├── map_printer            # Guide: mapping printers on Windows machines
└── email-server/          # Containerized email server application
    ├── docker-compose.yml
    ├── .env.example
    ├── README.md
    ├── admin/             # FastAPI web admin panel (Python)
    │   ├── app/           # API routes, models, auth, DKIM management
    │   ├── static/        # CSS + JS frontend
    │   └── templates/     # HTML templates
    ├── config/
    │   ├── postfix/       # SMTP server config + Dockerfile
    │   ├── dovecot/       # IMAP/POP3 server config + Dockerfile
    │   ├── rspamd/        # Spam filter + DKIM signing config
    │   └── nginx/         # Reverse proxy + TLS + Dockerfile
    ├── db/                # PostgreSQL schema (init.sql)
    └── scripts/           # Helper scripts (cert setup)
```

## Content Conventions

- Root-level files are plain text or Markdown documentation with technical procedures and command examples.
- The `email-server/` directory is a full application with Python (FastAPI), Docker Compose, and service configs.
- Windows-focused docs target **PowerShell and DOS/batch** environments.

## Email Server Tech Stack

- **Language**: Python 3.12 (FastAPI, SQLAlchemy async, Pydantic)
- **Database**: PostgreSQL 16 (virtual mailbox backend)
- **Mail**: Postfix (SMTP), Dovecot (IMAP/POP3), Rspamd (spam/DKIM), ClamAV (antivirus)
- **Frontend**: Vanilla HTML/CSS/JS (single-page admin UI)
- **Infrastructure**: Docker Compose, Nginx reverse proxy, Redis
- **Auth**: JWT tokens, bcrypt password hashing (Dovecot BLF-CRYPT compatible)

## File Format Guidelines

- Use Markdown (`.md`) for documentation files when formatting adds clarity.
- Use plain text for concise, single-topic reference notes.
- Embed command examples inline within documentation rather than creating separate script files.

## Git Workflow

- **Primary branch**: `master`
- Commit messages should be short and descriptive.

## Notes for AI Assistants

- The `email-server/` directory is a Docker Compose application — no build/test runs outside containers.
- The admin panel API docs are available at `/api/docs` (Swagger UI) when running.
- Passwords are hashed with `{BLF-CRYPT}` prefix for Dovecot compatibility.
- DKIM keys are written to disk at `/etc/opendkim/keys/<domain>/<selector>.key` for Rspamd.
- Autodiscover endpoints serve XML for Outlook (POX), Thunderbird (autoconfig), and Apple Mail (mobileconfig).
- When modifying Postfix/Dovecot configs, the SQL lookup files reference the PostgreSQL `mailserver` database.
