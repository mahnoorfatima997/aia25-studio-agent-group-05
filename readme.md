# AIA25-Studio-Agent

Welcome to the AIA25-Studio-Agent template repository! This serves as a starting point for students in the AIA25-Studio class to create their design assistant copilots. The goal of the project is to orchestrate Large Language Models (LLMs) to assist in architectural design tasks. The assistant copilots can be connected to platforms such as Grasshopper in Rhino, Revit, or web apps, depending on your needs, but that is beyond the scope of this starting template.

## Project Structure

The project follows a modular directory structure, which allows for easy extension and customization.

```
AIA25-Studio-Agent/
│
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

## Features

### Design Assistant
- Interactive chat interface for courtyard design
- Multi-phase design process (concept, functions, attributes, graph, criticism)
- Graph visualization and editing
- Export functionality for Grasshopper integration

### Graph Query (New!)
- Natural language queries for graph analysis
- Neo4j database integration
- LLM-powered query generation and interpretation
- Sample questions and query suggestions
- Real-time graph exploration

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Neo4j (for Graph Query functionality):**
   - Download and install [Neo4j Desktop](https://neo4j.com/download/)
   - Create a new project and database
   - Start the database
   - Set your password (default username: neo4j)

3. **Configure API keys:**
   - Copy `server/keys_template.py` to `server/keys.py`
   - Add your OpenAI API key

4. **Start the integrated system:**
   ```bash
   python gh_server.py
   ```

## Graph Query Feature

The new Graph Query feature allows you to explore your generated courtyard designs using natural language. After generating a graph and exporting it to CSV:

1. Switch to the "Graph Query" tab
2. Click "Load Graph Data" to load your CSV files into Neo4j
3. Ask questions like:
   - "How many nodes are in the graph?"
   - "Which nodes have the highest weight?"
   - "Show me all anchored nodes"
   - "What are the connections between play and rest areas?"

For detailed instructions, see [GRAPH_QUERY_README.md](GRAPH_QUERY_README.md).

## Working with the Code

- **Adding New LLM Calls**  
  If you need to add new LLM calls, modify the `llm_calls.py` file. This file is where you define different system prompts and interface with the LLM API.

- **Creating New Knowledge Databases**  
  To add new knowledge databases (such as post-processed embeddings), place the new JSON files in the `knowledge/` directory. Modify `embeddings.json` or add new files To learn how to create the embeddings, visit my other repository [Knowledge-Pool-RAG](https://github.com/jomiguelcarv/LLM-Knowledge-Pool-RAG).

- **Main Pipeline**  
  The `main.py` file orchestrates the pipeline for calling LLM functions and integrating the responses into your design workflow. You can expand this file as needed to suit your design assistant copilot's business logic.

- **Utility Functions**  
  The `utils/rag_utils.py` file contains functions related to Retrieval-Augmented Generation (RAG), useful for incorporating external knowledge into your LLM queries. You can add additional utility functions to extend the project's capabilities.

- **Graph Query Engine**
  The `graph_query.py` file contains the GraphQueryEngine class that handles Neo4j integration and natural language query processing. You can extend this to support more complex graph analysis features.

### Customizing Your Assistant Copilot

Feel free to customize and extend this template to meet your specific design needs. The project structure is flexible, and you are encouraged to add new directories or files as necessary. However, be sure to keep the essential files organized and maintain the clear separation of concerns in the existing directory structure.
