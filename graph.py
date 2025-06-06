import networkx as nx
import matplotlib.pyplot as plt

def generate_network_graph(json_data, output_path="network_graph.png"):
    G = nx.Graph()

    # Add nodes
    pos_dict = {}
    node_colors = []
    node_sizes = []
    labels = {}

    for node in json_data["nodes"]:
        node_id = node["id"]
        pos = (node["pos"]["x"], node["pos"]["y"])
        pos_dict[node_id] = pos
        labels[node_id] = node_id

        # Use different color for anchors
        if node.get("anchor", False):
            node_colors.append("#ff7f0e")  # orange for anchors
            node_sizes.append(400)
        else:
            node_colors.append("#1f77b4")  # blue for regular nodes
            node_sizes.append(300)

        G.add_node(node_id, **node)

    # Add edges
    for link in json_data["links"]:
        G.add_edge(link["source"], link["target"])

    # Draw
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_edges(G, pos_dict, width=1.5, alpha=0.6)
    nx.draw_networkx_nodes(G, pos_dict, node_color=node_colors, node_size=node_sizes)
    nx.draw_networkx_labels(G, pos_dict, labels=labels, font_size=9)

    plt.title("Courtyard Space Network Graph")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return output_path