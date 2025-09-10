from pydantic import Field, SecretStr

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env",), env_file_encoding="utf-8")

    app_host: str = Field(description="APP host")
    app_port: int = Field(description="APP port")
    mcp_path: str = Field(description="MCP path")
    api_path: str = Field(description="API path")
    log_level: str = Field(description="Log level")
    cert_file: str = Field(description="Certificate file")
    key_file: str = Field(description="Private key file")
    app_root_path: str = Field(description="FastAPI root path")

    client_ip_encryption_key: str = Field(description="Client IP encryption key")
    context7_api_base_url: str = Field(description="Context 7 API base url")
    default_tokens: int = Field(description="Default tokens")
    minimum_tokens: int = Field(description="Minimum tokens")
    api_key: SecretStr = Field(description="API key")

    fastmcp_experimental_enable_new_openapi_parser: bool = Field(description="Enable new openapi parser in FastAPI-MCP")

    def __str__(self):
        secret_terms = ["secret", "password"]

        msg = "\nLoaded config:\n"
        for key, value in self.model_dump().items():
            for secret_term in secret_terms:
                if secret_term.lower() in key.lower():
                    value = "***"
            msg += f"  {key}: {value}\n"
        return msg


def get_settings() -> Settings:
    return Settings()


settings = Settings()
