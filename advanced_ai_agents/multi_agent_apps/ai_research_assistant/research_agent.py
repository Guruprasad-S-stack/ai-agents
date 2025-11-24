# Import the required libraries
import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.google import Gemini
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.tools.newspaper4k import Newspaper4kTools

# Set up the Streamlit app
st.title("Multi-Agent AI Researcher 🔍🤖")
st.caption("This app allows you to research top stories and users on HackerNews and write blogs, reports and social posts.")

# Get Google API key from user
google_api_key = st.text_input("Google API Key (for Gemini)", type="password", help="Get your API key from https://aistudio.google.com/apikey")

if google_api_key:
    hn_researcher = Agent(
        name="HackerNews Researcher",
        model=Gemini(id="gemini-2.5-flash", api_key=google_api_key),
        role="Gets top stories from hackernews.",
        tools=[HackerNewsTools()],
    )

    web_searcher = Agent(
        name="Web Searcher",
        model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key),
        role="Searches the web for information on a topic",
        tools=[DuckDuckGoTools()],
        add_datetime_to_context=True,
    )

    article_reader = Agent(
        name="Article Reader",
        model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key),
        role="Reads articles from URLs.",
        tools=[Newspaper4kTools()],
    )

    hackernews_team = Team(
        name="HackerNews Team",
        model=Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key),
        members=[hn_researcher, web_searcher, article_reader],
        instructions=[
            "First, search hackernews for what the user is asking about.",
            "Then, ask the article reader to read the links for the stories to get more information.",
            "Important: you must provide the article reader with the links to read.",
            "Then, ask the web searcher to search for each story to get more information.",
            "Finally, provide a thoughtful and engaging summary.",
        ],
        markdown=True,
        debug_mode=True,
        show_members_responses=True,
    )

    # Input field for the report query
    query = st.text_input("Enter your report query")

    if query:
        # Get the response from the assistant
        response: RunOutput = hackernews_team.run(query, stream=False)
        st.write(response.content)