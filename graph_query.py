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
            csv_dir: Directory containing nodes.csv and edges.csv files
            neo4j_uri: Neo4j database URI (default: bolt://localhost:7687 for serveo.net)
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.csv_dir = csv_dir or os.path.expanduser("~/Downloads/courtyard_graph")
        self.neo4j_uri = neo4j_uri or "bolt://localhost:7687"  # Default for serveo.net
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        
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
    
    def load_csv_to_neo4j(self):
        """Load CSV data into Neo4j database"""
        if not self.driver:
            print("❌ Neo4j not connected")
            return False
            
        nodes_path = os.path.join(self.csv_dir, "nodes.csv")
        edges_path = os.path.join(self.csv_dir, "edges.csv")
        
        if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
            print(f"❌ CSV files not found in {self.csv_dir}")
            return False
        
        try:
            with self.driver.session() as session:
                # Clear existing data
                session.run("MATCH (n) DETACH DELETE n")
                
                # Load nodes
                with open(nodes_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Create node with all properties
                        properties = {k: v for k, v in row.items() if v != ''}
                        node_id = properties.get('id', properties.get('Id', properties.get('ID')))
                        if node_id:
                            # Remove id from properties for Neo4j
                            if 'id' in properties:
                                del properties['id']
                            if 'Id' in properties:
                                del properties['Id']
                            if 'ID' in properties:
                                del properties['ID']
                            # Create node with all properties
                            props_str = ', '.join([f'{k}: "{v}"' for k, v in properties.items()])
                            query = f'CREATE (n:Node {{id: "{node_id}", {props_str}}})'
                            session.run(query)
                
                # Load edges (with optional distance property)
                with open(edges_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        source = row.get('source', row.get('Source'))
                        target = row.get('target', row.get('Target'))
                        distance = row.get('distance')
                        if source and target:
                            if distance is not None and distance != '':
                                try:
                                    distance_val = float(distance)
                                except ValueError:
                                    print(f"⚠️ Invalid distance value for edge {source}->{target}: {distance}")
                                    distance_val = None
                                if distance_val is not None:
                                    query = f'''
                                    MATCH (a:Node {{id: "{source}"}})
                                    MATCH (b:Node {{id: "{target}"}})
                                    CREATE (a)-[:CONNECTS {{distance: {distance_val}}}]->(b)
                                    '''
                                    print(f"Creating relationship: {source} -[CONNECTS (distance: {distance_val})]-> {target}")
                                else:
                                    query = f'''
                                    MATCH (a:Node {{id: "{source}"}})
                                    MATCH (b:Node {{id: "{target}"}})
                                    CREATE (a)-[:CONNECTS]->(b)
                                    '''
                                    print(f"Creating relationship: {source} -[CONNECTS]-> {target} (distance invalid)")
                            else:
                                query = f'''
                                MATCH (a:Node {{id: "{source}"}})
                                MATCH (b:Node {{id: "{target}"}})
                                CREATE (a)-[:CONNECTS]->(b)
                                '''
                                print(f"Creating relationship: {source} -[CONNECTS]-> {target}")
                            session.run(query)
                
                print("✅ CSV data loaded into Neo4j")
                return True
                
        except Exception as e:
            print(f"❌ Error loading CSV to Neo4j: {e}")
            return False
    
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
                
                # Get node properties
                properties = {}
                for label in labels:
                    result = session.run(f"MATCH (n:{label}) RETURN keys(n) LIMIT 1")
                    for record in result:
                        properties[label] = record["keys(n)"]
                        break
                
                return {
                    "labels": labels,
                    "relationship_types": rel_types,
                    "properties": properties
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

IMPORTANT:
- Nodes are identified by their 'id' property (e.g., id: 'flower').
- Do NOT use 'anchor' or any other property to identify nodes.
- For spatial calculations, always use 'point.distance' (not 'distance'). For example, use:
  point.distance(point({{x: a.x, y: a.y}}), point({{x: b.x, y: b.y}}))

When answering, return only the Cypher query, no explanations, no preamble, no comments. Do not include any text outside of the query.
"""
        
        try:
            response = client.chat.completions.create(
                model=completion_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=200,
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
        
        return sample_questions
    
    def close(self):
        """Close the database connection and clean up resources"""
        if self.driver:
            self.driver.close()
            print("✅ Neo4j connection closed") 