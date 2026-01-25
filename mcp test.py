import asyncio
from typing import List

from mcp.server.fastmcp import FastMCP

# Your existing logic
from tool_utils.confluence_content_extractor import fetch_confluence_page
from tool_utils.confluence_search import confluence_search

# Azure env + auth
from config.env_setup import init_env_and_session

# --------------------------------------------------
# Init
# --------------------------------------------------

init_env_and_session()

mcp = FastMCP(
    name="confluence-mcp",
    instructions="Fetch and search Confluence pages using internal APIs"
)

# --------------------------------------------------
# TOOL: Fetch page content
# --------------------------------------------------

@mcp.tool(
    name="confluence_fetch_page",
    description="Fetch full structured content of a Confluence page by URL"
)
async def confluence_fetch_page(url: str) -> dict:
    """
    Input:
      url: Full Confluence page URL

    Output:
      Structured page content optimized for LLM + vector DB
    """
    try:
        return fetch_confluence_page(url)
    except Exception as e:
        return {
            "error": str(e),
            "url": url
        }

# --------------------------------------------------
# TOOL: Search pages
# --------------------------------------------------

@mcp.tool(
    name="confluence_search",
    description="Search Confluence pages using keywords"
)
async def confluence_search_pages(
    keywords: List[str],
    max_results: int = 5
) -> dict:
    """
    Input:
      keywords: List of search keywords
      max_results: Max number of results

    Output:
      List of pages with title, space, url, page_id
    """
    try:
        return confluence_search(
            keywords=keywords,
            max_results=max_results
        )
    except Exception as e:
        return {
            "error": str(e),
            "keywords": keywords
        }

# --------------------------------------------------
# Entrypoint
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run()
