import redis
import os

# Get Redis connection details from environment variables
# Default to localhost, 6379, db 0 if environment variables are not set
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379)) # Ensure port is an integer
REDIS_DB = int(os.getenv('REDIS_DB', 0))       # Ensure DB is an integer

try:
    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    # Ping the Redis server to check connection immediately
    cache.ping()
    print(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")
    # Depending on your application's needs, you might want to exit here
    # or handle a graceful degradation if caching is not critical.
    cache = None # Set cache to None to indicate a failed connection

def cache_query(key, value):
    if cache:
        try:
            cache.set(key, value, ex=3600)  # Cache for 1 hour
            # print(f"Cached key: {key}") # Optional: for debugging
        except redis.exceptions.ConnectionError as e:
            print(f"Error setting cache for key '{key}': {e}")
    else:
        print("Cache is not available. Cannot set key.")

def get_cached_query(key):
    if cache:
        try:
            # print(f"Attempting to retrieve key: {key}") # Optional: for debugging
            return cache.get(key)
        except redis.exceptions.ConnectionError as e:
            print(f"Error getting cache for key '{key}': {e}")
            return None
    else:
        print("Cache is not available. Cannot get key.")
        return None
