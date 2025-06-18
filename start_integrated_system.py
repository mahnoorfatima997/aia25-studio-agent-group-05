#!/usr/bin/env python3
"""
Startup script for the Integrated Courtyard Design Assistant with Graph Query
"""

import subprocess
import sys
import os
import time

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check if Neo4j is mentioned in the environment
    try:
        import neo4j
        print("✅ Neo4j Python driver available")
    except ImportError:
        print("⚠️ Neo4j Python driver not found. Install with: pip install neo4j")
    
    # Check if PyQt5 is available
    try:
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5 available")
    except ImportError:
        print("❌ PyQt5 not found. Install with: pip install PyQt5")
        return False
    
    # Check if Flask is available
    try:
        import flask
        print("✅ Flask available")
    except ImportError:
        print("❌ Flask not found. Install with: pip install flask")
        return False
    
    return True

def check_neo4j_running():
    """Check if Neo4j is running"""
    print("\n🔍 Checking Neo4j connection...")
    try:
        from graph_query import GraphQueryEngine
        engine = GraphQueryEngine()
        if engine.driver:
            print("✅ Neo4j is running and accessible")
            engine.close()
            return True
        else:
            print("❌ Neo4j is not running or not accessible")
            print("   Please start Neo4j database first")
            return False
    except Exception as e:
        print(f"❌ Error checking Neo4j: {e}")
        print("   Please ensure Neo4j is running on the default port")
        return False

def start_integrated_system():
    """Start the integrated system"""
    print("\n🚀 Starting Integrated Courtyard Design Assistant...")
    print("=" * 60)
    print("This will start:")
    print("  • Flask server on port 5000")
    print("  • PyQt5 UI with Design Assistant and Graph Query tabs")
    print("  • Graph Query engine for Neo4j integration")
    print("=" * 60)
    
    try:
        # Start the integrated server
        print("\n📡 Starting server and UI...")
        subprocess.run([sys.executable, "gh_server.py"])
    except KeyboardInterrupt:
        print("\n\n⏹️ System stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting system: {e}")
        print("Please check the error messages above")

def main():
    """Main function"""
    print("🏡 Integrated Courtyard Design Assistant with Graph Query")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install them first.")
        return
    
    # Check Neo4j
    neo4j_ok = check_neo4j_running()
    if not neo4j_ok:
        print("\n⚠️ Neo4j is not running. The Graph Query functionality will not work.")
        print("   You can still use the Design Assistant, but Graph Query will fail.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Start the system
    start_integrated_system()

if __name__ == "__main__":
    main() 