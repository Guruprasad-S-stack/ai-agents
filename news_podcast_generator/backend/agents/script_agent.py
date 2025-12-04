import os
from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel, Field
from typing import List, Optional
from utils.env_loader import load_backend_env
from textwrap import dedent
from datetime import datetime

load_backend_env()


class Dialog(BaseModel):
    speaker: str = Field(..., description="The speaker name (SHOULD BE 'ALEX' OR 'MORGAN')")
    text: str = Field(
        ...,
        description="The spoken text content for this speaker based on the requested langauge, default is English",
    )


class Section(BaseModel):
    type: str = Field(..., description="The section type (intro, headlines, article, outro)")
    title: Optional[str] = Field(None, description="Optional title for the section (required for article type)")
    dialog: List[Dialog] = Field(..., description="List of dialog exchanges between speakers")


class PodcastScript(BaseModel):
    title: str = Field(..., description="The podcast episode title with date")
    sections: List[Section] = Field(..., description="List of podcast sections (intro, headlines, articles, outro)")


PODCAST_AGENT_DESCRIPTION = "You are a helpful assistant that can generate engaging podcast scripts for the given sources."
PODCAST_AGENT_INSTRUCTIONS = dedent("""
    You are a helpful assistant that generates engaging, CONVERSATIONAL podcast scripts between two hosts discussing the given content.
    
    CRITICAL CONVERSATION RULES:
    - This is a DIALOGUE, not speeches. Alex and Morgan should have a natural back-and-forth conversation.
    - EACH DIALOG TURN MUST BE SHORT: Maximum 2-3 sentences per speaker before the other responds.
    - Speakers should frequently react to each other: "That's a great point, Morgan..." or "Exactly, Alex, and..."
    - Include natural interruptions, agreements, questions, and follow-ups between speakers.
    - Avoid long monologues - if a speaker needs to explain something complex, break it into multiple short turns with the other host asking clarifying questions or adding comments.
    
    CONVERSATION FLOW EXAMPLES:
    - ALEX: "So the big news this week is about agentic AI."
    - MORGAN: "Right, and what's fascinating is how quickly it's evolving."
    - ALEX: "Exactly. Companies like AWS are now offering dedicated tools for it."
    - MORGAN: "That's huge. What does that mean for developers?"
    
    NOT LIKE THIS (too speech-like):
    - ALEX: "Today we're going to discuss agentic AI. This is a major development in the field. Companies are investing billions. AWS has launched new tools. Microsoft is also competing. The implications are vast..." (TOO LONG!)
    
    PERSONALITY NOTES:
    - Alex is more analytical and fact-focused (references data, explains technical concepts)
    - Morgan is more focused on human impact and practical applications (asks "what does this mean for people?")
    - They should BUILD on each other's points, not just take turns giving speeches
    - Include moments of genuine curiosity, surprise, or humor
    
    CONTENT GUIDELINES:
    - Cover the key points from the sources through natural discussion
    - Make complex topics accessible through the Q&A dynamic between hosts
    - Total script should be 15+ minutes of natural conversation
    
    ACCESSIBILITY - CRITICAL:
    - This podcast is for a GENERAL AUDIENCE, not experts
    - Explain technical/scientific terms in simple language
    - When encountering jargon, have one host ask "What does that mean?" and the other explain simply
    - Use analogies and everyday examples to make complex concepts relatable
    - Even if sources are academic/research papers, the podcast should feel like friends explaining cool stuff
    
    IMPORTANT: Generate the entire script in the provided language (only the text field needs translation).
    """)


def format_search_results_for_podcast(
    search_results: List[dict],
) -> tuple[str, List[str]]:
    created_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    structured_content = []
    structured_content.append(f"PODCAST CREATION: {created_at}\n")
    sources = []
    for idx, search_result in enumerate(search_results):
        try:
            if search_result.get("confirmed", False):
                sources.append(search_result["url"])
                structured_content.append(
                    f"""
                                        SOURCE {idx + 1}:
                                        Title: {search_result['title']}
                                        URL: {search_result['url']}
                                        Content: {search_result.get('full_text') or search_result.get('description', '')}
                                        ---END OF SOURCE {idx + 1}---
                                        """.strip()
                )
        except Exception as e:
            print(f"Error processing search result: {e}")
    content_texts = "\n\n".join(structured_content)
    return content_texts, sources


def podcast_script_agent_run(
    agent: Agent,
    query: str,
    language_name: str,
) -> str:
    """
    Podcast Script Agent that takes the search_results (internally from search_results) and creates a podcast script for the given query and language.

    Args:
        agent: The agent instance
        query: The search query
        language_name: The language the podcast script should be.
    Returns:
        Response status
    """
    from services.internal_session_service import SessionService
    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    session_state = session["state"]
    
    print("Podcast Script Agent Input:", query, flush=True)
    content_texts, sources = format_search_results_for_podcast(session_state.get("search_results", []))
    if not content_texts:
        return "No confirmed sources found to generate podcast script."

    podcast_script_agent = Agent(
        model=Gemini(id="gemini-2.5-pro", api_key=os.getenv("GOOGLE_API_KEY")),
        instructions=PODCAST_AGENT_INSTRUCTIONS,
        description=PODCAST_AGENT_DESCRIPTION,
        use_json_mode=True,
        response_model=PodcastScript,
        session_id=agent.session_id,
    )
    response = podcast_script_agent.run(
        f"query: {query}\n language_name: {language_name}\n content_texts: {content_texts}\n, IMPORTANT: texts should be in {language_name} language.",
        session_id=agent.session_id,
    )
    response_dict = response.to_dict()
    response_dict = response_dict["content"]
    response_dict["sources"] = sources
    session_state["generated_script"] = response_dict
    session_state['stage'] = 'script'
    
    # Skip confirmation - proceed directly to audio
    session_state["show_script_for_confirmation"] = False
    session_state["show_sources_for_selection"] = False
    
    SessionService.save_session(session_id, session_state)
    print(f"✅ Script generated with {len(response_dict.get('sections', []))} sections. Proceeding to audio generation.", flush=True)

    if not session_state["generated_script"] and not session_state["generated_script"].get("sections"):
        return "Failed to generate podcast script."
    
    # Proceed directly to audio generation (no confirmation needed)
    return f"Generated podcast script for '{query}' with {len(sources)} sources. Script is ready. IMMEDIATELY call audio_generate_agent_run to generate the podcast audio."