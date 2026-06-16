from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
import tempfile
import os
from dotenv import load_dotenv
import uuid
from langchain_core.messages import AIMessageChunk
from pathlib import Path
from langchain.agents.middleware import SummarizationMiddleware


load_dotenv()
api_key_local=os.getenv('GROQ_API_KEY')

import streamlit as st

api_prod=st.sidebar.text_input(type='password',label='Enter your groq api key')

if api_prod:
    llm=ChatGroq(model='qwen/qwen3-32b',streaming=True,api_key=api_prod,temperature=0.6,top_p=0.95,reasoning_format='hidden')
    summarization_llm=ChatGroq(model='llama-3.3-70b-versatile',api_key=api_prod)
else:
    llm=ChatGroq(model='qwen/qwen3-32b',streaming=True,api_key=api_key_local,temperature=0.6,top_p=0.95,reasoning_format='hidden')
    summarization_llm=ChatGroq(model='llama-3.3-70b-versatile',api_key=api_key_local)


def connect_db(uri, llm):
    try:
        db = SQLDatabase.from_uri(uri)
        toolkit = SQLDatabaseToolkit(db=db,llm=llm)
        st.success("Connected successfully")
        return toolkit.get_tools(),db.dialect
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None,None



#streamlit settings for storing messages
if 'messages' not in st.session_state:
    st.session_state['messages']=[
        {'role':'assistant','content':'hi i am your db assistant.you can ask me any information from db.'}
    ]

if 'thread_id' not in st.session_state:
    st.session_state['thread_id']=str(uuid.uuid4())

if "memory" not in st.session_state:
    st.session_state.memory = InMemorySaver()

if 'current_db' not in st.session_state:
    st.session_state.current_db=None

for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])




db_tools = None 
dialect=None

radio_opt=['connect through url','upload db','load sample books db']
selected_opt=st.sidebar.radio(label='Choose the way you want to connect the db',options=radio_opt)
if radio_opt.index(selected_opt)==1:

    uploaded_file=st.sidebar.file_uploader(label='upload .db or .sqlite file',accept_multiple_files=False,type=["db", "sqlite", "sqlite3"])

    if uploaded_file is not None:
        # Identify the uploaded file by name + size to detect new uploads
        file_identity = f"{uploaded_file.name}_{uploaded_file.size}"

        # Only create a new temp file if this is a different upload
        if st.session_state.get('uploaded_file_id') != file_identity:
            # Clean up previous temp file if it exists
            prev_path = st.session_state.get('uploaded_tmp_path')
            if prev_path and os.path.exists(prev_path):
                os.unlink(prev_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                st.session_state['uploaded_tmp_path'] = tmp_file.name
                st.session_state['uploaded_file_id'] = file_identity

        # Reuse the cached temp file path on every rerun
        sqlite_uri = f"sqlite:///{st.session_state['uploaded_tmp_path']}"
        new_db=sqlite_uri
        db_tools,dialect=connect_db(sqlite_uri,llm)

    else:
        st.info('Please upload a .db or .sqlite file to get started.')

elif radio_opt.index(selected_opt)==0:
    url=st.sidebar.text_input(label='enter the url to connect to the db (locally or hosted)')
    if url:
        new_db=url
        db_tools,dialect=connect_db(url,llm)

else:
    st.sidebar.markdown('A sample books db will be used . credit : https://sample-db.net')
    BASE_DIR = Path(__file__).parent
    db_path = BASE_DIR / "books.sqlite"
    sqlite_uri = f"sqlite:///{db_path}"
    new_db=sqlite_uri
    db_tools,dialect=connect_db(sqlite_uri,llm)





if db_tools is None:
    st.info("Connect a database from sidebar to start chatting.")



  
else:

    if st.session_state.current_db!=new_db:
        st.session_state.current_db=new_db
        st.session_state['thread_id']=str(uuid.uuid4())
        st.session_state.memory = InMemorySaver()
        st.session_state.messages = [
    {
        'role': 'assistant',
        'content': 'Connected to new database. How can I help?'
    }
]


        #system prompt for SQL agent
    generate_query_system_prompt = """You are a SQL analyst that queries a {dialect} database. Follow these rules strictly.

For EVERY question, you MUST do these steps in order:
1. Call `sql_db_list_tables` to list tables.
2. Call `sql_db_schema` on relevant tables to get exact column names and types.
3. For any text/string column you need to filter on, FIRST run a broad search to find exact values, e.g., `SELECT DISTINCT column_name FROM table_name WHERE LOWER(column_name) LIKE '%partial_value%' LIMIT 10`. Use the exact values you find.
4. Write your query, then call `sql_db_query_checker` to validate it.
5. Call `sql_db_query` to execute.

Text filtering rules (MUST follow):
- NEVER use `=` for text columns. ALWAYS use `LOWER(column) LIKE '%value%'` for text matching.
- Never assume how values are stored. Always sample actual values first as described in step 3.

If you get 0 results:
- Do NOT say "not found" immediately.
- Run a broader search, e.g., `SELECT DISTINCT column_name FROM table_name WHERE LOWER(column_name) LIKE '%partial_value%' LIMIT 10` on the column you filtered, and show the user what values exist.
- Try exploring related columns or using even broader matches and retry.
- Only say "not found" after you have verified and shown the actual values in the column.

Query rules:
- Never use `SELECT *`. Select only needed columns.
- LIMIT to {top_k} rows unless user asks for more.
- Use aggregate functions (COUNT, SUM, AVG) for aggregate questions.
- Never run INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.

Output:
- More than 3 records → markdown table.
- Report only exact database values. Never estimate or invent data.
""".format(
        dialect=dialect,
        top_k=5,
    )

   

    agent=create_agent(
            model=llm,
            tools=db_tools,
            system_prompt=generate_query_system_prompt,
            middleware=[ SummarizationMiddleware(
            model=summarization_llm,
            trigger=('messages',10), #when length of messages reached 10,
            keep=('messages',4) # do not summarize recent top 4
        )],
            checkpointer=st.session_state.memory,

        )
    prompt=st.chat_input(placeholder='What you want to know from your db')
    if prompt:
        st.chat_message('human').write(prompt)
        st.session_state.messages.append({'role':'human','content':prompt})

        with st.chat_message("assistant"):
            placeholder = st.empty()
            final_response = ""

            for chunk, metadata in agent.stream(
                {
                    "messages": [("user", prompt)]
                },
                config={
                    "configurable": {
                        "thread_id": st.session_state.thread_id
                    }
                },
                stream_mode="messages"
            ):

                if isinstance(chunk, AIMessageChunk):
                    # Filter out empty chunks and the summarization middleware leaks
                    if isinstance(chunk.content, str) and chunk.content:
                        if "## SESSION INTENT" not in chunk.content and "SUMMARY" not in chunk.content:
                            final_response += chunk.content
                            placeholder.markdown(final_response + "▌")
                            
            placeholder.markdown(final_response)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": final_response
                }
            )





