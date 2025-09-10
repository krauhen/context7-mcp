# src/context7/api.py
import asyncio

from fastapi import HTTPException, APIRouter

from context7.core import search_libraries, format_search_results, fetch_library_docs
from context7.exceptions import LibraryNotFoundException, DocumentationNotFoundException
from context7.schemas import (
    GetDefaultPromptResponse,
    ResolveLibraryIDRequest,
    ResolveLibraryIDResponse,
    GetLibraryDocsRequest,
    GetLibraryDocsResponse,
    ResolveMultipleLibraryIDsResponse,
    GetMultipleLibraryDocsResponse,
    GetMultipleLibraryDocsRequest,
    ResolveMultipleLibraryIDsRequest,
    GetDefaultPromptRequest,
)
from context7.settings import settings
from context7.logger import logger


router = APIRouter()


@router.post(
    "/get_default_prompt",
    response_model=GetDefaultPromptResponse,
    description=(
        "This endpoint provides the default instructional prompt used by the Context7 assistant. "
        "It describes the overall query-resolution workflow, library matching strategies, "
        "multi-library handling, and general guidelines the assistant should follow while answering "
        "software related questions."
    ),
    operation_id="get_default_prompt",
)
async def get_default_prompt(
    request: GetDefaultPromptRequest,
) -> GetDefaultPromptResponse:
    logger.success("Tool call: get_default_prompt()")
    logger.debug(request.model_dump())

    return GetDefaultPromptResponse(
        default_prompt="""
You are an assistant specialized in answering software development questions by using library documentation from Context7.

Guidelines:

1. **Library Identification**
   - Detect when the user’s question involves one or more software libraries.
   - If a single library is mentioned, issue a `resolve_library_id` query for that name.
   - If multiple libraries are mentioned (e.g., FastAPI + SQLAlchemy), issue a `resolve_multiple_library_ids` query providing all library names in a list.
   - Combine the results to obtain the corresponding library IDs.
   - Use the identified IDs with either `get_library_docs` (for one) or `get_multiple_library_docs` (for many).

2. **Multi-Library Query Execution**
   - The API supports querying multiple libraries at once.
   - `resolve_multiple_library_ids` takes a list of library names and returns results for each asynchronously.
   - `get_multiple_library_docs` accepts three aligned lists:
     * `library_ids`: A list of valid Context7 library IDs.
     * `tokens`: A list of token counts, one per library, to control the maximum size of the returned text.
     * `topics`: A list of topic strings, one per library, to narrow down which documentation sections are retrieved.
   - Each index across `library_ids`, `tokens`, and `topics` corresponds to the same library request.
   - Calls for multiple libraries are run concurrently so that results are retrieved in parallel.

3. **Query Strategy**
   - Start with a smaller request (~2,500 tokens) focused on the most relevant topic keywords.
   - If the response seems incomplete or ambiguous, follow up with a larger request (≈25,000 tokens).
   - Always provide a topic for each library so Context7 narrows results to the most relevant sections.
   - Use parallel queries where appropriate when a question spans multiple libraries.

4. **Clarification over Guessing**
   - If documentation is unclear, missing, or if there is risk of producing an incorrect answer, do not guess.
   - Instead, return a clarifying question back to the user.
   - Example: “Do you want guidance on FastAPI request handling, or on SQLAlchemy ORM integration?”

5. **Answer Construction**
   - Combine context from all relevant libraries when the question spans multiple dependencies.
   - Be explicit about how the answer was derived from the retrieved documentation.
   - Do not invent or assume APIs, parameters, or behaviors that are not present in the documentation.
   - Stay strictly aligned with actual documentation results.

6. **Fallback**
   - If no matching docs are found for one or more libraries, state this clearly.
   - Ask the user to refine or restate the query if needed.
"""
    )


