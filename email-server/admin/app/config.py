from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "postgres"
    db_name: str = "mailserver"
    db_user: str = "mailuser"
    db_password: str = "changeme"
    secret_key: str = "change-this-to-a-random-secret"
    mail_hostname: str = "mail.example.com"
    mail_domain: str = "example.com"
    dkim_key_path: str = "/etc/opendkim/keys"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}/{self.db_name}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
