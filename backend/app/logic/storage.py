import json
import os
from uuid import UUID
from typing import Optional, List
from ..models import ExamSession

# Define data dir relative to project root
# current file: backend/app/logic/storage.py -> up 3 levels to root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(BASE_DIR, "data", "sessions")

class Storage:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _get_path(self, session_id: UUID) -> str:
        return os.path.join(DATA_DIR, f"{session_id}.json")

    def save_session(self, session: ExamSession):
        path = self._get_path(session.id)
        temp_path = f"{path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(session.model_dump_json(indent=2))
            os.replace(temp_path, path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"STORAGE ERROR: Failed to save session {session.id}: {e}")
            raise

    def get_session(self, session_id: UUID) -> Optional[ExamSession]:
        path = self._get_path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ExamSession(**data)
        except Exception as e:
            print(f"STORAGE ERROR: Could not load session {session_id}: {e}")
            return None

    def list_sessions(self) -> List[dict]:
        sessions = []
        if not os.path.exists(DATA_DIR): return []
        
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                try:
                    p = os.path.join(DATA_DIR, filename)
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sessions.append({
                            "id": data.get("id"),
                            "candidate_name": data.get("candidate_name"),
                            "status": data.get("status"),
                            "created_at": data.get("created_at"),
                            "score": data.get("current_score", 0),
                            "total": data.get("total_questions_count", 0)
                        })
                except Exception:
                    continue # Skip bad files
        
        # Sort by date desc
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions
