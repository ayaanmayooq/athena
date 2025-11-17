from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    # DB
    database_url: str = "sqlite:///./athena.db"

    # History / context
    max_history_messages: int = 20

    # Neo4j Graph DB
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
