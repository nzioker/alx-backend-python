"""
Concurrent Asynchronous Database Queries
"""

import asyncio
import aiosqlite

async def async_fetch_users():
    """Fetch all users from the database asynchronously"""
    async with aiosqlite.connect('example.db') as db:
        async with db.execute("SELECT * FROM users") as cursor:
            results = await cursor.fetchall()
            print("All users fetched asynchronously:")
            print("-" * 40)
            for row in results:
                print(f"ID: {row[0]:2} | Name: {row[1]:15} | Age: {row[2]:2}")
            print(f"Total users: {len(results)}\n")
            return results

async def async_fetch_older_users():
    """Fetch users older than 40 asynchronously"""
    async with aiosqlite.connect('example.db') as db:
        async with db.execute("SELECT * FROM users WHERE age > ?", (40,)) as cursor:
            results = await cursor.fetchall()
            print("Users older than 40 fetched asynchronously:")
            print("-" * 40)
            for row in results:
                print(f"ID: {row[0]:2} | Name: {row[1]:15} | Age: {row[2]:2}")
            print(f"Users older than 40: {len(results)}\n")
            return results

async def setup_database():
    """Setup the database with sample data"""
    async with aiosqlite.connect('example.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT
            )
        ''')
        
        # Clear existing data and insert fresh sample data
        await db.execute("DELETE FROM users")
        await db.executemany('''
            INSERT INTO users (name, age, email)
            VALUES (?, ?, ?)
        ''', [
            ('Alice Johnson', 28, 'alice@example.com'),
            ('Bob Smith', 32, 'bob@example.com'),
            ('Charlie Brown', 45, 'charlie@example.com'),
            ('Diana Prince', 23, 'diana@example.com'),
            ('Eve Wilson', 35, 'eve@example.com'),
            ('Frank Miller', 52, 'frank@example.com'),
            ('Grace Lee', 29, 'grace@example.com'),
            ('Henry Ford', 61, 'henry@example.com')
        ])
        await db.commit()

async def fetch_concurrently():
    """Execute both queries concurrently using asyncio.gather"""
    print("Executing concurrent asynchronous database queries:")
    print("=" * 50)
    
    # Execute both queries concurrently
    results = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users(),
        return_exceptions=True
    )
    
    return results

async def main():
    """Main async function to run the demonstration"""
    # Setup the database first
    await setup_database()
    
    # Run concurrent queries
    await fetch_concurrently()
    
    print("Both queries completed concurrently!")

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
