"""
IFC Data Preparation Utility

This script helps prepare IFC building data for integration with the courtyard graph query system.
It provides tools to filter, clean, and structure IFC data for optimal querying.
"""

import pandas as pd
import os
import json
from typing import Dict, List, Any

class IFCDataPrep:
    def __init__(self, output_dir: str = None):
        """
        Initialize the IFC Data Preparation utility
        
        Args:
            output_dir: Directory to save processed CSV files (default: ~/Downloads/courtyard_graph)
        """
        self.output_dir = output_dir or os.path.expanduser("~/Downloads/courtyard_graph")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_ifc_data(self, filepath: str) -> pd.DataFrame:
        """
        Load IFC data from CSV file
        
        Args:
            filepath: Path to the IFC CSV file
            
        Returns:
            DataFrame with IFC data
        """
        try:
            df = pd.read_csv(filepath)
            print(f"✅ Loaded IFC data: {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            print(f"❌ Error loading IFC data: {e}")
            return None
    
    def filter_by_ifc_type(self, df: pd.DataFrame, ifc_types: List[str]) -> pd.DataFrame:
        """
        Filter IFC data by specific IFC types
        
        Args:
            df: IFC DataFrame
            ifc_types: List of IFC types to include (e.g., ['IfcWindow', 'IfcWall'])
            
        Returns:
            Filtered DataFrame
        """
        if 'IfcType' not in df.columns:
            print("❌ No IfcType column found in data")
            return df
        
        filtered_df = df[df['IfcType'].isin(ifc_types)]
        print(f"✅ Filtered to {len(filtered_df)} {ifc_types} elements")
        return filtered_df
    
    def clean_ifc_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare IFC data for graph querying
        
        Args:
            df: Raw IFC DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Remove unnamed columns
        unnamed_cols = [col for col in df.columns if 'Unnamed' in col]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)
            print(f"✅ Removed {len(unnamed_cols)} unnamed columns")
        
        # Add missing required columns if they don't exist
        if 'GlobalId' not in df.columns:
            # Create a GlobalId from index or existing ID column
            if 'Tag' in df.columns:
                df['GlobalId'] = df['Tag']
                print("✅ Created GlobalId from Tag column")
            else:
                df['GlobalId'] = [f"element_{i}" for i in range(len(df))]
                print("✅ Created GlobalId from index")
        
        if 'IfcType' not in df.columns:
            # Create IfcType from category or set default
            if 'category' in df.columns:
                df['IfcType'] = df['category']
                print("✅ Created IfcType from category column")
            else:
                df['IfcType'] = 'BuildingElement'
                print("✅ Created default IfcType")
        
        # Add location columns if they don't exist
        if 'LocationX' not in df.columns or 'LocationY' not in df.columns:
            # Don't create dummy location data - it causes excessive relationships
            print("⚠️ No location data found - spatial relationships will be skipped")
            print("   Consider adding LocationX and LocationY columns with real coordinates")
            print("   Or use explicit relationships in building_edges.csv")
        
        # Ensure GlobalId exists and is unique
        if 'GlobalId' in df.columns:
            df = df.dropna(subset=['GlobalId'])
            df = df.drop_duplicates(subset=['GlobalId'])
            print(f"✅ Cleaned GlobalId: {len(df)} unique elements")
        
        # Convert location columns to numeric
        location_cols = ['LocationX', 'LocationY', 'LocationZ']
        for col in location_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert environmental data to numeric
        env_cols = ['courtyard_view', 'view_distance', 'sun_hours_winter', 'sun_hours_summer',
                   'incident_radiation_annual', 'incident_radiation_winter', 'incident_radiation_summer']
        for col in env_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def create_window_focused_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a dataset focused on windows and their relationships
        
        Args:
            df: IFC DataFrame
            
        Returns:
            Window-focused DataFrame
        """
        # Filter for windows and adjacent elements
        window_df = df[df['IfcType'] == 'IfcWindow'].copy()
        
        if len(window_df) == 0:
            print("❌ No windows found in the data")
            return df
        
        print(f"✅ Found {len(window_df)} windows")
        
        # Add window-specific properties
        window_df['is_window'] = True
        window_df['window_type'] = 'standard'  # You can enhance this based on other properties
        
        return window_df
    
    def create_spatial_relationships(self, df: pd.DataFrame, max_distance: float = 20.0) -> pd.DataFrame:
        """
        Create spatial relationships between IFC elements
        
        Args:
            df: IFC DataFrame
            max_distance: Maximum distance for adjacency relationships
            
        Returns:
            DataFrame with spatial relationships
        """
        if 'LocationX' not in df.columns or 'LocationY' not in df.columns:
            print("❌ Location data not available for spatial relationships")
            return pd.DataFrame()
        
        # Check if we have meaningful location data
        x_values = df['LocationX'].dropna()
        y_values = df['LocationY'].dropna()
        
        # If all coordinates are the same (like 0,0), don't create spatial relationships
        if len(x_values) > 0 and len(y_values) > 0:
            if x_values.nunique() <= 1 and y_values.nunique() <= 1:
                print("⚠️ All elements have the same coordinates - skipping spatial relationships")
                print("   Consider adding real location data or use explicit relationships in building_edges.csv")
                return pd.DataFrame()
        
        # Limit the number of elements to process to avoid excessive relationships
        max_elements = 1000  # Limit to prevent performance issues
        if len(df) > max_elements:
            print(f"⚠️ Large dataset detected ({len(df)} elements). Limiting to {max_elements} elements for spatial relationships.")
            df_sample = df.head(max_elements)
        else:
            df_sample = df
        
        relationships = []
        processed = 0
        
        # Create relationships between elements within max_distance
        for i, row1 in df_sample.iterrows():
            for j, row2 in df_sample.iterrows():
                if i < j:  # Avoid duplicate relationships
                    x1, y1 = row1['LocationX'], row1['LocationY']
                    x2, y2 = row2['LocationX'], row2['LocationY']
                    
                    if pd.notna(x1) and pd.notna(y1) and pd.notna(x2) and pd.notna(y2):
                        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                        
                        if distance <= max_distance and distance > 0:  # Avoid self-connections
                            relationships.append({
                                'source': row1['GlobalId'],
                                'target': row2['GlobalId'],
                                'relationship_type': 'adjacent',
                                'distance': round(distance, 2),
                                'source_type': row1.get('IfcType', 'BuildingElement'),
                                'target_type': row2.get('IfcType', 'BuildingElement')
                            })
                            
                            # Limit total relationships to prevent excessive output
                            if len(relationships) >= 10000:
                                print(f"⚠️ Reached relationship limit (10,000). Stopping to prevent performance issues.")
                                break
                    
                    processed += 1
                    if processed % 10000 == 0:
                        print(f"   Processed {processed} element pairs...")
            
            if len(relationships) >= 10000:
                break
        
        relationships_df = pd.DataFrame(relationships)
        print(f"✅ Created {len(relationships_df)} spatial relationships (limited for performance)")
        
        if len(relationships_df) == 0:
            print("💡 No spatial relationships created. Consider:")
            print("   - Adding real location coordinates")
            print("   - Creating explicit relationships in building_edges.csv")
            print("   - Using a larger max_distance value")
        
        return relationships_df
    
    def save_processed_data(self, df: pd.DataFrame, filename: str) -> str:
        """
        Save processed IFC data to CSV
        
        Args:
            df: DataFrame to save
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"✅ Saved {filename}: {len(df)} rows")
        return filepath
    
    def analyze_ifc_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze IFC data and provide insights
        
        Args:
            df: IFC DataFrame
            
        Returns:
            Analysis results
        """
        analysis = {
            'total_elements': len(df),
            'ifc_types': {},
            'location_stats': {},
            'environmental_stats': {}
        }
        
        # IFC type analysis - check both IfcType and category columns
        if 'IfcType' in df.columns:
            type_counts = df['IfcType'].value_counts()
            analysis['ifc_types'] = type_counts.to_dict()
        elif 'category' in df.columns:
            type_counts = df['category'].value_counts()
            analysis['ifc_types'] = type_counts.to_dict()
        
        # Location analysis
        if 'LocationX' in df.columns and 'LocationY' in df.columns:
            analysis['location_stats'] = {
                'x_range': [df['LocationX'].min(), df['LocationX'].max()],
                'y_range': [df['LocationY'].min(), df['LocationY'].max()],
                'elements_with_location': df[['LocationX', 'LocationY']].notna().all(axis=1).sum()
            }
        
        # Environmental data analysis
        env_cols = ['courtyard_view', 'view_distance', 'sun_hours_winter', 'sun_hours_summer',
                   'incident_radiation_annual', 'incident_radiation_winter', 'incident_radiation_summer']
        
        env_stats = {}
        for col in env_cols:
            if col in df.columns:
                env_stats[col] = {
                    'mean': df[col].mean(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'non_null_count': df[col].notna().sum()
                }
        analysis['environmental_stats'] = env_stats
        
        return analysis
    
    def create_sample_queries(self, df: pd.DataFrame) -> List[str]:
        """
        Generate sample queries based on the IFC data
        
        Args:
            df: IFC DataFrame
            
        Returns:
            List of sample queries
        """
        queries = []
        
        # Check if IfcType column exists
        if 'IfcType' in df.columns:
            ifc_types = df['IfcType'].unique()
            for ifc_type in ifc_types:
                queries.append(f"How many {ifc_type} elements are there?")
                queries.append(f"What are the properties of {ifc_type} elements?")
            
            # Window-specific queries
            if 'IfcWindow' in df['IfcType'].values:
                queries.extend([
                    "Which windows have the best view quality?",
                    "What is the average view distance for windows?",
                    "Show me windows with view quality above 0.8",
                    "Which windows receive the most solar radiation?",
                    "What is the orientation of windows relative to the courtyard?"
                ])
        elif 'category' in df.columns:
            # Use category column instead of IfcType
            categories = df['category'].unique()
            for category in categories:
                queries.append(f"How many {category} elements are there?")
                queries.append(f"What are the properties of {category} elements?")
            
            # Window-specific queries using category
            if 'window' in df['category'].str.lower().values:
                queries.extend([
                    "Which windows have the best view quality?",
                    "What is the average view distance for windows?",
                    "Show me windows with view quality above 0.8",
                    "Which windows receive the most solar radiation?",
                    "What is the orientation of windows relative to the courtyard?"
                ])
        else:
            # Generic queries when IfcType is not available
            queries.extend([
                "How many building elements are there?",
                "What are the properties of building elements?",
                "Show me all building elements with their properties",
                "What is the spatial distribution of building elements?"
            ])
        
        # Environmental queries using actual column names
        if 'courtyard_view' in df.columns:
            queries.extend([
                "Which elements have the highest courtyard view quality?",
                "What is the average view distance to courtyard spaces?",
                "Show me elements with view quality above 0.8"
            ])
        
        if 'incident_radiation_summer' in df.columns:
            queries.extend([
                "Which elements receive the most summer radiation?",
                "What is the annual solar radiation exposure for each element?",
                "Show me elements with high summer radiation but low winter radiation"
            ])
        
        # Location-based queries
        if 'LocationX' in df.columns and 'LocationY' in df.columns:
            queries.extend([
                "Which elements are closest to the courtyard?",
                "What is the spatial distribution of building elements?",
                "Calculate distances between building elements"
            ])
        
        # Area and perimeter queries
        if 'GrossArea' in df.columns:
            queries.extend([
                "What is the total gross area of all building elements?",
                "Which elements have the largest gross area?",
                "What is the average gross area per element?"
            ])
        
        if 'Perimeter' in df.columns:
            queries.extend([
                "Which elements have the longest perimeter?",
                "What is the total perimeter of all building elements?"
            ])
        
        # Load bearing and compartmentation queries
        if 'LoadBearing' in df.columns:
            queries.extend([
                "How many load-bearing elements are there?",
                "Which elements are load-bearing?",
                "What is the distribution of load-bearing vs non-load-bearing elements?"
            ])
        
        if 'Compartmentation' in df.columns:
            queries.extend([
                "How many compartmentation elements are there?",
                "Which elements are part of compartmentation?",
                "What is the distribution of compartmentation elements?"
            ])
        
        # UTCI queries
        if 'UTCI' in df.columns:
            queries.extend([
                "What is the average UTCI for all elements?",
                "Which elements have the highest UTCI values?",
                "Show me elements with UTCI above a certain threshold"
            ])
        
        # If no specific queries can be generated, provide generic ones
        if not queries:
            queries = [
                "How many nodes are in the graph?",
                "What are all the unique node types?",
                "Show me the first 5 nodes with their properties",
                "What are the available properties in the data?"
            ]
        
        return queries


def main():
    """Example usage of the IFCDataPrep utility"""
    prep = IFCDataPrep()
    
    print("🏗️ IFC Data Preparation Utility")
    print("=" * 50)
    
    # Example: Process IFC data
    print("\n1. Example IFC data processing workflow:")
    print("   - Load your IFC CSV file")
    print("   - Clean and filter the data")
    print("   - Create spatial relationships")
    print("   - Save processed data")
    
    print("\n2. Usage example:")
    print("   prep = IFCDataPrep()")
    print("   df = prep.load_ifc_data('your_ifc_data.csv')")
    print("   df = prep.clean_ifc_data(df)")
    print("   window_df = prep.filter_by_ifc_type(df, ['IfcWindow'])")
    print("   relationships = prep.create_spatial_relationships(df)")
    print("   prep.save_processed_data(df, 'building_nodes.csv')")
    print("   prep.save_processed_data(relationships, 'building_edges.csv')")
    
    print(f"\n✅ IFC data preparation utility ready!")
    print(f"📁 Output directory: {prep.output_dir}")


if __name__ == "__main__":
    main() 