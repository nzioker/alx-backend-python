#!/usr/bin/python3
"""
Database Seeding and Streaming Script
Sets up MySQL database and provides a generator to stream rows one by one
"""

import mysql.connector
import csv
import uuid
import os
from typing import Generator, Tuple, Any, Optional


def connect_db() -> Optional[mysql.connector.MySQLConnection]:
    """
    Connects to the MySQL database server
    
    Returns:
        MySQLConnection: Connection object to MySQL server or None if failed
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',      # Replace with your MySQL username
            password=''       # Replace with your MySQL password
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def create_database(connection: mysql.connector.MySQLConnection) -> None:
    """
    Creates the database ALX_prodev if it does not exist
    
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        print("Database ALX_prodev created or already exists")
        cursor.close()
    except mysql.connector.Error as e:
        print(f"Error creating database: {e}")


def connect_to_prodev() -> Optional[mysql.connector.MySQLConnection]:
    """
    Connects to the ALX_prodev database in MySQL
    
    Returns:
        MySQLConnection: Connection object to ALX_prodev database or None if failed
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',      # Replace with your MySQL username
            password='',      # Replace with your MySQL password
            database='ALX_prodev'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to ALX_prodev database: {e}")
        return None


def create_table(connection: mysql.connector.MySQLConnection) -> None:
    """
    Creates a table user_data if it does not exist with the required fields
    
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_data (
            user_id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            age DECIMAL(3,0) NOT NULL,
            INDEX idx_user_id (user_id)
        )
        """
        
        cursor.execute(create_table_query)
        print("Table user_data created successfully")
        cursor.close()
    except mysql.connector.Error as e:
        print(f"Error creating table: {e}")


def insert_data(connection: mysql.connector.MySQLConnection, csv_file: str) -> None:
    """
    Inserts data in the database if it does not exist
    
    Args:
        connection: MySQL connection object
        csv_file: Path to the CSV file containing user data
    """
    try:
        # Check if data already exists
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_data")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Data already exists in user_data table ({count} records)")
            cursor.close()
            return
        
        # Check if CSV file exists
        if not os.path.exists(csv_file):
            print(f"CSV file {csv_file} not found. Creating sample data...")
            create_sample_data(csv_file)
        
        # Read CSV and insert data
        inserted_count = 0
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            insert_query = """
            INSERT IGNORE INTO user_data (user_id, name, email, age)
            VALUES (%s, %s, %s, %s)
            """
            
            batch_data = []
            for row in csv_reader:
                # Use UUID from CSV or generate new one
                user_id = row.get('user_id', str(uuid.uuid4()))
                name = row['name']
                email = row['email']
                age = int(row['age'])
                
                batch_data.append((user_id, name, email, age))
                inserted_count += 1
                
                # Insert in batches of 100 for efficiency
                if len(batch_data) >= 100:
                    cursor.executemany(insert_query, batch_data)
                    batch_data = []
            
            # Insert any remaining records
            if batch_data:
                cursor.executemany(insert_query, batch_data)
            
            connection.commit()
            print(f"Successfully inserted {inserted_count} records into user_data table")
            cursor.close()
            
    except FileNotFoundError:
        print(f"CSV file {csv_file} not found")
    except mysql.connector.Error as e:
        print(f"Error inserting data: {e}")
        connection.rollback()
    except Exception as e:
        print(f"Unexpected error: {e}")
        connection.rollback()


def create_sample_data(csv_file: str, num_records: int = 100) -> None:
    """
    Creates sample CSV data if the original file is not found
    
    Args:
        csv_file: Path to the CSV file to create
        num_records: Number of sample records to generate
    """
    import random
    from faker import Faker
    
    fake = Faker()
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['user_id', 'name', 'email', 'age']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for i in range(num_records):
            writer.writerow({
                'user_id': str(uuid.uuid4()),
                'name': fake.name(),
                'email': fake.email(),
                'age': random.randint(18, 100)
            })
    
    print(f"Created sample CSV file '{csv_file}' with {num_records} records")


def stream_users(connection: mysql.connector.MySQLConnection) -> Generator[Tuple[Any, ...], None, None]:
    """
    Generator that streams rows from user_data table one by one
    
    Args:
        connection: MySQL connection object
    
    Yields:
        Tuple: One row from the user_data table as (user_id, name, email, age)
    
    Raises:
        mysql.connector.Error: If there's a database error during streaming
    """
    cursor = None
    try:
        # Use a server-side cursor for efficient memory usage with large datasets
        cursor = connection.cursor(buffered=False)
        
        # Execute query to get all users
        query = "SELECT user_id, name, email, age FROM user_data ORDER BY user_id"
        cursor.execute(query)
        
        print("Starting to stream users from database...")
        
        # Stream rows one by one using generator
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row
            
    except mysql.connector.Error as e:
        print(f"Database error during streaming: {e}")
        raise
    finally:
        # Ensure cursor is closed even if an exception occurs
        if cursor:
            cursor.close()
            print("Database cursor closed.")


def stream_users_with_batch(connection: mysql.connector.MySQLConnection, 
                           batch_size: int = 100) -> Generator[Tuple[Any, ...], None, None]:
    """
    Generator that streams rows in batches for better performance with large datasets
    
    Args:
        connection: MySQL connection object
        batch_size: Number of rows to fetch at a time from database
    
    Yields:
        Tuple: One row from the user_data table
    """
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Get total count for progress tracking
        cursor.execute("SELECT COUNT(*) FROM user_data")
        total_rows = cursor.fetchone()[0]
        print(f"Streaming {total_rows} rows from user_data table in batches of {batch_size}...")
        
        # Fetch data in batches to avoid memory issues with large datasets
        offset = 0
        processed = 0
        
        while True:
            query = f"SELECT user_id, name, email, age FROM user_data ORDER BY user_id LIMIT {batch_size} OFFSET {offset}"
            cursor.execute(query)
            
            batch = cursor.fetchall()
            if not batch:
                break
            
            for row in batch:
                processed += 1
                yield row
            
            offset += batch_size
            
        print(f"Streaming completed. Processed {processed} rows.")
            
    except mysql.connector.Error as e:
        print(f"Error streaming data: {e}")
        raise
    finally:
        if cursor:
            cursor.close()


def get_user_count(connection: mysql.connector.MySQLConnection) -> int:
    """
    Get total number of users in the database
    
    Args:
        connection: MySQL connection object
    
    Returns:
        int: Total number of users
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_data")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except mysql.connector.Error as e:
        print(f"Error getting user count: {e}")
        return 0


