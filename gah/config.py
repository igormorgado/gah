import os
from typing import Any
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

class Neo4jConfig(BaseModel):
    uri: str
    username: str
    database: str


class SpacyConfig(BaseModel):
    model_name: str
    

class RebelConfig(BaseModel):
    model_name: str


class TransformerConfig(BaseModel):
    model_name: str
    

class Config(BaseModel):
    neo4j: Neo4jConfig
    spacy: SpacyConfig
    rebel: RebelConfig
    transformer: TransformerConfig
    

class Secrets(BaseModel):
    neo4j_password: str
    huggingface_token: str
    

def _load_secrets(secrets_path: str) -> dict[str, Any]:
    with open(secrets_path, "r", encoding="UTF-8") as file:
        secrets_dict = yaml.safe_load(file)
    return secrets_dict


def _load_secret(secrets_path: str, key: str) -> str:
    secrets_dict = _load_secrets(secrets_path)
    return secrets_dict.get(key, '')


def load_config(
    config_path: str | Path = "config.yaml",
    secrets_path: str | Path = "secrets.yaml"
) -> tuple[Config, Secrets]:
    """Load config from yaml files"""

    with open(config_path, 'r') as file:
        config_dict = yaml.safe_load(file)

    config = Config(**config_dict)

    secrets_entries = ['neo4j_password', 'huggingface_token']
    secrets_dict = {
        key: os.getenv(key.upper()) or _load_secret(secrets_path, key)
        for key in secrets_entries
    }

    secrets = Secrets(**secrets_dict)

    return config, secrets

