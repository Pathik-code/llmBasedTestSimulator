import os
import json
import base64
import io
import google.generativeai as genai
from openai import OpenAI
from typing import Any, Dict
from ..models import SetupPrompt, QuestionGenerated, BatchQuestions, AnswerEvaluation
from .prompts import SETUP_SYSTEM_PROMPT, QUESTION_GENERATION_PROMPT, CLARIFICATION_PROMPT, BATCH_QUESTION_GENERATION_PROMPT, ANSWER_EVALUATION_PROMPT

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # OpenAI Init
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not set.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
            
        # Gemini Init
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel("gemini-pro")
        else:
            print("Warning: GEMINI_API_KEY not set.")
            self.gemini_model = None

    def _call_llm(self, system_prompt: str, user_prompt: str, response_model: Any = None, provider: str = "openai") -> Dict:
        if provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)

        if not self.client or self.api_key == "sk-placeholder":
            print("LLM: Using Mock Response")
            return self._mock_response(system_prompt, user_prompt)
        
        params = {
            "model": "gpt-4o",
            "temperature": 0.2,
        }

        if response_model:
             # strict json mode compatible invocation if needed
             params["response_format"] = {"type": "json_object"}
             if "json" not in system_prompt.lower():
                 system_prompt += " You must output JSON."

        # For structured JSON outputs
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        params["messages"] = messages

        try:
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            
            # Simple sanitization
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
                
            return json.loads(content)
        except Exception as e:
            print(f"LLM Call Error: {e}")
            raise

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> Dict:
        if not self.gemini_model:
             raise ValueError("Gemini API Key not configured.")
        
        try:
            # Gemini doesn't have system prompts in the same way, usually prepended
            full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
            
            response = self.gemini_model.generate_content(full_prompt)
            content = response.text
            
            # Clean JSON
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
        except Exception as e:
             print(f"Gemini Call Error: {e}")
             raise

    def get_setup_prompt(self) -> str:
        return SETUP_SYSTEM_PROMPT
    
    def generate_question(self, session_context: dict) -> QuestionGenerated:
        system = self.get_setup_prompt()
        
        # Prepare context strings
        diff = session_context.get('difficulty', 'Intermediate')
        tops = ", ".join(session_context.get('topics', []))
        typs = ", ".join(session_context.get('types', []))
        
        user = QUESTION_GENERATION_PROMPT.format(
            context=str(session_context),
            difficulty=diff,
            topics=tops,
            types=typs
        )
        
        # Ensure json keyword for API
        if "json" not in system.lower(): system += " Output must be JSON."
        
        res = self._call_llm(system, user, response_model=True)
        return QuestionGenerated(**res)

    def get_setup_question(self, current_info: str) -> str:
        prompt = CLARIFICATION_PROMPT.format(current_info=current_info)
        res = self._call_llm("You are an exam coordinator.", prompt, response_model=True)
        return res.get("clarifying_question", "Could you provide more details?")

    def extract_setup_info(self, user_input: str) -> Dict[str, Any]:
        system = "You are a helper extracting structured data from user text."
        user = f"""
        User said: "{user_input}"
        Extract 'difficulty' (Junior, Intermediate, Senior) and 'topics' (list of strings) if present.
        If not present, use null.
        Format:
        {{
            "difficulty": "extracted_difficulty_or_null",
            "topics": ["topic1", "topic2"] or null
        }}
        """
        return self._call_llm(system, user, response_model=True)

    def generate_batch_questions(self, count: int, difficulty: str, topics: list[str], types: list[str], provider: str = "openai") -> BatchQuestions:
        system = self.get_setup_prompt()
        if "json" not in system.lower(): system += " Output must be JSON."
        
        user_prompt = BATCH_QUESTION_GENERATION_PROMPT.format(
            count=count,
            difficulty=difficulty,
            topics=", ".join(topics),
            types=", ".join(types)
        )
        
        res = self._call_llm(system, user_prompt, response_model=True, provider=provider)
        return BatchQuestions(**res)

    def evaluate_answer(self, question_text: str, correct_ref: str, user_answer: str, options: list[str] = None, constraints: str = None, provider: str = "openai") -> AnswerEvaluation:
        system = "You are a fair Data Engineering Interviewer. Evaluate the answer. Output JSON."
        options_str = ", ".join(options) if options else "N/A"
        constraints_str = constraints if constraints else "None"
        
        user_prompt = ANSWER_EVALUATION_PROMPT.format(
            question=question_text,
            options=options_str,
            constraints=constraints_str,
            correct_answer_ref=correct_ref,
            user_answer=user_answer
        )
        
        res = self._call_llm(system, user_prompt, response_model=True, provider=provider)
        return AnswerEvaluation(**res)

    def transcribe_audio(self, audio_b64: str) -> str:
        if not self.client or self.api_key == "sk-placeholder":
            print("LLM: Mocking Transcription")
            return "This is a mock transcription of the user's voice answer."

        try:
            # Decode base64
            audio_bytes = base64.b64decode(audio_b64)
            # Create file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav" # Important for OpenAI API to detect format

            print("LLM: sending audio to Whisper...")
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en" 
            )
            return transcript.text
        except Exception as e:
            print(f"Transcription Error: {e}")
            return "[Error: Could not transcribe audio]"

    def _mock_response(self, system: str, user: str) -> Dict:
        # Mock logic
        if "Generate" in user:
            return {
                "questions": [
                    {
                        "question": "Mock Question 1",
                        "options": ["A", "B"],
                        "correct_answer": "A",
                        "concept": "Mock",
                        "difficulty": "Easy",
                        "type": "MCQ",
                        "explanation": "Mock explanation"
                    }
                ]
            }
        
        if "Evaluate" in user:
             return {
                 "is_correct": True,
                 "confidence": 0.9,
                 "reason": "Matches mock",
                 "explanation": "This is a mock evaluation."
             }
             
        return {}
