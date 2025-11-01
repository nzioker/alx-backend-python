import mysql.connector
from typing import Generator, Dict, Any


def stream_users() -> Generator[Dict[str, Any], None, None]:
    """
    Generator that streams rows from user_data table one by one
    
    Yields:
        Dictionary with user data: {'user_id': str, 'name': str, 'email': str, 'age': int}
    
    Raises:
        Exception: If database connection or query fails
    """
    connection = None
    cursor = None
    
    try:
        # Establish database connection
        connection = mysql.connector.connect(
            host='localhost',
            user='root',      # Replace with your MySQL username
            password='',      # Replace with your MySQL password
            database='ALX_prodev'
        )
        
        # Create a cursor that doesn't buffer all results
        cursor = connection.cursor(buffered=False)
        
        # Execute query to get all users
        query = "SELECT user_id, name, email, age FROM user_data"
        cursor.execute(query)
        
        # Single loop to yield rows one by one
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            
            # Convert row to dictionary
            user_dict = {
                'user_id': row[0],
                'name': row[1],
                'email': row[2],
                'age': int(row[3]) if row[3] is not None else 0
            }
            
            yield user_dict
            
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        raise Exception(f"Failed to stream users: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection:
            connection.close()
