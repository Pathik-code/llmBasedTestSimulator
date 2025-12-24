from uuid import UUID
from typing import Optional, List
from ..models import ExamSession, Phase, Question, QuestionType
from ..services.llm_service import LLMService
from .storage import Storage

class ExamOrchestrator:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.llm = LLMService()
        self.setup_questions = [
            "What is the exam difficulty level? (Beginner, Intermediate, Advanced)",
            "Which topics should be included? (e.g. SQL, PySpark, Kafka, AWS)",
            "How many total questions do you want? (Numeric)",
            "Which question types should be included? (MCQ, Coding, Architecture)",
            "Do you want project-based questions? (Yes/No)"
        ]

    def create_session(self, candidate_name: str, difficulty: str = "Intermediate", topics: List[str] = [], total_questions_count: int = 5, question_types: List[str] = ["MCQ"], provider: str = "openai") -> ExamSession:
        print(f"ORCH: Creating session for {candidate_name} with {provider}")
        session = ExamSession(candidate_name=candidate_name)
        
        # Apply Configuration
        session.difficulty = difficulty
        session.topics = topics
        session.total_questions_count = total_questions_count
        session.question_types = question_types
        session.provider = provider
        session.setup_step = 5 

        # BATCH GENERATION
        print("ORCH: Generating Batch Questions...")
        batch = self.llm.generate_batch_questions(
            count=total_questions_count,
            difficulty=difficulty,
            topics=topics,
            types=question_types,
            provider=provider
        )
        
        # Convert to Internal Questions
        for q_gen in batch.questions:
            # Safe enum conversion
            try:
                q_type_str = q_gen.type.upper().replace(" ", "_")
                q_type = QuestionType[q_type_str]
            except:
                q_type = QuestionType.MCQ

            new_q = Question(
                question_text=q_gen.question,
                difficulty=q_gen.difficulty,
                type=q_type,
                options=q_gen.options,
                correct_answer=q_gen.correct_answer,
                explanation=q_gen.explanation,
                concept=q_gen.concept,
                constraints=q_gen.constraints
            )
            session.questions.append(new_q)

        session.status = Phase.EXAM_LOOP
        session.current_question_index = 0
        
        print(f"ORCH: Saving session {session.id} with {len(session.questions)} questions")
        self.storage.save_session(session)
        return session
    
    def get_session(self, session_id: UUID) -> ExamSession:
        session = self.storage.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        return session

    def submit_answer(self, session_id: UUID, answer: str, audio_data: str = None):
        session = self.get_session(session_id)
        current_q = session.questions[session.current_question_index]
        
        # Handle Audio Transcription
        final_answer = answer
        if audio_data:
            print(f"ORCH: Transcribing Audio for {session_id}")
            transcript = self.llm.transcribe_audio(audio_data)
            if final_answer:
                final_answer += f"\n\n[Audio Transcript]: {transcript}"
            else:
                final_answer = f"[Audio Transcript]: {transcript}"
        
        current_q.user_answer = final_answer
        
        # LLM EVALUATION
        print(f"ORCH: Evaluating Answer for {current_q.id} using {session.provider}")
        evaluation = self.llm.evaluate_answer(
            question_text=current_q.question_text,
            correct_ref=current_q.correct_answer or "Assessed by constraints",
            user_answer=final_answer,
            options=current_q.options, # Pass options for context
            constraints=current_q.constraints, # Pass constraints for context
            provider=session.provider
        )
        
        current_q.is_correct = evaluation.is_correct
        current_q.feedback = evaluation.reason
        
        # Enriched explanation construction
        full_explanation = f"{evaluation.explanation}\n\nConfidence: {evaluation.confidence}"
        
        if evaluation.code_snippet:
             full_explanation += f"\n\n#### 💻 Reference Code\n```python\n{evaluation.code_snippet}\n```"
        
        if evaluation.related_topics:
             topics_list = ", ".join(evaluation.related_topics)
             full_explanation += f"\n\n#### 🧠 Related Concepts\n{topics_list}"
             
        if evaluation.learning_resources:
             resources_str = "\n".join([f"- {r}" for r in evaluation.learning_resources])
             full_explanation += f"\n\n#### 🔗 Learning Resources\n{resources_str}"
        
        current_q.explanation = full_explanation
        
        if current_q.is_correct: 
            session.current_score += 1
        
        self.storage.save_session(session)
        return evaluation.is_correct, current_q.explanation

    def next_question_state(self, session_id: UUID):
         session = self.get_session(session_id)
         if session.current_question_index < len(session.questions) - 1:
             session.current_question_index += 1
         else:
             session.status = Phase.COMPLETED
         self.storage.save_session(session)
         return session
