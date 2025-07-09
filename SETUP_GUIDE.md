# PostgreSQL MCP Server Setup Guide

## How to Set Up the PostgreSQL MCP Server

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# PostgreSQL Configuration
PG_HOST=localhost
PG_PORT=5432
PG_USER=your_username
PG_PASSWORD=your_password
PG_DATABASE=your_database_name
```

### 3. Initialize Database Schema

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

## How LLMs Access the MCP Server Tools

### For Claude Desktop:

1. Install your MCP server using `mcp install`
2. Claude Desktop will automatically discover and load your tools
3. Users can then ask Claude to use your database tools

### For Other Applications:

- Use MCP-compatible clients (IDEs, AI tools)
- Connect via stdio, SSE, or WebSocket transports
- Tools are automatically discovered via MCP protocol

## Testing the PostgreSQL MCP Server

### 1. Test with Python Client

```bash
python client_test.py
```

### 2. Test with MCP Inspector

```bash
mcp dev postgres_mcp_server.py
```

### 3. Test with Claude Desktop

After installation, ask Claude:

- "Create a new item in the database"
- "Query all items from the database"
- "Update item with ID 1"

## Transport Options

### stdio (Default - Most Common)

```python
# Your server runs as a subprocess
# Claude Desktop uses this by default
mcp.run()  # Uses stdio transport
```

### SSE (Server-Sent Events)

```python
# For web-based clients
mcp.run(transport="sse", port=8000)
```

### WebSocket

```python
# For real-time applications
mcp.run(transport="websocket", port=8000)
```

## Security Considerations

- **Input Validation**: MCP SDK handles basic validation
- **Database Security**: Use connection pooling and prepared statements
- **Access Control**: Implement authentication if needed
- **Error Handling**: Return proper error messages to LLMs

## Next Steps

1. **Replace your current server** with `postgres_mcp_server.py`
2. **Test the functionality** using the test client
3. **Install for Claude Desktop** to enable LLM access
4. **Add more tools** as needed using `@mcp.tool()` decorator

Your database CRUD operations will now be properly accessible to LLMs through the standard MCP protocol!
