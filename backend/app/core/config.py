from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "图纸管理系统 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/blueprint_db"

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时

    # 文件存储配置
    FILE_STORAGE_PATH: str = "/data/drawings"
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:5173"
    ]
    # 允许所有 localhost 端口
    ALLOW_ALL_LOCALHOST: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
