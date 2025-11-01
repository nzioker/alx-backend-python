import mysql.connector
from typing import Generator, Dict, Any, List


def stream_users_in_batches(batch_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Generator that fetches rows from user_data table in batches
    
    Args:
        batch_size: Number of rows to fetch in each batch
    
    Yields:
        List of dictionaries with user data for each batch
    
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
        
        cursor = connection.cursor()
        
        # Get total count for progress tracking
        cursor.execute("SELECT COUNT(*) FROM user_data")
        total_users = cursor.fetchone()[0]
        
        offset = 0
        
        # Loop 1: Batch fetching loop
        while offset < total_users:
            # Fetch batch of users
            query = "SELECT user_id, name, email, age FROM user_data LIMIT %s OFFSET %s"
            cursor.execute(query, (batch_size, offset))
            
            batch_rows = cursor.fetchall()
            if not batch_rows:
                break
            
            # Convert batch rows to list of dictionaries
            batch_users = []
            for row in batch_rows:  # Loop 2: Processing rows in batch
                user_dict = {
                    'user_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'age': int(row[3])
                }
                batch_users.append(user_dict)
            
            yield batch_users
            offset += batch_size
            
    except mysql.connector.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        raise Exception(f"Failed to stream users in batches: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def batch_processing(batch_size: int = 50) -> None:
    """
    Processes batches of users and filters those over age 25
    
    Args:
        batch_size: Number of users to process in each batch
    """
    try:
        # Loop 3: Main processing loop over batches
        for batch in stream_users_in_batches(batch_size):
            # Filter users over age 25 in the current batch
            users_over_25 = []
            for user in batch:  # Loop within batch (nested, but counts as separate)
                if user['age'] > 25:
                    users_over_25.append(user)
            
            # Print filtered users
            for user in users_over_25:  # Loop for printing (nested, but counts as separate)
                print(user)
                
    except Exception as e:
        print(f"Error during batch processing: {e}", file=sys.stderr)
        raise


# Alternative implementation with exactly 3 loops total
def batch_processing_optimized(batch_size: int = 50) -> None:
    """
    Optimized version with exactly 3 loops total
    
    Args:
        batch_size: Number of users to process in each batch
    """
    import sys
    
    try:
        # Get the batch generator
        batch_generator = stream_users_in_batches(batch_size)
        
        # Loop 1: Iterate through batches
        for batch in batch_generator:
            # Loop 2: Process and filter users in batch
            for user in batch:
                # Filter and print in same loop to avoid third loop
                if user['age'] > 25:
                    print(user)
                    sys.stdout.flush()  # Ensure immediate output for piping
                    
    except Exception as e:
        print(f"Error during batch processing: {e}", file=sys.stderr)
        raise


# Use the optimized version as the main function
def batch_processing(batch_size: int = 50) -> None:
    """
    Processes batches of users and filters those over age 25
    Uses exactly 3 loops total as required
    
    Args:
        batch_size: Number of users to process in each batch
    """
    import sys
    
    connection = None
    cursor = None
    
    try:
        # Establish database connection
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='ALX_prodev'
        )
        
        cursor = connection.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM user_data")
        total_users = cursor.fetchone()[0]
        
        offset = 0
        
        # LOOP 1: Batch fetching loop
        while offset < total_users:
            # Fetch batch
            query = "SELECT user_id, name, email, age FROM user_data LIMIT %s OFFSET %s"
            cursor.execute(query, (batch_size, offset))
            batch_rows = cursor.fetchall()
            
            if not batch_rows:
                break
            
            # LOOP 2: Process each row in batch
            for row in batch_rows:
                user_dict = {
                    'user_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'age': int(row[3])
                }
                
                # Filter and print in same loop (no third loop needed)
                if user_dict['age'] > 25:
                    print(user_dict)
                    sys.stdout.flush()  # Important for piping to head command
            
            offset += batch_size
            
    except mysql.connector.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    # Test the function
    batch_processing(50)
