"""
Custom class-based context manager for database connection
"""

import sqlite3

class DatabaseConnection:
    """Custom context manager for SQLite database connections"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
    
    def __enter__(self):
        """Setup the database connection when entering the context"""
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        return self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the database connection when exiting the context"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            if exc_type is not None:  # An exception occurred
                self.connection.rollback()
            else:
                self.connection.commit()
            self.connection.close()

def main():
    """Demonstrate the DatabaseConnection context manager"""
    # Create a sample database with users table
    with sqlite3.connect('example.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT
            )
        ''')
        # Insert sample data
        conn.executemany('''
            INSERT OR IGNORE INTO users (name, age, email)
            VALUES (?, ?, ?)
        ''', [
            ('Alice Johnson', 28, 'alice@example.com'),
            ('Bob Smith', 32, 'bob@example.com'),
            ('Charlie Brown', 45, 'charlie@example.com'),
            ('Diana Prince', 23, 'diana@example.com'),
            ('Eve Wilson', 35, 'eve@example.com')
        ])
        conn.commit()

    # Use our custom context manager
    print("Using custom DatabaseConnection context manager:")
    print("=" * 50)
    
    with DatabaseConnection('example.db') as cursor:
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        
        # Print column headers
        column_names = [description[0] for description in cursor.description]
        print(f"{' | '.join(column_names)}")
        print("-" * 50)
        
        # Print results
        for row in results:
            print(f"{row[0]:2} | {row[1]:15} | {row[2]:3} | {row[3]:20}")

if __name__ == "__main__":
    main()
