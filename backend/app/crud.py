# crud.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text # For executing raw SQL
from typing import List, Dict, Any

# Get database URL from environment variable
# Ensure DATABASE_URL is set in your environment before running the application
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it (e.g., export DATABASE_URL='postgresql+asyncpg://user:password@host:port/database').")

# Create an async SQLAlchemy engine
# 'echo=True' will log all SQL queries, useful for debugging
# pool_size and max_overflow can be adjusted based on anticipated concurrent connections
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)

# Create an async session factory
AsyncSessionLocal = sessionmaker(
    autocommit=False, # Do not commit automatically
    autoflush=False,  # Do not flush automatically
    bind=engine,      # Bind to the async engine
    class_=AsyncSession, # Use AsyncSession for async operations
    expire_on_commit=False, # Prevents objects from being expired after commit
)

async def get_db_session():
    """
    Asynchronous context manager to provide a database session.
    Use with 'async with get_db_session() as session:'
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            print(f"Session error: {e}")
            raise
        finally:
            await session.close()

async def execute_read_query(query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Executes a read-only SQL query and returns all results as a list of dictionaries.
    Args:
        query (str): The SQL query string.
        params (Dict[str, Any], optional): Dictionary of parameters to pass to the query.
                                          SQLAlchemy uses named parameters (e.g., :param_name).
                                          Defaults to None.
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a row.
                              Returns an empty list if no results or on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(query), params)
            # Fetch all rows and return as list of dictionaries for easier consumption
            return [row._asdict() for row in result.mappings().all()]
        except Exception as e:
            print(f"Error executing read query: {e}")
            return []

async def execute_write_query(query: str, params: Dict[str, Any] = None) -> int:
    """
    Executes a write SQL query (INSERT, UPDATE, DELETE) and returns the number of rows affected.
    Args:
        query (str): The SQL query string.
        params (Dict[str, Any], optional): Dictionary of parameters to pass to the query.
                                          Defaults to None.
    Returns:
        int: Number of rows affected. Returns -1 on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(query), params)
            await session.commit() # Commit the transaction
            return result.rowcount
        except Exception as e:
            await session.rollback() # Rollback in case of error
            print(f"Error executing write query: {e}")
            return -1

# --- Example CRUD functions for Assets (based on chatbot.py queries) ---
# You can define similar functions for Employees and Asset_Vendor_Link tables.

async def get_all_assets() -> List[Dict[str, Any]]:
    """Fetches all assets from the database."""
    query = "SELECT id, asset_tag, name, status, location FROM Assets;"
    return await execute_read_query(query)

async def get_asset_details_by_tag(asset_tag: str) -> List[Dict[str, Any]]:
    """Fetches details for a specific asset by its tag."""
    query = "SELECT id, asset_tag, name, status, location FROM Assets WHERE asset_tag = :asset_tag;"
    return await execute_read_query(query, {"asset_tag": asset_tag})

async def get_assets_under_maintenance() -> List[Dict[str, Any]]:
    """Fetches assets currently under maintenance."""
    query = "SELECT asset_tag, name, location FROM Assets WHERE status = 'Under Maintenance';"
    return await execute_read_query(query)

async def get_last_service_date_for_asset(asset_tag: str) -> List[Dict[str, Any]]:
    """Fetches the last service date for a specific asset."""
    query = """
    SELECT v.service_type, v.last_service_date
    FROM Asset_Vendor_Link v
    JOIN Assets a ON v.asset_id = a.id
    WHERE a.asset_tag = :asset_tag;
    """
    return await execute_read_query(query, {"asset_tag": asset_tag})

async def get_employee_designation(employee_name: str) -> List[Dict[str, Any]]:
    """Fetches the designation of an employee by name."""
    query = "SELECT designation FROM Employees WHERE name = :employee_name;"
    return await execute_read_query(query, {"employee_name": employee_name})

# Example: Adding a new asset
async def add_new_asset(asset_tag: str, name: str, status: str, location: str) -> int:
    """Adds a new asset to the Assets table."""
    query = """
    INSERT INTO Assets (asset_tag, name, status, location)
    VALUES (:asset_tag, :name, :status, :location);
    """
    return await execute_write_query(query, {
        "asset_tag": asset_tag,
        "name": name,
        "status": status,
        "location": location
    })

# Example: Updating an asset's status
async def update_asset_status(asset_tag: str, new_status: str) -> int:
    """Updates the status of an existing asset."""
    query = "UPDATE Assets SET status = :new_status WHERE asset_tag = :asset_tag;"
    return await execute_write_query(query, {
        "new_status": new_status,
        "asset_tag": asset_tag
    })

# Example: Deleting an asset
async def delete_asset_by_tag(asset_tag: str) -> int:
    """Deletes an asset from the Assets table by its tag."""
    query = "DELETE FROM Assets WHERE asset_tag = :asset_tag;"
    return await execute_write_query(query, {"asset_tag": asset_tag})