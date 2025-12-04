from agno.agent import Agent
from utils.env_loader import load_backend_env
from typing import List

load_backend_env()


def user_source_selection_run(
    agent: Agent,
    selected_sources: List[int] = None,
) -> str:
    """
    User Source Selection that takes the selected sources indices as input and updates the final confirmed sources.
    If selected_sources is empty/None, AUTO-SELECT ALL sources (fast mode).
    
    Args:
        agent: The agent instance
        selected_sources: The selected sources indices (optional - if None, selects ALL)
    Returns:
        Response status
    """
    from services.internal_session_service import SessionService
    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    session_state = session["state"]
    
    search_results = session_state.get("search_results", [])
    
    # AUTO-SELECT ALL if no selection provided (fast mode)
    if not selected_sources:
        selected_sources = list(range(1, len(search_results) + 1))  # [1, 2, 3, ...]
        print(f"⚡ AUTO-SELECT: Selecting all {len(search_results)} sources", flush=True)
    
    for i, src in enumerate(search_results):
        if (i+1) in selected_sources:
            src["confirmed"] = True
        else:
            src["confirmed"] = False
    
    SessionService.save_session(session_id, session_state)
    confirmed_count = sum(1 for s in search_results if s.get("confirmed", False))
    print(f"✅ Confirmed {confirmed_count}/{len(search_results)} sources", flush=True)
    return f"Auto-selected all {confirmed_count} sources. Ready for script generation."
