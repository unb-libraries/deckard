from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class Link(BaseModel):
    label: str
    url: HttpUrl

class Question(BaseModel):
    queries: List[str]
    response: str
    links: Optional[List[Link]]

class DatabaseConfig(BaseModel):
    module_name: str
    class_name: str
    name: str

class EncoderConfig(BaseModel):
    module_name: str
    class_name: str
    model: str

class QAStackConfig(BaseModel):
    module_name: str
    class_name: str
    top_k: int = Field(..., ge=1)  # Must be an integer >= 1
    max_distance: float = Field(..., ge=0, le=1)  # Float between 0 and 1
    database: DatabaseConfig
    encoder: EncoderConfig
    questions: Optional[List[Question]]

class CollectorConfig(BaseModel):
    name: str
    module_name: str
    class_name: str
    output: str
    config: dict

class ChunkerConfig(BaseModel):
    module_name: str
    class_name: str
    config: dict

class ContextBuilderConfig(BaseModel):
    module_name: str
    class_name: str

class SparseSearchConfig(BaseModel):
    module_name: str
    class_name: str
    uri: HttpUrl

class QueryProcessorConfig(BaseModel):
    module_name: str
    class_name: str

class RerankerConfig(BaseModel):
    module_name: str
    class_name: str
    model: str
    max_raw_results: int = Field(..., ge=1)

class ResponseProcessorConfig(BaseModel):
    module_name: str
    class_name: str

class RagConfig(BaseModel):
    name: str
    stack: QAStackConfig
    collectors: Optional[List[CollectorConfig]]
    context: Optional[dict]
    chunker: Optional[ChunkerConfig]
    context_builder: Optional[ContextBuilderConfig]
    context_database: Optional[DatabaseConfig]
    embedding_database: Optional[DatabaseConfig]
    sparse_search: Optional[SparseSearchConfig]
    embedding_encoder: Optional[EncoderConfig]
    query_processor: Optional[QueryProcessorConfig]
    reranker: Optional[RerankerConfig]
    response_processor: Optional[ResponseProcessorConfig]

class LLMModelConfig(BaseModel):
    type: str
    repo: str
    filename: str
    max_response_tokens: int = Field(..., ge=1)
    n_batch: int = Field(..., ge=1)
    n_ctx: int = Field(..., ge=1)
    n_gpu_layers: int
    repeat_penalty: float = Field(..., ge=0)
    temperature: float = Field(..., ge=0, le=1)
    top_k: int = Field(..., ge=1)
    top_p: float = Field(..., ge=0, le=1)
    min_p: float = Field(..., ge=0, le=1)
    verbose: bool

class APIConfig(BaseModel):
    host: str = Field(..., regex=r"^\d{1,3}(\.\d{1,3}){3}$")  # Matches IPv4 addresses
    port: int = Field(..., ge=1, le=65535)
    llm: LLMModelConfig
    gpu_lock_file: str
    gpu_exclusive_mode: bool

class ClientConfig(BaseModel):
    timeout: int = Field(..., ge=1)
    uri: HttpUrl
    user_agent: str
    pub_key: str
    priv_key: str

class SlackBotConfig(BaseModel):
    api_pub_key: str
    api_priv_key: str
    slack_app_token: str
    slack_bot_token: str

class Config(BaseModel):
    api: APIConfig
    data_dir: str
    rag: RagConfig
    client: ClientConfig
    slackbot: SlackBotConfig
