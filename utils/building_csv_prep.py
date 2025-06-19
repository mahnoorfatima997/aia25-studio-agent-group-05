"""
Building CSV Preparation Utility

This script helps prepare building data CSV files for integration with the courtyard graph query system.
It provides templates and validation for different types of building elements.
"""

import pandas as pd
import os
import json
from typing import Dict, List, Any

class BuildingCSVPrep:
    def __init__(self, output_dir: str = None):
        """
        Initialize the Building CSV Preparation utility
        
        Args:
            output_dir: Directory to save CSV files (default: ~/Downloads/courtyard_graph)
        """
        self.output_dir = output_dir or os.path.expanduser("~/Downloads/courtyard_graph")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Define templates for different building element types
        self.templates = {
            'building_nodes': {
                'columns': ['id', 'x', 'y', 'courtyard_view_numeric', 'view_quality', 'direction_angle', 
                           'incident_radiation_summer', 'incident_radiation_annual', 'sun_hours_summer', 
                           'sun_hours_winter', 'incident_radiation_winter', 'view_distance'],
                'sample_data': [
                    ['space_001', -15, 45, 0.85, 'excellent', 180, 1200, 800, 6.5, 4.2, 600, 25.5],
                    ['space_002', -20, 40, 0.72, 'good', 135, 950, 750, 5.8, 3.8, 550, 32.1],
                    ['space_003', -25, 50, 0.45, 'fair', 90, 650, 600, 4.2, 2.5, 400, 45.8],
                    ['space_004', -18, 35, 0.91, 'excellent', 225, 1100, 850, 7.2, 5.1, 700, 18.3],
                    ['space_005', -22, 48, 0.38, 'poor', 45, 480, 420, 3.1, 1.8, 320, 52.7]
                ]
            },
            'building_edges': {
                'columns': ['source', 'target', 'relationship_type', 'distance', 'weight'],
                'sample_data': [
                    ['space_001', 'space_002', 'adjacent', 5.2, 0.8],
                    ['space_002', 'space_003', 'connected', 8.7, 0.6],
                    ['space_001', 'space_004', 'adjacent', 10.1, 0.7],
                    ['space_003', 'space_005', 'connected', 6.3, 0.9],
                    ['space_004', 'space_005', 'adjacent', 7.8, 0.5]
                ]
            },
            'rooms': {
                'columns': ['id', 'name', 'function', 'area', 'floor', 'x', 'y', 'orientation', 'has_window', 'has_door'],
                'sample_data': [
                    ['room_001', 'Living Room', 'living', 25.5, 1, -15, 45, 'south', True, True],
                    ['room_002', 'Kitchen', 'kitchen', 18.2, 1, -20, 40, 'east', True, True],
                    ['room_003', 'Bedroom 1', 'bedroom', 15.8, 1, -25, 50, 'north', True, False],
                    ['room_004', 'Bathroom', 'bathroom', 8.5, 1, -18, 35, 'west', False, True]
                ]
            },
            'windows': {
                'columns': ['id', 'room_id', 'orientation', 'size', 'x', 'y', 'height', 'type'],
                'sample_data': [
                    ['window_001', 'room_001', 'south', 'large', -15, 44, 1.2, 'sliding'],
                    ['window_002', 'room_002', 'east', 'medium', -19, 40, 1.0, 'casement'],
                    ['window_003', 'room_003', 'north', 'small', -25, 51, 0.8, 'fixed']
                ]
            },
            'doors': {
                'columns': ['id', 'room_id', 'type', 'width', 'height', 'x', 'y', 'opens_to'],
                'sample_data': [
                    ['door_001', 'room_001', 'sliding', 2.4, 2.1, -15, 46, 'courtyard'],
                    ['door_002', 'room_002', 'hinged', 0.9, 2.1, -20, 41, 'courtyard'],
                    ['door_003', 'room_004', 'hinged', 0.8, 2.1, -18, 36, 'courtyard']
                ]
            },
            'floors': {
                'columns': ['id', 'level', 'area', 'height', 'material', 'finish'],
                'sample_data': [
                    ['floor_001', 1, 120.5, 2.8, 'concrete', 'tiles'],
                    ['floor_002', 2, 95.2, 2.6, 'concrete', 'carpet']
                ]
            },
            'walls': {
                'columns': ['id', 'room_id', 'type', 'length', 'height', 'material', 'x', 'y'],
                'sample_data': [
                    ['wall_001', 'room_001', 'exterior', 6.0, 2.8, 'brick', -15, 45],
                    ['wall_002', 'room_002', 'exterior', 4.5, 2.8, 'brick', -20, 40],
                    ['wall_003', 'room_001', 'interior', 5.0, 2.8, 'drywall', -12, 45]
                ]
            },
            'furniture': {
                'columns': ['id', 'room_id', 'type', 'name', 'x', 'y', 'dimensions'],
                'sample_data': [
                    ['furniture_001', 'room_001', 'seating', 'Sofa', -14, 44, '2.4x0.8x0.9'],
                    ['furniture_002', 'room_002', 'storage', 'Kitchen Cabinet', -19, 39, '3.0x0.6x2.1'],
                    ['furniture_003', 'room_003', 'sleeping', 'Bed', -24, 50, '1.6x2.0x0.5']
                ]
            },
            'equipment': {
                'columns': ['id', 'room_id', 'type', 'name', 'power', 'x', 'y', 'status'],
                'sample_data': [
                    ['equipment_001', 'room_002', 'appliance', 'Refrigerator', '220V', -21, 40, 'active'],
                    ['equipment_002', 'room_002', 'appliance', 'Oven', '220V', -19, 39, 'active'],
                    ['equipment_003', 'room_004', 'fixture', 'Toilet', 'N/A', -18, 35, 'active']
                ]
            }
        }
    
    def create_template_csv(self, element_type: str, filename: str = None) -> str:
        """
        Create a template CSV file for a specific building element type
        
        Args:
            element_type: Type of building element (rooms, windows, doors, etc.)
            filename: Optional custom filename
            
        Returns:
            Path to the created CSV file
        """
        if element_type not in self.templates:
            raise ValueError(f"Unknown element type: {element_type}. Available types: {list(self.templates.keys())}")
        
        template = self.templates[element_type]
        
        # Create DataFrame
        df = pd.DataFrame(template['sample_data'], columns=template['columns'])
        
        # Generate filename
        if filename is None:
            filename = f"{element_type}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Save CSV
        df.to_csv(filepath, index=False)
        print(f"✅ Created template CSV: {filepath}")
        print(f"   Columns: {template['columns']}")
        print(f"   Sample rows: {len(template['sample_data'])}")
        
        return filepath
    
    def create_all_templates(self) -> Dict[str, str]:
        """
        Create template CSV files for all building element types
        
        Returns:
            Dictionary mapping element types to file paths
        """
        created_files = {}
        
        for element_type in self.templates.keys():
            filepath = self.create_template_csv(element_type)
            created_files[element_type] = filepath
        
        return created_files
    
    def validate_csv(self, filepath: str, element_type: str = None) -> Dict[str, Any]:
        """
        Validate a CSV file against expected schema
        
        Args:
            filepath: Path to the CSV file
            element_type: Expected element type (optional)
            
        Returns:
            Validation results dictionary
        """
        try:
            df = pd.read_csv(filepath)
            
            validation_result = {
                'valid': True,
                'filepath': filepath,
                'rows': len(df),
                'columns': list(df.columns),
                'missing_required': [],
                'data_types': {},
                'issues': []
            }
            
            # Determine element type from filename if not provided
            if element_type is None:
                filename = os.path.basename(filepath)
                for template_type in self.templates.keys():
                    if template_type in filename.lower():
                        element_type = template_type
                        break
            
            # Validate against template if element type is known
            if element_type and element_type in self.templates:
                template = self.templates[element_type]
                required_columns = template['columns']
                
                # Check for missing required columns
                missing = [col for col in required_columns if col not in df.columns]
                if missing:
                    validation_result['missing_required'] = missing
                    validation_result['issues'].append(f"Missing required columns: {missing}")
                
                # Check data types
                for col in df.columns:
                    validation_result['data_types'][col] = str(df[col].dtype)
            
            # Check for empty values in ID column
            id_columns = ['id', 'Id', 'ID']
            for id_col in id_columns:
                if id_col in df.columns:
                    empty_ids = df[id_col].isna().sum()
                    if empty_ids > 0:
                        validation_result['issues'].append(f"Found {empty_ids} empty values in {id_col} column")
            
            # Check for duplicate IDs
            for id_col in id_columns:
                if id_col in df.columns:
                    duplicates = df[id_col].duplicated().sum()
                    if duplicates > 0:
                        validation_result['issues'].append(f"Found {duplicates} duplicate values in {id_col} column")
            
            if validation_result['issues']:
                validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'filepath': filepath,
                'error': str(e),
                'issues': [f"File reading error: {str(e)}"]
            }
    
    def merge_csv_files(self, csv_files: Dict[str, str], output_filename: str = "building_data.csv") -> str:
        """
        Merge multiple CSV files into a single file with a type column
        
        Args:
            csv_files: Dictionary mapping element types to file paths
            output_filename: Name of the merged output file
            
        Returns:
            Path to the merged CSV file
        """
        merged_data = []
        
        for element_type, filepath in csv_files.items():
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                df['element_type'] = element_type
                merged_data.append(df)
        
        if merged_data:
            merged_df = pd.concat(merged_data, ignore_index=True)
            output_path = os.path.join(self.output_dir, output_filename)
            merged_df.to_csv(output_path, index=False)
            print(f"✅ Merged {len(merged_data)} CSV files into: {output_path}")
            return output_path
        else:
            print("❌ No valid CSV files to merge")
            return None
    
    def get_coordinate_ranges(self, csv_files: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Analyze coordinate ranges across multiple CSV files
        
        Args:
            csv_files: List of CSV file paths to analyze
            
        Returns:
            Dictionary with coordinate ranges for each file
        """
        ranges = {}
        
        for filepath in csv_files:
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                file_ranges = {}
                
                for coord in ['x', 'y']:
                    if coord in df.columns:
                        file_ranges[coord] = {
                            'min': float(df[coord].min()),
                            'max': float(df[coord].max()),
                            'mean': float(df[coord].mean())
                        }
                
                if file_ranges:
                    ranges[os.path.basename(filepath)] = file_ranges
        
        return ranges
    
    def suggest_coordinate_adjustments(self, courtyard_range: Dict[str, Dict[str, float]], 
                                     building_ranges: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Suggest coordinate adjustments to align building data with courtyard coordinates
        
        Args:
            courtyard_range: Coordinate range of courtyard data
            building_ranges: Coordinate ranges of building data
            
        Returns:
            Dictionary with adjustment suggestions
        """
        suggestions = {
            'scaling_needed': False,
            'translation_needed': False,
            'adjustments': {},
            'recommendations': []
        }
        
        # Check if scaling is needed
        courtyard_x_range = courtyard_range['x']['max'] - courtyard_range['x']['min']
        courtyard_y_range = courtyard_range['y']['max'] - courtyard_range['y']['min']
        
        for filename, ranges in building_ranges.items():
            if 'x' in ranges and 'y' in ranges:
                building_x_range = ranges['x']['max'] - ranges['x']['min']
                building_y_range = ranges['y']['max'] - ranges['y']['min']
                
                # Check if ranges are significantly different
                if building_x_range > courtyard_x_range * 2 or building_y_range > courtyard_y_range * 2:
                    suggestions['scaling_needed'] = True
                    suggestions['recommendations'].append(
                        f"Consider scaling {filename} coordinates to match courtyard scale"
                    )
                
                # Check if translation is needed
                if (ranges['x']['min'] > courtyard_range['x']['max'] or 
                    ranges['x']['max'] < courtyard_range['x']['min'] or
                    ranges['y']['min'] > courtyard_range['y']['max'] or 
                    ranges['y']['max'] < courtyard_range['y']['min']):
                    suggestions['translation_needed'] = True
                    suggestions['recommendations'].append(
                        f"Consider translating {filename} coordinates to align with courtyard"
                    )
        
        return suggestions


def main():
    """Example usage of the BuildingCSVPrep utility"""
    prep = BuildingCSVPrep()
    
    print("🏗️ Building CSV Preparation Utility")
    print("=" * 50)
    
    # Create all template files
    print("\n1. Creating template CSV files...")
    created_files = prep.create_all_templates()
    
    # Validate the created files
    print("\n2. Validating created files...")
    for element_type, filepath in created_files.items():
        validation = prep.validate_csv(filepath, element_type)
        status = "✅" if validation['valid'] else "❌"
        print(f"{status} {element_type}: {validation['rows']} rows, {len(validation['columns'])} columns")
        if validation['issues']:
            for issue in validation['issues']:
                print(f"   ⚠️ {issue}")
    
    # Analyze coordinate ranges
    print("\n3. Analyzing coordinate ranges...")
    ranges = prep.get_coordinate_ranges(list(created_files.values()))
    for filename, file_ranges in ranges.items():
        print(f"📊 {filename}:")
        for coord, range_data in file_ranges.items():
            print(f"   {coord}: {range_data['min']:.2f} to {range_data['max']:.2f} (mean: {range_data['mean']:.2f})")
    
    print(f"\n✅ All template files created in: {prep.output_dir}")
    print("\nNext steps:")
    print("1. Edit the CSV files with your actual building data")
    print("2. Ensure coordinates align with your courtyard coordinate system")
    print("3. Load the files into the graph query system")


if __name__ == "__main__":
    main() 