from agno.agent import Agent
from agno.models.google import Gemini
from agno.storage.sqlite import SqliteStorage
import os
import time
from utils.env_loader import load_backend_env
from services.celery_app import app, SessionLockedTask
from db.config import get_agent_session_db_path
from db.agent_config_v2 import (
    AGENT_DESCRIPTION,
    AGENT_INSTRUCTIONS,
    AGENT_MODEL,
    INITIAL_SESSION_STATE,
)
from agents.search_agent import search_agent_run
from agents.scrape_agent import scrape_agent_run
from agents.script_agent import podcast_script_agent_run
from tools.ui_manager import ui_manager_run
from tools.user_source_selection import user_source_selection_run
from tools.session_state_manager import update_language, update_chat_title, mark_session_finished
from agents.audio_generate_agent import audio_generate_agent_run
import json

load_backend_env()

db_file = get_agent_session_db_path()


@app.task(bind=True, max_retries=0, base=SessionLockedTask)
def agent_chat(self, session_id, message):
    try:
        t0 = time.time()
        print(f"[T+0.0s] Processing message for session {session_id}: {message[:50]}...", flush=True)
        
        db_file = get_agent_session_db_path()
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        print(f"[T+{time.time()-t0:.2f}s] DB path ready", flush=True)
        
        from services.internal_session_service import SessionService
        session_state = SessionService.get_session(session_id).get("state", INITIAL_SESSION_STATE)
        print(f"[T+{time.time()-t0:.2f}s] Session state loaded", flush=True)
        
        # Initialize model separately to measure time
        print(f"[T+{time.time()-t0:.2f}s] Initializing Gemini model...", flush=True)
        gemini_model = Gemini(id=AGENT_MODEL, api_key=os.getenv("GOOGLE_API_KEY"))
        print(f"[T+{time.time()-t0:.2f}s] Gemini model ready", flush=True)
        
        # Initialize storage separately
        print(f"[T+{time.time()-t0:.2f}s] Initializing storage...", flush=True)
        storage = SqliteStorage(table_name="podcast_sessions", db_file=db_file)
        print(f"[T+{time.time()-t0:.2f}s] Storage ready", flush=True)
        
        # Initialize agent
        print(f"[T+{time.time()-t0:.2f}s] Creating agent...", flush=True)
        _agent = Agent(
            model=gemini_model,
            storage=storage,
            add_history_to_messages=True,
            read_chat_history=True,
            add_state_in_messages=True,
            num_history_runs=30,
            instructions=AGENT_INSTRUCTIONS,
            description=AGENT_DESCRIPTION,
            session_state=session_state,
            session_id=session_id,
            tools=[
                search_agent_run,
                scrape_agent_run,
                ui_manager_run,
                user_source_selection_run,
                update_language,
                podcast_script_agent_run,
                audio_generate_agent_run,
                update_chat_title,
                mark_session_finished,
            ],
            markdown=True,
        )
        print(f"[T+{time.time()-t0:.2f}s] Agent ready, starting run...", flush=True)
        
        response = _agent.run(message, session_id=session_id)
        print(f"Response generated for session {session_id}", flush=True)
        _agent.write_to_storage(session_id=session_id)
        session_state = SessionService.get_session(session_id).get("state", INITIAL_SESSION_STATE)
        return {
            "session_id": session_id,
            "response": response.content,
            "stage": _agent.session_state.get("stage", "unknown"),
            "session_state": json.dumps(session_state),
            "is_processing": False,
            "process_type": None,
        }
    except Exception as e:
        print(f"Error in agent_chat for session {session_id}: {str(e)}", flush=True)
        return {
            "session_id": session_id,
            "response": f"I'm sorry, I encountered an error: {str(e)}. Please try again.",
            "stage": "error",
            "session_state": "{}",
            "is_processing": False,
            "process_type": None,
        }
