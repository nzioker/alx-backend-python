import mysql.connector
from typing import Generator, List, Dict, Any
import seed  # Import the seed module for database connection


def paginate_users(page_size: int, offset: int) -> List[Dict[str, Any]]:
    """
    Fetches a page of users from the database
    
    Args:
        page_size: Number of users to fetch per page
        offset: Starting position for the page
    
    Returns:
        List of user dictionaries for the requested page
    """
    connection = seed.connect_to_prodev()
    if not connection:
        return []
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}")
        rows = cursor.fetchall()
        return rows
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def lazy_paginate(page_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Generator that lazily loads paginated user data
    
    Args:
        page_size: Number of users per page
    
    Yields:
        List of user dictionaries for each page
    """
    offset = 0
    
    # Single loop as required - continues until no more data
    while True:
        # Fetch the next page only when needed
        page = paginate_users(page_size, offset)
        
        # If no data returned, stop the generator
        if not page:
            break
        
        # Yield the current page
        yield page
        
        # Move to next page
        offset += page_size


# Alternative implementation with total count check
def lazy_paginate_with_count(page_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Alternative implementation that knows total count in advance
    
    Args:
        page_size: Number of users per page
    
    Yields:
        List of user dictionaries for each page
    """
    # Get total count first
    connection = seed.connect_to_prodev()
    if not connection:
        return
    
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM user_data")
        total_users = cursor.fetchone()[0]
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return
    finally:
        cursor.close()
        connection.close()
    
    offset = 0
    
    # Single loop - knows exactly how many pages to fetch
    while offset < total_users:
        page = paginate_users(page_size, offset)
        if page:
            yield page
        offset += page_size


# Main function to use (meets all requirements)
def lazy_pagination(page_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Main lazy pagination generator function
    
    Args:
        page_size: Number of users per page
    
    Yields:
        List of user dictionaries for each page
    
    This implementation:
    - Uses only one loop
    - Includes paginate_users function
    - Uses yield generator
    - Starts at offset 0
    - Fetches pages only when needed
    """
    offset = 0
    
    # Single loop that continues until no more data
    while True:
        # Fetch page using the paginate_users function
        current_page = paginate_users(page_size, offset)
        
        # If page is empty, we've reached the end
        if not current_page:
            break
        
        # Yield the current page
        yield current_page
        
        # Prepare for next page
        offset += page_size


# For backward compatibility and testing
if __name__ == "__main__":
    # Test the lazy pagination
    print("Testing lazy pagination with page size 5:")
    page_num = 0
    for page in lazy_pagination(5):
        page_num += 1
        print(f"\nPage {page_num} ({len(page)} users):")
        for user in page[:2]:  # Show first 2 users per page for demo
            print(f"  {user['name']} - {user['email']}")
        
        if page_num >= 3:  # Limit for demo
            print("... (more pages available)")
            break
