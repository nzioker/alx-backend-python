import time
import sqlite3 
import functools

def with_db_connection(func):
    """Decorator that automatically handles database connections."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            result = func(conn, *args, **kwargs)
            return result
        finally:
            conn.close()
    return wrapper

def retry_on_failure(retries=3, delay=2):
    """Decorator that retries the function if it raises an exception."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < retries - 1:
                        print(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

# Example usage
if __name__ == "__main__":
    # Create test database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO users (name, email) VALUES ('John Doe', 'john@example.com')")
    conn.commit()
    conn.close()
    
    # Attempt to fetch users with automatic retry on failure
    users = fetch_users_with_retry()
    print(users)
