"""
IFC File Processor (Optional Enhancement)

This module provides optional support for processing full IFC files and extracting
relevant data for the courtyard analysis system. This is an enhancement to the
existing CSV-based approach.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

# Optional IFC processing - only import if available
try:
    import ifcopenshell
    import ifcopenshell.util.element
    import ifcopenshell.util.placement
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False
    print("⚠️ IFC processing not available. Install with: pip install ifcopenshell")

class IFCFileProcessor:
    """Process full IFC files and extract relevant data for courtyard analysis"""
    
    def __init__(self):
        self.ifc_file = None
        self.extracted_data = []
        
    def load_ifc_file(self, filepath: str) -> bool:
        """
        Load an IFC file
        
        Args:
            filepath: Path to the IFC file
            
        Returns:
            True if successful, False otherwise
        """
        if not IFC_AVAILABLE:
            print("❌ IFC processing not available. Install ifcopenshell first.")
            return False
            
        try:
            self.ifc_file = ifcopenshell.open(filepath)
            print(f"✅ Loaded IFC file: {len(self.ifc_file.by_type('IfcProduct'))} products")
            return True
        except Exception as e:
            print(f"❌ Error loading IFC file: {e}")
            return False
    
    def extract_window_data(self) -> pd.DataFrame:
        """
        Extract window data with environmental properties
        
        Returns:
            DataFrame with window data
        """
        if not self.ifc_file:
            return pd.DataFrame()
        
        windows = []
        
        # Get all windows
        ifc_windows = self.ifc_file.by_type('IfcWindow')
        
        for window in ifc_windows:
            window_data = self._extract_element_data(window)
            if window_data:
                windows.append(window_data)
        
        return pd.DataFrame(windows)
    
    def extract_building_elements(self, element_types: List[str] = None) -> pd.DataFrame:
        """
        Extract data for specified building element types
        
        Args:
            element_types: List of IFC types to extract (e.g., ['IfcWindow', 'IfcWall'])
            
        Returns:
            DataFrame with building element data
        """
        if not self.ifc_file:
            return pd.DataFrame()
        
        if element_types is None:
            element_types = ['IfcWindow', 'IfcWall', 'IfcDoor', 'IfcSpace', 'IfcSlab']
        
        all_elements = []
        
        for element_type in element_types:
            elements = self.ifc_file.by_type(element_type)
            for element in elements:
                element_data = self._extract_element_data(element)
                if element_data:
                    all_elements.append(element_data)
        
        return pd.DataFrame(all_elements)
    
    def _extract_element_data(self, element) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single IFC element
        
        Args:
            element: IFC element object
            
        Returns:
            Dictionary with element data
        """
        try:
            # Basic properties
            data = {
                'GlobalId': element.GlobalId,
                'Name': element.Name or '',
                'Description': element.Description or '',
                'IfcType': element.is_a(),
                'ObjectType': element.ObjectType or ''
            }
            
            # Get location
            location = self._get_element_location(element)
            if location:
                data.update(location)
            
            # Get properties
            properties = self._get_element_properties(element)
            if properties:
                data.update(properties)
            
            # Get quantities
            quantities = self._get_element_quantities(element)
            if quantities:
                data.update(quantities)
            
            return data
            
        except Exception as e:
            logging.warning(f"Error extracting data from element {element.GlobalId}: {e}")
            return None
    
    def _get_element_location(self, element) -> Optional[Dict[str, float]]:
        """Extract location data from IFC element"""
        try:
            if hasattr(element, 'ObjectPlacement'):
                placement = element.ObjectPlacement
                if placement and hasattr(placement, 'RelativePlacement'):
                    location = placement.RelativePlacement.Location
                    if location and hasattr(location, 'Coordinates'):
                        coords = location.Coordinates
                        if len(coords) >= 2:
                            return {
                                'LocationX': float(coords[0]),
                                'LocationY': float(coords[1]),
                                'LocationZ': float(coords[2]) if len(coords) > 2 else 0.0
                            }
        except Exception as e:
            logging.warning(f"Error extracting location: {e}")
        
        return None
    
    def _get_element_properties(self, element) -> Optional[Dict[str, Any]]:
        """Extract property sets from IFC element"""
        try:
            properties = {}
            
            # Get property sets
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_set = definition.RelatingPropertyDefinition
                    if property_set.is_a('IfcPropertySet'):
                        for prop in property_set.HasProperties:
                            if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                value = prop.NominalValue.wrappedValue
                                properties[prop.Name] = value
            
            # Look for environmental properties
            env_properties = {}
            for key, value in properties.items():
                key_lower = key.lower()
                if 'view' in key_lower or 'radiation' in key_lower or 'sun' in key_lower:
                    env_properties[key] = value
            
            return env_properties
            
        except Exception as e:
            logging.warning(f"Error extracting properties: {e}")
        
        return None
    
    def _get_element_quantities(self, element) -> Optional[Dict[str, float]]:
        """Extract quantities from IFC element"""
        try:
            quantities = {}
            
            # Get quantity sets
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    quantity_set = definition.RelatingPropertyDefinition
                    if quantity_set.is_a('IfcElementQuantity'):
                        for quantity in quantity_set.Quantities:
                            if hasattr(quantity, 'LengthValue'):
                                quantities[f"{quantity.Name}_length"] = quantity.LengthValue
                            elif hasattr(quantity, 'AreaValue'):
                                quantities[f"{quantity.Name}_area"] = quantity.AreaValue
                            elif hasattr(quantity, 'VolumeValue'):
                                quantities[f"{quantity.Name}_volume"] = quantity.VolumeValue
            
            return quantities
            
        except Exception as e:
            logging.warning(f"Error extracting quantities: {e}")
        
        return None
    
    def create_spatial_relationships(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create spatial relationships between IFC elements
        
        Args:
            df: DataFrame with IFC element data
            
        Returns:
            DataFrame with spatial relationships
        """
        relationships = []
        
        # Create relationships between elements with location data
        for i, row1 in df.iterrows():
            for j, row2 in df.iterrows():
                if i < j:  # Avoid duplicate relationships
                    if pd.notna(row1.get('LocationX')) and pd.notna(row1.get('LocationY')) and \
                       pd.notna(row2.get('LocationX')) and pd.notna(row2.get('LocationY')):
                        
                        distance = ((row2['LocationX'] - row1['LocationX']) ** 2 + 
                                  (row2['LocationY'] - row1['LocationY']) ** 2) ** 0.5
                        
                        if distance <= 20.0:  # Within 20 units
                            relationships.append({
                                'source': row1['GlobalId'],
                                'target': row2['GlobalId'],
                                'relationship_type': 'adjacent',
                                'distance': round(distance, 2),
                                'source_type': row1['IfcType'],
                                'target_type': row2['IfcType']
                            })
        
        return pd.DataFrame(relationships)
    
    def export_to_csv(self, df: pd.DataFrame, output_path: str) -> bool:
        """
        Export extracted data to CSV
        
        Args:
            df: DataFrame to export
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            df.to_csv(output_path, index=False)
            print(f"✅ Exported {len(df)} elements to {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")
            return False


def process_ifc_file_to_csv(ifc_filepath: str, output_dir: str = None) -> bool:
    """
    Process an IFC file and convert it to CSV format for the graph query system
    
    Args:
        ifc_filepath: Path to the IFC file
        output_dir: Output directory for CSV files
        
    Returns:
        True if successful
    """
    if not IFC_AVAILABLE:
        print("❌ IFC processing not available. Install ifcopenshell first.")
        print("   pip install ifcopenshell")
        return False
    
    output_dir = output_dir or os.path.expanduser("~/Downloads/courtyard_graph")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🏗️ Processing IFC file: {ifc_filepath}")
    
    # Initialize processor
    processor = IFCFileProcessor()
    
    # Load IFC file
    if not processor.load_ifc_file(ifc_filepath):
        return False
    
    # Extract building elements
    print("📊 Extracting building elements...")
    elements_df = processor.extract_building_elements()
    
    if len(elements_df) == 0:
        print("❌ No elements found in IFC file")
        return False
    
    print(f"✅ Extracted {len(elements_df)} building elements")
    
    # Create spatial relationships
    print("🔗 Creating spatial relationships...")
    relationships_df = processor.create_spatial_relationships(elements_df)
    
    # Export to CSV
    building_nodes_path = os.path.join(output_dir, 'building_nodes.csv')
    building_edges_path = os.path.join(output_dir, 'building_edges.csv')
    
    if processor.export_to_csv(elements_df, building_nodes_path) and \
       processor.export_to_csv(relationships_df, building_edges_path):
        
        print(f"✅ IFC file processed successfully!")
        print(f"📁 Output files:")
        print(f"   - {building_nodes_path}")
        print(f"   - {building_edges_path}")
        
        # Show element type distribution
        if 'IfcType' in elements_df.columns:
            type_counts = elements_df['IfcType'].value_counts()
            print(f"\n📋 Element type distribution:")
            for ifc_type, count in type_counts.items():
                print(f"   {ifc_type}: {count}")
        
        return True
    
    return False


def main():
    """Example usage of IFC file processor"""
    print("🏗️ IFC File Processor (Optional Enhancement)")
    print("=" * 50)
    
    if not IFC_AVAILABLE:
        print("❌ IFC processing not available.")
        print("\nTo enable IFC file processing, install ifcopenshell:")
        print("   pip install ifcopenshell")
        print("\nThen you can use:")
        print("   python -c \"from utils.ifc_file_processor import process_ifc_file_to_csv; process_ifc_file_to_csv('your_file.ifc')\"")
        return
    
    print("✅ IFC processing available!")
    print("\nUsage:")
    print("   from utils.ifc_file_processor import process_ifc_file_to_csv")
    print("   process_ifc_file_to_csv('your_file.ifc')")
    print("\nThis will:")
    print("   1. Load your IFC file")
    print("   2. Extract building elements and properties")
    print("   3. Create spatial relationships")
    print("   4. Export to CSV format for the graph query system")


if __name__ == "__main__":
    main() 