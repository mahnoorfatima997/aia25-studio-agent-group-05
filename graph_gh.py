import sys
import json
import os
import random
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QComboBox, QLabel, QMessageBox
)
from PyQt5.QtGui import QPen, QBrush, QFont, QPainter, QColor
from PyQt5.QtCore import Qt
from matplotlib import colormaps
from ui_pyqt import *


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, node_id, x, y, anchor=False, label="", color=QColor("gray"), weight=20):
        self.radius = weight
        super().__init__(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.setPos(x, y)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.transparent))
        self.setZValue(1)
        self.setFlags(QGraphicsEllipseItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        if not anchor:
            self.setFlag(QGraphicsEllipseItem.ItemIsMovable)

        self.node_id = node_id
        self.anchor = anchor
        self.resizing = False

        self.label = QGraphicsTextItem(label)
        self.label.setFont(QFont("Arial", 10))
        self.label.setDefaultTextColor(Qt.white)
        self.label.setParentItem(self)
        self.center_label()

    def center_label(self):
        self.label.setPos(-self.label.boundingRect().width() / 2, -10)

    def hoverMoveEvent(self, event):
        dist = event.pos().manhattanLength()
        if abs(dist - self.radius) < 6:
            self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        dist = event.pos().manhattanLength()
        if abs(dist - self.radius) < 6:
            self.resizing = True
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing and not self.anchor:
            new_radius = max(10, event.pos().manhattanLength())
            self.radius = new_radius
            self.setRect(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
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
                min_dist = self.radius + item.radius

                if dist < min_dist and dist != 0:
                    overlap = min_dist - dist + 1
                    nx, ny = dx / dist, dy / dist
                    self.moveBy(nx * overlap / 2, ny * overlap / 2)
                    if not item.anchor:
                        item.moveBy(-nx * overlap / 2, -ny * overlap / 2)


class EdgeItem(QGraphicsLineItem):
    def __init__(self, node1, node2):
        super().__init__()
        self.node1 = node1
        self.node2 = node2
        self.default_pen = QPen(Qt.black, 2)
        self.highlight_pen = QPen(Qt.red, 2)
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

        self.nodes = {}
        self.edges = []
        self.edge_pairs = set()
        self.selected_node = None

        self.summer = colormaps.get_cmap("summer")
        # Define size conversion constants
        self.WEIGHT_TO_RADIUS = 5  # Multiply weight by this to get radius
        self.RADIUS_TO_WEIGHT = 1/self.WEIGHT_TO_RADIUS  # Divide radius by this to get weight
        self.load_graph(graph_data)
        self.add_cardinal_directions()

    def add_cardinal_directions(self):
        # Add cardinal direction nodes
        directions = {
            "N": (500, 50),   # North at top
            "E": (950, 400),  # East at right
            "S": (500, 750),  # South at bottom
            "W": (50, 400)    # West at left
        }
        
        for direction, (x, y) in directions.items():
            item = NodeItem(direction, x, y, True, direction, QColor("black"), 30)
            item.label.setDefaultTextColor(Qt.black)  # Set text color to black
            self.scene().addItem(item)
            self.nodes[direction] = item

    def load_graph(self, data):
        xs = [n["pos"]["x"] for n in data["nodes"]]
        ys = [n["pos"]["y"] for n in data["nodes"]]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        def transform(x, y):
            # Adjust the transformation to leave space for cardinal directions
            sx = (x - min_x) / (max_x - min_x + 1e-5) * 700 + 150  # Reduced width to 700, offset by 150
            sy = (1 - (y - min_y) / (max_y - min_y + 1e-5)) * 500 + 150  # Reduced height to 500, offset by 150
            return sx, sy

        for i, node in enumerate(data["nodes"]):
            nid = node["id"]
            x, y = transform(node["pos"]["x"], node["pos"]["y"])
            anchor = node.get("anchor", False)
            weight = node.get("weight", 4)  # Default weight of 4 gives radius of 20
            # Scale weight to a reasonable node size (between 30 and 100)
            node_size = min(max(weight * self.WEIGHT_TO_RADIUS, 30), 100)

            if anchor:
                color = QColor.fromHsv(300 + random.randint(-20, 20), 200, 255)
            else:
                rgba = self.summer(i / max(1, len(data["nodes"]) - 1))
                color = QColor.fromRgbF(*rgba[:3])

            item = NodeItem(nid, x, y, anchor, nid, color, node_size)
            item.label.setDefaultTextColor(Qt.black)  # Set text color to black
            self.scene().addItem(item)
            self.nodes[nid] = item

        for link in data["links"]:
            self.add_edge(link["source"], link["target"])

    def add_edge(self, id1, id2):
        if (id1, id2) in self.edge_pairs or (id2, id1) in self.edge_pairs:
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
        node = self.nodes[node_id]
        if node.anchor:
            node.setBrush(QBrush(QColor(200, 80, 200)))
        else:
            index = list(self.nodes.keys()).index(node_id)
            rgba = self.summer(index / max(1, len(self.nodes) - 1))
            node.setBrush(QBrush(QColor.fromRgbF(*rgba[:3])))

    def save_graph(self):
        """Legacy save method - now just calls save_new_version on the parent window"""
        if hasattr(self.parent(), "save_new_version"):
            self.parent().save_new_version()

    def get_graph_data(self):
        """Get the current state of the graph as a data structure"""
        nodes = []
        for nid, item in self.nodes.items():
            # Skip cardinal direction nodes when saving
            if nid in ["N", "E", "S", "W"]:
                continue
                
            x, y = item.scenePos().x(), item.scenePos().y()
            node_data = {
                "id": nid,
                "pos": {"x": round(x, 2), "y": round(y, 2)},
                "anchor": item.anchor
            }
            if not item.anchor:
                # Convert radius back to weight using the same conversion factor
                node_data["weight"] = round(item.radius * self.RADIUS_TO_WEIGHT, 1)
            nodes.append(node_data)

        links = [{"source": e.node1.node_id, "target": e.node2.node_id} 
                for e in self.edges 
                if e.node1.node_id not in ["N", "E", "S", "W"] 
                and e.node2.node_id not in ["N", "E", "S", "W"]]

        return {
            "nodes": nodes,
            "links": links,
            "directed": False,
            "multigraph": False,
            "graph": {}
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