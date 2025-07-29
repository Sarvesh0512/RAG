from rag import db_chain, answer_query_nl_to_sql
from vector_store import vector_store
import asyncio
import re
from cache import cache_query, get_cached_query # Import caching functions


# Intent keywords dictionary (add more intents as needed)
intents = {
    "assets_under_maintenance": ["under maintenance", "currently under maintenance"],
    "last_service_date": ["last service", "recent service", "last maintenance"],
    "employee_designation": ["designation", "role", "position"],
}

async def get_relevant_docs(message: str):
    """
    Performs similarity search against the vector store to find relevant documents.
    """
    loop = asyncio.get_event_loop()
    # Assuming vector_store.similarity_search is synchronous
    docs = await loop.run_in_executor(None, vector_store.similarity_search, message, 3)
    return docs

async def match_intent(message: str):
    """
    Matches the user's message to a predefined intent based on keywords.
    """
    lowered = message.lower()
    for intent, keywords in intents.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    return None

def extract_asset_tag(message: str):
    """
    Extracts an asset tag (e.g., GNT-243) from the message using regex.
    """
    match = re.search(r'\b[A-Z]{2,}-\d{1,}\b', message)
    if match:
        return match.group(0)
    return None

def extract_employee_name(message: str):
    """
    Extracts an employee name from the message, specifically after "designation of".
    """
    match = re.search(r'designation of ([a-zA-Z ]+)', message.lower())
    if match:
        name = match.group(1).strip()
        # Capitalize each word in name (simple title-case)
        return " ".join(w.capitalize() for w in name.split())
    return None

async def answer_query_from_intent(intent: str, message: str):
    """
    Generates an SQL query and fetches results based on a matched intent.
    """
    query = ""
    result_message = ""

    if intent == "assets_under_maintenance":
        query = """
        SELECT asset_tag, name, location
        FROM Assets
        WHERE status = 'Under Maintenance';
        """
        result = await db_chain.run(query)
        if not result or "No results" in str(result): # Ensure result is string for "No results" check
            result_message = "No assets are currently under maintenance."
        else:
            result_message = result

    elif intent == "last_service_date":
        asset_tag = extract_asset_tag(message)
        if not asset_tag:
            return "I couldn't find an asset tag in your message. Please specify it like 'GNT-243'."
        query = f"""
        SELECT v.service_type, v.last_service_date
        FROM Asset_Vendor_Link v
        JOIN Assets a ON v.asset_id = a.id
        WHERE a.asset_tag = '{asset_tag}';
        """
        result = await db_chain.run(query)
        if not result or "No results" in str(result):
            result_message = f"No service information found for asset '{asset_tag}'."
        else:
            result_message = result

    elif intent == "employee_designation":
        employee_name = extract_employee_name(message)
        if not employee_name:
            return "Please specify the employee name for the designation query."
        query = f"""
        SELECT designation FROM Employees
        WHERE name = '{employee_name}';
        """
        result = await db_chain.run(query)
        if not result or "No results" in str(result):
            result_message = f"No designation found for employee '{employee_name}'."
        else:
            result_message = result

    return result_message or "Sorry, I couldn't find relevant information for your query based on intent."

async def process_message(message: str):
    """
    Processes the incoming message, attempting to answer using a hierarchical approach:
    1. Greetings
    2. Cache lookup
    3. Intent matching
    4. NL-to-SQL
    5. Vector store search (RAG fallback)
    """
    lowered_message = message.lower()

    # 1. Handle simple greetings/farewells
    if lowered_message in ["hi", "hello", "hey"]:
        return "Hello!👋🏻 How can I assist you with company assets today?🤩"
    if lowered_message in ["bye", "goodbye", "tata"]:
        return "Goodbye! Have a great day!🥰"
    if lowered_message in ["thanks", "thank you"]:
        return "You're welcome! If you have any more questions, feel free to ask.🥰"
    if lowered_message in ["hi, how are you?", "hello, how are you?"]:
        return "Hey there! I'm fine, thanks for asking. What can I do for you?🥰"

    # 2. Check cache first for any query
    cached_answer = get_cached_query(message)
    if cached_answer:
        print(f"Returning cached answer for: '{message}'") # For debugging
        return cached_answer.decode('utf-8') # Redis returns bytes, decode to string

    final_answer = ""

    # 3. Match intents
    intent = await match_intent(message)
    if intent:
        final_answer = await answer_query_from_intent(intent, message)
    
    # 4. Try NL-to-SQL if no intent matched or intent-based answer is generic
    if not final_answer or "Sorry, I couldn't find relevant information" in final_answer:
        nl_to_sql_answer = await answer_query_nl_to_sql(message)
        if nl_to_sql_answer and nl_to_sql_answer.strip() != "" and "No results" not in nl_to_sql_answer:
            final_answer = nl_to_sql_answer

    # 5. Finally fallback to vector store search if no SQL answer found
    if not final_answer or "Sorry, I couldn't find relevant information" in final_answer:
        relevant_docs = await get_relevant_docs(message)
        if relevant_docs:
            final_answer = f"I found some related information: {', '.join([doc.page_content for doc in relevant_docs])}"

    # Default fallback if nothing found
    if not final_answer or "Sorry, I couldn't find relevant information" in final_answer:
        final_answer = "Sorry, I couldn't find relevant information for your query."
    
    # Cache the final answer before returning
    cache_query(message, final_answer)
    return final_answer