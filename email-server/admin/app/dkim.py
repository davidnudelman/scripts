"""DKIM key generation and file management."""

import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings


def generate_dkim_keypair(key_size: int = 2048) -> tuple[str, str]:
    """Generate an RSA keypair for DKIM signing.

    Returns (private_key_pem, public_key_pem) as strings.
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def public_key_to_dns_record(public_pem: str, selector: str, domain: str) -> str:
    """Convert a PEM public key to a DNS TXT record value for DKIM."""
    # Strip PEM headers and join into single line
    lines = public_pem.strip().split("\n")
    key_data = "".join(line for line in lines if not line.startswith("-----"))

    record_name = f"{selector}._domainkey.{domain}"
    record_value = f"v=DKIM1; k=rsa; p={key_data}"
    return f"{record_name} IN TXT \"{record_value}\""


def write_dkim_key_to_disk(domain: str, selector: str, private_pem: str) -> str:
    """Write the DKIM private key to disk for Rspamd to use.

    Returns the file path written.
    """
    key_dir = Path(settings.dkim_key_path) / domain
    key_dir.mkdir(parents=True, exist_ok=True)

    key_path = key_dir / f"{selector}.key"
    key_path.write_text(private_pem)
    os.chmod(key_path, 0o600)

    return str(key_path)


def delete_dkim_key_from_disk(domain: str, selector: str) -> None:
    """Remove a DKIM key file from disk."""
    key_path = Path(settings.dkim_key_path) / domain / f"{selector}.key"
    if key_path.exists():
        key_path.unlink()
