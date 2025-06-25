# Captain CAT - Courtyard Advisory Tool

A comprehensive AI-powered courtyard design system that combines conversational AI, climate analysis, graph-based visualization, and professional plan generation. The system integrates with Grasshopper for 3D modeling and provides a complete workflow from concept to detailed design.

## 🏗️ System Architecture

### Core Components

#### 1. **Main UI Application** (`ui_pyqt.py`)
- **Purpose**: Primary user interface built with PyQt5
- **Features**:
  - Multi-phase design workflow (concept → functions → attributes → graph → criticism)
  - Real-time chat interface with Captain CAT AI assistant
  - Climate analysis integration
  - Image generation (concept and plan views)
  - Graph visualization and editing
  - Professional plan export
- **Key Classes**: `FlaskClientChatUI`, `ImageGenerationSignals`

#### 2. **AI/LLM Integration** (`llm_calls.py`)
- **Purpose**: Handles all AI interactions and data extraction
- **Features**:
  - Concept generation from user input
  - Function and attribute extraction
  - Spatial relationship analysis
  - Tree placement and water requirements
  - Design criticism and tips
- **Key Functions**: `generate_concept_with_conversation`, `extract_spaces`, `extract_links`, etc.

#### 3. **Flask Server** (`gh_server.py`)
- **Purpose**: Backend server for Grasshopper integration
- **Features**:
  - Plot area data management
  - UTCI thermal comfort analysis
  - Climate data processing
  - Graph data storage and retrieval
  - Screenshot capture for plan generation
- **Endpoints**: `/plot_area`, `/utci_values`, `/climate_data`, `/graph_data`, etc.

#### 4. **Graph Visualization** (`graph_gh.py`)
- **Purpose**: Interactive graph editor for courtyard layout
- **Features**:
  - Node-based spatial representation
  - Drag-and-drop interface
  - Real-time layout editing
  - Export to CSV for Grasshopper
  - Version control for design iterations
- **Key Classes**: `MainWindow`, `GraphEditor`, `NodeItem`

#### 5. **Professional Plan Export** (`plan_export.py`)
- **Purpose**: Generates professional PDF plans and documentation
- **Features**:
  - Multi-page PDF generation
  - Cover page, concept, requirements, and analysis sections
  - Technical drawings with grid system
  - Material specifications and tree placement
  - Climate analysis integration
- **Key Classes**: `PlanExportTab`, `ProfessionalPlanExporter`

#### 6. **Climate Analysis** (`epw_analysis.py`, `epw_handler.py`)
- **Purpose**: Weather data analysis and UTCI calculations
- **Features**:
  - EPW (EnergyPlus Weather) file processing
  - Location-based weather data retrieval
  - UTCI (Universal Thermal Climate Index) analysis
  - Time-based climate queries
  - Integration with Grasshopper for thermal analysis
- **Key Functions**: `handle_zip_request`, `get_hoys_from_intent`, `load_epw_dataframe`

#### 7. **Image Generation** (`image_gen.py`)
- **Purpose**: AI-powered image generation for design visualization
- **Features**:
  - Text-to-image concept generation
  - Image-to-image plan enhancement
  - Architectural visualization with LoRA weights
  - Integration with external AI servers
- **Key Functions**: `generate_ai_enhanced_image`, `generate_concept_view_from_text`

#### 8. **Graph Query System** (`graph_query.py`)
- **Purpose**: Natural language querying of design data
- **Features**:
  - Neo4j graph database integration
  - Natural language to Cypher query conversion
  - Design data analysis and insights
  - Results export to Grasshopper
- **Key Functions**: `load_graph_data`, `ask_graph_question`

#### 9. **Fallback System** (`fallback_utils.py`)
- **Purpose**: Robust error handling and default values
- **Features**:
  - Safe JSON extraction with fallbacks
  - Default design data when LLM fails
  - Graceful degradation of functionality
  - Comprehensive error recovery
- **Key Functions**: `safe_extract_json`, `create_robust_geometry_data`

### Supporting Components

#### **Server Configuration** (`server/config.py`, `server/keys.py`)
- API key management
- LLM client configuration
- Server settings

#### **Utilities** (`utils/`)
- **IFC Data Processing**: Building information modeling data preparation
- **RAG Utilities**: Retrieval-augmented generation for knowledge base queries
- **Building CSV Prep**: Building data preparation for analysis

#### **Knowledge Base** (`knowledge/`)
- EPW weather data indices
- Merged knowledge base for RAG queries

## 🚀 Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

### Required Files
- `cat_icon.png`: Application icon (2.2MB)
- `knowledge/merged.json`: Knowledge base for RAG queries (66MB)

### Starting the System

1. **Start the Flask Server**:
   ```bash
   python gh_server.py
   ```

2. **Launch the Main UI**:
   ```bash
   python ui_pyqt.py
   ```

3. **Optional: Start Graph Query System**:
   ```bash
   python graph_query.py
   ```

## 🔄 Workflow

