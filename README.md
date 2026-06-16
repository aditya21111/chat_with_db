# 💬 Chat with DB

An AI-powered Streamlit application that lets you **chat with any SQL database** using natural language. Built with LangChain, LangGraph, and Groq (DeepSeek-R1-Distill-Llama-70B), the app converts your questions into SQL queries and returns human-readable answers — with streaming responses and conversation memory.

---

## ✨ Features

- **Natural Language to SQL** — Ask questions in plain English; the AI agent writes and executes SQL for you.
- **Multiple Connection Methods**:
  - 🔗 Connect via a database URL (SQLite, PostgreSQL, MySQL, etc.)
  - 📤 Upload a `.db` / `.sqlite` / `.sqlite3` file directly
  - 📚 Use the bundled sample **Books** database (credit: [sample-db.net](https://sample-db.net))
- **Streaming Responses** — See the AI's answer appear token-by-token in real time.
- **Conversation Memory** — Follow-up questions maintain context within a session, with automatic summarization of older messages to stay within context limits.
- **Bring Your Own Key** — Optionally enter your own Groq API key from the sidebar.
- **Read-Only Safety** — The agent is instructed never to run DML statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`).
- **Auto-Formatted Output** — Results with more than 3 records are returned as markdown tables.

---

## 📁 Project Structure

```
chat_with_db/
├── main.py            # Streamlit app — UI, agent setup, and streaming logic
├── books.sqlite       # Sample SQLite database (books dataset)
├── requirements.txt   # Python dependencies
├── .env               # Environment variables 
└── README.md          # This file
```

---

## 🛠️ Tech Stack

| Layer        | Technology                          |
| ------------ | ----------------------------------- |
| LLM          | Groq — `deepseek-r1-distill-llama-70b` |
| Framework    | LangChain + LangGraph               |
| SQL Toolkit  | LangChain `SQLDatabaseToolkit`       |
| UI           | Streamlit                            |
| DB Drivers   | SQLAlchemy, PyMySQL, Psycopg2        |

---

## 🚀 Getting Started

### Prerequisites

- Python **3.13+**
- A [Groq API key](https://console.groq.com/)
- *(Optional)* A [LangChain API key](https://smith.langchain.com/) for tracing

### 1. Clone the repository

```bash
git clone https://github.com/aditya21111/chat_with_db.git
cd chat-with-db
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key_here   # optional
```

### 5. Run the app

```bash
streamlit run main.py
```

The app will open in browser.

---

## 💡 Usage

1. **Choose a connection method** from the sidebar:
   - Paste a database URL (e.g. `sqlite:///mydata.db`, `postgresql://user:pass@host/dbname`)
   - Upload a SQLite file
   - Or just use the built-in sample Books database
2. **Ask questions** in the chat input — for example:
   - *"How many books are in the database?"*
   - *"Show me the top 5 highest-rated books"*
   - *"Which authors have more than 3 books?"*
3. The agent generates SQL, runs it, and streams the answer back to you.

---


