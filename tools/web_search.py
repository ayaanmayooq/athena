from .base import Tool

def _web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo and return relevant results.
    
    Args:
        query: Search query string
    
    Returns:
        Formatted string with search results
    """
    try:
        from ddgs import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        
        if not results:
            return f"No results found for: {query}"
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            url = result.get("href", "")
            formatted_results.append(f"{i}. {title}\n   {body[:200]}...\n   {url}")
        
        return "\n\n".join(formatted_results)
    except ImportError:
        return f"Error: duckduckgo-search package not installed. Install with: pip install duckduckgo-search"
    except Exception as e:
        return f"Error searching the web: {str(e)}"

web_search_tool = Tool(
    name="web_search",
    description="Search the web for recent information using DuckDuckGo. Returns top 5 relevant results with titles, snippets, and URLs.",
    parameters_schema={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
    func=_web_search,
)
