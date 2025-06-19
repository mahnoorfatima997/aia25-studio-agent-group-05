import csv
import os
import json
import pandas as pd
from neo4j import GraphDatabase
from server.config import *  # Import OpenAI configuration
import re

class GraphQueryEngine:
    def __init__(self, csv_dir=None, neo4j_uri=None, neo4j_user="neo4j", neo4j_password="12345678"):
        """
        Initialize the Graph Query Engine
        
        Args:
            csv_dir: Directory containing CSV files (nodes.csv, edges.csv, building_*.csv, etc.)
            neo4j_uri: Neo4j database URI (default: bolt://localhost:7687 for serveo.net)
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.csv_dir = csv_dir or os.path.expanduser("~/Downloads/courtyard_graph")
        self.neo4j_uri = neo4j_uri or "bolt://localhost:7687"  # Default for serveo.net
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.csv_files = {}  # Store loaded CSV data for reference
        
        # Initialize Neo4j connection
        self._init_neo4j()
        
    def _init_neo4j(self):
        """Initialize Neo4j database connection"""
        try:
            self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Neo4j connection established")
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def discover_csv_files(self):
        """Discover all CSV files in the directory"""
        csv_files = {}
        if os.path.exists(self.csv_dir):
            for filename in os.listdir(self.csv_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.csv_dir, filename)
                    csv_files[filename] = filepath
        return csv_files
    
    def load_csv_to_neo4j(self):
        """Load all CSV data into Neo4j database"""
        if not self.driver:
            print("❌ Neo4j not connected")
            return False
        
        # Discover all CSV files
        csv_files = self.discover_csv_files()
        if not csv_files:
            print(f"❌ No CSV files found in {self.csv_dir}")
            return False
        
        print(f"📁 Found CSV files: {list(csv_files.keys())}")
        
        try:
            with self.driver.session() as session:
                # Clear existing data
                session.run("MATCH (n) DETACH DELETE n")
                
                # Load each CSV file
                for filename, filepath in csv_files.items():
                    self._load_single_csv(session, filename, filepath)
                
                # Create relationships between courtyard and building elements
                self._create_building_courtyard_relationships(session)
                
                print("✅ All CSV data loaded into Neo4j")
                return True
                
        except Exception as e:
            print(f"❌ Error loading CSV to Neo4j: {e}")
            return False
    
    def _load_single_csv(self, session, filename, filepath):
        """Load a single CSV file into Neo4j"""
        try:
            # Read CSV to determine structure
            df = pd.read_csv(filepath)
            print(f"📊 Loading {filename}: {len(df)} rows, columns: {list(df.columns)}")
            
            # Determine node type based on filename
            node_type = self._determine_node_type(filename)
            
            # Store CSV data for reference
            self.csv_files[filename] = {
                'data': df.to_dict('records'),
                'columns': list(df.columns),
                'node_type': node_type
            }
            
            # Handle building edges differently - create relationships instead of nodes
            if node_type == 'BuildingEdge':
                self._load_building_edges(session, df)
                return
            
            # Load data into Neo4j as nodes
            for _, row in df.iterrows():
                properties = {k: v for k, v in row.items() if pd.notna(v) and v != ''}
                
                # Handle different ID column names (including IFC GlobalId)
                id_column = self._find_id_column(properties)
                if id_column:
                    node_id = str(properties[id_column])
                    # Remove id from properties for Neo4j
                    if id_column in properties:
                        del properties[id_column]
                    
                    # Convert numeric values and handle IFC-specific columns
                    for key, value in properties.items():
                        if isinstance(value, (int, float)):
                            properties[key] = value
                        else:
                            # Clean string values to avoid Neo4j syntax errors
                            if isinstance(value, str):
                                # Escape quotes and backslashes
                                value = value.replace('\\', '\\\\').replace('"', '\\"')
                            properties[key] = str(value)
                    
                    # Add IFC type as a special property for querying
                    if 'IfcType' in properties:
                        ifc_type = properties['IfcType']
                        # Create additional node with IFC type label for easier querying
                        ifc_label = ifc_type.replace('Ifc', '')  # Remove 'Ifc' prefix
                        
                        # Clean the label to avoid Neo4j syntax errors
                        ifc_label = re.sub(r'[^a-zA-Z0-9_]', '_', ifc_label)
                        
                        # Create node with all properties using parameter binding
                        properties['id'] = node_id
                        query = f'CREATE (n:{node_type}:{ifc_label} $props)'
                        session.run(query, props=properties)
                    else:
                        # Create node with all properties using parameter binding
                        properties['id'] = node_id
                        query = f'CREATE (n:{node_type} $props)'
                        session.run(query, props=properties)
            
            print(f"✅ Loaded {len(df)} {node_type} nodes from {filename}")
            
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
    
    def _load_building_edges(self, session, df):
        """Load building edges as relationships in Neo4j"""
        try:
            # Look for source and target columns
            source_col = None
            target_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'source' in col_lower or 'from' in col_lower:
                    source_col = col
                elif 'target' in col_lower or 'to' in col_lower:
                    target_col = col
            
            # If no explicit source/target columns, create relationships based on IFC types and spatial proximity
            if not source_col or not target_col:
                print(f"📊 No explicit source/target columns found. Creating relationships based on IFC types and spatial proximity...")
                self._create_ifc_based_relationships(session, df)
                return
            
            print(f"📊 Found source column: {source_col}, target column: {target_col}")
            
            # First, let's find out what ID field is used in BuildingNode
            result = session.run("MATCH (n:BuildingNode) RETURN n LIMIT 1")
            sample_node = result.single()
            if sample_node:
                node_props = dict(sample_node["n"])
                # Find the ID field used
                id_field = None
                for field in ['id', 'Id', 'ID', 'GlobalId', 'globalid', 'Tag', 'tag']:
                    if field in node_props:
                        id_field = field
                        break
                
                if not id_field:
                    print("❌ Could not determine ID field for BuildingNode")
                    return
                
                print(f"📊 Using ID field: {id_field}")
            else:
                print("❌ No BuildingNode found in database")
                return
            
            # Create relationships from explicit source/target data
            relationships_created = 0
            failed_relationships = 0
            
            for _, row in df.iterrows():
                source = str(row[source_col])
                target = str(row[target_col])
                
                # Get additional properties for the relationship - filter out unwanted columns
                rel_properties = {}
                unwanted_columns = ['Unnamed: 0', 'Unnamed: 0.1', 'Unnamed: 0.2', 'Unnamed: 0.3', 'Unnamed: 0.4', 'Unnamed: 0.5']
                
                for col in df.columns:
                    if (col not in [source_col, target_col] and 
                        col not in unwanted_columns and 
                        pd.notna(row[col]) and 
                        row[col] != ''):
                        
                        value = row[col]
                        # Only include simple values that can be serialized
                        if isinstance(value, (int, float, str)) and len(str(value)) < 100:
                            rel_properties[col] = value
                
                # Create relationship with properties using parameter binding
                try:
                    if rel_properties:
                        query = f'''
                        MATCH (a:BuildingNode {{{id_field}: $source}})
                        MATCH (b:BuildingNode {{{id_field}: $target}})
                        CREATE (a)-[:BUILDING_CONNECTS $props]->(b)
                        '''
                        session.run(query, source=source, target=target, props=rel_properties)
                    else:
                        query = f'''
                        MATCH (a:BuildingNode {{{id_field}: $source}})
                        MATCH (b:BuildingNode {{{id_field}: $target}})
                        CREATE (a)-[:BUILDING_CONNECTS]->(b)
                        '''
                        session.run(query, source=source, target=target)
                    
                    relationships_created += 1
                    
                except Exception as e:
                    failed_relationships += 1
                    if failed_relationships <= 5:  # Only show first 5 errors
                        print(f"⚠️ Failed to create relationship {source} -> {target}: {e}")
            
            print(f"✅ Loaded {relationships_created} building relationships from building_edges.csv")
            if failed_relationships > 0:
                print(f"⚠️ Failed to create {failed_relationships} relationships")
            
        except Exception as e:
            print(f"❌ Error loading building edges: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_ifc_based_relationships(self, session, df):
        """Create relationships based on IFC types and spatial proximity"""
        try:
            # Get all building nodes
            result = session.run("MATCH (n:BuildingNode) RETURN n.id as id, n.LocationX as x, n.LocationY as y, n.IfcType as ifc_type")
            building_nodes = [(record["id"], record["x"], record["y"], record["ifc_type"]) for record in result]
            
            relationships_created = 0
            
            # Create relationships between different IFC types
            for i, (id1, x1, y1, ifc_type1) in enumerate(building_nodes):
                for j, (id2, x2, y2, ifc_type2) in enumerate(building_nodes[i+1:], i+1):
                    # Calculate distance
                    if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
                        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                        
                        # Create relationships based on proximity and IFC types
                        if distance < 20:  # Within 20 units
                            # Adjacent relationship
                            query = f'''
                            MATCH (a:BuildingNode {{id: "{id1}"}})
                            MATCH (b:BuildingNode {{id: "{id2}"}})
                            CREATE (a)-[:ADJACENT {{distance: {distance}, ifc_type1: "{ifc_type1}", ifc_type2: "{ifc_type2}"}}]->(b)
                            '''
                            session.run(query)
                            relationships_created += 1
                        
                        # Special relationships for windows
                        if ifc_type1 == "IfcWindow" or ifc_type2 == "IfcWindow":
                            if distance < 50:  # Windows can view further
                                query = f'''
                                MATCH (a:BuildingNode {{id: "{id1}"}})
                                MATCH (b:BuildingNode {{id: "{id2}"}})
                                CREATE (a)-[:WINDOW_VIEW {{distance: {distance}, ifc_type1: "{ifc_type1}", ifc_type2: "{ifc_type2}"}}]->(b)
                                '''
                                session.run(query)
                                relationships_created += 1
            
            print(f"✅ Created {relationships_created} IFC-based relationships")
            
        except Exception as e:
            print(f"❌ Error creating IFC-based relationships: {e}")
    
    def _determine_node_type(self, filename):
        """Determine Neo4j node type based on filename"""
        filename_lower = filename.lower()
        
        if 'node' in filename_lower:
            if 'building' in filename_lower:
                return 'BuildingNode'
            else:
                return 'Node'
        elif 'edge' in filename_lower:
            if 'building' in filename_lower:
                return 'BuildingEdge'
            else:
                return 'Edge'
        elif 'building' in filename_lower:
            return 'BuildingNode'
        elif 'ifc' in filename_lower:
            return 'BuildingNode'
        elif 'room' in filename_lower:
            return 'Room'
        elif 'floor' in filename_lower:
            return 'Floor'
        elif 'wall' in filename_lower:
            return 'Wall'
        elif 'window' in filename_lower:
            return 'Window'
        elif 'door' in filename_lower:
            return 'Door'
        elif 'furniture' in filename_lower:
            return 'Furniture'
        elif 'equipment' in filename_lower:
            return 'Equipment'
        elif 'system' in filename_lower:
            return 'System'
        else:
            return 'BuildingElement'
    
    def _find_id_column(self, properties):
        """Find the ID column in the properties"""
        id_columns = ['id', 'Id', 'ID', 'GlobalId', 'globalid', 'Tag', 'tag', 'name', 'Name', 'NAME', 'identifier', 'Identifier']
        for col in id_columns:
            if col in properties:
                return col
        return None
    
    def _create_building_courtyard_relationships(self, session):
        """Create relationships between building elements and courtyard elements"""
        try:
            # Create spatial relationships based on proximity
            session.run("""
                MATCH (courtyard:Node), (building:BuildingNode)
                WHERE courtyard.x IS NOT NULL AND courtyard.y IS NOT NULL 
                AND building.x IS NOT NULL AND building.y IS NOT NULL
                WITH courtyard, building, 
                     point.distance(point({x: courtyard.x, y: courtyard.y}), 
                                  point({x: building.x, y: building.y})) as distance
                WHERE distance < 50  // Within 50 units
                CREATE (building)-[:NEAR_COURTYARD {distance: distance}]->(courtyard)
            """)
            
            # Create environmental relationships based on view quality and radiation
            session.run("""
                MATCH (courtyard:Node), (building:BuildingNode)
                WHERE building.courtyard_view_numeric IS NOT NULL 
                AND building.view_quality IS NOT NULL
                AND courtyard.id IN ['play', 'rest', 'pond', 'flower', 'tree']
                WITH courtyard, building
                CREATE (building)-[:VIEWS_COURTYARD {
                    view_quality: building.view_quality,
                    view_numeric: building.courtyard_view_numeric,
                    direction_angle: building.direction_angle,
                    view_distance: building.view_distance
                }]->(courtyard)
            """)
            
            # Create solar radiation relationships
            session.run("""
                MATCH (courtyard:Node), (building:BuildingNode)
                WHERE building.incident_radiation_summer IS NOT NULL 
                OR building.incident_radiation_winter IS NOT NULL
                OR building.incident_radiation_annual IS NOT NULL
                AND courtyard.id IN ['play', 'rest', 'pond', 'flower', 'tree']
                WITH courtyard, building
                CREATE (building)-[:SOLAR_EXPOSURE {
                    radiation_summer: building.incident_radiation_summer,
                    radiation_winter: building.incident_radiation_winter,
                    radiation_annual: building.incident_radiation_annual,
                    sun_hours_summer: building.sun_hours_summer,
                    sun_hours_winter: building.sun_hours_winter
                }]->(courtyard)
            """)
            
            print("✅ Created building-courtyard relationships")
            
        except Exception as e:
            print(f"⚠️ Error creating building-courtyard relationships: {e}")
    
    def get_graph_schema(self):
        """Get the schema of the loaded graph"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Get node labels
                result = session.run("CALL db.labels() YIELD label RETURN label")
                labels = [record["label"] for record in result]
                
                # Get relationship types
                result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
                rel_types = [record["relationshipType"] for record in result]
                
                # Get node properties for each label
                properties = {}
                for label in labels:
                    result = session.run(f"MATCH (n:{label}) RETURN keys(n) LIMIT 1")
                    for record in result:
                        properties[label] = record["keys(n)"]
                        break
                
                # Get sample data for each label
                sample_data = {}
                for label in labels:
                    result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 3")
                    sample_data[label] = [dict(record["n"]) for record in result]
                
                return {
                    "labels": labels,
                    "relationship_types": rel_types,
                    "properties": properties,
                    "sample_data": sample_data,
                    "csv_files": list(self.csv_files.keys())
                }
        except Exception as e:
            print(f"❌ Error getting schema: {e}")
            return {}
    
    def generate_cypher_query(self, question):
        """Generate Cypher query from natural language question using OpenAI"""
        # Get graph schema for context
        schema = self.get_graph_schema()
        
        system_prompt = f"""
You are a Cypher expert. The Neo4j graph database contains nodes with the following schema:
{json.dumps(schema, indent=2)}

Available node labels: {', '.join(schema.get('labels', []))}
Available relationship types: {', '.join(schema.get('relationship_types', []))}
Available CSV files: {', '.join(schema.get('csv_files', []))}

IMPORTANT:
- Nodes are identified by their 'id' property (e.g., id: 'flower').
- For spatial calculations, always use 'point.distance' (not 'distance'). For example, use:
  point.distance(point({{x: a.x, y: a.y}}), point({{x: b.x, y: b.y}}))
- Building elements can be related to courtyard elements through relationships like NEAR_COURTYARD, OPENS_TO, VIEWS
- You can query across different node types (Node, Building, Room, Window, etc.)
- Use MATCH clauses to find relationships between building and courtyard elements

When answering, return only the Cypher query, no explanations, no preamble, no comments. Do not include any text outside of the query.
"""
        
        try:
            response = client.chat.completions.create(
                model=completion_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=300,
                temperature=0
            )
            
            generated = response.choices[0].message.content.strip()
            return generated
        except Exception as e:
            print(f"❌ Error generating Cypher query: {e}")
            return None
    
    def clean_cypher_query(self, query):
        """Remove Markdown code block formatting from Cypher queries."""
        # Remove triple backticks and optional 'cypher' after them
        cleaned = re.sub(r'^```cypher\s*|^```|```$', '', query.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
        return cleaned
    
    def execute_query(self, cypher_query):
        """Execute a Cypher query and return results"""
        if not self.driver:
            return None
        try:
            # Clean up the query before execution
            cypher_query = self.clean_cypher_query(cypher_query)
            with self.driver.session() as session:
                result = session.run(cypher_query)
                records = [dict(record) for record in result]
                return records
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return None
    
    def generate_human_response(self, question, cypher_query, raw_data):
        """Generate human-readable response from query results using OpenAI"""
        response_prompt = f"""
You are an assistant that interprets results from Cypher queries executed on a Neo4j database.

Question: {question}
Cypher Query: {cypher_query}
Query Results: {json.dumps(raw_data, indent=2)}

Please provide a clear, concise answer to the user's question based on the query results. 
If the results are empty, explain what that means in the context of the question.
Keep your response under 200 words and focus on the most relevant information.
"""
        
        try:
            response = client.chat.completions.create(
                model=completion_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that explains database query results in simple terms."},
                    {"role": "user", "content": response_prompt}
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            print(f"❌ Error generating human response: {e}")
            return f"Query executed successfully. Raw results: {raw_data}"
    
    def ask_question(self, question):
        """Main method to ask a question and get a response"""
        # Generate Cypher query
        cypher_query = self.generate_cypher_query(question)
        if not cypher_query:
            return "Unable to generate query.", None, None
        
        # Execute query
        raw_data = self.execute_query(cypher_query)
        if raw_data is None:
            return "Error executing query.", cypher_query, None
        
        # Generate human response
        human_answer = self.generate_human_response(question, cypher_query, raw_data)
        
        return human_answer, cypher_query, raw_data
    
    def get_sample_questions(self):
        """Get sample questions based on the graph schema"""
        schema = self.get_graph_schema()
        labels = schema.get('labels', [])
        properties = schema.get('properties', {})
        csv_files = schema.get('csv_files', [])
        
        sample_questions = [
            "How many nodes are in the graph?",
            "What are all the unique node types?",
            "Show me the first 5 nodes with their properties"
        ]
        
        # Add schema-specific questions
        for label in labels:
            props = properties.get(label, [])
            if props:
                sample_questions.append(f"How many {label} nodes are there?")
                sample_questions.append(f"What are the properties of {label} nodes?")
        
        # Add IFC-specific questions
        if any('Window' in label for label in labels):
            sample_questions.extend([
                "How many IFC windows are there?",
                "Which windows have the best view quality?",
                "What is the average view distance for windows?",
                "Show me windows with view quality above 0.8",
                "Which windows receive the most solar radiation?",
                "What is the orientation of windows relative to the courtyard?"
            ])
        
        # Add building-courtyard relationship questions
        if 'Node' in labels and any('building' in label.lower() or 'BuildingNode' in label for label in labels):
            sample_questions.extend([
                "Which building nodes are near the courtyard?",
                "What building elements have the best view quality to the courtyard?",
                "Which building spaces have the highest solar radiation exposure?",
                "How many building elements are within 50 units of the courtyard?",
                "What is the relationship between building view quality and courtyard spaces?",
                "Which courtyard spaces receive the most building shade?",
                "Show me all building elements that connect to courtyard areas"
            ])
        
        # Add connection and relationship questions
        if 'BuildingNode' in labels:
            sample_questions.extend([
                "What nodes are connected to each other?",
                "Show me the connections between building elements",
                "What is the distance between connected nodes?",
                "Which building elements are closest to each other?",
                "How are building spaces connected?",
                "Show me all BUILDING_CONNECTS relationships",
                "What are the distances between connected building elements?",
                "Which building elements have the most connections?",
                "Show me building elements with their connection counts",
                "What is the average distance between connected building elements?",
                "Which building elements are isolated (no connections)?",
                "Show me the shortest paths between building elements"
            ])
        
        # Add environmental analysis questions
        if 'BuildingNode' in labels:
            building_props = properties.get('BuildingNode', [])
            if any('view' in prop.lower() for prop in building_props):
                sample_questions.extend([
                    "Which building spaces have the highest courtyard view quality?",
                    "What is the average view distance to courtyard spaces?",
                    "Which building elements have the best direction angle for courtyard views?",
                    "Show me building spaces with view quality above 0.8"
                ])
            
            if any('radiation' in prop.lower() for prop in building_props):
                sample_questions.extend([
                    "Which building spaces receive the most summer radiation?",
                    "What is the annual solar radiation exposure for each building space?",
                    "Which building elements have the highest winter sun hours?",
                    "Show me building spaces with high summer radiation but low winter radiation"
                ])
        
        # Add spatial analysis questions
        if any('x' in props and 'y' in props for props in properties.values()):
            sample_questions.extend([
                "What is the spatial distribution of building elements around the courtyard?",
                "Which courtyard spaces are closest to building entrances?",
                "Calculate the distance between building elements and courtyard features"
            ])
        
        # Add building connectivity questions
        if 'BuildingNode' in labels:
            sample_questions.extend([
                "How are building spaces connected to each other?",
                "Which building spaces have the most connections?",
                "Show me the building connectivity network",
                "What is the shortest path between building spaces?"
            ])
        
        # Add IFC type-specific questions
        if any('IfcType' in props for props in properties.values()):
            sample_questions.extend([
                "What IFC types are present in the building?",
                "How many elements of each IFC type are there?",
                "Which IFC elements are adjacent to windows?",
                "Show me all IFC windows with their properties",
                "What is the relationship between IFC types and courtyard access?"
            ])
        
        return sample_questions
    
    def close(self):
        """Close the database connection and clean up resources"""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j connection closed") 