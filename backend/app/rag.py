# rag.py (Altered)

import google.generativeai as genai
import os
import json # For formatting JSON output
from typing import List, Dict, Any, Optional
import asyncio # For running synchronous LLM calls in a thread pool

# Import CRUD operations for database interaction
from crud import execute_read_query
# Import models to provide schema context to the LLM
from models import Department, Employee, Asset, MaintenanceLog, Vendor, AssetVendorLink
from sqlalchemy import inspect # To inspect schema if needed for LLM prompt


# --- Configuration for Google Generative AI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL_NL_TO_SQL = os.getenv("LLM_MODEL_NAME", 'gemini-pro') # Use LLM_MODEL_NAME from env
GEMINI_MODEL_QA = os.getenv("LLM_MODEL_NAME", 'gemini-pro')       # Use LLM_MODEL_NAME from env


# --- Helper Function to get Database Schema ---
def get_db_schema_representation() -> str:
    """
    Generates a string representation of the database schema based on SQLAlchemy models.
    This will be fed to the LLM for NL-to-SQL generation.
    """
    schema_parts = []
    # Loop through all defined models inherited from Base
    for model_class in [Department, Employee, Asset, MaintenanceLog, Vendor, AssetVendorLink]:
        table_name = model_class.__tablename__
        columns = []
        for col in model_class.__table__.columns:
            col_type = str(col.type).split('(')[0] # e.g., 'VARCHAR' from 'VARCHAR(255)'
            is_pk = "PK" if col.primary_key else ""
            is_fk = ""
            if col.foreign_keys:
                for fk in col.foreign_keys:
                    is_fk += f" FK->{fk.column.table.name}.{fk.column.name}"
            columns.append(f"  - {col.name} ({col_type}{is_pk}{is_fk})")
        
        # Add relationships for context
        relationships = []
        for prop in model_class.__mapper__.relationships:
            relationships.append(f"  - {prop.key} (relates to {prop.mapper.class_.__tablename__})")
        
        schema_parts.append(f"Table: {table_name}\nColumns:\n" + "\n".join(columns) + "\nRelationships:\n" + "\n".join(relationships) + "\n")
    
    return "\n".join(schema_parts)


# Global variable to store schema representation once
_DB_SCHEMA_STR = get_db_schema_representation()


# --- Main RAG and NL-to-SQL Functions ---

async def answer_with_llm(user_query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Answers a user query using an LLM, leveraging provided context chunks.
    This is the general RAG function, typically used as a fallback or for general knowledge.
    """
    
    # Prepare context for the prompt
    context_text = "\n\n".join([chunk["page_content"] if hasattr(chunk, 'page_content') else str(chunk) for chunk in context_chunks])
    
    prompt = (
        "You are an expert Q&A assistant for company asset management. "
        "Use the provided context below to answer the user's question accurately and concisely. "
        "If the answer is not in the context, state that you don't have enough information.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {user_query}\nAnswer:"
    )

    model = genai.GenerativeModel(GEMINI_MODEL_QA)
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, model.generate_content, prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content with LLM: {e}")
        return "Sorry, I am currently unable to generate a response."


async def answer_query_nl_to_sql(user_query: str) -> str:
    """
    Translates a natural language query into SQL, executes it, and returns the result.
    This function handles the core NL-to-SQL logic.
    """
    loop = asyncio.get_event_loop()

    schema_prompt = (
        "You are an expert PostgreSQL database assistant. "
        "Your task is to convert natural language questions into executable SQL queries. "
        "Only generate the SQL query, without any additional text, explanations, or backticks. "
        "Ensure the SQL query is syntactically correct and uses the provided schema. "
        "If the question cannot be answered by the database schema, respond with 'N/A'.\n\n"
        "Here is the database schema:\n"
        f"{_DB_SCHEMA_STR}\n"
        "IMPORTANT: Always use 'status' column from 'assets' table for maintenance queries. "
        "For employee names, ensure case-insensitivity if possible or use LIKE. "
        "For 'last service date', join 'Asset_Vendor_Link' with 'Assets' on 'asset_id' and 'id'.\n"
        "Example Queries:\n"
        "-- Get assets under maintenance\n"
        "SELECT asset_tag, name, location FROM Assets WHERE status = 'Under Maintenance';\n"
        "-- Get last service date for an asset (e.g., GNT-243)\n"
        "SELECT avl.service_type, avl.last_service_date FROM Asset_Vendor_Link avl JOIN Assets a ON avl.asset_id = a.id WHERE a.asset_tag = 'GNT-243';\n"
        "-- Get designation of an employee (e.g., John Doe)\n"
        "SELECT designation FROM Employees WHERE name = 'John Doe';\n\n"
        f"Question: {user_query}\nSQL Query:"
    )

    model = genai.GenerativeModel(GEMINI_MODEL_NL_TO_SQL)
    try:
        # Generate the SQL query (run in executor as generate_content is synchronous)
        sql_response = await loop.run_in_executor(None, model.generate_content, schema_prompt)
        generated_sql = sql_response.text.strip()

        if generated_sql.lower() == "n/a" or not generated_sql.lower().startswith("select"):
            return "I couldn't generate a suitable SQL query for that request."

        # Execute the SQL query using crud.py
        print(f"Generated SQL: {generated_sql}") # For debugging
        db_results = await execute_read_query(generated_sql)

        if not db_results:
            return "No results found for your query in the database."
        
        # Format the results for the user
        formatted_results = []
        for row in db_results:
            row_str = ", ".join(f"{k}: {v}" for k, v in row.items())
            formatted_results.append(row_str)
        
        return "Database Results:\n" + "\n".join(formatted_results)

    except Exception as e:
        print(f"Error in NL-to-SQL process: {e}")
        return "An error occurred while trying to fetch data from the database."


# The 'db_chain' concept from LangChain is now primarily handled by
# the 'answer_query_nl_to_sql' function for natural language inputs.
# However, chatbot.py's `answer_query_from_intent` sends raw SQL to `db_chain.run`.
# So, we need a compatible simulator for that.
class DBChainSimulator:
    async def run(self, query: str):
        """
        Executes a raw SQL query using crud.py and formats the results.
        This simulates the behavior of LangChain's SQLDatabaseChain.run for direct SQL execution.
        """
        print(f"Executing raw SQL via db_chain simulator: {query}")
        
        # Ensure it's a SELECT query for read operations
        if not query.strip().upper().startswith("SELECT"):
            print(f"Warning: db_chain simulator received non-SELECT query: {query}. Only SELECT queries are supported for direct fetching.")
            return "Unsupported SQL operation."

        results = await execute_read_query(query)
        
        if not results:
            return "No results" # Compatible with "No results" check in chatbot.py
        
        # Format the results into a string representation
        formatted_results = []
        # Get headers (column names) from the first row's keys
        headers = list(results[0].keys())
        formatted_results.append(", ".join(headers))
        
        # Add data rows
        for row in results:
            formatted_results.append(", ".join(map(str, row.values())))
        
        return "\n".join(formatted_results)

# Instantiate the simulator to be imported by chatbot.py
db_chain = DBChainSimulator()