# Example usage and demonstration
if __name__ == "__main__":
    # Demo the streaming functionality
    print("=== Database Setup and Streaming Demo ===")
    
    # Setup database
    connection = connect_db()
    if connection:
        create_database(connection)
        connection.close()
        print("Database setup completed")
    else:
        print("Failed to connect to MySQL server")
        exit(1)
    
    # Connect to specific database
    connection = connect_to_prodev()
    if connection:
        create_table(connection)
        insert_data(connection, 'user_data.csv')
        
        # Demonstrate the streaming generator
        print("\n--- Streaming users one by one ---")
        user_stream = stream_users(connection)
        
        # Process first 5 users as demonstration
        for i, user in enumerate(user_stream):
            if i >= 5:  # Limit for demo
                remaining = get_user_count(connection) - 5
                print(f"... and {remaining} more users in the stream")
                break
            print(f"User {i+1}: ID={user[0]}, Name={user[1]}, Email={user[2]}, Age={user[3]}")
        
        # Demonstrate batch streaming
        print("\n--- Streaming with batch processing ---")
        batch_stream = stream_users_with_batch(connection, batch_size=50)
        
        batch_count = 0
        for i, user in enumerate(batch_stream):
            if i >= 3:  # Just show first 3 from batch stream for demo
                break
            print(f"Batch Stream User {i+1}: {user}")
            batch_count = i + 1
        
        print(f"Showed {batch_count} users from batch stream")
        
        connection.close()
    else:
        print("Failed to connect to ALX_prodev database")
