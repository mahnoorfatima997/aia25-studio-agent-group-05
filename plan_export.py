import os
import json
import math
from datetime import datetime
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import (
    Color, black, white, gray, HexColor
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, Flowable
)
from reportlab.graphics.shapes import (
    Drawing, Rect, Circle, Line, Polygon, String
)
from reportlab.graphics.charts.textlabels import Label
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle as MplCircle, Polygon as MplPolygon
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextBrowser
)
from PyQt5.QtCore import Qt

class PlanExportTab:
    """Plan Export Tab functionality for the UI"""
    
    def __init__(self, tab_widget, main_ui):
        self.tab_widget = tab_widget
        self.main_ui = main_ui
        self.create_plan_export_tab()
    
    def create_plan_export_tab(self):
        """Create the Plan Export tab for professional PDF export"""
        plan_export_widget = QWidget()
        layout = QVBoxLayout(plan_export_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Export Professional Courtyard Plan")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Generate a high-quality, professional PDF plan of your courtyard design. "
            "The plan will include a site layout, materials, tree placement, and all design details."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 16px; margin-bottom: 15px;")
        layout.addWidget(description)

        # Design summary area
        self.plan_summary_display = QTextBrowser()
        self.plan_summary_display.setPlaceholderText("Design summary will appear here once your design is ready.")
        self.plan_summary_display.setFixedHeight(180)
        self.plan_summary_display.setStyleSheet("""
            QTextBrowser {
                background-color: #f0f0f0;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
            }
        """)
        layout.addWidget(self.plan_summary_display)

        # Export button
        self.plan_export_button = QPushButton("📋 Export Professional Plan (PDF)")
        self.plan_export_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
            QPushButton:pressed {
                background-color: #BF360C;
            }
        """)
        self.plan_export_button.clicked.connect(self.export_professional_plan_handler)
        layout.addWidget(self.plan_export_button)

        # Status display
        self.plan_export_status = QTextBrowser()
        self.plan_export_status.setPlaceholderText("Status updates will appear here...")
        self.plan_export_status.setFixedHeight(100)
        self.plan_export_status.setStyleSheet("""
            QTextBrowser {
                background-color: #f0f0f0;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
            }
        """)
        layout.addWidget(self.plan_export_status)

        self.tab_widget.addTab(plan_export_widget, "📋 Plan Export")

    def update_plan_summary(self):
        """Update the plan summary display in the Plan Export tab."""
        if hasattr(self.main_ui, 'design_data') and self.main_ui.design_data:
            summary = ["<b>Design Data Summary:</b>"]
            summary.append(f"<b>Concept:</b> {getattr(self.main_ui, 'concept', 'N/A')[:120]}...")
            summary.append(f"<b>Spaces:</b> {self.main_ui.design_data.get('spaces', {})}")
            summary.append(f"<b>External Functions:</b> {self.main_ui.design_data.get('external_functions', {})}")
            summary.append(f"<b>Attributes:</b> {getattr(self.main_ui, 'attributes', {})}")
            if hasattr(self.main_ui, 'tree_data') and self.main_ui.tree_data:
                summary.append(f"<b>Tree Placement:</b> {self.main_ui.tree_data.get('tree_placement', {})}")
            self.plan_summary_display.setHtml('<br/>'.join(summary))
        else:
            self.plan_summary_display.setText("No design data available yet. Complete the design process to enable plan export.")

    def export_professional_plan_handler(self):
        """Handler for the Export Professional Plan button in the Plan Export tab."""
        try:
            # Check if we have all the necessary data
            if not hasattr(self.main_ui, 'design_data') or not self.main_ui.design_data:
                raise Exception("No design data available. Please complete the design process first.")
            if not hasattr(self.main_ui, 'concept') or not self.main_ui.concept:
                raise Exception("No design concept available. Please complete the concept phase first.")
            if not hasattr(self.main_ui, 'attributes') or not self.main_ui.attributes:
                raise Exception("No attributes data available. Please complete the attributes phase first.")
            if not hasattr(self.main_ui, 'tree_data') or not self.main_ui.tree_data:
                raise Exception("No tree data available. Please complete the design process first.")
            
            # Debug: Print data types and content
            print(f"DEBUG: design_data type: {type(self.main_ui.design_data)}")
            print(f"DEBUG: attributes type: {type(self.main_ui.attributes)}")
            print(f"DEBUG: tree_data type: {type(self.main_ui.tree_data)}")
            
            # Debug: Check links data specifically
            if hasattr(self.main_ui, 'design_data') and isinstance(self.main_ui.design_data, dict):
                links = self.main_ui.design_data.get('links', [])
                print(f"DEBUG: links type: {type(links)}")
                print(f"DEBUG: links content: {links}")
                if isinstance(links, list) and len(links) > 0:
                    print(f"DEBUG: First link type: {type(links[0])}")
                    print(f"DEBUG: First link content: {links[0]}")
            
            # Parse data if they are JSON strings
            design_data = self.main_ui.design_data
            if isinstance(design_data, str):
                try:
                    design_data = json.loads(design_data)
                    print("DEBUG: Successfully parsed design_data from string")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Failed to parse design_data: {e}")
                    print(f"DEBUG: design_data content: {design_data[:200]}...")
                    raise Exception("Invalid design data format")
            
            attributes = self.main_ui.attributes
            if isinstance(attributes, str):
                try:
                    attributes = json.loads(attributes)
                    print("DEBUG: Successfully parsed attributes from string")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Failed to parse attributes: {e}")
                    print(f"DEBUG: attributes content: {attributes[:200]}...")
                    raise Exception("Invalid attributes format")
            
            tree_data = self.main_ui.tree_data
            if isinstance(tree_data, str):
                try:
                    tree_data = json.loads(tree_data)
                    print("DEBUG: Successfully parsed tree_data from string")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: Failed to parse tree_data: {e}")
                    print(f"DEBUG: tree_data content: {tree_data[:200]}...")
                    raise Exception("Invalid tree data format")
            
            # Final validation
            if not isinstance(design_data, dict):
                raise Exception(f"Design data must be a dictionary, got {type(design_data)}")
            if not isinstance(attributes, dict):
                raise Exception(f"Attributes must be a dictionary, got {type(attributes)}")
            if not isinstance(tree_data, dict):
                raise Exception(f"Tree data must be a dictionary, got {type(tree_data)}")
            
            print("DEBUG: All data validated successfully")
            
            # Show status message
            self.plan_export_status.setText("🔄 Generating professional courtyard plan... This may take a moment.")
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Generate the professional plan
            plan_path = export_courtyard_plan(
                design_data=design_data,
                tree_data=tree_data,
                attributes=attributes,
                concept=self.main_ui.concept
            )
            
            # Show success message with file location
            self.plan_export_status.setText(
                f"🎉 Professional courtyard plan generated successfully!\n\n"
                f"📄 Plan saved to: {plan_path}\n\n"
                f"The plan includes:\n"
                f"• Professional site layout with all spaces\n"
                f"• Materials and specifications\n"
                f"• Tree placement and water requirements\n"
                f"• Design concept and spatial analysis\n"
                f"• Professional legend and notes\n\n"
                f"Open the PDF to view your complete courtyard design documentation!"
            )
        except Exception as e:
            self.plan_export_status.setText(
                f"❌ Error generating professional plan: {str(e)}\n\n"
                f"Please ensure you have completed all design phases (concept, functions, attributes, graph) before exporting."
            )
            print(f"Error exporting professional plan: {e}")
            import traceback
            traceback.print_exc()

class ProfessionalPlanExporter:
    def __init__(self, output_dir=None):
        """Initialize the professional plan exporter"""
        self.output_dir = output_dir or os.path.expanduser("~/Downloads/courtyard_plans")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Professional color palette for architectural plans
        self.colors = {
            'play': HexColor('#FF6B6B'),      # Coral red for active spaces
            'rest': HexColor('#4ECDC4'),      # Teal for quiet spaces
            'pond': HexColor('#45B7D1'),      # Blue for water features
            'flower': HexColor('#96CEB4'),    # Sage green for gardens
            'tree': HexColor('#2E8B57'),      # Forest green for trees
            'path': HexColor('#8B7355'),      # Brown for paths
            'building': HexColor('#696969'),  # Dark gray for buildings
            'text': black,
            'grid': HexColor('#E0E0E0'),
            'border': HexColor('#2C3E50')
        }
        
        # Material patterns and symbols
        self.materials = {
            'wood': 'wooden texture',
            'stone': 'stone pattern',
            'concrete': 'concrete finish',
            'grass': 'grass texture',
            'water': 'water pattern',
            'gravel': 'gravel texture'
        }
    
    def generate_professional_plan(self, design_data, tree_data, attributes, concept, output_filename=None):
        """
        Generate a professional PDF courtyard plan
        
        Args:
            design_data: Complete design data with positions, spaces, etc.
            tree_data: Tree placement and water requirements
            attributes: Material and specification data
            concept: Design concept text
            output_filename: Optional custom filename
        """
        # Debug: Check links data in generate_professional_plan
        print(f"DEBUG: generate_professional_plan - design_data type: {type(design_data)}")
        if isinstance(design_data, dict):
            links = design_data.get('links', [])
            print(f"DEBUG: generate_professional_plan - links type: {type(links)}")
            print(f"DEBUG: generate_professional_plan - links content: {links}")
            if isinstance(links, list) and len(links) > 0:
                print(f"DEBUG: generate_professional_plan - First link type: {type(links[0])}")
                print(f"DEBUG: generate_professional_plan - First link content: {links[0]}")
        
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"courtyard_plan_{timestamp}.pdf"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A3),
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        # Build the plan content - TEXT FIRST, THEN PLAN
        story = []
        
        # 1. Title Page
        story.extend(self._create_title_page(concept))
        story.append(PageBreak())
        
        # 2. Design Documentation & Analysis (TEXT CONTENT FIRST)
        story.extend(self._create_design_documentation_page(design_data, concept, tree_data, attributes))
        story.append(PageBreak())
        
        # 3. Specifications (TEXT CONTENT)
        story.extend(self._create_specifications_page(attributes, tree_data))
        story.append(PageBreak())
        
        # 4. Site Plan (VISUAL CONTENT LAST)
        story.extend(self._create_site_plan(design_data, tree_data))
        story.append(PageBreak())
        
        # 5. Details and Notes (TEXT CONTENT)
        story.extend(self._create_details_page(design_data, concept))
        
        # Build the PDF
        doc.build(story)
        
        print(f"✅ Professional courtyard plan saved to: {output_path}")
        return output_path
    
    def _create_title_page(self, concept):
        """Create the title page with project information"""
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=getSampleStyleSheet()['Title'],
            fontSize=36,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=self.colors['border']
        )
        elements.append(Paragraph("COURTYARD DESIGN PLAN", title_style))
        elements.append(Spacer(1, 20))
        
        # Project info
        info_style = ParagraphStyle(
            'ProjectInfo',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(f"<b>Project Date:</b> {datetime.now().strftime('%B %d, %Y')}", info_style))
        elements.append(Paragraph(f"<b>Design Concept:</b> {concept[:100]}...", info_style))
        elements.append(Spacer(1, 40))
        
        # Professional stamp/logo area
        elements.append(Paragraph("AI-Assisted Design", info_style))
        elements.append(Paragraph("Courtyard Design Copilot", info_style))
        
        return elements
    
    def _create_site_plan(self, design_data, tree_data):
        """Create the main site plan page"""
        elements = []
        
        # Debug: Check links data in _create_site_plan
        print(f"DEBUG: _create_site_plan - design_data type: {type(design_data)}")
        if isinstance(design_data, dict):
            links = design_data.get('links', [])
            print(f"DEBUG: _create_site_plan - links type: {type(links)}")
            print(f"DEBUG: _create_site_plan - links content: {links}")
            if isinstance(links, list) and len(links) > 0:
                print(f"DEBUG: _create_site_plan - First link type: {type(links[0])}")
                print(f"DEBUG: _create_site_plan - First link content: {links[0]}")
        
        # Page title
        title_style = ParagraphStyle(
            'SiteTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=28,
            spaceAfter=15,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("SITE PLAN", title_style))
        
        # Create the plan drawing - BIGGER AND WITHOUT BOUNDARY BOX
        plan_drawing = self._create_plan_drawing(design_data, tree_data)
        elements.append(plan_drawing)
        elements.append(Spacer(1, 15))
        
        # Add legend
        elements.extend(self._create_legend())
        
        return elements
    
    def _create_plan_drawing(self, design_data, tree_data):
        """Create the main plan drawing - BIGGER AND WITHOUT BOUNDARY BOX"""
        # Validate and parse design_data if it's a string
        if isinstance(design_data, str):
            try:
                import json
                design_data = json.loads(design_data)
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not parse design_data as JSON: {design_data}")
                design_data = {}
        
        # Ensure design_data is a dictionary
        if not isinstance(design_data, dict):
            design_data = {}
        
        # Validate links data structure
        links = design_data.get('links', [])
        if isinstance(links, dict):
            # Convert dict format to list format for consistency
            links_list = []
            for source, target in links.items():
                if isinstance(target, str):
                    links_list.append({"source": source, "target": target})
                elif isinstance(target, list):
                    for t in target:
                        links_list.append({"source": source, "target": t})
            links = links_list
        elif isinstance(links, str):
            # Try to parse as JSON if it's a string
            try:
                import json
                parsed_links = json.loads(links)
                if isinstance(parsed_links, dict):
                    links_list = []
                    for source, target in parsed_links.items():
                        if isinstance(target, str):
                            links_list.append({"source": source, "target": target})
                        elif isinstance(target, list):
                            for t in target:
                                links_list.append({"source": source, "target": t})
                    links = links_list
                else:
                    links = parsed_links
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not parse links as JSON: {links}")
                links = []
        elif not isinstance(links, list):
            print(f"Warning: Unexpected links format: {type(links)}")
            links = []
        
        # Update design_data with validated links
        design_data['links'] = links
        
        # Get positions and spaces
        positions = design_data.get('pos', {})
        spaces = design_data.get('spaces', [])
        external_functions = design_data.get('external_functions', {})
        external_anchors = design_data.get('external_anchors', {})
        
        # Calculate bounds
        all_coords = []
        for pos_list in positions.values():
            if isinstance(pos_list, list) and len(pos_list) >= 2:
                all_coords.extend([pos_list[0], pos_list[1]])
        
        if not all_coords:
            # Default bounds if no positions available
            min_x, max_x, min_y, max_y = 0, 100, 0, 100
        else:
            min_x, max_x = min(all_coords[::2]), max(all_coords[::2])
            min_y, max_y = min(all_coords[1::2]), max(all_coords[1::2])
        
        # Add padding for better visualization
        padding = 30
        min_x -= padding
        max_x += padding
        min_y -= padding
        max_y += padding
        
        # Calculate scale - MAKE IT BIGGER
        scale = 4.0  # Increased from 2.0 to 4.0 for bigger plan
        
        # Create drawing - MAKE IT MUCH BIGGER
        drawing_width = (max_x - min_x) * scale
        drawing_height = (max_y - min_y) * scale
        
        # Ensure minimum size for better visibility
        drawing_width = max(drawing_width, 600)
        drawing_height = max(drawing_height, 400)
        
        drawing = Drawing(drawing_width, drawing_height)
        
        # Draw grid
        self._draw_grid(drawing, min_x, max_x, min_y, max_y, scale)
        
        # Draw courtyard spaces (inside boundary)
        self._draw_spaces(drawing, positions, spaces, min_x, min_y, max_y, scale)
        
        # Draw external functions (at corners)
        self._draw_external_functions(drawing, positions, external_functions, min_x, min_y, max_y, scale, external_anchors)
        
        # Draw trees
        tree_placement = tree_data.get('tree_placement', {}) if tree_data else {}
        self._draw_trees(drawing, tree_placement, positions, min_x, min_y, max_y, scale)
        
        # Draw connections
        self._draw_connections(drawing, links, positions, min_x, min_y, max_y, scale)
        
        return drawing
    
    def _draw_grid(self, drawing, min_x, max_x, min_y, max_y, scale):
        """Draw a professional grid system"""
        # Grid lines
        for x in range(int(min_x), int(max_x) + 1, 5):
            x_scaled = (x - min_x) * scale
            drawing.add(Line(x_scaled, 0, x_scaled, (max_y - min_y) * scale, 
                           strokeColor=self.colors['grid'], strokeWidth=0.5))
        
        for y in range(int(min_y), int(max_y) + 1, 5):
            y_scaled = (max_y - min_y) * scale - (y - min_y) * scale
            drawing.add(Line(0, y_scaled, (max_x - min_x) * scale, y_scaled, 
                           strokeColor=self.colors['grid'], strokeWidth=0.5))
    
    def _draw_spaces(self, drawing, positions, spaces, min_x, min_y, max_y, scale):
        """Draw courtyard spaces with appropriate symbols - BIGGER AND MORE VISIBLE"""
        space_symbols = {
            'play': 'circle',
            'rest': 'rectangle',
            'pond': 'polygon',
            'flower': 'diamond',
            'tree': 'triangle'
        }
        
        for space_name, space_type in spaces.items():
            if space_name in positions and isinstance(positions[space_name], list):
                x, y = positions[space_name][:2]
                x_scaled = (x - min_x) * scale
                y_scaled = (max_y - min_y) * scale - (y - min_y) * scale
                
                # Draw space symbol - BIGGER SIZE
                if space_type in space_symbols:
                    symbol = space_symbols[space_type]
                    size = 15  # Increased from 8 to 15 for better visibility
                    
                    if symbol == 'circle':
                        drawing.add(Circle(x_scaled, y_scaled, size, 
                                         fillColor=self.colors[space_type], 
                                         strokeColor=self.colors['border'],
                                         strokeWidth=2))
                    elif symbol == 'rectangle':
                        drawing.add(Rect(x_scaled - size, y_scaled - size, size*2, size*2,
                                       fillColor=self.colors[space_type],
                                       strokeColor=self.colors['border'],
                                       strokeWidth=2))
                    elif symbol == 'polygon':
                        points = [(x_scaled, y_scaled + size), (x_scaled - size, y_scaled - size),
                                (x_scaled + size, y_scaled - size)]
                        drawing.add(Polygon(points, fillColor=self.colors[space_type],
                                          strokeColor=self.colors['border'],
                                          strokeWidth=2))
                    elif symbol == 'diamond':
                        points = [(x_scaled, y_scaled + size), (x_scaled + size, y_scaled),
                                (x_scaled, y_scaled - size), (x_scaled - size, y_scaled)]
                        drawing.add(Polygon(points, fillColor=self.colors[space_type],
                                          strokeColor=self.colors['border'],
                                          strokeWidth=2))
                    elif symbol == 'triangle':
                        points = [(x_scaled, y_scaled + size), (x_scaled - size, y_scaled - size),
                                (x_scaled + size, y_scaled - size)]
                        drawing.add(Polygon(points, fillColor=self.colors[space_type],
                                          strokeColor=self.colors['border'],
                                          strokeWidth=2))
                
                # Add label - BIGGER FONT
                drawing.add(String(x_scaled, y_scaled - 25, space_name.upper(),
                                 fontSize=12, fillColor=self.colors['text']))
    
    def _draw_external_functions(self, drawing, positions, external_functions, min_x, min_y, max_y, scale, external_anchors):
        """Draw external functions as anchor points at corners - BIGGER AND MORE VISIBLE"""
        for func_name, direction in external_functions.items():
            if func_name in positions and isinstance(positions[func_name], list):
                x, y = positions[func_name][:2]
                x_scaled = (x - min_x) * scale
                y_scaled = (max_y - min_y) * scale - (y - min_y) * scale
                
                # Check if this is an anchor point
                if func_name in external_anchors:
                    anchor_info = external_anchors[func_name]
                    corner = anchor_info.get('corner', 'Unknown')
                    
                    # Draw anchor point - BIGGER SIZE
                    size = 18  # Increased from 12 to 18
                    drawing.add(Circle(x_scaled, y_scaled, size,
                                     fillColor=self.colors['building'],
                                     strokeColor=self.colors['border'],
                                     strokeWidth=2))
                    
                    # Add anchor label - BIGGER FONT
                    drawing.add(String(x_scaled, y_scaled - 25, f"{func_name.upper()}\n({corner})",
                                     fontSize=10, fillColor=white))  # Increased from 7 to 10
                else:
                    # Draw regular external function - BIGGER SIZE
                    size = 18  # Increased from 12 to 18
                    drawing.add(Rect(x_scaled - size, y_scaled - size, size*2, size*2,
                                   fillColor=self.colors['building'],
                                   strokeColor=self.colors['border'],
                                   strokeWidth=2))
                    
                    # Add label - BIGGER FONT
                    drawing.add(String(x_scaled, y_scaled - 25, func_name.upper(),
                                     fontSize=10, fillColor=white))  # Increased from 7 to 10
    
    def _draw_trees(self, drawing, tree_placement, positions, min_x, min_y, max_y, scale):
        """Draw trees based on placement data"""
        for tree_type, placement_range in tree_placement.items():
            if isinstance(placement_range, str) and ' to ' in placement_range:
                start, end = map(int, placement_range.split(' to '))
                
                # Place trees in the range (simplified placement)
                for i in range(start, end + 1, 2):
                    x = min_x + (i % 20) * 2
                    y = min_y + (i % 15) * 2
                    x_scaled = (x - min_x) * scale
                    y_scaled = (max_y - min_y) * scale - (y - min_y) * scale
                    
                    # Draw tree symbol
                    drawing.add(Circle(x_scaled, y_scaled, 4,
                                     fillColor=self.colors['tree'],
                                     strokeColor=self.colors['border']))
                    
                    # Add tree type label
                    drawing.add(String(x_scaled, y_scaled - 8, tree_type[:3].upper(),
                                     fontSize=6, fillColor=self.colors['text']))
    
    def _draw_connections(self, drawing, links, positions, min_x, min_y, max_y, scale):
        """Draw connections between spaces - THICKER AND MORE VISIBLE"""
        for link in links:
            if isinstance(link, dict):
                source = link.get('source')
                target = link.get('target')
                
                if source in positions and target in positions:
                    source_pos = positions[source]
                    target_pos = positions[target]
                    
                    if isinstance(source_pos, list) and isinstance(target_pos, list) and len(source_pos) >= 2 and len(target_pos) >= 2:
                        x1 = (source_pos[0] - min_x) * scale
                        y1 = (max_y - min_y) * scale - (source_pos[1] - min_y) * scale
                        x2 = (target_pos[0] - min_x) * scale
                        y2 = (max_y - min_y) * scale - (target_pos[1] - min_y) * scale
                        
                        # Draw connection line - THICKER
                        drawing.add(Line(x1, y1, x2, y2,
                                       strokeColor=self.colors['path'],
                                       strokeWidth=3))  # Increased from default to 3
    
    def _create_legend(self):
        """Create a professional legend without boundary box references"""
        elements = []
        
        # Legend title
        legend_style = ParagraphStyle(
            'LegendTitle',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=16,
            spaceAfter=15
        )
        elements.append(Paragraph("LEGEND", legend_style))
        
        # Legend items - REMOVED BOUNDARY BOX REFERENCES
        legend_data = [
            ['Symbol', 'Element Type', 'Description'],
            ['●', 'ANCHOR', 'External function anchor point at corner'],
            ['●', 'PLAY', 'Active social spaces'],
            ['■', 'REST', 'Quiet contemplative areas'],
            ['▲', 'POND', 'Water features'],
            ['◆', 'FLOWER', 'Garden and planting areas'],
            ['▲', 'TREE', 'Tree and shade areas'],
            ['■', 'EXTERNAL', 'External functions'],
            ['━━', 'PATH', 'Connections and circulation']
        ]
        
        legend_table = Table(legend_data, colWidths=[30, 80, 200])
        legend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['border']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        elements.append(legend_table)
        
        return elements
    
    def _create_specifications_page(self, attributes, tree_data):
        """Create specifications and materials page"""
        elements = []
        
        # Validate and parse attributes if it's a string
        if isinstance(attributes, str):
            try:
                import json
                attributes = json.loads(attributes)
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not parse attributes as JSON: {attributes}")
                attributes = {}
        
        # Validate and parse tree_data if it's a string
        if isinstance(tree_data, str):
            try:
                import json
                tree_data = json.loads(tree_data)
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not parse tree_data as JSON: {tree_data}")
                tree_data = {}
        
        # Ensure both are dictionaries
        if not isinstance(attributes, dict):
            attributes = {}
        if not isinstance(tree_data, dict):
            tree_data = {}
        
        # Page title
        title_style = ParagraphStyle(
            'SpecTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("SPECIFICATIONS & MATERIALS", title_style))
        
        # Materials and specifications
        if attributes:
            elements.append(Paragraph("MATERIALS & SPECIFICATIONS", 
                                    getSampleStyleSheet()['Heading2']))
            
            spec_data = [['Item', 'Specification', 'Quantity']]
            for key, value in attributes.items():
                if key and value:
                    spec_data.append([key.replace('_', ' ').title(), str(value), 'As specified'])
            
            spec_table = Table(spec_data, colWidths=[120, 200, 100])
            spec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['border']),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), white),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(spec_table)
            elements.append(Spacer(1, 20))
        
        # Tree specifications
        if tree_data and 'tree_placement' in tree_data:
            elements.append(Paragraph("TREE SPECIFICATIONS", 
                                    getSampleStyleSheet()['Heading2']))
            
            tree_data_table = [['Tree Type', 'Placement Range', 'Water Requirement']]
            for tree_type, placement in tree_data['tree_placement'].items():
                water_req = tree_data.get('PWR', {}).get(tree_type, 'N/A')
                tree_data_table.append([tree_type.title(), placement, str(water_req)])
            
            tree_table = Table(tree_data_table, colWidths=[100, 100, 100])
            tree_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['border']),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), white),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(tree_table)
        
        return elements
    
    def _create_design_documentation_page(self, design_data, concept, tree_data, attributes):
        """Create comprehensive design documentation and analysis page"""
        elements = []
        
        # Validate and parse design_data if it's a string
        if isinstance(design_data, str):
            try:
                import json
                design_data = json.loads(design_data)
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not parse design_data as JSON: {design_data}")
                design_data = {}
        
        # Ensure design_data is a dictionary
        if not isinstance(design_data, dict):
            design_data = {}
        
        # Page title
        title_style = ParagraphStyle(
            'DocTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("DESIGN DOCUMENTATION & ANALYSIS", title_style))
        
        # Design concept
        elements.append(Paragraph("DESIGN CONCEPT", 
                                getSampleStyleSheet()['Heading2']))
        concept_text = f"""
        {concept}
        
        This courtyard design creates a harmonious outdoor environment that balances functionality, 
        aesthetics, and environmental sustainability. The design integrates multiple functional zones 
        while maintaining visual coherence and spatial flow.
        """
        elements.append(Paragraph(concept_text, getSampleStyleSheet()['Normal']))
        elements.append(Spacer(1, 15))
        
        # Functional zones
        if isinstance(design_data, dict) and 'spaces' in design_data:
            spaces = design_data['spaces']
            if spaces:
                elements.append(Paragraph("FUNCTIONAL ZONES", 
                                        getSampleStyleSheet()['Heading2']))
                
                space_descriptions = []
                for space_name, space_type in spaces.items():
                    if space_type == 'play':
                        space_descriptions.append(f"• <b>{space_name.title()}:</b> Active recreation and social interaction area")
                    elif space_type == 'rest':
                        space_descriptions.append(f"• <b>{space_name.title()}:</b> Quiet contemplation and relaxation zone")
                    elif space_type == 'pond':
                        space_descriptions.append(f"• <b>{space_name.title()}:</b> Water feature for visual interest and cooling")
                    elif space_type == 'flower':
                        space_descriptions.append(f"• <b>{space_name.title()}:</b> Garden area with seasonal color and fragrance")
                    elif space_type == 'tree':
                        space_descriptions.append(f"• <b>{space_name.title()}:</b> Shade and canopy area for comfort")
                    else:
                        space_descriptions.append(f"• <b>{space_name.title()}:</b> {space_type} functional area")
                
                if space_descriptions:
                    elements.append(Paragraph("<br/>".join(space_descriptions), 
                                            getSampleStyleSheet()['Normal']))
                elements.append(Spacer(1, 15))
        
        # External functions
        if isinstance(design_data, dict) and 'external_functions' in design_data:
            external_functions = design_data['external_functions']
            if external_functions:
                elements.append(Paragraph("EXTERNAL FUNCTIONS", 
                                        getSampleStyleSheet()['Heading2']))
                
                external_list = []
                for func_name, direction in external_functions.items():
                    external_list.append(f"• <b>{func_name.title()}:</b> Positioned facing {direction}")
                
                if external_list:
                    elements.append(Paragraph("<br/>".join(external_list), 
                                            getSampleStyleSheet()['Normal']))
                elements.append(Spacer(1, 15))
        
        # Climate-specific design features
        elements.append(Paragraph("CLIMATE & ENVIRONMENTAL FEATURES", 
                                getSampleStyleSheet()['Heading2']))
        climate_features = [
            "• <b>Solar Orientation:</b> Optimized for maximum winter sun exposure and summer shade",
            "• <b>Wind Protection:</b> Strategic placement of trees and structures to reduce wind exposure",
            "• <b>Thermal Mass:</b> Use of materials with high thermal mass to moderate temperature fluctuations",
            "• <b>Ventilation:</b> Natural airflow patterns designed for cooling and air quality",
            "• <b>Water Management:</b> Sustainable drainage and water retention systems",
            "• <b>Seasonal Adaptability:</b> Flexible spaces that accommodate different seasonal uses"
        ]
        elements.append(Paragraph("<br/>".join(climate_features), getSampleStyleSheet()['Normal']))
        elements.append(Spacer(1, 15))
        
        # Understanding the Courtyard
        elements.append(Paragraph("DESIGN PHILOSOPHY", 
                                getSampleStyleSheet()['Heading2']))
        understanding_text = """
        This courtyard is designed as a comprehensive outdoor living environment that serves multiple 
        functions while maintaining visual and functional coherence. The design creates distinct 
        activity zones while ensuring smooth transitions and connections between spaces. Each element 
        has been carefully considered for its contribution to the overall experience and functionality.
        """
        elements.append(Paragraph(understanding_text, getSampleStyleSheet()['Normal']))
        elements.append(Spacer(1, 15))
        
        # Spatial analysis
        if 'pos' in design_data:
            elements.append(Paragraph("SPATIAL ANALYSIS", 
                                    getSampleStyleSheet()['Heading2']))
            
            pos_data = design_data['pos']
            if isinstance(pos_data, dict):
                spatial_info = []
                for space_name, coords in pos_data.items():
                    if isinstance(coords, list) and len(coords) >= 2:
                        spatial_info.append(f"• {space_name}: Position ({coords[0]:.1f}, {coords[1]:.1f})")
                
                if spatial_info:
                    elements.append(Paragraph("<br/>".join(spatial_info), 
                                            getSampleStyleSheet()['Normal']))
        
        return elements
    
    def _create_details_page(self, design_data, concept):
        """Create details and notes page"""
        elements = []
        
        # Validate and parse design_data if it's a string
        if isinstance(design_data, str):
            try:
                import json
                design_data = json.loads(design_data)
            except (json.JSONDecodeError, TypeError):
                print(f"Warning: Could not parse design_data as JSON: {design_data}")
                design_data = {}
        
        # Ensure design_data is a dictionary
        if not isinstance(design_data, dict):
            design_data = {}
        
        # Page title
        title_style = ParagraphStyle(
            'DetailsTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("DESIGN DETAILS & NOTES", title_style))
        
        # Design concept
        elements.append(Paragraph("DESIGN CONCEPT", 
                                getSampleStyleSheet()['Heading2']))
        elements.append(Paragraph(concept, getSampleStyleSheet()['Normal']))
        elements.append(Spacer(1, 20))
        
        # Spatial analysis
        if 'pos' in design_data:
            elements.append(Paragraph("SPATIAL ANALYSIS", 
                                    getSampleStyleSheet()['Heading2']))
            
            pos_data = design_data['pos']
            if isinstance(pos_data, dict):
                spatial_info = []
                for space_name, coords in pos_data.items():
                    if isinstance(coords, list) and len(coords) >= 2:
                        spatial_info.append(f"• {space_name}: Position ({coords[0]:.1f}, {coords[1]:.1f})")
                
                if spatial_info:
                    elements.append(Paragraph("<br/>".join(spatial_info), 
                                            getSampleStyleSheet()['Normal']))
        
        # General notes
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("GENERAL NOTES", 
                                getSampleStyleSheet()['Heading2']))
        
        notes = [
            "• All dimensions are approximate and subject to site verification",
            "• Tree placement considers mature canopy spread and root systems",
            "• Materials should be selected for local climate and maintenance requirements",
            "• Circulation paths should accommodate accessibility standards",
            "• Water features require proper drainage and circulation systems",
            "• Lighting design should be developed based on usage patterns"
        ]
        
        elements.append(Paragraph("<br/>".join(notes), 
                                getSampleStyleSheet()['Normal']))
        
        return elements

def export_courtyard_plan(design_data, tree_data, attributes, concept, output_filename=None):
    """
    Convenience function to export a professional courtyard plan
    
    Args:
        design_data: Complete design data dictionary
        tree_data: Tree placement and water requirements
        attributes: Material and specification data
        concept: Design concept text
        output_filename: Optional custom filename
    
    Returns:
        Path to the generated PDF file
    """
    # Debug: Check links data before passing to exporter
    print(f"DEBUG: export_courtyard_plan - design_data type: {type(design_data)}")
    if isinstance(design_data, dict):
        links = design_data.get('links', [])
        print(f"DEBUG: export_courtyard_plan - links type: {type(links)}")
        print(f"DEBUG: export_courtyard_plan - links content: {links}")
        if isinstance(links, list) and len(links) > 0:
            print(f"DEBUG: export_courtyard_plan - First link type: {type(links[0])}")
            print(f"DEBUG: export_courtyard_plan - First link content: {links[0]}")
    
    exporter = ProfessionalPlanExporter()
    return exporter.generate_professional_plan(
        design_data, tree_data, attributes, concept, output_filename
    ) 