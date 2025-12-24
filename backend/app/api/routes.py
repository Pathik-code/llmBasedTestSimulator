from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from uuid import UUID
from ..logic.orchestrator import ExamOrchestrator
from ..logic.storage import Storage
from ..models import ExamSession

router = APIRouter()
storage = Storage()

class StartRequest(BaseModel):
    candidate_name: str
    difficulty: str
    topics: list[str]
    total_questions_count: int
    question_types: list[str]
    provider: str = "openai"
    start_immediately: bool = True

class InteractRequest(BaseModel):
    user_input: str

class AnswerRequest(BaseModel):
    answer: str | None = None
    audio_data: str | None = None

@router.post("/exams/start", response_model=ExamSession)
def start_exam(req: StartRequest):
    print(f"API: Received start_exam request for {req.candidate_name}")
    orch = ExamOrchestrator(storage)
    session = orch.create_session(
        candidate_name=req.candidate_name,
        difficulty=req.difficulty,
        topics=req.topics,
        total_questions_count=req.total_questions_count,
        question_types=req.question_types,
        provider=req.provider
    )
    print(f"API: Created session {session.id}")
    return session

@router.get("/exams", response_model=list[dict])
def list_exams():
    return storage.list_sessions()

@router.get("/exams/{exam_id}", response_model=ExamSession)
def get_exam(exam_id: UUID):
    orch = ExamOrchestrator(storage)
    try:
        return orch.get_session(exam_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Session not found or corrupted")

@router.post("/exams/{exam_id}/interact")
def interact(exam_id: UUID, req: InteractRequest):
    # This might be deprecated in new batch flow, keeping for safety
    orch = ExamOrchestrator(storage)
    try:
        response = orch.handle_setup_interaction(exam_id, req.user_input)
        return {"message": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/exams/{exam_id}/answer")
def answer(exam_id: UUID, req: AnswerRequest):
    orch = ExamOrchestrator(storage)
    try:
        if not req.answer and not req.audio_data:
             raise ValueError("Answer or Audio Data required")
        
        # We pass raw answer (if any) and raw audio data (if any)
        # The orchestrator will handle transcription and combination
        text_answer = req.answer if req.answer else ""

        is_correct, explanation = orch.submit_answer(
            session_id=exam_id, 
            answer=text_answer, 
            audio_data=req.audio_data
        )
        return {
            "is_correct": is_correct,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/exams/{exam_id}/next", response_model=ExamSession)
def next_question(exam_id: UUID):
    orch = ExamOrchestrator(storage)
    try:
        return orch.next_question_state(exam_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
