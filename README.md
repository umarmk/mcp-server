# PostgreSQL CRUD MCP Server

A comprehensive **Model Context Protocol (MCP)** server that provides CRUD operations and advanced querying capabilities for PostgreSQL databases. This server allows LLMs like Claude to interact with PostgreSQL databases through standardized MCP tools.

## Features

- **Complete CRUD Operations**: Create, Read, Update, Delete records
- **Advanced Querying**: Filtering, sorting, pagination, and custom SQL
- **Schema Introspection**: List tables, describe columns, constraints, and indexes
- **Connection Pooling**: Efficient database connection management
- **Proper MCP Protocol**: Full compliance with MCP specification
- **Type Safety**: Comprehensive type hints and validation
- **Error Handling**: Robust error handling and logging
- **Test Coverage**: Comprehensive test suite with pytest

## Tech Stack

- **Python 3.10+**
- **MCP Python SDK**: Official Model Context Protocol implementation
- **asyncpg**: High-performance PostgreSQL adapter
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework with async support

## Prerequisites

- Python 3.10 or higher
- PostgreSQL database (local or remote)
- Environment variables configured (see setup below)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mcp-server
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# PostgreSQL Configuration
PG_HOST=localhost
PG_PORT=5432
PG_USER=your_username
PG_PASSWORD=your_password
PG_DATABASE=your_database_name
```

### 5. Initialize Database Schema

```bash
python db/init_db.py
```

This will create sample tables and insert test data for demonstration.

## Usage

### Running the MCP Server

```bash
# Run the server directly
python postgres_mcp_server.py

# Or test with the comprehensive client
python client_test.py
```

### Installing for Claude Desktop

```bash
# Install the MCP CLI tool (if not already installed)
pip install mcp

# Install your server for Claude Desktop
mcp install postgres_mcp_server.py --name "PostgreSQL CRUD Server"
```

After installation, Claude Desktop will automatically discover and load your database tools.

## Available Tools

The MCP server provides the following tools that LLMs can use:

### Health & Information

- **`ping`**: Health check for the server
- **`get_server_info`**: Get server and database information

### Schema Introspection

- **`list_tables`**: List all tables in a schema
- **`describe_table`**: Get detailed table information (columns, constraints, indexes)
- **`get_table_statistics`**: Get table statistics (row count, size, etc.)

### CRUD Operations

- **`insert_record`**: Insert new records into tables
- **`select_records`**: Select records with advanced filtering and pagination
- **`update_records`**: Update existing records with WHERE conditions
- **`delete_records`**: Delete records with WHERE conditions (safety required)

### Advanced Querying

- **`execute_custom_query`**: Execute custom SQL queries with parameters

## Example Usage with Claude

Once installed, you can ask Claude to interact with your database:

```
"Show me all tables in the database"
"Create a new user with name 'John Doe' and email 'john@example.com'"
"Find all products in the 'Electronics' category"
"Update the price of product ID 1 to $999.99"
"Get statistics for the users table"
```

## Testing

### Basic Server Test

```bash
# Test that the server can start
python postgres_mcp_server.py --help

# Test database connectivity
python db/init_db.py
```

### Test the Server

```bash
# Test basic connectivity
python -c "import asyncio; from postgres_mcp_server import main; print('✅ Server can start')"
```

## Project Structure

```
mcp-server/
├── postgres_mcp_server.py    # Main MCP server implementation
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
├── SETUP_GUIDE.md          # Detailed setup guide
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT License
└── db/
    ├── connection.py        # Database connection utilities
    ├── schema.sql          # Database schema and sample data
    └── init_db.py          # Database initialization script
```

## Security Considerations

- **Parameterized Queries**: All queries use parameterized statements to prevent SQL injection
- **WHERE Clause Required**: UPDATE and DELETE operations require WHERE clauses for safety
- **Input Validation**: Comprehensive input validation and error handling
- **Connection Pooling**: Secure connection management with timeouts
- **Environment Variables**: Sensitive credentials stored in environment variables

## Safety Features

- **Required WHERE Clauses**: UPDATE and DELETE operations must include WHERE conditions
- **Query Type Validation**: Custom queries are validated against their declared type
- **Error Handling**: Comprehensive error handling with informative messages
- **Connection Timeouts**: Database operations have configurable timeouts
- **Logging**: Detailed logging for debugging and monitoring

## Configuration

### Environment Variables

| Variable      | Description              | Default     | Required |
| ------------- | ------------------------ | ----------- | -------- |
| `PG_HOST`     | PostgreSQL host          | `localhost` | No       |
| `PG_PORT`     | PostgreSQL port          | `5432`      | No       |
| `PG_USER`     | PostgreSQL username      | -           | Yes      |
| `PG_PASSWORD` | PostgreSQL password      | -           | Yes      |
| `PG_DATABASE` | PostgreSQL database name | -           | Yes      |

### Connection Pool Settings

The server uses connection pooling with the following defaults:

- **Min connections**: 2
- **Max connections**: 20
- **Command timeout**: 60 seconds

## Troubleshooting

### Common Issues

1. **Connection Failed**

   - Verify PostgreSQL is running
   - Check environment variables in `.env`
   - Ensure database exists and user has permissions

2. **MCP Import Error**

   - Install the MCP Python SDK: `pip install mcp`
   - Ensure you're using Python 3.10+

3. **Table Not Found**
   - Run the database initialization: `python db/init_db.py`
   - Verify the schema exists in your database

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
