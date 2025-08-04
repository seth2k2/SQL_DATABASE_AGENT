import streamlit as st
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain import hub
from langgraph.prebuilt import create_react_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
import pyodbc
import pandas as pd

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="SQL Database Assistant",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'db' not in st.session_state:
    st.session_state.db = None
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False

@st.cache_resource
def initialize_database():
    """Initialize the database connection"""

    #db = SQLDatabase.from_uri('sqlite:///classicmodels.db') initally used local db classicmodels.db for testing purposes

    try:
        # Get the connection string from environment variables
        connection_string = os.getenv("CONNECTION_STRING")
        
        if not connection_string:
            st.error("CONNECTION_STRING not found in .env file.")
            return None
        
        # Remove quotes if they exist in the connection string
        connection_string = connection_string.strip("'\"")
        
        # Convert pyodbc connection string to SQLAlchemy format
        # Replace the pyodbc format with SQLAlchemy format
        sqlalchemy_connection_string = f"mssql+pyodbc:///?odbc_connect={connection_string}"
        
        # Initialize database connection
        db = SQLDatabase.from_uri(sqlalchemy_connection_string)
        return db
    except Exception as e:
        st.error(f"Error connecting to Azure SQL Server: {e}")
        st.error("Please verify your connection string and network connectivity.")
        return None

@st.cache_resource
def initialize_agent(_db):
    """Initialize the SQL agent"""
    try:
        # Initialize LLM using OpenRouter.ai
        llm = init_chat_model(
            model="openai/gpt-4o-mini",
            model_provider="openai",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
        # Initialize the toolkit
        toolkit = SQLDatabaseToolkit(db=_db, llm=llm)
        tools = toolkit.get_tools()
        
        # Get prompt template
        prompt_template = hub.pull('langchain-ai/sql-agent-system-prompt')
        system_message = prompt_template.format(dialect='SQLite', top_k=5)
        
        # Create the SQL AI agent
        sql_agent = create_react_agent(llm, tools, prompt=system_message)
        
        return sql_agent
    except Exception as e:
        st.error(f"Error initializing agent: {e}")
        return None

def get_table_info(db, table_name):
    """Get information about a specific table"""
    try:
        # Get table schema
        query = f"PRAGMA table_info({table_name})"
        result = db.run(query)
        return result
    except Exception as e:
        return f"Error getting table info: {e}"

def get_sample_data(db, table_name, limit=5):
    """Get sample data from a table"""
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        result = db.run(query)
        return result
    except Exception as e:
        return f"Error getting sample data: {e}"

def main():
    st.title("🗄️ SQL Database Assistant")
    st.markdown("Ask questions about your database in plain English!")
    
    # Initialize database
    if st.session_state.db is None:
        with st.spinner("Connecting to database..."):
            st.session_state.db = initialize_database()
    
    if st.session_state.db is None:
        st.error("Failed to connect to database. Please check your database file.")
        return
    
    # Initialize agent
    if st.session_state.agent is None:
        with st.spinner("Initializing AI agent..."):
            st.session_state.agent = initialize_agent(st.session_state.db)
    
    if st.session_state.agent is None:
        st.error("Failed to initialize AI agent. Please check your API key.")
        return
    
    # Sidebar - Database Information
    with st.sidebar:
        st.header("📊 Database Tables")
        
        # Get table names
        try:
            table_names = st.session_state.db.get_usable_table_names()
            
            # Display tables with expandable info
            for table_name in table_names:
                with st.expander(f"📋 {table_name}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(f"Schema", key=f"schema_{table_name}"):
                            st.session_state[f"show_schema_{table_name}"] = True
                    
                    with col2:
                        if st.button(f"Sample", key=f"sample_{table_name}"):
                            st.session_state[f"show_sample_{table_name}"] = True
                    
                    # Show schema if requested
                    if st.session_state.get(f"show_schema_{table_name}", False):
                        schema_info = get_table_info(st.session_state.db, table_name)
                        st.text(schema_info)
                    
                    # Show sample data if requested
                    if st.session_state.get(f"show_sample_{table_name}", False):
                        sample_data = get_sample_data(st.session_state.db, table_name)
                        st.text(sample_data)
            
        except Exception as e:
            st.error(f"Error getting table names: {e}")
    
    # Main content area
    st.header("💬 Ask Your Question")
    
    # Sample questions
    st.markdown("**Example questions you can ask:**")
    example_questions = [
        "How many customers are in the database?",
        "What are the top 10 best-selling products?",
        "Show me customers from France",
        "What's the total revenue by product line?",
        "Which employees have the most sales?",
        "Show me orders from the last month"
    ]
    
    selected_example = st.selectbox(
        "Choose an example question or write your own:",
        [""] + example_questions
    )
    
    # Check if clear button was pressed
    if st.session_state.clear_input:
        selected_example = ""
        st.session_state.clear_input = False
    
    # Text input for user query
    user_query = st.text_area(
        "Enter your question about the database:",
        value=selected_example if selected_example else "",
        height=100,
        placeholder="e.g., Show me the top 5 customers by order value"
    )
    
    # Query button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        query_button = st.button("🔍 Run Query", type="primary")
    
    with col_btn2:
        clear_button = st.button("🗑️ Clear")
    
    if clear_button:
        st.session_state.clear_input = True
        st.rerun()
    
    # Execute query when button is pressed
    if query_button and user_query.strip():
        with st.spinner("🤖 AI is processing your query..."):
            try:
                # Create a container for the results
                results_container = st.container()
                
                with results_container:
                    st.header("📊 Query Results")
                    
                    # Stream the agent's response
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # Execute the agent
                    for event in st.session_state.agent.stream(
                        {"messages": [('user', user_query)]},
                        stream_mode='values'
                    ):
                        if 'messages' in event and len(event['messages']) > 0:
                            latest_message = event['messages'][-1]
                            if hasattr(latest_message, 'content'):
                                full_response = latest_message.content
                                response_placeholder.markdown(full_response)
                    
            except Exception as e:
                st.error(f"Error executing query: {e}")
                st.error("Please check your API key and database connection.")
    
    elif query_button and not user_query.strip():
        st.warning("⚠️ Please enter a question before running the query.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            🤖 Powered by LangChain & OpenRouter.ai | 🗄️ Azure SQL Server
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
