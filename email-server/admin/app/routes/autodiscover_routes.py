"""Autodiscover endpoints for email client auto-configuration.

Supports:
- Microsoft Outlook Autodiscover (POX XML)
- Mozilla Thunderbird Autoconfig
- Apple Mail Mobileconfig profile
"""

from fastapi import APIRouter, Request, Response

from app.config import settings

router = APIRouter(tags=["autodiscover"])

HOSTNAME = settings.mail_hostname
DOMAIN = settings.mail_domain


# ── Outlook Autodiscover (POX) ───────────────────────────
@router.post("/autodiscover/autodiscover.xml")
@router.get("/autodiscover/autodiscover.xml")
async def outlook_autodiscover(request: Request):
    """Outlook Autodiscover POX endpoint.

    Outlook sends a POST with XML containing the user's email.
    We return server settings for IMAP + SMTP.
    """
    # Try to extract email from POST body
    email = ""
    if request.method == "POST":
        try:
            body = await request.body()
            body_str = body.decode("utf-8", errors="ignore")
            # Simple extraction — avoid full XML parse dependency
            start = body_str.find("<EMailAddress>")
            end = body_str.find("</EMailAddress>")
            if start != -1 and end != -1:
                email = body_str[start + 14:end].strip()
        except Exception:
            pass

    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/responseschema/2006">
  <Response xmlns="http://schemas.microsoft.com/exchange/autodiscover/outlook/responseschema/2006a">
    <Account>
      <AccountType>email</AccountType>
      <Action>settings</Action>
      <Protocol>
        <Type>IMAP</Type>
        <Server>{HOSTNAME}</Server>
        <Port>993</Port>
        <DomainRequired>off</DomainRequired>
        <LoginName>{email}</LoginName>
        <SPA>off</SPA>
        <SSL>on</SSL>
        <AuthRequired>on</AuthRequired>
      </Protocol>
      <Protocol>
        <Type>SMTP</Type>
        <Server>{HOSTNAME}</Server>
        <Port>587</Port>
        <DomainRequired>off</DomainRequired>
        <LoginName>{email}</LoginName>
        <SPA>off</SPA>
        <Encryption>TLS</Encryption>
        <AuthRequired>on</AuthRequired>
        <UsePOPAuth>on</UsePOPAuth>
        <SMTPLast>off</SMTPLast>
      </Protocol>
    </Account>
  </Response>
</Autodiscover>"""

    return Response(content=xml, media_type="application/xml")


# ── Mozilla Autoconfig ───────────────────────────────────
@router.get("/mail/config-v1.1.xml")
async def mozilla_autoconfig(emailaddress: str = ""):
    """Mozilla/Thunderbird autoconfig endpoint.

    Thunderbird requests: /mail/config-v1.1.xml?emailaddress=user@domain.com
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<clientConfig version="1.1">
  <emailProvider id="{DOMAIN}">
    <domain>{DOMAIN}</domain>
    <displayName>{DOMAIN} Mail</displayName>
    <displayShortName>{DOMAIN}</displayShortName>

    <incomingServer type="imap">
      <hostname>{HOSTNAME}</hostname>
      <port>993</port>
      <socketType>SSL</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILADDRESS%</username>
    </incomingServer>

    <incomingServer type="pop3">
      <hostname>{HOSTNAME}</hostname>
      <port>995</port>
      <socketType>SSL</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILADDRESS%</username>
    </incomingServer>

    <outgoingServer type="smtp">
      <hostname>{HOSTNAME}</hostname>
      <port>587</port>
      <socketType>STARTTLS</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILADDRESS%</username>
    </outgoingServer>
  </emailProvider>
