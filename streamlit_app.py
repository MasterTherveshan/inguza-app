import streamlit as st
from openai import OpenAI
from utils import (
    delete_files,
    delete_thread,
    EventHandler,
    render_custom_css,
    render_download_files,
    retrieve_messages_from_thread,
    retrieve_assistant_created_files
)
import requests
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

# -------------------------------------------------------------------
# Page Setup & Custom Styling
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Bond Analysis Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Enhanced custom CSS with dark theme
st.markdown("""
    <style>
        /* Global theme */
        .stApp {
            background-color: #0E1117;
            color: #E0E0E0;
        }
        
        /* Main container styling */
        .block-container {
            padding: 2rem 3rem;
        }
        
        /* Headers styling */
        h1 {
            color: #2196F3;
            font-family: 'Helvetica Neue', sans-serif;
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        h2, h3 {
            color: #2196F3;
            font-family: 'Helvetica Neue', sans-serif;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Chat container */
        .chat-container {
            background-color: #1A1F25;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Input field styling */
        .stTextInput > div > div > input {
            background-color: #2D3748;
            color: white;
            border: 1px solid #4A5568;
            border-radius: 8px;
            padding: 1rem;
            font-size: 16px;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #2196F3;
            box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #2196F3;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .stButton > button:hover {
            background-color: #1976D2;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transform: translateY(-1px);
        }
        
        /* Quick queries section */
        .quick-queries {
            background-color: #1A1F25;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
        }
        
        /* Chat messages */
        .user-message {
            background-color: #2D3748;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .assistant-message {
            background-color: #1A1F25;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #2196F3;
        }
        
        /* Code blocks */
        .stCodeBlock {
            background-color: #2D3748 !important;
            border-radius: 8px;
        }
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Spinner */
        .stSpinner > div {
            border-top-color: #2196F3 !important;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #1A1F25;
        }
        
        /* Status indicators */
        .status-online {
            color: #4CAF50;
            font-size: 0.8rem;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "login_status": False,
        "username": None,
        "thread_id": None,
        "text_boxes": [],
        "assistant_created_file_ids": [],
        "download_files": [],
        "download_file_names": [],
        "code_input": [],
        "code_output": [],
        "assistant_text": [""],
        "file": None,
        "file_uploaded": False,
        "read_terms": False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Ensure code_input and code_output are lists
    if not isinstance(st.session_state.code_input, list):
        st.session_state.code_input = []
    if not isinstance(st.session_state.code_output, list):
        st.session_state.code_output = []

init_session_state()

# -------------------------------------------------------------------
# Login Page
# -------------------------------------------------------------------
def login_page():
    st.markdown("""
        <div style='padding: 2rem; text-align: center;'>
            <h1 style='color: #2196F3; font-size: 2.5rem; margin-bottom: 2rem;'>
                Bond Analysis Assistant
            </h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container():
            st.markdown("---")
            st.markdown("""
                <div style='background-color: #1A1F25; padding: 2rem; border-radius: 10px; margin: 1rem 0;'>
                    <h2 style='color: #2196F3; text-align: center; margin-bottom: 1.5rem;'>Login</h2>
                </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            col1, col2, col3 = st.columns([1,1,1])
            with col2:
                if st.button("Login", use_container_width=True):
                    if username == "admin" and password == "admin":
                        st.session_state["login_status"] = True
                        st.session_state["username"] = username
                        st.success("🎉 Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")

# -------------------------------------------------------------------
# Chat Interface
# -------------------------------------------------------------------
def chat_interface():
    # Top banner with title
    st.markdown("""
        <div style='background-color: #1A1F25; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;'>
            <h1 style='margin: 0;'>Bond Analysis Assistant</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        assistant = client.beta.assistants.retrieve(st.secrets["ASSISTANT_ID"])
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {str(e)}")
        return

    # Create thread if needed
    if not st.session_state["thread_id"]:
        try:
            thread = client.beta.threads.create()
            st.session_state["thread_id"] = thread.id
            if "FILE_ID" in st.secrets:
                client.beta.threads.update(
                    thread_id=thread.id,
                    tool_resources={"code_interpreter": {"file_ids": [st.secrets["FILE_ID"]]}},
                )
        except Exception as e:
            st.error(f"Failed to create thread: {str(e)}")
            return

    # Data Snapshot Section
    st.markdown("<h2>📊 Data Snapshot</h2>", unsafe_allow_html=True)
    try:
        df = pd.read_excel('assets/data.xlsx')
        # Make a copy of the dataframe to avoid SettingWithCopyWarning
        df = df.copy()
        st.markdown("""
            <div style='background-color: #1A1F25; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
                <p style='color: #E0E0E0;'>Preview of available bond data:</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Style the dataframe
        st.dataframe(
            df.head(5),
            use_container_width=True,
            hide_index=True,
            column_config={
                col: st.column_config.Column(
                    width="medium"
                ) for col in df.columns
            }
        )
        
        # Display data info
        st.markdown(f"""
            <div style='background-color: #1A1F25; padding: 1rem; border-radius: 10px; margin-top: 1rem;'>
                <p style='color: #E0E0E0;'>Total records: {len(df):,}</p>
                <p style='color: #E0E0E0;'>Columns: {', '.join(df.columns)}</p>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Unable to load data preview: {str(e)}")

    # Chat section
    st.markdown("<h2>💬 Chat</h2>", unsafe_allow_html=True)
    user_query = st.text_input(
        "Ask your question:",
        placeholder="Type your question here...",
        label_visibility="collapsed"
    )
    if st.button("Submit", use_container_width=True) and user_query.strip():
        submit_question(client, assistant, user_query)

    # Quick queries section
    st.markdown("<h2>📌 Quick Queries</h2>", unsafe_allow_html=True)
    quick_queries = [
        "tell me about the inguza notes since 2008 matured vs unmatured, give me a quarterly bar chart over time with matured vs unmatured",
        "Give me a line chart from 2008 - present at a monthly level of matured vs unmatured inguza notes",
        "Give me a yearly table from 2008 - present of Matured vs Unmatured inguza notes"
    ]
    
    for query in quick_queries:
        if st.button(
            query,
            key=f"quick_{query}",
            use_container_width=True,
            help=f"Click to analyze: {query}"
        ):
            submit_question(client, assistant, query)

    # Chat history
    st.markdown("<h2>📜 Conversation History</h2>", unsafe_allow_html=True)
    assistant_messages = retrieve_messages_from_thread(st.session_state['thread_id'])
    st.session_state.assistant_created_file_ids = retrieve_assistant_created_files(assistant_messages)
    st.session_state.download_files, st.session_state.download_file_names = render_download_files(
        st.session_state.assistant_created_file_ids)

def submit_question(client, assistant, question):
    # Send the question to the assistant
    client.beta.threads.messages.create(
        thread_id=st.session_state["thread_id"],
        role="user",
        content=question,
    )

    # Display the user's question
    st.session_state.text_boxes.append(st.empty())
    st.session_state.text_boxes[-1].success(f"**> 🤔 User:** {question}")

    # Create the optica around returning the response
    with st.spinner("Analyzing your question. Please wait..."):
        with client.beta.threads.runs.stream(
                thread_id=st.session_state["thread_id"],
                assistant_id=assistant.id,
                tool_choice={"type": "code_interpreter"},
                event_handler=EventHandler(),
                temperature=0
        ) as stream:
            stream.until_done()

    st.success("✅ Analysis complete!")

# -------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------
def cleanup():
    if st.session_state["thread_id"]:
        try:
            delete_thread(st.session_state["thread_id"])
        except Exception:
            pass
    
    if st.session_state["assistant_created_file_ids"]:
        try:
            delete_files(st.session_state["assistant_created_file_ids"])
        except Exception:
            pass

st.session_state["_cleanup"] = cleanup

# -------------------------------------------------------------------
# Main App Flow
# -------------------------------------------------------------------
if not st.session_state["login_status"]:
    login_page()
else:
    chat_interface()
