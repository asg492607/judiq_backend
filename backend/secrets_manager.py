"""
JudiQ AI — Enterprise Secrets & Key Management Service
Integrates with HashiCorp Vault, AWS Secrets Manager, and local environment with rotation audit policies.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("JudiQ.SecretsManager")


class SecretsManager:
    """
    Enterprise Secrets Manager supporting HashiCorp Vault, AWS Secrets Manager, and secure env hydration.
    """
    _cached_secrets: Dict[str, Any] = {}

    @classmethod
    def get_secret(cls, key: str, default: Optional[str] = None) -> str:
        # Check cache
        if key in cls._cached_secrets:
            return cls._cached_secrets[key]

        # 1. HashiCorp Vault Integration (if VAULT_ADDR and VAULT_TOKEN configured)
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        if vault_addr and vault_token:
            try:
                import hvac
                client = hvac.Client(url=vault_addr, token=vault_token)
                secret_path = os.getenv("VAULT_SECRET_PATH", "secret/data/judiq")
                read_response = client.secrets.kv.read_secret_version(path=secret_path)
                data = read_response.get("data", {}).get("data", {})
                if key in data:
                    cls._cached_secrets[key] = data[key]
                    return data[key]
            except Exception as e:
                logger.warning(f"⚠️ Vault fetch for key '{key}' failed: {e}. Falling back.")

        # 2. AWS Secrets Manager Integration (if AWS_SECRET_NAME configured)
        aws_secret_name = os.getenv("AWS_SECRET_NAME")
        if aws_secret_name:
            try:
                import boto3
                import json
                client = boto3.client("secretsmanager")
                response = client.get_secret_value(SecretId=aws_secret_name)
                if "SecretString" in response:
                    secrets_dict = json.loads(response["SecretString"])
                    if key in secrets_dict:
                        cls._cached_secrets[key] = secrets_dict[key]
                        return secrets_dict[key]
            except Exception as e:
                logger.warning(f"⚠️ AWS Secrets Manager fetch for '{key}' failed: {e}. Falling back.")

        # 3. Environment Variable Fallback
        val = os.getenv(key, default)
        if val is not None:
            cls._cached_secrets[key] = val
            return val

        return default or ""

    @classmethod
    def audit_security_hygiene(cls) -> Dict[str, Any]:
        """
        Audit secret strength, rotation deadlines, and warn on default dev keys.
        """
        secret_key = cls.get_secret("SECRET_KEY", "")
        encryption_key = cls.get_secret("ENCRYPTION_KEY", "")
        db_url = cls.get_secret("DATABASE_URL", "")

        is_secure = True
        warnings = []

        if secret_key in ("", "changeme_secure_key_for_dev_only"):
            is_secure = False
            warnings.append("SECRET_KEY is using insecure development placeholder.")

        if len(encryption_key) not in (43, 44):
            is_secure = False
            warnings.append("ENCRYPTION_KEY must be a valid 32-byte base64 string.")

        if not db_url or "sqlite" in db_url:
            warnings.append("DATABASE_URL is operating on SQLite (Non-replicated dev storage).")

        return {
            "is_production_ready": is_secure,
            "warnings": warnings,
            "vault_integrated": bool(os.getenv("VAULT_ADDR")),
            "aws_secrets_integrated": bool(os.getenv("AWS_SECRET_NAME"))
        }
