from typing import List
from pydantic import BaseModel, Field

from context7.settings import settings


class GetDefaultPromptRequest(BaseModel): ...


class GetDefaultPromptResponse(BaseModel):
    default_prompt: str = Field(
        description="Returns a long instructional prompt string for guiding users of the assistant."
    )


class ResolveLibraryIDRequest(BaseModel):
    library_name: str = Field(
        description="The plain name or keyword of the target library to search for within Context7’s registry. "
        "Examples include common project names such as 'FastAPI' or 'SQLAlchemy'.",
        examples=[{"library_name": "fastAPI"}],
    )


class ResolveLibraryIDResponse(BaseModel):
    library_id: str = Field(
        description="Formatted list of matching libraries with metadata, including ID, title, and description."
    )


class ResolveMultipleLibraryIDsRequest(BaseModel):
    library_names: List[str] = Field(
        description="List of plain library names or identifiers to search for. Each entry is submitted separately "
        "to the backend search API. Typical use case: resolving multiple dependencies simultaneously.",
        examples=[{"library_names": ["fastAPI", "SQLAlchemy"]}],
    )


class ResolveMultipleLibraryIDsResponse(BaseModel):
    library_ids: List[str] = Field(
        description="Array of formatted summaries of matching libraries for each search term provided."
    )


class GetLibraryDocsRequest(BaseModel):
    library_id: str = Field(
        description="Canonical Context7 ID string identifying a library. Typically prefixed with a username "
        "or organization. Example: '/tiangolo/fastapi'.",
        examples=[{"library_id": "/tiangolo/fastapi"}],
    )
    tokens: int = Field(
        description="Maximum token budget for the returned content. Serverside enforces a minimum of "
        "settings.minimum_tokens, so very small requested values are adjusted upwards. "
        "Default is drawn from settings.default_tokens.",
        default=settings.default_tokens,
        examples=[{"tokens": settings.default_tokens}],
    )
    topic: str = Field(
        description="Optional string keyword used to filter content to specific documentation topics, "
        "such as 'async requests' or 'ORM integration'. This improves precision when querying large projects.",
        default="",
        examples=[{"topic": "simple example"}],
    )


class GetLibraryDocsResponse(BaseModel):
    library_info: str = Field(
        description="Raw documentation text retrieved for the requested library ID."
    )


class GetMultipleLibraryDocsRequest(BaseModel):
    library_id: List[str] = Field(
        description="Array of valid Context7 library IDs, such as '/tiangolo/fastapi' or '/sqlalchemy/sqlalchemy'. "
        "Must correspond index-wise with 'tokens' and 'topics'.",
        examples=[{"library_ids": ["/tiangolo/fastapi", "/sqlalchemy/sqlalchemy"]}],
    )
    tokens: List[int] = Field(
        description="Array of token budgets (one per library ID). Each integer indicates how many tokens to retrieve "
        "per documentation query. Must be the same length as 'library_ids'.",
        examples=[{"tokens": [2500, 25000]}],
    )
    topics: List[str] = Field(
        description="Topics array providing query refinements for each library requested. Each entry corresponds to "
        "the index of 'library_ids' and 'tokens'.",
        examples=[{"topics": ["request handling", "ORM integration"]}],
    )


class GetMultipleLibraryDocsResponse(BaseModel):
    library_infos: List[str] = Field(
        description="Array of documentation strings, aligned positionally with the input arrays of library IDs, tokens, and topics."
    )
