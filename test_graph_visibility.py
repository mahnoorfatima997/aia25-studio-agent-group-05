#!/usr/bin/env python3
"""
Test script to verify graph visibility improvements:
- Black text on nodes for better visibility
- Cardinal directions positioned further from nodes
- Larger, more visible cardinal direction text
"""

import sys
import json
from PyQt5.QtWidgets import QApplication
from graph_gh import MainWindow

def create_test_graph_data():
    """Create test graph data with various node types"""
    return {
        "nodes": [
            {"id": "play", "pos": {"x": -25, "y": 45}, "weight": 6, "anchor": False},
            {"id": "rest", "pos": {"x": -15, "y": 35}, "weight": 4, "anchor": False},
            {"id": "pond", "pos": {"x": -20, "y": 50}, "weight": 8, "anchor": True},
            {"id": "tree", "pos": {"x": -30, "y": 40}, "weight": 5, "anchor": False},
            {"id": "flower", "pos": {"x": -10, "y": 55}, "weight": 3, "anchor": False}
        ],
        "links": [
            {"source": "play", "target": "rest"},
            {"source": "play", "target": "pond"},
            {"source": "rest", "target": "tree"},
            {"source": "pond", "target": "flower"}
        ],
        "directed": False,
        "multigraph": False,
        "graph": {}
    }

def test_graph_visibility():
    """Test the graph visibility improvements"""
    app = QApplication(sys.argv)
    
    # Create test graph data
    test_data = create_test_graph_data()
    
    # Create and show the graph window
    window = MainWindow(graph_data=test_data)
    window.show()
    
    print("✅ Graph window opened successfully!")
    print("📋 Test features:")
    print("   - Node text should be black and clearly visible")
    print("   - Cardinal directions (N, S, E, W) should be positioned away from nodes")
    print("   - Cardinal directions should be large and bold")
    print("   - No text should overlap with nodes")
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_graph_visibility() 