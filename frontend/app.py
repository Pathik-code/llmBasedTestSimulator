import streamlit as st
import requests
import base64
from code_editor import code_editor

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Data Engineer Exam Simulator", layout="wide", page_icon="🎓")

# --- Custom CSS ---
st.markdown("""
<style>
    .stTextArea textarea {
        background-color: #1e1e1e;
        color: #d4d4d4;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4f46e5;
        margin-bottom: 1rem;
    }
    .phase-badge {
        background-color: #4338ca;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- Session Init ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "exam_status" not in st.session_state:
    st.session_state.exam_status = "SETUP"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# --- Actions ---
def start_exam():
    name = st.session_state.get("candidate_name")
    diff = st.session_state.get("difficulty")
    topics_str = st.session_state.get("topics")
    q_count = st.session_state.get("q_count")
    q_types = st.session_state.get("q_types")

    if not name:
        st.error("Please enter your name.")
        return
    
    topics_list = [t.strip() for t in topics_str.split(",")] if topics_str else ["General"]
    
    prov_map = {"OpenAI (GPT-4o)": "openai", "Google (Gemini Pro)": "gemini"}
    provider = prov_map.get(st.session_state.get("provider_select"), "openai")

    payload = {
        "candidate_name": name,
        "difficulty": diff,
        "topics": topics_list,
        "total_questions_count": q_count,
        "question_types": q_types,
        "provider": provider
    }
    
    try:
        with st.spinner("Generating Batch Questions... This may take a moment."):
            res = requests.post(f"{API_URL}/exams/start", json=payload)
            res.raise_for_status()
            data = res.json()
            st.session_state.session_id = data["id"]
            st.session_state.exam_status = data["status"]
    except Exception as e:
        st.error(f"Failed to start exam: {e}")

def resume_exam(sess_id):
    st.session_state.session_id = sess_id
    st.session_state.last_result = None
    # Fetch status
    try:
        res = requests.get(f"{API_URL}/exams/{sess_id}")
        data = res.json()
        st.session_state.exam_status = data["status"]
    except Exception as e:
        st.error(f"Error resuming: {e}")

def submit_answer():
    # Get current index to build dynamic keys
    # We need to fetch the session status locally to know the index
    # But for a cleaner approach, reliance on st.session_state which might be updated is tricky?
    # Actually, we can just fetch the latest known index from exam loop logic? No, submit_answer is a callback.
    # Best way: Check st.session_state keys or use passing args.
    # Or cleaner: Since we are in the same script re-run, we can just look up what keys exist?
    # No, let's fetch exam state again or rely on session_state persistence of logic?
    # Let's assume we are viewing the current question.
    
    # We can retrieve the session details from backend? Too slow for just getting index?
    # Better: We previously fetched session in "Main UI", but that variable scope is outside.
    # We will assume st.session_state['exam_status'] logic holds and we can try to guess index?
    # Actually, `start_exam` sets index to 0. `next_question` increments it.
    # The frontend doesn't strictly track `index` in session_state, it relies on API.
    # We need to retrieve the question index from the API or store it in session_state.
    
    # Let's add current_question_index to session_state in the main loop to make this accessible.
    
    idx = st.session_state.get("current_q_index", 0) 
    key_suffix = f"_{idx}"
    
    # DEBUG LOGGING
    print(f"DEBUG: submit_answer idx={idx}, keys suffix={key_suffix}")
    print(f"DEBUG: Keys in session: {list(st.session_state.keys())}")

    answer = st.session_state.get(f"answer_text_input{key_suffix}")
    radio = st.session_state.get(f"answer_radio_input{key_suffix}")
    audio_val = st.session_state.get(f"audio_answer{key_suffix}")
    
    # Check Code Editor State (if defined)
    # Check Code Editor State (if defined)
    # 1. Try manual shadow key first
    manual_code = st.session_state.get(f"manual_code_input{key_suffix}")
    if manual_code:
        answer = manual_code
    else:
        # 2. Fallback to widget Key
        code_state = st.session_state.get(f"code_editor_data{key_suffix}")
        if code_state:
            if isinstance(code_state, dict) and code_state.get('text'):
                answer = code_state.get('text')
            elif isinstance(code_state, str):
                answer = code_state

    final_answer = answer if answer else radio
    audio_b64 = None
    
    if audio_val:
        try:
            bytes_data = audio_val.read()
            audio_b64 = base64.b64encode(bytes_data).decode()
        except Exception as e:
            st.warning(f"Failed to process audio: {e}")

    if not final_answer and not audio_b64: 
        st.warning("Please provide an answer")
        return
    
    payload = {}
    if final_answer: payload["answer"] = final_answer
    if audio_b64: payload["audio_data"] = audio_b64

    try:
        with st.spinner("Evaluating Answer..."):
            res = requests.post(f"{API_URL}/exams/{st.session_state.session_id}/answer", json=payload)
            res.raise_for_status()
            st.session_state.last_result = res.json()
    except Exception as e:
        st.error(f"Error submitting answer: {e}")

def next_question():
    try:
        res = requests.post(f"{API_URL}/exams/{st.session_state.session_id}/next")
        res.raise_for_status()
        st.session_state.last_result = None
        # status update needed?
        data = res.json()
        st.session_state.exam_status = data["status"]
    except Exception as e:
        st.error(f"Error fetching next question: {e}")

def reset_app():
    st.session_state.session_id = None
    st.session_state.exam_status = "SETUP"
    st.session_state.last_result = None

# --- Main UI ---

if not st.session_state.session_id:
    # Landing Page
    st.markdown("<div class='main-header'>Data Engineer Assessment</div>", unsafe_allow_html=True)
    
    # Dashboard Tabs
    tab1, tab2 = st.tabs(["🚀 Start New Exam", "📂 Exam History"])
    
    with tab1:
        st.write("Configure your exam environment below.")
        with st.form("setup_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Candidate Name", key="candidate_name", placeholder="e.g. Jane Doe")
                st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], key="difficulty")
                st.number_input("Total Questions", min_value=1, max_value=20, value=5, key="q_count")
            
            with col2:
                st.text_input("Topics (comma-separated)", value="SQL, Python, Kafka, Spark", key="topics")
                st.multiselect("Question Types", 
                            ["MCQ", "CODING", "SQL", "DEBUGGING", "SHORT_ANSWER", "SCENARIO", "ARCHITECTURE", "DATA_MODELING", "OPTIMIZATION", "DATA_QUALITY", "CASE_STUDY", "PROJECT"], 
                            default=["MCQ", "CODING", "SQL"], 
                            key="q_types")
                st.selectbox("AI Model Provider", ["OpenAI (GPT-4o)", "Google (Gemini Pro)"], key="provider_select")
                
            st.form_submit_button("Start Assessment", on_click=start_exam, type="primary")

    with tab2:
        st.subheader("Previous Sessions")
        if st.button("Refresh List"): pass 
        
        try:
            res = requests.get(f"{API_URL}/exams")
            sessions = res.json()
            if sessions:
                for s in sessions:
                    with st.expander(f"{s['candidate_name']} - {s['created_at'][:16]} ({s['status']})"):
                        st.write(f"Score: {s['score']} / {s['total']}")
                        if s['status'] != "COMPLETED":
                            if st.button(f"Resume Exam {s['id'][:8]}", key=s['id']):
                                resume_exam(s['id'])
                        else:
                             st.info("Completed")
            else:
                st.info("No exam history found.")
        except Exception as e:
            st.error(f"Failed to fetch history: {e}")

else:
    # Fetch State
    try:
        res = requests.get(f"{API_URL}/exams/{st.session_state.session_id}")
        if res.status_code != 200:
            st.error(f"Failed to load session (Error {res.status_code}): {res.text}")
            st.button("Return to Dashboard", on_click=reset_app)
            st.stop()
            
        session = res.json()
        current_status = session.get("status")
        # Sync status if changed externally
        if current_status != st.session_state.exam_status:
             st.session_state.exam_status = current_status
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

    # Sidebar Status
    with st.sidebar:
        st.title("Exam Status")
        st.button("Exit to Dashboard", on_click=reset_app)
        st.write("---")
        st.write(f"**User**: {session.get('candidate_name')}")
        st.write(f"**Phase**: {session.get('status')}")
        st.write(f"**Score**: {session.get('current_score')} / {session.get('total_questions_count')}")
        if session.get("topics"):
            st.info(f"topics: {', '.join(session['topics'])}")

    # Phase Logic
    
    if session["status"] == "EXAM_LOOP":
        questions = session.get("questions", [])
        idx = session.get("current_question_index", 0)
        st.session_state.current_q_index = idx # Store for callbacks
        
        if idx < len(questions):
            q = questions[idx]
            
            # --- RESULT VIEW ---
            if st.session_state.last_result:
                res = st.session_state.last_result
                
                # 1. Show Question Context First (User Request)
                st.subheader(f"Question {idx + 1} Analysis")
                st.markdown(f"**Question:** {q['question_text']}")
                
                if q["type"] == "MCQ" and q.get("options"):
                    st.write("Options:")
                    for opt in q["options"]:
                        st.text(f"- {opt}")
                
                st.write("---")

                # 2. Status
                if res["is_correct"]:
                    st.success("✅ **Correct Answer!**")
                else:
                    st.error("❌ **Incorrect Answer**")
                
                # 3. Explanation
                with st.expander("📝 Detailed Feedback & Analysis", expanded=True):
                    st.markdown(res["explanation"])
                
                st.button("Next Question ➡", on_click=next_question, type="primary")
            
            # --- QUESTION VIEW ---
            else:
                st.subheader(f"Question {idx + 1} ({q['type']})")
                st.progress((idx) / session.get("total_questions_count", 5))
                st.markdown(f"### {q['question_text']}")
                
                if q.get("constraints"):
                    st.info(f"**Constraints:** {q['constraints']}")

                # Different Input Modes
                key_suffix = f"_{idx}"
                if q["type"] == "MCQ" and q.get("options"):
                    st.radio("Choose Option", q["options"], key=f"answer_radio_input{key_suffix}", index=None)
                
                elif q["type"] in ["CODING", "SQL", "OPTIMIZATION", "DEBUGGING"]:
                    st.write("Write your solution below:")
                    st.caption("💡 Tip: Press **Ctrl + Enter** or click the **Save** (floppy disk) icon inside the editor to ensure your code is captured before submitting.")
                    # Code Editor Support
                    lang = "sql" if q["type"] == "SQL" else "python"
                    editor_key = f"code_editor_data{key_suffix}"
                    editor_res = code_editor("", lang=lang, height=300, key=editor_key)
                    
                    # Store in a separate manual key to avoid widget conflict
                    if editor_res and editor_res.get('text'):
                         st.session_state[f"manual_code_input_{idx}"] = editor_res['text']
                
                elif q["type"] == "ARCHITECTURE":
                    st.write("Describe your architecture or upload a diagram:")
                    st.file_uploader("Upload Diagram (Optional)", type=["png", "jpg", "pdf"], key=f"file_uploader{key_suffix}")
                    st.text_area("Architecture Description", height=200, key=f"answer_text_input{key_suffix}")
                
                elif q["type"] in ["PROJECT", "CASE_STUDY", "SCENARIO"]:
                    st.text_area("Detailed Analysis", height=300, key=f"answer_text_input{key_suffix}")
                
                else:
                    # Generic fallback
                    st.text_input("Your Answer", key=f"answer_text_input{key_suffix}")
                
                # Voice Input Section
                st.write("---")
                st.caption("Voice Submission (Optional)")
                try:
                    st.audio_input("Record Answer", key=f"audio_answer{key_suffix}")
                except AttributeError:
                    st.file_uploader("Upload Audio Answer", type=["wav", "mp3", "m4a"], key=f"audio_answer{key_suffix}")

                st.button("Submit Answer", on_click=submit_answer, type="primary")

    elif session["status"] == "COMPLETED":
        st.balloons()
        st.success("Assessment Completed Successfully!")
        st.markdown(f"### Final Score: {session.get('current_score')} / {session.get('total_questions_count')}")
        st.write("Detailed breakdown and feedback report would be generated here.")
        
        st.button("Return to Dashboard", on_click=reset_app)
