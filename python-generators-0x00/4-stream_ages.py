import mysql.connector
from typing import Generator, Tuple


def stream_user_ages() -> Generator[int, None, None]:
    """
    Generator that yields user ages one by one from the database
    
    Yields:
        int: Age of each user
    
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
        
        # Use unbuffered cursor for memory efficiency
        cursor = connection.cursor(buffered=False)
        
        # Execute query to get only ages
        query = "SELECT age FROM user_data"
        cursor.execute(query)
        
        # Loop 1: Yield ages one by one
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            
            age = int(row[0])
            yield age
            
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        raise Exception(f"Failed to stream user ages: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def calculate_average_age() -> float:
    """
    Calculates the average age of all users without loading entire dataset into memory
    
    Returns:
        float: Average age of all users
    
    Uses the stream_user_ages generator to process ages one by one
    """
    total_age = 0
    user_count = 0
    
    # Loop 2: Process ages from generator
    for age in stream_user_ages():
        total_age += age
        user_count += 1
    
    # Calculate average
    if user_count == 0:
        return 0.0
    
    average_age = total_age / user_count
    return average_age


def calculate_average_age_with_progress() -> float:
    """
    Alternative implementation that shows progress during calculation
    
    Returns:
        float: Average age of all users
    """
    total_age = 0
    user_count = 0
    
    for age in stream_user_ages():
        total_age += age
        user_count += 1
        
        # Show progress every 1000 users
        if user_count % 1000 == 0:
            current_avg = total_age / user_count
            print(f"Processed {user_count} users... Current average: {current_avg:.2f}")
    
    if user_count == 0:
        return 0.0
    
    average_age = total_age / user_count
    return average_age


# Main execution
if __name__ == "__main__":
    try:
        # Calculate average age using generator
        average_age = calculate_average_age()
        
        # Print the result
        print(f"Average age of users: {average_age:.2f}")
        
    except Exception as e:
        print(f"Error calculating average age: {e}")
