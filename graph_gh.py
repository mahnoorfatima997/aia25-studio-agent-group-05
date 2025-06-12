import sys
import json
import os
import random
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QMainWindow
)
from PyQt5.QtGui import QPen, QBrush, QFont, QPainter, QColor
from PyQt5.QtCore import Qt
from matplotlib import colormaps


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

        self.summer = colormaps.get_cmap("summer")  # ✅ Use 'summer' colormap
        self.load_graph(graph_data)

            # Accept both the full design_data or a pre-built graph JSON
        if "nodes" in graph_data and "links" in graph_data:
            # Already in graph format (from LLM call)
            self.load_graph(graph_data)
        else:
            # Convert design_data to graph format
            graph_json = self.convert_design_data_to_graph(graph_data)
            self.load_graph(graph_json)

    def convert_design_data_to_graph(self, design_data):
        nodes = []
        weights = design_data.get("weights", {})
        anchors = design_data.get("anchors", {})
        positions = design_data.get("positions", {})
        for node_id in design_data.get("spaces", []):
            pos = positions.get(node_id, {"x": 0, "y": 0})
            node = {
                "id": node_id,
                "pos": {"x": pos.get("x", 0), "y": pos.get("y", 0)},
                "anchor": anchors.get(node_id, False),
                "weight": weights.get(node_id, 20)
            }
            nodes.append(node)
        links = []
        for link in design_data.get("links", []):
            if isinstance(link, dict):
                source = link.get("source")
                target = link.get("target")
            elif isinstance(link, (list, tuple)) and len(link) == 2:
                source, target = link
            else:
                continue
            links.append({"source": source, "target": target})
        return {"nodes": nodes, "links": links}

    def load_graph(self, data):
        xs = [n["pos"]["x"] for n in data["nodes"]]
        ys = [n["pos"]["y"] for n in data["nodes"]]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        def transform(x, y):
            sx = (x - min_x) / (max_x - min_x + 1e-5) * 800 + 100
            sy = (1 - (y - min_y) / (max_y - min_y + 1e-5)) * 600 + 100
            return sx, sy

        for i, node in enumerate(data["nodes"]):
            nid = node["id"]
            x, y = transform(node["pos"]["x"], node["pos"]["y"])
            anchor = node.get("anchor", False)
            base_weight = node.get("weight", 20)
            weight = min(max(base_weight * 1.5, 15), 80)

            if anchor:
                color = QColor.fromHsv(300 + random.randint(-20, 20), 200, 255)
            else:
                rgba = self.summer(i / max(1, len(data["nodes"]) - 1))  # ✅ correct usage
                color = QColor.fromRgbF(*rgba[:3])

            item = NodeItem(nid, x, y, anchor, nid, color, weight)
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
            rgba = self.summer(index / max(1, len(self.nodes) - 1))  # ✅ correct usage
            node.setBrush(QBrush(QColor.fromRgbF(*rgba[:3])))

    def save_graph(self):
        nodes = []
        for nid, item in self.nodes.items():
            x, y = item.scenePos().x(), item.scenePos().y()
            node_data = {
                "id": nid,
                "pos": {"x": round(x, 2), "y": round(y, 2)},
                "anchor": item.anchor
            }
            if not item.anchor:
                node_data["weight"] = round(item.radius / 1.5, 1)
            nodes.append(node_data)

        links = [{"source": e.node1.node_id, "target": e.node2.node_id} for e in self.edges]

        new_data = {"nodes": nodes, "links": links}

        out_path = os.path.expanduser("~/Downloads/edited_graph.json")
        with open(out_path, "w") as f:
            json.dump(new_data, f, indent=2)
        print(f"✅ Graph saved to: {out_path}")

    def get_graph_json(self):
        """
        Return the current graph as a JSON-serializable dict with 'nodes' and 'links'.
        Each node includes id, pos, anchor, and weight (if not anchor).
        Each link includes source and target.
        """
        nodes = []
        for nid, item in self.nodes.items():
            x, y = item.scenePos().x(), item.scenePos().y()
            node_data = {
                "id": nid,
                "pos": {"x": round(x, 2), "y": round(y, 2)},
                "anchor": item.anchor
            }
            if not item.anchor:
                node_data["weight"] = round(item.radius / 1.5, 1)
            nodes.append(node_data)
        links = [{"source": e.node1.node_id, "target": e.node2.node_id} for e in self.edges]
        return {"nodes": nodes, "links": links}

    def convert_graph_to_design_data(self, graph_json):
        """
        Convert the graph JSON (nodes/links) to the design_data_post structure expected by the Flask server.
        """
        design_data_post = {
            "spaces": [node["id"] for node in graph_json["nodes"]],
            "positions": {node["id"]: node["pos"] for node in graph_json["nodes"]},
            "anchors": {node["id"]: node.get("anchor", False) for node in graph_json["nodes"]},
            "weights": {node["id"]: node.get("weight", 20) for node in graph_json["nodes"]},
            "links": graph_json["links"]
            # Add other fields as needed
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