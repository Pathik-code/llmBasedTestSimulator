from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class Phase(str, Enum):
    SETUP = "SETUP"
    EXAM_LOOP = "EXAM_LOOP" # Phase 2 & 3 Combined
    PROJECT = "PROJECT"    # Phase 4
    COMPLETED = "COMPLETED" # Phase 5

class QuestionType(str, Enum):
    MCQ = "MCQ"
    CODING = "CODING"
    SQL = "SQL"
    DEBUGGING = "DEBUGGING"
    SHORT_ANSWER = "SHORT_ANSWER"
    SCENARIO = "SCENARIO"
    ARCHITECTURE = "ARCHITECTURE"
    DATA_MODELING = "DATA_MODELING"
    OPTIMIZATION = "OPTIMIZATION"
    DATA_QUALITY = "DATA_QUALITY"
    CASE_STUDY = "CASE_STUDY"
    PROJECT = "PROJECT"

class Question(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    question_text: str
    difficulty: str
    type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None # For MCQs/Short Answer
    explanation: Optional[str] = None
    concept: Optional[str] = None
    
    # Coding/Project specific
    problem_statement: Optional[str] = None
    constraints: Optional[str] = None
    
    # State
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    feedback: Optional[str] = None

class ExamSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: Phase = Phase.SETUP
    candidate_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Setup Data (Phase 1)
    provider: str = "openai" # openai or gemini
    setup_step: int = 1 # 1 to 5
    difficulty: Optional[str] = None
    topics: List[str] = []
    total_questions_count: int = 0
    question_types: List[str] = []
    project_enabled: bool = False
    
    # Phase 2/3 Data
    questions: List[Question] = []
    current_question_index: int = 0
    questions_asked_ids: List[str] = [] # Legacy field to keep compatible
    current_score: float = 0.0
    
    # Chat History (for context)
    chat_history: List[Dict[str, str]] = []

# LLM interaction models
class AnswerEvaluation(BaseModel):
    is_correct: bool
    confidence: float
    reason: str
    explanation: str
    code_snippet: Optional[str] = None
    related_topics: Optional[List[str]] = None
    learning_resources: Optional[List[str]] = None

# LLM interaction models
class SetupPrompt(BaseModel):
    difficulty: Optional[str] = None
    topics: Optional[List[str]] = None

class QuestionGenerated(BaseModel):
    question: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    concept: str
    difficulty: str
    type: str # mcq, coding, etc.
    explanation: Optional[str] = None
    constraints: Optional[str] = None

class BatchQuestions(BaseModel):
    questions: List[QuestionGenerated]
