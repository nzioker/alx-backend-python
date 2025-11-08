"""
Reusable Query Context Manager
"""

import sqlite3

class ExecuteQuery:
    """Reusable context manager for executing database queries"""
    
    def __init__(self, db_path, query, params=None):
        self.db_path = db_path
        self.query = query
        self.params = params if params is not None else ()
        self.connection = None
        self.cursor = None
        self.results = None
    
    def __enter__(self):
        """Setup connection and execute the query"""
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute(self.query, self.params)
        self.results = self.cursor.fetchall()
        return self.results
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            if exc_type is not None:  # An exception occurred
                self.connection.rollback()
            else:
                self.connection.commit()
            self.connection.close()

def main():
    """Demonstrate the ExecuteQuery context manager"""
    # Ensure the database exists with sample data
    with sqlite3.connect('example.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT
            )
        ''')
        # Insert sample data if not exists
        conn.executemany('''
            INSERT OR IGNORE INTO users (name, age, email)
            VALUES (?, ?, ?)
        ''', [
            ('Alice Johnson', 28, 'alice@example.com'),
            ('Bob Smith', 32, 'bob@example.com'),
            ('Charlie Brown', 45, 'charlie@example.com'),
            ('Diana Prince', 23, 'diana@example.com'),
            ('Eve Wilson', 35, 'eve@example.com'),
            ('Frank Miller', 52, 'frank@example.com'),
            ('Grace Lee', 29, 'grace@example.com')
        ])
        conn.commit()

    # Use the reusable ExecuteQuery context manager
    print("Using reusable ExecuteQuery context manager:")
    print("Query: SELECT * FROM users WHERE age > ?")
    print("Parameter: 25")
    print("=" * 50)
    
    query = "SELECT * FROM users WHERE age > ?"
    params = (25,)
    
    with ExecuteQuery('example.db', query, params) as results:
        # Print results
        if results:
            print(f"Found {len(results)} users older than 25:")
            print("-" * 50)
            for row in results:
                print(f"ID: {row[0]:2} | Name: {row[1]:15} | Age: {row[2]:2} | Email: {row[3]}")
        else:
            print("No users found matching the criteria.")

if __name__ == "__main__":
    main()
