# 🎓 Data Engineering Exam Simulator

An AI-powered mock interview platform designed to simulate realistic Data Engineering technical assessments. This application generates custom exam scenarios, evaluates answers using advanced LLMs (OpenAI GPT-4o / Google Gemini), and provides detailed, actionable feedback with revision notes.

## 🚀 Features

*   **🤖 Multi-Model AI Support**: Choose between **OpenAI (GPT-4o)** and **Google (Gemini Pro)** for question generation and evaluation.
*   **🎙️ Voice-First Experience**: Answer questions using your voice (powered by OpenAI Whisper) to simulate real interview pressure.
*   **💻 Integrated Code Editor**: Write and execute Python/SQL solutions directly within the browser using a VS Code-like editor.
*   **📝 Structured Feedback**: deeply analytical feedback including:
    *   ✅ **Analysis**: Why your answer is correct/incorrect.
    *   ❌ **Distractor Analysis**: Why other MCQ options were wrong.
    *   📖 **Revision Notes**: High-yield bullet points for quick study.
    *   🔗 **Resources**: Related topics and learning materials.
*   **📊 Exam History Dashboard**: Resume incomplete exams or review past performance.
*   **⚙️ Customizable Exams**: Set difficulty, topics (Spark, Kafka, SQL, AWS), and question types (MCQ, Coding, System Design).

## 🛠️ Tech Stack

*   **Frontend**: Streamlit
*   **Backend**: FastAPI, Uvicorn
*   **AI/ML**: OpenAI API (GPT-4o, Whisper), Google Generative AI (Gemini Pro)
*   **Storage**: JSON-based file storage (local)

## 📦 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Pathik-code/llmBasedTestSimulator.git
    cd llmBasedTestSimulator
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv myenv
    # Windows
    .\myenv\Scripts\activate
    # Mac/Linux
    source myenv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=sk-your-openai-key
    GEMINI_API_KEY=your-gemini-key
    ```

## 🏃‍♂️ Running the Application

This project runs as two separate services: Backend and Frontend.

**1. Start the Backend API**
```bash
uvicorn backend.app.main:app --reload
```
*Server will start at `http://127.0.0.1:8000`*

**2. Start the Frontend UI** (Open a new terminal)
```bash
streamlit run frontend/app.py
```
*App will open at `http://localhost:8501`*

## 📂 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/            # API Routes
│   │   ├── logic/          # Exam Orchestration & Storage
│   │   ├── services/       # LLM Integration (OpenAI/Gemini)
│   │   └── models.py       # Pydantic Models
├── frontend/
│   └── app.py              # Streamlit Application
├── data/
│   └── sessions/           # Exam session storage (JSON)
├── requirements.txt
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.
