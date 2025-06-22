import sys
import json
import os
import random
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QComboBox, QLabel, QMessageBox, QGraphicsItem,
    QGraphicsRectItem, QFileDialog
)
from PyQt5.QtGui import QPen, QBrush, QFont, QPainter, QColor, QPainterPath
from PyQt5.QtCore import Qt, QPointF
from matplotlib import colormaps



class NodeItem(QGraphicsEllipseItem):
    def __init__(self, node_id, x, y, anchor=False, label="", color=QColor("gray"), weight=20):
        # The radius is now derived from the weight
        radius = weight * 5 # Using a constant factor for visualization
        super().__init__(-radius, -radius, 2 * radius, 2 * radius) # Draw around origin
        self.setPos(x, y) # Set the center position in the scene
        
        self.node_id = node_id
        self.anchor = anchor
        self.weight = weight # Store the weight directly
        self.resizing = False # Restore the resizing flag
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self.label = QGraphicsTextItem(label, self)
        self.center_label()

    def center_label(self):
        label_rect = self.label.boundingRect()
        # Center the label within the ellipse, which is centered at (0,0)
        self.label.setPos(-label_rect.width() / 2, -label_rect.height() / 2)

    def wheelEvent(self, event):
        """Handle mouse wheel scrolling to change node weight."""
        if self.anchor:
            return  # Anchors cannot be resized

        # Adjust weight based on scroll direction
        delta = event.delta()
        if delta > 0:
            self.weight += 1  # Increase weight
        else:
            self.weight -= 1  # Decrease weight
        
        # Ensure weight stays within a reasonable range (e.g., 1 to 20)
        self.weight = max(1, min(self.weight, 20))
        
        # Update the visual radius based on the new weight
        new_radius = self.weight * 5
        self.setRect(-new_radius, -new_radius, 2 * new_radius, 2 * new_radius)
        self.center_label()

    def hoverMoveEvent(self, event):
        if self.anchor:
            self.setToolTip(f"ID: {self.node_id} (Anchor)")
        else:
            self.setToolTip(f"ID: {self.node_id}\nWeight: {self.weight}")
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        # Position is relative to the item's center (0,0)
        dist_from_center = (event.pos().x()**2 + event.pos().y()**2)**0.5
        radius = self.rect().width() / 2
        
        # Check if the click is near the edge for resizing
        if abs(dist_from_center - radius) < 6:
            self.resizing = True
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing and not self.anchor:
            new_radius = max(10, (event.pos().x()**2 + event.pos().y()**2)**0.5)
            self.weight = new_radius / 5
            self.setRect(-new_radius, -new_radius, 2 * new_radius, 2 * new_radius)
            self.center_label()
            self.resolve_collisions()
        else:
            super().mouseMoveEvent(event)
            self.resolve_collisions()

    def mouseReleaseEvent(self, event):
        self.resizing = False
        super().mouseReleaseEvent(event)

    def resolve_collisions(self):
        for item in self.scene().items():
            if isinstance(item, NodeItem) and item != self:
                dx = self.scenePos().x() - item.scenePos().x()
                dy = self.scenePos().y() - item.scenePos().y()
                dist = (dx ** 2 + dy ** 2) ** 0.5
                min_dist = self.rect().width() / 2 + item.rect().width() / 2

                if dist < min_dist and dist != 0:
                    overlap = min_dist - dist + 1
                    nx, ny = dx / dist, dy / dist
                    self.moveBy(nx * overlap / 2, ny * overlap / 2)
                    if not item.anchor:
                        item.moveBy(-nx * overlap / 2, -ny * overlap / 2)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Get the new position
            new_pos = value
            # Get the parent GraphEditor
            editor = self.scene().views()[0]
            if isinstance(editor, GraphEditor):
                # Transform to grid coordinates and clamp
                grid_x, grid_y = editor.transform_to_grid_coords(new_pos.x(), new_pos.y())
                # Transform back to scene coordinates
                scene_x, scene_y = editor.transform_to_scene_coords(grid_x, grid_y)
                # Return the clamped scene position
                return QPointF(scene_x, scene_y)
        return super().itemChange(change, value)


class CardinalDirectionItem(QGraphicsTextItem):
    """Special item for cardinal directions as letters instead of circles"""
    def __init__(self, direction, x, y):
        super().__init__(direction)
        self.setPos(x, y)
        
        # Enhanced styling for cardinal directions - larger and more visible
        self.setFont(QFont("Arial Black", 28, QFont.Bold))  # Even larger font size
        self.setDefaultTextColor(QColor("#1A1A1A"))  # Very dark text for maximum contrast
        
        # Add a subtle background for better visibility
        self.setZValue(2)  # Higher than regular nodes
        
        # Center the text
        self.setPos(x - self.boundingRect().width() / 2, y - self.boundingRect().height() / 2)


