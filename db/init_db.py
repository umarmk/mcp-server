"""
Database Initialization Script for PostgreSQL MCP Server

This script initializes the PostgreSQL database with the required schema
and sample data for testing the PostgreSQL MCP server functionality.

Usage:
    python db/init_db.py

Environment Variables Required:
    PG_HOST: PostgreSQL host (default: localhost)
    PG_PORT: PostgreSQL port (default: 5432)
    PG_USER: PostgreSQL username (required)
    PG_PASSWORD: PostgreSQL password (required)
    PG_DATABASE: PostgreSQL database name (required)
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")


async def check_connection():
    """Test the database connection"""
    try:
        conn = await asyncpg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        print(f"Successfully connected to {PG_DATABASE}@{PG_HOST}:{PG_PORT}")
        return True
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return False


async def run_sql_file(file_path: Path):
    """Execute SQL commands from a file"""
    if not file_path.exists():
        print(f"SQL file not found: {file_path}")
        return False
    
    try:
        conn = await asyncpg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        
        # Read and execute the SQL file
        sql_content = file_path.read_text(encoding='utf-8')
        await conn.execute(sql_content)
        await conn.close()
        
        print(f"Successfully executed SQL file: {file_path.name}")
        return True
    except Exception as e:
        print(f"Failed to execute SQL file {file_path.name}: {e}")
        return False


async def verify_schema():
    """Verify that the schema was created correctly"""
    try:
        conn = await asyncpg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        
        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in tables]
        expected_tables = ['items', 'products', 'users', 'orders', 'order_items']
        
        print("\nDatabase Tables:")
        for table in table_names:
            status = "YES" if table in expected_tables else "NO"
            print(f"  {status} {table}")
        
        # Check sample data
        items_count = await conn.fetchval("SELECT COUNT(*) FROM items")
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        products_count = await conn.fetchval("SELECT COUNT(*) FROM products")
        
        print(f"\nSample Data:")
        print(f"  Items: {items_count} records")
        print(f"  Users: {users_count} records")
        print(f"  Products: {products_count} records")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"Failed to verify schema: {e}")
        return False


async def main():
    """Main initialization function"""
    print("Initializing PostgreSQL database for PostgreSQL MCP Server...")
    
    # Validate required environment variables
    required_vars = ["PG_USER", "PG_PASSWORD", "PG_DATABASE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file in the project root")
        sys.exit(1)
    
    # Check database connection
    if not await check_connection():
        print("Cannot proceed without database connection")
        sys.exit(1)
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    schema_file = script_dir / "schema.sql"
    
    # Run the schema initialization
    print("\nCreating database schema...")
    if not await run_sql_file(schema_file):
        print("Failed to initialize database schema")
        sys.exit(1)
    
    # Verify the schema
    print("\nVerifying database schema...")
    if not await verify_schema():
        print("Schema verification failed")
        sys.exit(1)
    
    print("\nDatabase initialization completed successfully!")
    print("\nYou can now run the PostgreSQL MCP server:")
    print("  python postgres_mcp_server.py")
    print("\nOr test it with the client:")
    print("  python client_test.py")


if __name__ == "__main__":
    asyncio.run(main())
