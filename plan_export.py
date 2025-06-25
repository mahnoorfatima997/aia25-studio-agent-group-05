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
import requests

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

        self.tab_widget.addTab(plan_export_widget, "Plan Export")

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
        Generate a professional PDF courtyard plan following the new structure:
        1. Cover page with cat image
        2. Plan concept and concept images
        3. Courtyard requirements and existing data
        4. Picture of plan and graph
        5. Climate analysis with suggestions
        6. Advantages and disadvantages
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"captain_cat_courtyard_plan_{timestamp}.pdf"
        
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
        
        # Build the plan content following the new structure
        story = []
        
        # 1. Cover Page with Cat
        story.extend(self._create_cover_page())
        story.append(PageBreak())
        
        # 2. Plan Concept and Concept Images
        story.extend(self._create_concept_page(concept))
        story.append(PageBreak())
        
        # 3. Courtyard Requirements and Existing Data
        story.extend(self._create_requirements_page(design_data, attributes))
        story.append(PageBreak())
        
        # 4. Plan and Graph Visualization
        story.extend(self._create_plan_and_graph_page(design_data, tree_data))
        story.append(PageBreak())
        
        # 5. Climate Analysis and Suggestions
        story.extend(self._create_climate_analysis_page())
        story.append(PageBreak())
        
        # 6. Advantages and Disadvantages
        story.extend(self._create_analysis_page(design_data, concept, attributes, tree_data))
        
        # Build the PDF
        doc.build(story)
        
        print(f"✅ Captain CAT - Courtyard Advisory Tool Plan saved to: {output_path}")
        return output_path
    
    def _create_cover_page(self):
        """Create the cover page with cat image and title"""
        elements = []
        
        # Try to add cat image if available
        try:
            cat_image_path = "cat_icon.png"
            if os.path.exists(cat_image_path):
                cat_img = Image(cat_image_path, width=150*mm, height=150*mm)
                cat_img.hAlign = 'CENTER'
                elements.append(cat_img)
                elements.append(Spacer(1, 20))
        except Exception as e:
            print(f"Could not load cat image: {e}")
        
        # Main title
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=getSampleStyleSheet()['Title'],
            fontSize=48,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=self.colors['border']
        )
        elements.append(Paragraph("Captain CAT - Courtyard Advisory Tool", title_style))
        
        # Subtitle
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=self.colors['border']
        )
        elements.append(Paragraph("Professional Design Plan", subtitle_style))
        
        # Date
        date_style = ParagraphStyle(
            'CoverDate',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=16,
            spaceAfter=40,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", date_style))
        
        # Footer
        footer_style = ParagraphStyle(
            'CoverFooter',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            textColor=gray
        )
        elements.append(Paragraph("AI-Assisted Courtyard Design", footer_style))
        
        return elements
    
    def _create_concept_page(self, concept):
        """Create the plan concept and concept images page"""
        elements = []
        
        # Page title
        title_style = ParagraphStyle(
            'ConceptTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=32,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("1. PLAN CONCEPT & CONCEPT IMAGES", title_style))
        
        # Concept description
        concept_style = ParagraphStyle(
            'ConceptText',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=16,
            spaceAfter=15,
            alignment=TA_LEFT,
            leading=20
        )
        
        elements.append(Paragraph("<b>Design Concept:</b>", concept_style))
        elements.append(Paragraph(concept, concept_style))
        elements.append(Spacer(1, 20))
        
        # Concept images section
        elements.append(Paragraph("<b>Concept Visualizations:</b>", concept_style))
        
        # Try to find and include concept images
        concept_images_dir = os.path.expanduser("~/Downloads")
        concept_images = []
        
        # Look for concept images in Downloads folder
        if os.path.exists(concept_images_dir):
            for file in os.listdir(concept_images_dir):
                if file.startswith("concept_") and file.endswith(".png"):
                    concept_images.append(os.path.join(concept_images_dir, file))
        
        if concept_images:
            # Add the most recent concept image
            latest_image = max(concept_images, key=os.path.getctime)
            try:
                concept_img = Image(latest_image, width=200*mm, height=150*mm)
                concept_img.hAlign = 'CENTER'
                elements.append(concept_img)
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("Generated concept visualization of the courtyard design", concept_style))
            except Exception as e:
                elements.append(Paragraph(f"Concept image available but could not be displayed: {latest_image}", concept_style))
        else:
            elements.append(Paragraph("No concept images found. Generate concept images in the Image Generation tab.", concept_style))
        
        return elements
    
    def _create_requirements_page(self, design_data, attributes):
        """Create the courtyard requirements and existing data page"""
        elements = []
        
        # Page title
        title_style = ParagraphStyle(
            'RequirementsTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=32,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("2. COURTYARD REQUIREMENTS & EXISTING DATA", title_style))
        
        # Content style
        content_style = ParagraphStyle(
            'RequirementsText',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_LEFT,
            leading=18
        )
        
        # External Functions
        elements.append(Paragraph("<b>External Functions & Requirements:</b>", content_style))
        external_functions = design_data.get('external_functions', {})
        if external_functions:
            for func_name, direction in external_functions.items():
                elements.append(Paragraph(f"• {func_name}: {direction} facing", content_style))
        else:
            elements.append(Paragraph("No external functions specified", content_style))
        
        elements.append(Spacer(1, 15))
        
        # Design Attributes
        elements.append(Paragraph("<b>Design Attributes & Specifications:</b>", content_style))
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, dict):
                    elements.append(Paragraph(f"• {key}:", content_style))
                    for sub_key, sub_value in value.items():
                        elements.append(Paragraph(f"  - {sub_key}: {sub_value}", content_style))
                else:
                    elements.append(Paragraph(f"• {key}: {value}", content_style))
        else:
            elements.append(Paragraph("No design attributes specified", content_style))
        
        elements.append(Spacer(1, 15))
        
        # Spaces and Layout
        elements.append(Paragraph("<b>Design Spaces:</b>", content_style))
        spaces = design_data.get('spaces', {})
        if spaces:
            for space_name, space_type in spaces.items():
                elements.append(Paragraph(f"• {space_name}: {space_type}", content_style))
        else:
            elements.append(Paragraph("No spaces defined", content_style))
        
        elements.append(Spacer(1, 15))
        
        # Plot area information
        try:
            plot_response = requests.get("http://127.0.0.1:5000/plot_area", timeout=5)
            if plot_response.status_code == 200:
                plot_data = plot_response.json()
                area = plot_data.get('area')
                width = plot_data.get('width')
                length = plot_data.get('length')
                
                if area:
                    elements.append(Paragraph(f"• Plot Area: {area} m²", content_style))
                if width and length:
                    elements.append(Paragraph(f"• Dimensions: {width}m x {length}m", content_style))
                elif area:
                    # Calculate dimensions if we only have area
                    try:
                        area_float = float(area)
                        side_length = (area_float ** 0.5)
                        elements.append(Paragraph(f"• Dimensions: {side_length:.1f}m x {side_length:.1f}m (calculated)", content_style))
                    except (ValueError, TypeError):
                        pass
            else:
                elements.append(Paragraph("• Plot Area: Not available", content_style))
        except:
            elements.append(Paragraph("• Plot Area: Not available", content_style))
        
        return elements
    
    def _ensure_enhanced_plan_image(self, concept, design_data, tree_data, attributes):
        """Ensure an enhanced plan image exists by generating one if needed"""
        try:
            # Check if enhanced plan images already exist
            ai_images_dir = os.path.expanduser("~/Downloads/ai_generated_images")
            if os.path.exists(ai_images_dir):
                enhanced_plan_images = []
                for file in os.listdir(ai_images_dir):
                    if file.startswith("enhanced_plan_") and file.endswith(".png"):
                        enhanced_plan_images.append(os.path.join(ai_images_dir, file))
                
                if enhanced_plan_images:
                    print(f"✅ Found existing enhanced plan images: {len(enhanced_plan_images)}")
                    return True
            
            # Check if we have a Grasshopper screenshot to work with
            gh_screenshots_dir = os.path.expanduser("~/Downloads/gh_screenshots")
            if os.path.exists(gh_screenshots_dir):
                screenshot_files = [f for f in os.listdir(gh_screenshots_dir) if f.endswith('.png')]
                if screenshot_files:
                    # Use the most recent screenshot
                    latest_screenshot = max(screenshot_files, key=lambda x: os.path.getctime(os.path.join(gh_screenshots_dir, x)))
                    screenshot_path = os.path.join(gh_screenshots_dir, latest_screenshot)
                    
                    print(f"🔄 Generating enhanced plan image from screenshot: {latest_screenshot}")
                    
                    # Import the image generation function
                    try:
                        from image_gen import generate_plan_view_from_screenshot, generate_detailed_plan_courtyard_prompt
                        
                        # Generate plan prompt
                        plan_prompt = generate_detailed_plan_courtyard_prompt(concept, design_data, tree_data, attributes)
                        enhanced_prompt = f"{plan_prompt}, brown square building surrounding the courtyard, courtyard space inside the building perimeter, architectural plan view, technical drawing style, clean lines, professional layout, top-down perspective, precise measurements, clear zone boundaries, elegant spatial composition, coordinate system, realistic materials, professional architectural documentation"
                        
                        # Generate enhanced plan image
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_filename = f"enhanced_plan_{timestamp}.png"
                        
                        success, output_path, message = generate_plan_view_from_screenshot(
                            screenshot_path, 
                            enhanced_prompt, 
                            output_filename
                        )
                        
                        if success:
                            print(f"✅ Generated enhanced plan image: {output_path}")
                            return True
                        else:
                            print(f"❌ Failed to generate enhanced plan image: {message}")
                            return False
                            
                    except ImportError as e:
                        print(f"⚠️ Could not import image generation functions: {e}")
                        return False
                    except Exception as e:
                        print(f"❌ Error generating enhanced plan image: {e}")
                        return False
                else:
                    print("⚠️ No Grasshopper screenshots found")
                    return False
            else:
                print("⚠️ No Grasshopper screenshots directory found")
                return False
                
        except Exception as e:
            print(f"❌ Error in _ensure_enhanced_plan_image: {e}")
            return False

    def _create_plan_and_graph_page(self, design_data, tree_data):
        """Create the plan and graph visualization page"""
        elements = []
        
        # Page title
        title_style = ParagraphStyle(
            'PlanTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=32,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("3. PLAN & GRAPH VISUALIZATION", title_style))
        
        # Try to find and include the enhanced plan image from Grasshopper screenshot
        enhanced_plan_found = False
        try:
            # Look for enhanced plan images in the AI generated images folder
            ai_images_dir = os.path.expanduser("~/Downloads/ai_generated_images")
            if os.path.exists(ai_images_dir):
                enhanced_plan_images = []
                for file in os.listdir(ai_images_dir):
                    if file.startswith("enhanced_plan_") and file.endswith(".png"):
                        enhanced_plan_images.append(os.path.join(ai_images_dir, file))
                
                if enhanced_plan_images:
                    # Use the most recent enhanced plan image
                    latest_enhanced_plan = max(enhanced_plan_images, key=os.path.getctime)
                    try:
                        enhanced_plan_img = Image(latest_enhanced_plan, width=250*mm, height=200*mm)
                        enhanced_plan_img.hAlign = 'CENTER'
                        elements.append(Paragraph("<b>AI-Enhanced Plan View (from Grasshopper Screenshot):</b>", 
                                                ParagraphStyle('PlanSubtitle', parent=getSampleStyleSheet()['Heading2'], fontSize=18, spaceAfter=10)))
                        elements.append(enhanced_plan_img)
                        elements.append(Spacer(1, 20))
                        enhanced_plan_found = True
                        print(f"✅ Added enhanced plan image to documentation: {latest_enhanced_plan}")
                    except Exception as e:
                        print(f"⚠️ Could not add enhanced plan image: {e}")
        except Exception as e:
            print(f"⚠️ Error looking for enhanced plan images: {e}")
        
        # Also include the basic plan drawing for reference
        elements.append(Paragraph("<b>Technical Plan Drawing (from Design Data):</b>", 
                                ParagraphStyle('PlanSubtitle', parent=getSampleStyleSheet()['Heading2'], fontSize=18, spaceAfter=10)))
        
        # Create the plan drawing
        plan_drawing = self._create_plan_drawing(design_data, tree_data)
        elements.append(plan_drawing)
        elements.append(Spacer(1, 15))
        
        # Add legend
        elements.extend(self._create_legend())
        
        # Graph data information
        content_style = ParagraphStyle(
            'GraphText',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_LEFT,
            leading=18
        )
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("<b>Graph Data Summary:</b>", content_style))
        
        # Count nodes and edges
        nodes = design_data.get('pos', {})
        links = design_data.get('links', [])
        
        if isinstance(links, dict):
            link_count = len(links)
        elif isinstance(links, list):
            link_count = len(links)
        else:
            link_count = 0
        
        elements.append(Paragraph(f"• Total Spaces/Nodes: {len(nodes)}", content_style))
        elements.append(Paragraph(f"• Connections/Links: {link_count}", content_style))
        
        # Tree information
        if tree_data and 'tree_placement' in tree_data:
            tree_count = len(tree_data['tree_placement'])
            elements.append(Paragraph(f"• Trees: {tree_count}", content_style))
        
        # Note about images and graph file
        elements.append(Spacer(1, 10))
        if enhanced_plan_found:
            elements.append(Paragraph("<b>Note:</b> The enhanced plan view was generated using AI image-to-image processing of a Grasshopper screenshot, providing a realistic visualization of the courtyard design.", content_style))
        else:
            elements.append(Paragraph("<b>Note:</b> No enhanced plan image found. Generate an enhanced plan view in the Image Generation tab using a Grasshopper screenshot for a realistic visualization.", content_style))
        
        elements.append(Paragraph("<b>Note:</b> The complete graph data has been exported to CSV files in the Downloads/courtyard_graph folder for further analysis.", content_style))
        
        return elements
    
    def _create_climate_analysis_page(self):
        """Create the climate analysis and suggestions page"""
        elements = []
        
        # Page title
        title_style = ParagraphStyle(
            'ClimateTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=32,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("4. CLIMATE ANALYSIS & SUGGESTIONS", title_style))
        
        # Content style
        content_style = ParagraphStyle(
            'ClimateText',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_LEFT,
            leading=18
        )
        
        # Try to get climate data from the server
        try:
            climate_response = requests.get("http://127.0.0.1:5000/climate_data", timeout=5)
            if climate_response.status_code == 200:
                climate_data = climate_response.json()
                if 'climate_data' in climate_data:
                    data = climate_data['climate_data']
                    
                    elements.append(Paragraph("<b>Climate Analysis Results:</b>", content_style))
                    elements.append(Paragraph(f"• Location: {data.get('location', 'N/A')}", content_style))
                    elements.append(Paragraph(f"• Analysis Type: {data.get('analysis_type', 'N/A')}", content_style))
                    
                    if data.get('is_single_hour', False):
                        elements.append(Paragraph(f"• Date/Time: Day {data.get('day_of_year', 'N/A')}, Hour {data.get('hour_of_day', 'N/A')}:00", content_style))
                        elements.append(Paragraph(f"• Temperature: {data.get('temperature', 'N/A')}°C", content_style))
                        elements.append(Paragraph(f"• Humidity: {data.get('humidity', 'N/A')}%", content_style))
                    else:
                        temp_stats = data.get('temperature_stats', {})
                        if temp_stats:
                            elements.append(Paragraph(f"• Average Temperature: {temp_stats.get('average', 'N/A')}°C", content_style))
                            elements.append(Paragraph(f"• Maximum Temperature: {temp_stats.get('maximum', 'N/A')}°C", content_style))
                            elements.append(Paragraph(f"• Minimum Temperature: {temp_stats.get('minimum', 'N/A')}°C", content_style))
                        
                        hum_stats = data.get('humidity_stats', {})
                        if hum_stats:
                            elements.append(Paragraph(f"• Average Humidity: {hum_stats.get('average', 'N/A')}%", content_style))
                    
                    elements.append(Spacer(1, 15))
                    
                    # Climate improvement suggestions
                    elements.append(Paragraph("<b>Climate Improvement Suggestions:</b>", content_style))
                    
                    temp = data.get('temperature', 0)
                    if temp > 25:
                        elements.append(Paragraph("• High temperatures detected - consider adding shade structures, trees, or water features", content_style))
                    elif temp < 10:
                        elements.append(Paragraph("• Low temperatures detected - consider adding wind protection and sun-exposed seating areas", content_style))
                    
                    humidity = data.get('humidity', 0)
                    if humidity > 70:
                        elements.append(Paragraph("• High humidity detected - ensure good ventilation and avoid dense vegetation", content_style))
                    elif humidity < 30:
                        elements.append(Paragraph("• Low humidity detected - consider adding water features and moisture-loving plants", content_style))
                    
                    elements.append(Paragraph("• Add deciduous trees for seasonal shade and wind protection", content_style))
                    elements.append(Paragraph("• Consider orientation of seating areas relative to sun path", content_style))
                    elements.append(Paragraph("• Include water features for cooling and humidity regulation", content_style))
                    elements.append(Paragraph("• Use permeable surfaces to reduce heat island effect", content_style))
                    
                else:
                    elements.append(Paragraph("No climate analysis data available. Run climate analysis in the Climate Analysis tab.", content_style))
            else:
                elements.append(Paragraph("Climate analysis data not available. Please run climate analysis first.", content_style))
        except Exception as e:
            elements.append(Paragraph(f"Could not retrieve climate data: {str(e)}", content_style))
            elements.append(Paragraph("Please run climate analysis in the Climate Analysis tab to get detailed recommendations.", content_style))
        
        return elements
    
    def _create_analysis_page(self, design_data, concept, attributes, tree_data):
        """Create the advantages and disadvantages analysis page"""
        elements = []
        
        # Page title
        title_style = ParagraphStyle(
            'AnalysisTitle',
            parent=getSampleStyleSheet()['Heading1'],
            fontSize=32,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("5. DESIGN ANALYSIS: ADVANTAGES & DISADVANTAGES", title_style))
        
        # Content style
        content_style = ParagraphStyle(
            'AnalysisText',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_LEFT,
            leading=18
        )
        
        # Advantages
        elements.append(Paragraph("<b>Design Advantages:</b>", content_style))
        
        # Analyze design data for advantages
        spaces = design_data.get('spaces', {})
        external_functions = design_data.get('external_functions', {})
        links = design_data.get('links', [])
        
        if spaces:
            elements.append(Paragraph("• Well-defined functional spaces with clear purposes", content_style))
        
        if external_functions:
            elements.append(Paragraph("• Strategic placement of external functions for optimal access", content_style))
        
        if links:
            if isinstance(links, list) and len(links) > 0:
                elements.append(Paragraph("• Good connectivity between spaces for efficient circulation", content_style))
            elif isinstance(links, dict) and len(links) > 0:
                elements.append(Paragraph("• Strategic connections planned between key areas", content_style))
        
        if tree_data and 'tree_placement' in tree_data and tree_data['tree_placement']:
            elements.append(Paragraph("• Thoughtful tree placement for shade and environmental benefits", content_style))
        
        if attributes:
            elements.append(Paragraph("• Comprehensive material and specification planning", content_style))
        
        elements.append(Paragraph("• AI-assisted design ensures consideration of multiple factors", content_style))
        elements.append(Paragraph("• Modular approach allows for future modifications", content_style))
        
        elements.append(Spacer(1, 15))
        
        # Disadvantages and Areas for Improvement
        elements.append(Paragraph("<b>Areas for Improvement:</b>", content_style))
        
        if not spaces:
            elements.append(Paragraph("• Consider adding more defined functional spaces", content_style))
        
        if not external_functions:
            elements.append(Paragraph("• External functions could be better integrated", content_style))
        
        if not links or (isinstance(links, list) and len(links) == 0) or (isinstance(links, dict) and len(links) == 0):
            elements.append(Paragraph("• Circulation between spaces could be improved", content_style))
        
        if not tree_data or 'tree_placement' not in tree_data or not tree_data['tree_placement']:
            elements.append(Paragraph("• Tree placement could be optimized for shade and aesthetics", content_style))
        
        elements.append(Paragraph("• Consider seasonal variations in sun and wind patterns", content_style))
        elements.append(Paragraph("• Evaluate accessibility for different user groups", content_style))
        elements.append(Paragraph("• Assess maintenance requirements for chosen materials and plants", content_style))
        
        elements.append(Spacer(1, 15))
        
        # Recommendations
        elements.append(Paragraph("<b>Recommendations for Implementation:</b>", content_style))
        elements.append(Paragraph("• Conduct site-specific climate analysis before finalizing design", content_style))
        elements.append(Paragraph("• Consider local building codes and regulations", content_style))
        elements.append(Paragraph("• Plan for irrigation and drainage systems", content_style))
        elements.append(Paragraph("• Include lighting design for evening use", content_style))
        elements.append(Paragraph("• Consider future expansion possibilities", content_style))
        elements.append(Paragraph("• Plan for regular maintenance and seasonal care", content_style))
        
        return elements

    def _create_plan_drawing(self, design_data, tree_data):
        """Create the main plan drawing"""
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
        
        # Calculate scale
        scale = 4.0
        
        # Create drawing
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
        """Draw courtyard spaces with appropriate symbols"""
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
                
                # Draw space symbol
                if space_type in space_symbols:
                    symbol = space_symbols[space_type]
                    size = 15
                    
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
                        points = [x_scaled, y_scaled + size, x_scaled - size, y_scaled - size,
                                x_scaled + size, y_scaled - size]
                        drawing.add(Polygon(points, fillColor=self.colors[space_type],
                                          strokeColor=self.colors['border'],
                                          strokeWidth=2))
                    elif symbol == 'diamond':
                        points = [x_scaled, y_scaled + size, x_scaled + size, y_scaled,
                                x_scaled, y_scaled - size, x_scaled - size, y_scaled]
                        drawing.add(Polygon(points, fillColor=self.colors[space_type],
                                          strokeColor=self.colors['border'],
                                          strokeWidth=2))
                    elif symbol == 'triangle':
                        points = [x_scaled, y_scaled + size, x_scaled - size, y_scaled - size,
                                x_scaled + size, y_scaled - size]
                        drawing.add(Polygon(points, fillColor=self.colors[space_type],
                                          strokeColor=self.colors['border'],
                                          strokeWidth=2))
                
                # Add label
                drawing.add(String(x_scaled, y_scaled - 25, space_name.upper(),
                                 fontSize=12, fillColor=self.colors['text']))
    
    def _draw_external_functions(self, drawing, positions, external_functions, min_x, min_y, max_y, scale, external_anchors):
        """Draw external functions as anchor points at corners"""
        for func_name, direction in external_functions.items():
            if func_name in positions and isinstance(positions[func_name], list):
                x, y = positions[func_name][:2]
                x_scaled = (x - min_x) * scale
                y_scaled = (max_y - min_y) * scale - (y - min_y) * scale
                
                # Check if this is an anchor point
                if func_name in external_anchors:
                    anchor_info = external_anchors[func_name]
                    corner = anchor_info.get('corner', 'Unknown')
                    
                    # Draw anchor point
                    size = 18
                    drawing.add(Circle(x_scaled, y_scaled, size,
                                     fillColor=self.colors['building'],
                                     strokeColor=self.colors['border'],
                                     strokeWidth=2))
                    
                    # Add anchor label
                    drawing.add(String(x_scaled, y_scaled - 25, f"{func_name.upper()}\n({corner})",
                                     fontSize=10, fillColor=white))
                else:
                    # Draw regular external function
                    size = 18
                    drawing.add(Rect(x_scaled - size, y_scaled - size, size*2, size*2,
                                   fillColor=self.colors['building'],
                                   strokeColor=self.colors['border'],
                                   strokeWidth=2))
                    
                    # Add label
                    drawing.add(String(x_scaled, y_scaled - 25, func_name.upper(),
                                     fontSize=10, fillColor=white))
    
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
        """Draw connections between spaces"""
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
                        
                        # Draw connection line
                        drawing.add(Line(x1, y1, x2, y2,
                                       strokeColor=self.colors['path'],
                                       strokeWidth=3))
    
    def _create_legend(self):
        """Create a professional legend"""
        elements = []
        
        # Legend title
        legend_style = ParagraphStyle(
            'LegendTitle',
            parent=getSampleStyleSheet()['Heading2'],
            fontSize=16,
            spaceAfter=15
        )
        elements.append(Paragraph("LEGEND", legend_style))
        
        # Legend items
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