# src/context7/core.py
"""
Context7 Core Utilities
=======================

This module provides essential support functions for interacting with the Context7 API.

Main features:
- AES encryption of client IPs using a shared secret key.
- Header generation with encrypted IP and Bearer API key injection.
- Asynchronous HTTPX clients for searching libraries and retrieving documentation.
- Utility for formatting search results into human-readable summaries.
"""

import secrets
import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from context7.settings import settings


def encrypt_client_ip(ip: str) -> str:
    """Encrypt a client IP address with AES-CBC using the configured key.

    Args:
        ip (str): The plain text IPv4/IPv6 address to encrypt.

    Returns:
        str: A hex-formatted string consisting of `iv:ct` where `iv` is the
        initialization vector and `ct` is the cipher text.
    """
    key_hex = settings.client_ip_encryption_key
    key = bytes.fromhex(key_hex)
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded = padder.update(ip.encode()) + padder.finalize()
    ct = encryptor.update(padded) + encryptor.finalize()
    return iv.hex() + ":" + ct.hex()


def generate_headers(
    client_ip: str = None, api_key: str = None, extra: dict = None
) -> dict:
    """Generate HTTP request headers for interacting with Context7 API.

    Args:
        client_ip (str, optional): Client IP address to encrypt and include.
        api_key (str, optional): Bearer token for authentication.
        extra (dict, optional): Optional extra headers to merge.

    Returns:
        dict: Headers dictionary with MCP headers and authentication.
    """
    headers = extra.copy() if extra else {}
    if client_ip:
        headers["mcp-client-ip"] = encrypt_client_ip(client_ip)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


async def search_libraries(
    query: str, client_ip: str = None, api_key: str = None
) -> dict:
    """Search the Context7 API for libraries by query string.

    Args:
        query (str): Search term, e.g. 'FastAPI' or 'SQLAlchemy'.
        client_ip (str, optional): Client IP for header encryption.
        api_key (str, optional): Authentication token.

    Returns:
        dict: Context7 JSON response with 'results' and possible 'error' field.
    """
    url = f"{settings.context7_api_base_url}/v1/search"
    async with httpx.AsyncClient() as client:
        r = await client.get(
            url, params={"query": query}, headers=generate_headers(client_ip, api_key)
        )
    return (
        r.json()
        if r.status_code == 200
        else {"error": f"{r.status_code}", "results": []}
    )


async def fetch_library_docs(
    library_id: str,
    tokens: int = settings.default_tokens,
    topic: str = "",
    client_ip: str = None,
    api_key: str = None,
) -> str | None:
    """Fetch documentation text for a given library ID.

    Args:
        library_id (str): A valid Context7 library identifier (with or without leading '/').
        tokens (int, optional): Maximum token count for the returned content. Defaults to settings.default_tokens.
        topic (str, optional): Optional keyword filter to limit which sections are retrieved. Defaults to "".
        client_ip (str, optional): Client IP for header encryption.
        api_key (str, optional): Authentication token.

    Returns:
        str | None: Raw documentation text string if available, otherwise None.
    """
    if library_id.startswith("/"):
        library_id = library_id[1:]
    url = f"{settings.context7_api_base_url}/v1/{library_id}"
    params = {
        "tokens": str(max(tokens, settings.minimum_tokens)),
        "topic": topic,
        "type": "txt",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(
            url,
            params=params,
            headers=generate_headers(
                client_ip, api_key, {"X-Context7-Source": "mcp-server"}
            ),
        )
    if r.status_code == 200:
        text = r.text
        return (
            None
            if text in ("No content available", "No context data available")
            else text
        )
    return None


def format_search_results(resp: dict) -> str:
    """Convert Context7 search results into a human-readable summary.

    Args:
        resp (dict): JSON response object from `search_libraries`.

    Returns:
        str: Human formatted multi-line string describing the top matches, including
        title, ID, description, snippet count, trust score, and versions if present.
    """
    res = []
    for r in resp.get("results", []):
        out = [
            f"- Title: {r.get('title', '')}",
            f"- ID: {r.get('id', '')}",
            f"- Description: {r.get('description', '')}",
        ]
        if r.get("totalSnippets", -1) > 0:
            out.append(f"- Code Snippets: {r['totalSnippets']}")
        if r.get("trustScore"):
            out.append(f"- Trust Score: {r['trustScore']}")
        if r.get("versions"):
            out.append(f"- Versions: {', '.join(r['versions'])}")
        res.append("\n".join(out))
    return "\n----------\n".join(res)
