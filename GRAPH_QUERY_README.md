# Graph Query Functionality

This document explains how to use the new Graph Query functionality in the Courtyard Design Copilot.

## Overview

The Graph Query feature allows you to explore and analyze your generated courtyard design graphs using natural language queries. It uses:

- **Neo4j** as the graph database
- **Transformers** for natural language to Cypher query generation
- **LLM** for interpreting query results

## Prerequisites

### 1. Install Python Dependencies

```bash
pip install neo4j transformers torch pandas
```

### 2. Install Neo4j

#### Option A: Neo4j Desktop (Recommended)
1. Download from [https://neo4j.com/download/](https://neo4j.com/download/)
2. Install and create a new project
3. Create a new database or use the default 'neo4j' database
4. Start the database

#### Option B: Neo4j Community Edition
- **Windows/macOS**: Download and install from the Neo4j website
- **Linux**: `sudo apt-get install neo4j` (Ubuntu/Debian)

### 3. Setup Neo4j
1. Open Neo4j Browser at `http://localhost:7474`
2. Set initial password (default: `neo4j`)
3. Note your password for the connection settings

## Quick Setup

1. **Install Neo4j Desktop:**
   - Download from [https://neo4j.com/download/](https://neo4j.com/download/)
   - Install and create a new project
   - Start a database (default credentials: neo4j/neo4j)

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the integrated system:**
   ```bash
   python gh_server.py
   ```

## Usage

### 1. Generate a Graph
1. Use the main application to design your courtyard
2. Go through the design phases (concept, functions, attributes, graph)
3. Export your graph to CSV using the "Export Graph to CSV" button

### 2. Query Your Graph
1. Switch to the "Graph Query" tab
2. Click "Load Graph Data" to load your CSV files into Neo4j
3. Ask questions about your graph using natural language

### 3. Example Queries

#### Basic Questions
- "How many nodes are in the graph?"
- "What are all the unique node types?"
- "Show me the first 5 nodes with their properties"

#### Design-Specific Questions
- "Which nodes have the highest weight?"
- "Show me all anchored nodes"
- "What are the connections between play and rest areas?"
- "Which nodes are positioned in the northern area?"

#### Analysis Questions
- "Find nodes with weight greater than 5"
- "Show me the most connected nodes"
- "What are the properties of tree nodes?"
- "Which areas are closest to the center?"

## Configuration

### Connection Settings

The default connection settings are:
- **URI**: `bolt://localhost:7687`
- **Username**: `neo4j`
- **Password**: `[your password]`

To change these settings, edit the `GraphQueryEngine` initialization in `graph_query.py`:

```python
self.query_engine = GraphQueryEngine(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="your_password"
)
```

### Model Settings

The system uses a smaller transformer model for faster loading. To change the model, edit the `_init_llm` method in `graph_query.py`:

```python
model_name = "microsoft/DialoGPT-medium"  # Change this to other models
```

## File Structure

```
├── gh_server.py              # Integrated Flask server with UI and Graph Query
├── ui_pyqt.py               # PyQt5 UI with Design Assistant and Graph Query tabs
├── graph_query.py           # Graph query engine using OpenAI API
├── llm_calls.py             # LLM integration functions
├── graph_gh.py              # Graph visualization
├── test_integrated_server.py # Test script for the integrated system
├── start_integrated_system.py # Startup script with dependency checks
├── diagnose_connection.py   # Connection diagnostic tool
└── README_INTEGRATED.md     # Comprehensive documentation
```

## Troubleshooting

### Neo4j Connection Issues
1. Ensure Neo4j is running (`http://localhost:7474`)
2. Check your password is correct
3. Verify the database is started
4. Check firewall settings

### CSV Loading Issues
1. Ensure CSV files exist in `~/Downloads/courtyard_graph/`
2. Check file permissions
3. Verify CSV format (headers: id, source, target, etc.)

### LLM Issues
1. Check internet connection (for model download)
2. Ensure sufficient disk space for model files
3. Try a different model if generation fails

### Performance Issues
1. Use smaller models for faster loading
2. Limit query complexity
3. Consider using Neo4j Desktop for better performance

## Advanced Usage

### Custom Queries
You can write custom Cypher queries directly in the Neo4j Browser:

```cypher
// Find all nodes with weight > 5
MATCH (n:Node) WHERE n.weight > 5 RETURN n

// Find shortest path between two nodes
MATCH path = shortestPath((a:Node {id: "node1"})-[*]-(b:Node {id: "node5"}))
RETURN path

// Analyze node connectivity
MATCH (n:Node)
RETURN n.id, size((n)-[:CONNECTS]-()) as connections
ORDER BY connections DESC
```

### Extending the Query Engine
To add new query capabilities:

1. Modify the system prompt in `generate_cypher_query()`
2. Add new sample questions in `get_sample_questions()`
3. Extend the schema detection in `get_graph_schema()`

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all prerequisites are met
3. Run the setup script to diagnose issues
4. Check Neo4j logs for database errors

## Future Enhancements

Potential improvements:
- Support for more complex graph algorithms
- Integration with graph visualization tools
- Advanced query templates
- Query history and favorites
- Export query results to various formats 