### 1. Design Phase
1. **Concept**: User describes courtyard vision
2. **Functions**: Define building functions and spaces
3. **Attributes**: Specify materials, styles, requirements
4. **Graph**: Visualize and edit spatial relationships
5. **Criticism**: Get AI feedback and suggestions

### 2. Analysis Phase
1. **Climate Analysis**: Select location and analyze weather data
2. **UTCI Analysis**: Calculate thermal comfort with/without trees
3. **Graph Queries**: Ask questions about design data
4. **Image Generation**: Create concept and plan visualizations

### 3. Export Phase
1. **Professional Plans**: Generate PDF documentation
2. **CSV Export**: Export graph data for Grasshopper
3. **Screenshots**: Capture and enhance plan views

## 🔧 Integration Points

### Grasshopper Integration
- **Plot Area**: Real-time plot dimensions
- **UTCI Values**: Thermal comfort analysis results
- **Climate Data**: Weather information for analysis
- **Graph Data**: Spatial relationships and layout
- **Screenshots**: Plan view capture and enhancement

### External Services
- **AI Image Generation**: Text-to-image and image-to-image
- **Weather Data**: EPW file retrieval and processing
- **Neo4j Database**: Graph data storage and querying

## 📁 File Structure

```
aia25-studio-agent/
├── Core Application
│   ├── ui_pyqt.py              # Main UI application
│   ├── llm_calls.py            # AI/LLM integration
│   ├── gh_server.py            # Flask backend server
│   ├── graph_gh.py             # Graph visualization
│   ├── plan_export.py          # Professional plan export
│   ├── image_gen.py            # AI image generation
│   └── graph_query.py          # Graph query system
│
├── Climate Analysis
│   ├── epw_analysis.py         # Weather data analysis
│   ├── epw_handler.py          # EPW file handling
│   └── utci_epw_query.py       # UTCI query utilities
│
├── Robustness & Utilities
│   ├── fallback_utils.py       # Error handling and fallbacks
│   ├── send_utci_comparison.py # UTCI data transmission
│   └── utils/                  # Additional utilities
│
├── Server Configuration
│   └── server/
│       ├── config.py           # Server configuration
│       └── keys.py             # API keys
│
├── Knowledge Base
│   └── knowledge/
│       ├── merged.json         # RAG knowledge base
│       └── epw_index.json      # Weather data index
│
├── Assets
│   ├── cat_icon.png            # Application icon
│   └── workflow_graph.png      # System workflow diagram
│
└── Documentation
    ├── README.md               # This file
    ├── FALLBACK_SYSTEM_README.md
    ├── CLIMATE_ANALYSIS_README.md
    ├── GRAPH_QUERY_README.md
    └── QUERY_TO_GRASSHOPPER_README.md
```

## 🗑️ Files That Can Be Deleted

### Test and Demo Files
- `test_fallback_system.py` - Test script for fallback system
- `test_plot_area.py` - Test script for plot area functionality
- `demo_plot_area.py` - Demonstration script for plot area system
- `main.py` - Legacy command-line interface (superseded by UI)

### Temporary Files
- `__pycache__/` directories - Python cache files
- `.DS_Store` - macOS system file
- `.gradio/` - Empty Gradio cache directory
- `flagged/` - Empty flagged content directory
- `lora_weights/placeholder.txt` - Placeholder file

### Optional Utilities
- `utils/ifc_data_prep.py` - IFC data processing (if not using IFC files)
- `utils/ifc_file_processor.py` - IFC file processing (if not using IFC files)
- `utils/building_csv_prep.py` - Building CSV preparation (if not using building data)

## 🔑 Key Features

### AI-Powered Design Assistant
- Conversational design process with Captain CAT
- Context-aware tips and suggestions
- Multi-phase design workflow
- Real-time feedback and guidance

### Climate-Responsive Design
- Location-based weather analysis
- UTCI thermal comfort calculations
- Tree impact analysis
- Seasonal climate considerations

### Interactive Visualization
- Graph-based spatial layout editor
- Real-time design modifications
- Professional plan generation
- AI-enhanced image creation

### Robust Error Handling
- Fallback systems for LLM failures
- Graceful degradation of functionality
- Comprehensive error recovery
- Safe data processing

### Professional Output
- Multi-page PDF documentation
- Technical drawings with grid system
- Material specifications
- Climate analysis reports

## 🤝 Contributing

The system is designed with modularity in mind. Each component can be enhanced independently:

- **UI Enhancements**: Modify `ui_pyqt.py` for new interface features
- **AI Improvements**: Update `llm_calls.py` for better AI responses
- **Climate Analysis**: Extend `epw_analysis.py` for additional weather metrics
- **Graph Features**: Enhance `graph_gh.py` for new visualization capabilities
- **Export Options**: Add new export formats in `plan_export.py`

## 📄 License

This project is part of the AIA25 Studio Agent system for architectural design assistance.

---

**Captain CAT - Courtyard Advisory Tool** - Making courtyard design accessible, intelligent, and climate-responsive.