@router.post(
    "/resolve_library_id",
    response_model=ResolveLibraryIDResponse,
    description=(
        "Receives a single library name as input, queries Context7’s backend search API for matching entries, "
        "and returns a human-readable summary containing metadata. Each match contains the canonical Context7 "
        "library ID, title, potential descriptions, trust score, and available versions."
    ),
    operation_id="resolve_library_id",
)
async def resolve_library_id(
    request: ResolveLibraryIDRequest,
):
    logger.success("Tool call: resolve_library_id()")
    logger.debug(request.model_dump())

    resp = await search_libraries(
        request.library_name,
        client_ip=None,
        api_key=settings.api_key.get_secret_value(),
    )
    if not resp.get("results"):
        raise LibraryNotFoundException()
    result = format_search_results(resp)
    return ResolveLibraryIDResponse(library_id=result)


@router.post(
    "/get_library_docs",
    response_model=GetLibraryDocsResponse,
    description=(
        "Given a valid Context7 library ID, retrieves sections of documentation text. "
        "Optionally accepts a topic keyword to narrow retrieval and a maximum token budget "
        "to constrain the size of the response. This facilitates targeted exploration of documentation "
        "without overloading the client."
    ),
    operation_id="get_library_docs",
)
async def get_library_docs(
    request: GetLibraryDocsRequest,
) -> GetLibraryDocsResponse:
    logger.success("Tool call: get_library_docs()")
    logger.debug(request.model_dump())

    docs = await fetch_library_docs(
        request.library_id,
        request.tokens,
        request.topic,
        client_ip=None,
        api_key=settings.api_key.get_secret_value(),
    )
    if not docs:
        raise DocumentationNotFoundException()
    return GetLibraryDocsResponse(library_info=docs)


@router.post(
    "/resolve_multiple_library_ids",
    response_model=ResolveMultipleLibraryIDsResponse,
    description=(
        "Queries multiple library names concurrently against Context7’s API. Each string provided in 'library_names' "
        "is resolved independently, and results are returned in a list aligned to the request order. "
        "Each element includes metadata describing ID, title, versions, and trust score if available."
    ),
    operation_id="resolve_multiple_library_ids",
)
async def resolve_multiple_library_ids(
    request: ResolveMultipleLibraryIDsRequest,
) -> ResolveMultipleLibraryIDsResponse:
    logger.success("Tool call: resolve_multiple_library_ids()")
    logger.debug(request.model_dump())

    async def _search(name: str):
        resp = await search_libraries(
            name, client_ip=None, api_key=settings.api_key.get_secret_value()
        )
        if not resp.get("results"):
            raise LibraryNotFoundException(message=f"No matching library ids found for names {request.library_names}")
        return format_search_results(resp)

    results = await asyncio.gather(*[_search(name) for name in request.library_names])
    return ResolveMultipleLibraryIDsResponse(library_ids=results)


@router.post(
    "/get_multiple_library_docs",
    response_model=GetMultipleLibraryDocsResponse,
    description=(
        "Retrieves documentation for multiple libraries in parallel. Requires equal-length arrays of library IDs, "
        "token budgets, and topic filters. Each request is dispatched concurrently to maximize throughput. "
        "The result is a list aligned to the input order, with fetched documentation or explanatory error messages."
    ),
    operation_id="get_multiple_library_docs",
)
async def get_multiple_library_docs(
    request: GetMultipleLibraryDocsRequest,
) -> GetMultipleLibraryDocsResponse:
    logger.success("Tool call: get_multiple_library_docs()")
    logger.debug(request.model_dump())

    if not (len(request.library_ids) == len(request.tokens) == len(request.topics)):
        raise HTTPException(
            status_code=400,
            detail="Lengths of library_ids, tokens, and topics must match.",
        )

    async def _fetch(lib_id: str, t: int, top: str):
        docs = await fetch_library_docs(
            lib_id, t, top, client_ip=None, api_key=settings.api_key.get_secret_value()
        )
        return (
            docs
            if docs
            else f"Documentation not found for {lib_id} with topic '{top}'."
        )

    results = await asyncio.gather(
        *[
            _fetch(request.library_ids[i], request.tokens[i], request.topics[i])
            for i in range(len(request.library_ids))
        ]
    )
    return GetMultipleLibraryDocsResponse(library_infos=results)