</clientConfig>"""

    return Response(content=xml, media_type="application/xml")


# ── Apple Mobileconfig ──────────────────────────────────
@router.get("/email.mobileconfig")
async def apple_mobileconfig(email: str = ""):
    """Generate an Apple mobileconfig profile for iOS/macOS Mail."""
    username = email if email else "user@" + DOMAIN

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>PayloadContent</key>
  <array>
    <dict>
      <key>EmailAccountDescription</key>
      <string>{DOMAIN} Email</string>
      <key>EmailAccountName</key>
      <string>{username}</string>
      <key>EmailAccountType</key>
      <string>EmailTypeIMAP</string>
      <key>EmailAddress</key>
      <string>{username}</string>

      <key>IncomingMailServerAuthentication</key>
      <string>EmailAuthPassword</string>
      <key>IncomingMailServerHostName</key>
      <string>{HOSTNAME}</string>
      <key>IncomingMailServerPortNumber</key>
      <integer>993</integer>
      <key>IncomingMailServerUseSSL</key>
      <true/>
      <key>IncomingMailServerUsername</key>
      <string>{username}</string>

      <key>OutgoingMailServerAuthentication</key>
      <string>EmailAuthPassword</string>
      <key>OutgoingMailServerHostName</key>
      <string>{HOSTNAME}</string>
      <key>OutgoingMailServerPortNumber</key>
      <integer>587</integer>
      <key>OutgoingMailServerUseSSL</key>
      <true/>
      <key>OutgoingMailServerUsername</key>
      <string>{username}</string>
      <key>OutgoingPasswordSameAsIncomingPassword</key>
      <true/>

      <key>PayloadDescription</key>
      <string>{DOMAIN} email configuration</string>
      <key>PayloadDisplayName</key>
      <string>{DOMAIN} Email</string>
      <key>PayloadIdentifier</key>
      <string>com.{DOMAIN.replace('.', '-')}.email</string>
      <key>PayloadType</key>
      <string>com.apple.mail.managed</string>
      <key>PayloadUUID</key>
      <string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
      <key>PayloadVersion</key>
      <integer>1</integer>
    </dict>
  </array>
  <key>PayloadDisplayName</key>
  <string>{DOMAIN} Mail Setup</string>
  <key>PayloadIdentifier</key>
  <string>com.{DOMAIN.replace('.', '-')}.profile</string>
  <key>PayloadType</key>
  <string>Configuration</string>
  <key>PayloadUUID</key>
  <string>F1E2D3C4-B5A6-7890-ABCD-EF0987654321</string>
  <key>PayloadVersion</key>
  <integer>1</integer>
</dict>
</plist>"""

    return Response(
        content=xml,
        media_type="application/x-apple-aspen-config",
        headers={"Content-Disposition": f'attachment; filename="{DOMAIN}.mobileconfig"'},
    )


# ── DNS Records Helper ──────────────────────────────────
@router.get("/api/dns-records")
async def get_dns_records():
    """Return the recommended DNS records for this mail server."""
    return {
        "records": [
            {
                "type": "MX",
                "name": DOMAIN,
                "value": f"10 {HOSTNAME}.",
                "description": "Mail exchanger — directs email to this server",
            },
            {
                "type": "A",
                "name": HOSTNAME,
                "value": "<YOUR_SERVER_IP>",
                "description": "Mail server IP address",
            },
            {
                "type": "TXT",
                "name": DOMAIN,
                "value": f"v=spf1 mx a:{HOSTNAME} ~all",
                "description": "SPF — declares authorized mail senders",
            },
            {
                "type": "TXT",
                "name": f"_dmarc.{DOMAIN}",
                "value": f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{DOMAIN}; fo=1",
                "description": "DMARC — policy for SPF/DKIM failures",
            },
            {
                "type": "TXT",
                "name": f"mail._domainkey.{DOMAIN}",
                "value": "v=DKIM1; k=rsa; p=<generated via DKIM management>",
                "description": "DKIM — generate via admin panel, then paste here",
            },
            {
                "type": "PTR",
                "name": "<YOUR_SERVER_IP>",
                "value": f"{HOSTNAME}.",
                "description": "Reverse DNS — set via your hosting provider",
            },
            {
                "type": "SRV",
                "name": f"_imaps._tcp.{DOMAIN}",
                "value": f"0 1 993 {HOSTNAME}.",
                "description": "Autodiscover — IMAP service location",
            },
            {
                "type": "SRV",
                "name": f"_submission._tcp.{DOMAIN}",
                "value": f"0 1 587 {HOSTNAME}.",
                "description": "Autodiscover — SMTP submission service location",
            },
            {
                "type": "SRV",
                "name": f"_autodiscover._tcp.{DOMAIN}",
                "value": f"0 1 443 {HOSTNAME}.",
                "description": "Outlook Autodiscover SRV record",
            },
        ]
    }
