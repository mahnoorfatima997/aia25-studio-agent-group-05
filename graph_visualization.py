import networkx as nx
import plotly.graph_objs as go
import json


def infer_node_color(node_id):
    if "play" in node_id:
        return "green"
    if "rest" in node_id:
        return "orange"
    if "pond" in node_id:
        return "blue"
    if "tree" in node_id:
        return "brown"
    if "flower" in node_id:
        return "pink"
    if node_id in {"N", "S", "E", "W"}:
        return "black"
    return "gray"


def visualize_design_graph_3d(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    G = nx.Graph()
    pos_dict = {}

    for node in data["nodes"]:
        node_id = node["id"]
        G.add_node(node_id, **node)
        pos_dict[node_id] = (
            node["pos"]["x"],
            node["pos"]["y"],
            node.get("pos", {}).get("z", 0.0)
        )

    for link in data["links"]:
        G.add_edge(link["source"], link["target"])

    # Filter and collect node positions
    x_nodes, y_nodes, z_nodes, labels, colors = [], [], [], [], []
    for node in G.nodes():
        x, y, z = pos_dict[node]
        x_nodes.append(x)
        y_nodes.append(y)
        z_nodes.append(z)
        labels.append(node)
        colors.append(infer_node_color(node))

    # Edge line segments
    edge_x, edge_y, edge_z = [], [], []
    for u, v in G.edges():
        x0, y0, z0 = pos_dict[u]
        x1, y1, z1 = pos_dict[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    # Plotly traces
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        line=dict(color="lightgray", width=2),
        hoverinfo="none"
    )

    node_trace = go.Scatter3d(
        x=x_nodes, y=y_nodes, z=z_nodes,
        mode="markers+text",
        marker=dict(size=6, color=colors, opacity=0.8),
        text=labels,
        textposition="top center",
        hoverinfo="text"
    )

    layout = go.Layout(
        title="3D Design Graph",
        width=1000,
        height=700,
        scene=dict(
            xaxis=dict(title="X"),
            yaxis=dict(title="Y"),
            zaxis=dict(title="Z")
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        showlegend=False
    )

    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
    fig.show()
    fig.write_html("design_graph_3d.html")
    print("✅ Saved to design_graph_3d.html") 