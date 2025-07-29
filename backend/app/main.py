# main.py (Altered)

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn # For running the FastAPI app
from dotenv import load_dotenv
import os
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

print("Loaded DATABASE_URL:", os.getenv("DATABASE_URL"))

# Load variables from .env

# Import the main processing function from your chatbot logic
from chatbot import process_message

# Import the database connection setup from crud.py to ensure it's initialized
# and to potentially run migrations/seed data if needed at startup.
# Although crud.py handles the engine, importing it here ensures the DATABASE_URL
# check and engine creation happen when the app starts.
from crud import engine

app = FastAPI(
    title="Company Asset Chatbot API",
    description="An AI-powered chatbot to answer queries about company assets, employees, and maintenance.",
    version="1.0.0",
)

# --- CORS (Cross-Origin Resource Sharing) ---
# This is essential for allowing your React frontend to communicate with this backend.

origins = [
    "http://localhost:3000",  # The default port for React's development server
    "http://localhost:3001",  # Another common port
    "http://localhost",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # List of origins that are allowed to make requests
    allow_credentials=True,      # Allow cookies to be included in requests
    allow_methods=["*"],         # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],         # Allow all headers
)

class Query(BaseModel):
    """
    Pydantic model for incoming chat queries.
    """
    question: str

@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs when the FastAPI application starts up.
    Can be used for database initialization, loading models, etc.
    """
    print("Application startup: Initializing...")
    # You might want to run database migrations or seed data here.
    # For example, to create tables if they don't exist (uncomment for first run):
    from db import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    #
    # Or to run your seed_data.sql:
    # from crud import execute_write_query
    # with open("seed_data.sql", "r") as f:
    #     sql_script = f.read()
    #     # This is a simplified execution. For complex scripts, you might need
    #     # to split by semicolon and execute each statement.
    #     # await execute_write_query(sql_script)
    print("Application startup: Initialization complete.")


@app.post("/chat")
async def chat(query: Query):
    """
    Endpoint to process user chat queries and return a response.
    """
    try:
        # Use the process_message function from chatbot.py to get the answer
        response_text = await process_message(query.question)
        return {"answer": response_text}
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error processing chat message: {e}")
        # Return a more generic error message to the user
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your request.")

# To run this application, you would typically use:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Ensure you are in the directory containing main.py and other modules (chatbot.py, crud.py, etc.)
# And that your environment variables (DATABASE_URL, REDIS_HOST, etc.) are set.

if __name__ == "__main__":
    # This block allows you to run the app directly using `python main.py`
    # For production, use `uvicorn main:app` directly.
    # Ensure DATABASE_URL and Redis environment variables are set before running.
    # Example:
    # export DATABASE_URL="postgresql+asyncpg://postgres:Sarvesh@2003@localhost:5432/chatbot"
    # export REDIS_HOST="localhost"
    # export REDIS_PORT="6379"
    # export REDIS_DB="0"
    uvicorn.run(app, host="0.0.0.0", port=8000)