class EdgeItem(QGraphicsLineItem):
    def __init__(self, node1, node2):
        super().__init__()
        self.node1 = node1
        self.node2 = node2
        
        # Enhanced edge styling
        self.default_pen = QPen(QColor("#7F8C8D"), 2)  # Gray with better contrast
        self.highlight_pen = QPen(QColor("#E74C3C"), 3)  # Red highlight
        self.setPen(self.default_pen)
        self.setAcceptHoverEvents(True)
        self.update_position()
        self.setZValue(0)

    def update_position(self):
        p1 = self.node1.scenePos()
        p2 = self.node2.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

    def hoverEnterEvent(self, event):
        self.setPen(self.highlight_pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(self.default_pen)
        super().hoverLeaveEvent(event)


class GraphEditor(QGraphicsView):
    def __init__(self, graph_data):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setScene(QGraphicsScene(self))
        self.setSceneRect(0, 0, 1000, 800)
        
        # Set background color for better aesthetics
        self.setBackgroundBrush(QBrush(QColor("#F8F9FA")))  # Light gray background

        self.nodes = {}
        self.edges = []
        self.edge_pairs = set()
        self.selected_node = None

        # Enhanced color palette
        self.color_palette = [
            QColor("#3498DB"),  # Blue
            QColor("#E74C3C"),  # Red
            QColor("#2ECC71"),  # Green
            QColor("#F39C12"),  # Orange
            QColor("#9B59B6"),  # Purple
            QColor("#1ABC9C"),  # Turquoise
            QColor("#E67E22"),  # Dark Orange
            QColor("#34495E"),  # Dark Blue
            QColor("#16A085"),  # Dark Green
            QColor("#8E44AD"),  # Dark Purple
        ]
        
        # Define size conversion constants
        self.WEIGHT_TO_RADIUS = 5  # Multiply weight by this to get radius
        self.RADIUS_TO_WEIGHT = 1/self.WEIGHT_TO_RADIUS  # Divide radius by this to get weight
        
        # Define coordinate ranges
        self.X_MIN = -34
        self.X_MAX = -4
        self.Y_MIN = 30
        self.Y_MAX = 60
        self.X_RANGE = self.X_MAX - self.X_MIN
        self.Y_RANGE = self.Y_MAX - self.Y_MIN
        
        self.load_graph(graph_data)
        self.add_cardinal_directions()

    def add_cardinal_directions(self):
        # Add cardinal direction letters at the edges of the grid, positioned further out to avoid overlap
        directions = {
            "N": ((self.X_MIN + self.X_MAX)/2, self.Y_MAX + 5),  # North at top, further out
            "E": (self.X_MIN - 5, (self.Y_MIN + self.Y_MAX)/2),  # East at right, further out
            "S": ((self.X_MIN + self.X_MAX)/2, self.Y_MIN - 5),  # South at bottom, further out
            "W": (self.X_MAX + 5, (self.Y_MIN + self.Y_MAX)/2)   # West at left, further out
        }
        
        for direction, (x, y) in directions.items():
            # Transform coordinates to scene coordinates
            scene_x, scene_y = self.transform_to_scene_coords(x, y)
            
            # Create cardinal direction as text instead of circle
            cardinal_item = CardinalDirectionItem(direction, scene_x, scene_y)
            self.scene().addItem(cardinal_item)
            self.nodes[direction] = cardinal_item

    def transform_to_scene_coords(self, x, y):
        """Transform grid coordinates to scene coordinates"""
        # Handle coordinates outside the normal grid range (for cardinal directions)
        if x < self.X_MIN - 5 or x > self.X_MAX + 5 or y < self.Y_MIN - 5 or y > self.Y_MAX + 5:
            # For cardinal directions, use a wider range
            x_range = self.X_RANGE + 10  # Add 10 units on each side
            y_range = self.Y_RANGE + 10  # Add 10 units on each side
            x_min = self.X_MIN - 5
            y_min = self.Y_MIN - 5
        else:
            # Normal grid coordinates
            x_range = self.X_RANGE
            y_range = self.Y_RANGE
            x_min = self.X_MIN
            y_min = self.Y_MIN
        
        # Normalize coordinates
        normalized_x = (x - x_min) / x_range
        normalized_y = (y - y_min) / y_range
        
        # Transform to scene coordinates
        scene_x = normalized_x * 700 + 150
        scene_y = (1 - normalized_y) * 500 + 150  # Invert y for screen coordinates
        return scene_x, scene_y

    def transform_to_grid_coords(self, scene_x, scene_y):
        """Transform scene coordinates to grid coordinates"""
        # Convert scene coordinates to normalized coordinates [0, 1]
        normalized_x = (scene_x - 150) / 700
        normalized_y = 1 - (scene_y - 150) / 500  # Invert y for grid coordinates
        
        # Convert normalized coordinates to grid coordinates
        grid_x = normalized_x * self.X_RANGE + self.X_MIN
        grid_y = normalized_y * self.Y_RANGE + self.Y_MIN
        
        # Clamp values to valid ranges
        grid_x = max(self.X_MIN, min(self.X_MAX, grid_x))
        grid_y = max(self.Y_MIN, min(self.Y_MAX, grid_y))
        return grid_x, grid_y

    def load_graph(self, data):
        # Clear existing graph
        self.scene().clear()
        self.nodes = {}
        self.edges = []
        self.edge_pairs = set()

        # Add cardinal direction indicators
        self.add_cardinal_directions()

        # Create nodes
        for i, node_data in enumerate(data["nodes"]):
            node_id = node_data["id"]
            pos = node_data["pos"]
            weight = node_data.get("weight", 5) # Default weight
            anchor = node_data.get("anchor", False)
            
            # Transform coordinates
            scene_x, scene_y = self.transform_to_scene_coords(pos["x"], pos["y"])
            
            # Determine color
            color = QColor("#E74C3C") if anchor else self.color_palette[i % len(self.color_palette)]
            
            # Skip cardinal directions as they're handled separately
            if node_id not in ["N", "S", "E", "W"]:
                node = NodeItem(node_id, scene_x, scene_y, anchor, node_id, color, weight)
                self.scene().addItem(node)
                self.nodes[node_id] = node

        # Create edges
        print(f"Creating edges from {len(data['links'])} links...")
        for link in data["links"]:
            source = link["source"]
            target = link["target"]
            print(f"Creating edge: {source} -> {target}")
            self.add_edge(source, target)

    def add_edge(self, id1, id2):
        if (id1, id2) in self.edge_pairs or (id2, id1) in self.edge_pairs:
            return
        
        # Check if both nodes exist before creating the edge
        if id1 not in self.nodes:
            print(f"Warning: Node '{id1}' not found in graph. Skipping edge creation.")
            return
        if id2 not in self.nodes:
            print(f"Warning: Node '{id2}' not found in graph. Skipping edge creation.")
            return
            
        edge = EdgeItem(self.nodes[id1], self.nodes[id2])
        self.scene().addItem(edge)
        self.edges.append(edge)
        self.edge_pairs.add((id1, id2))

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        modifiers = QApplication.keyboardModifiers()

        if isinstance(item, NodeItem):
            node_id = item.node_id
            if modifiers == Qt.ControlModifier:
                if self.selected_node is None:
                    self.selected_node = node_id
                    item.setBrush(QBrush(Qt.yellow))
                else:
                    if self.selected_node != node_id:
                        self.add_edge(self.selected_node, node_id)
                    self.restore_node_color(self.selected_node)
                    self.selected_node = None
        elif isinstance(item, EdgeItem):
            if event.button() == Qt.RightButton:
                self.scene().removeItem(item)
                self.edges.remove(item)
                self.edge_pairs.discard((item.node1.node_id, item.node2.node_id))
                self.edge_pairs.discard((item.node2.node_id, item.node1.node_id))
        else:
            if self.selected_node:
                self.restore_node_color(self.selected_node)
                self.selected_node = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        for edge in self.edges:
            edge.update_position()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S:
            self.save_graph()

    def restore_node_color(self, node_id):
        if node_id in self.nodes:
            node = self.nodes[node_id]
            # Find original color (this part needs improvement if colors are dynamic)
            # For now, we revert to a default or based on anchor status
            original_color = QColor("#E74C3C") if node.anchor else QColor("gray")
            
            # A better way is to find its original index in the loaded data
            # but this is a quick fix.
            # Find node in self.nodes and get its original color from palette
            # This logic assumes the order hasn't changed, which is not robust
            all_nodes = list(self.nodes.keys())
            if node_id in all_nodes:
                idx = all_nodes.index(node_id)
                original_color = self.color_palette[idx % len(self.color_palette)]

            node.setBrush(QBrush(original_color))

    def save_graph(self):
        """Saves the current graph state to a JSON file."""
        graph_data = self.get_graph_data()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(graph_data, f, indent=4)
            print(f"Graph saved to {file_path}")

    def get_graph_data(self):
        """Constructs a JSON-serializable dictionary from the current graph state."""
        nodes_data = []
        for node_id, item in self.nodes.items():
            if isinstance(item, NodeItem):
                scene_pos = item.scenePos()
                # Use the center of the item for more accurate position, which is now just scenePos()
                grid_x, grid_y = self.transform_to_grid_coords(scene_pos.x(), scene_pos.y())

                node_info = {
                    "id": node_id,
                    "pos": {"x": round(grid_x, 2), "y": round(grid_y, 2)},
                    "anchor": item.anchor,
                    "weight": item.weight # Read the stored weight directly
                }
                nodes_data.append(node_info)

        links_data = []
        for edge in self.edges:
            links_data.append({
                "source": edge.node1.node_id,
                "target": edge.node2.node_id
            })

        return {
            "directed": False,
            "multigraph": False,
            "graph": {},
            "nodes": nodes_data, 
            "links": links_data
        }


class MainWindow(QMainWindow):
    def __init__(self, graph_data=None):
        super().__init__()
        self.setWindowTitle("Resizable Node Graph Editor")
        self.versions = []  # List to store all versions
        self.current_version = 0  # Index of current version

        if graph_data is None:
            # Fallback to reading from file if no data provided
            downloads = os.path.expanduser("~/Downloads/network_graph.json")
            if not os.path.exists(downloads):
                raise FileNotFoundError("network_graph.json not found in Downloads folder")

            with open(downloads) as f:
                graph_data = json.load(f)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create toolbar with save button and version dropdown
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Save button
        self.save_button = QPushButton("Save New Version")
        self.save_button.clicked.connect(self.save_new_version)
        toolbar_layout.addWidget(self.save_button)

        # Version label
        version_label = QLabel("Version:")
        toolbar_layout.addWidget(version_label)

        # Version dropdown
        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self.load_version)
        toolbar_layout.addWidget(self.version_combo)

        # Send to Grasshopper button
        self.send_to_gh_button = QPushButton("Send to Grasshopper")
        self.send_to_gh_button.clicked.connect(self.send_to_grasshopper)
        toolbar_layout.addWidget(self.send_to_gh_button)

        # Add toolbar to main layout
        layout.addWidget(toolbar)

        # Create and add graph editor
        self.editor = GraphEditor(graph_data)
        layout.addWidget(self.editor)

        # Store initial version
        self.versions.append(graph_data)
        self.version_combo.addItem("Version 1")
        self.resize(1000, 800)

    def save_new_version(self):
        # Get current graph state
        current_data = self.editor.get_graph_data()
        
        # Add new version
        self.versions.append(current_data)
        self.current_version = len(self.versions) - 1
        
        # Update dropdown
        self.version_combo.addItem(f"Version {len(self.versions)}")
        self.version_combo.setCurrentIndex(self.current_version)
        
        # Save to file
        self.save_version_to_file(current_data, len(self.versions))

    def load_version(self, index):
        if index < 0 or index >= len(self.versions):
            return
            
        self.current_version = index
        # Create new editor with the selected version
        new_editor = GraphEditor(self.versions[index])
        # Replace old editor
        layout = self.centralWidget().layout()
        old_editor = layout.itemAt(1).widget()
        layout.replaceWidget(old_editor, new_editor)
        old_editor.deleteLater()
        self.editor = new_editor

    def save_version_to_file(self, data, version_num):
        # Save to a versioned file
        out_dir = os.path.expanduser("~/Downloads/graph_versions")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"graph_version_{version_num}.json")
        
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Version {version_num} saved to: {out_path}")

    def send_to_grasshopper(self):
        """Send the current version to Grasshopper as JSON only (no CSV export)"""
        try:
            # Get the current version data (user's current layout)
            current_data = self.versions[self.current_version]

            # Create a directory for Grasshopper files if it doesn't exist
            gh_dir = os.path.expanduser("~/Downloads/grasshopper_versions")
            os.makedirs(gh_dir, exist_ok=True)

            # Save as JSON for Grasshopper to read
            gh_path = os.path.join(gh_dir, f"gh_version_{self.current_version + 1}.json")
            with open(gh_path, "w") as f:
                json.dump(current_data, f, indent=2)

            # Send the current graph data to the server endpoint for Grasshopper
            import requests
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                "http://127.0.0.1:5000/graph_data",
                json={"graph_data": current_data},
                headers=headers
            )
            if response.status_code != 200:
                raise Exception(f"Failed to send graph to Grasshopper server: {response.text}")

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Version {self.current_version + 1} exported to Grasshopper format.\n"
                f"JSON file saved in: {gh_dir}\n"
                f"Graph data sent to Grasshopper server."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export to Grasshopper: {str(e)}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Example of how to use with direct data:
    # window = MainWindow(graph_data=your_graph_data)
    window = MainWindow()  # Will fall back to reading from file
    window.show()
    sys.exit(app.exec_())