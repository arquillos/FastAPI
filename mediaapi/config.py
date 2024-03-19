from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    """Loads the dotenv file. Including this is necessary to get pydantic to load a .env file."""
    model_config = SettingsConfigDict(env_file="mediaapi/.env", extra="ignore")


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False
    # Configuration for JWT token creation
    SECRET_KEY: str = ""
    ALGORITHM: str = ""


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_")


class TestConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="TEST_")


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_")


@lru_cache
def get_config(env_state: str):
    config = {"dev": DevConfig, "test": TestConfig, "prod": ProdConfig}
    return config[env_state]()


config = get_config(BaseConfig().ENV_STATE)
