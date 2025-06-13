import sys
import json
import os
import random
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QMainWindow, QVBoxLayout, QWidget
)
from PyQt5.QtGui import QPen, QBrush, QFont, QPainter, QColor
from PyQt5.QtCore import Qt
from matplotlib import colormaps
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, node_id, x, y, anchor=False, label="", color=QColor("gray"), weight=20):
        # Make radius proportional to weight (with a minimum and maximum for visibility)
        self.weight = weight
        self.radius = max(18, min(weight * 2.2, 60))  # scale and clamp
        super().__init__(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
        self.setPos(x, y)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 1.5))  # subtle border for contrast
        self.setZValue(1)
        self.setFlags(QGraphicsEllipseItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        if not anchor:
            self.setFlag(QGraphicsEllipseItem.ItemIsMovable)

        self.node_id = node_id
        self.anchor = anchor
        self.resizing = False

        self.label = QGraphicsTextItem(label)
        font = QFont("Arial", 11, QFont.Bold)
        self.label.setFont(font)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setParentItem(self)
        self.center_label()

    def center_label(self):
        # Always center the label in the node, vertically and horizontally
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, -rect.height() / 2)

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
            new_radius = max(18, min(event.pos().manhattanLength(), 60))
            self.radius = new_radius
            self.setRect(-self.radius, -self.radius, self.radius * 2, self.radius * 2)
            self.center_label()
            self.resolve_collisions()
        else:
            super().mouseMoveEvent(event)
            self.resolve_collisions()

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


class NetworkXGraphCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.G = None
        self.pos = None
        self.node_colors = []
        self.node_sizes = []
        self.labels = {}
        
    def update_graph(self, G, pos=None):
        self.G = G
        if pos is None:
            self.pos = nx.spring_layout(G)
        else:
            self.pos = pos
            
        # Clear the axes
        self.axes.clear()
        
        # Get node attributes
        weights = nx.get_node_attributes(G, 'weight')
        anchors = nx.get_node_attributes(G, 'anchor')
        
        # Set node colors and sizes
        self.node_colors = ["#ff7f0e" if anchors.get(n, False) else "#1f77b4" for n in G.nodes()]
        self.node_sizes = [weights.get(n, 20) * 100 for n in G.nodes()]
        self.labels = {n: n for n in G.nodes()}
        
        # Draw the graph
        nx.draw_networkx_edges(G, self.pos, ax=self.axes, width=1.5, alpha=0.6)
        nx.draw_networkx_nodes(G, self.pos, ax=self.axes, 
                             node_color=self.node_colors, 
                             node_size=self.node_sizes)
        nx.draw_networkx_labels(G, self.pos, ax=self.axes, 
                              labels=self.labels, 
                              font_size=9)
        
        self.axes.set_title("Courtyard Space Network Graph")
        self.axes.axis('off')
        self.fig.tight_layout()
        self.draw()


class GraphEditor(QWidget):
    def __init__(self, graph_data):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Create NetworkX graph
        self.G = nx.Graph()
        self.load_graph(graph_data)
        
        # Create matplotlib canvas
        self.canvas = NetworkXGraphCanvas(self, width=10, height=8)
        self.layout.addWidget(self.canvas)
        
        # Update the canvas with the graph
        self.canvas.update_graph(self.G)
        
    def load_graph(self, data):
        # Add nodes with their attributes
        for node in data["nodes"]:
            node_id = node["id"]
            pos = (node["pos"]["x"], node["pos"]["y"])
            self.G.add_node(
                node_id,
                pos=pos,
                weight=node.get("weight", 20),
                anchor=node.get("anchor", False)
            )
        
        # Add edges
        for link in data["links"]:
            self.G.add_edge(link["source"], link["target"])
            
        # Store positions
        self.pos = {node["id"]: (node["pos"]["x"], node["pos"]["y"]) 
                   for node in data["nodes"]}
    
    def get_graph_json(self):
        """Convert the NetworkX graph back to JSON format"""
        nodes = []
        for node_id in self.G.nodes():
            pos = self.pos.get(node_id, (0, 0))
            node_data = {
                "id": node_id,
                "pos": {"x": pos[0], "y": pos[1]},
                "weight": self.G.nodes[node_id].get("weight", 20),
                "anchor": self.G.nodes[node_id].get("anchor", False)
            }
            nodes.append(node_data)
            
        links = [{"source": u, "target": v} for u, v in self.G.edges()]
        return {"nodes": nodes, "links": links}
    
    def convert_graph_to_design_data(self, graph_json):
        """Convert the graph JSON to design data format"""
        design_data_post = {
            "spaces": [node["id"] for node in graph_json["nodes"]],
            "positions": {node["id"]: node["pos"] for node in graph_json["nodes"]},
            "anchors": {node["id"]: node.get("anchor", False) for node in graph_json["nodes"]},
            "weights": {node["id"]: node.get("weight", 20) for node in graph_json["nodes"]},
            "links": graph_json["links"]
        }
        return design_data_post


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resizable Node Graph Editor")

        downloads = os.path.expanduser("F:\\network_graph.json")
        if not os.path.exists(downloads):
            raise FileNotFoundError("network_graph.json not found in Downloads folder")

        with open(downloads) as f:
            data = json.load(f)

        editor = GraphEditor(data)
        self.setCentralWidget(editor)
        self.resize(1000, 800)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())