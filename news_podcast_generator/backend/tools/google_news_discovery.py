
def search_news(google_news, keyword):
    resutls = google_news.get_news(keyword)
    return resutls


def get_top_news(google_news):
    resutls = google_news.get_top_news()
    return resutls


def get_news_by_topic(google_news, topic):
    resutls = google_news.get_news_by_topic(topic)
    return resutls


def google_news_discovery_run(
    keyword: str = None,
    max_results: int = 5,
    top_news: bool = False,
) -> str:
    from gnews import GNews
    import json
    
    """
    This is a wrapper function for the google news.

    Args:
        keyword: The search query for specific news
        top_news: Whether to get top news instead of keyword search (default: False)
        max_results: The maximum number of results to return (default: 20)

    Returns:
        List of news results

    Note:
        Either set top_news=True for top headlines or provide a keyword for search.
        If both are provided, top_news takes precedence.
    """
    print("Google News Discovery:", keyword)
    try:
        google_news = GNews(
            language=None,
            country=None,
            period=None,
            max_results=max_results,
            exclude_websites=[],
        )
        results = []
        if top_news:
            results = get_top_news(google_news)
        elif keyword:
            results = search_news(google_news, keyword)
        else:
            return "Error: Either keyword or top_news must be provided."
        
        if not results:
            return "No Google News results found for this query. Try other search tools."
        
        print('google news search found:', len(results))
        return f"for all results is_scrapping_required: True, results: {json.dumps(results)}"
    except Exception as e:
        print(f"Error during Google News search: {str(e)}")
        return f"Error in Google News search: {str(e)}. Try other search tools like browser_search or embedding_search."
