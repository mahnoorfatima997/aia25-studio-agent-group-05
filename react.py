import threading
from llm_calls import (
    extract_spaces, extract_links, extract_positions, extract_cardinal_directions,
    extract_weights, extract_anchors, assemble_full_courtyard_graph
)
import json
import networkx as nx
import matplotlib.pyplot as plt

class ReactAgent:
    def __init__(self, concept_prompt, functions_prompt):
        self.state = {
            "concept": concept_prompt,
            "functions": functions_prompt,
            "attributes": None,
            "graph": None,
            "history": []
        }
        self.design_data = {}
        self.thoughts = []

    def log(self, message):
        print(message)
        self.thoughts.append(message)

    def run(self):
        # Step 1: Concept phase
        self.log("Thought: Start with concept phase.")
        self.state["history"].append({"role": "user", "content": self.state["concept"]})
        # Step 2: Functions phase
        self.log("Thought: Move to functions phase.")
        self.state["history"].append({"role": "user", "content": self.state["functions"]})
        # Step 3: Extract all attributes using LLM tools
        self.log("Thought: Extracting spaces from conversation history.")
        spaces = extract_spaces(self.state["history"])
        self.log(f"Observation: Spaces extracted: {spaces}")
        self.log("Thought: Extracting links from conversation history.")
        links = extract_links(self.state["history"])
        self.log(f"Observation: Links extracted: {links}")
        self.log("Thought: Extracting positions from conversation history.")
        positions = extract_positions(self.state["history"])
        self.log(f"Observation: Positions extracted: {positions}")
        self.log("Thought: Extracting cardinal directions from conversation history.")
        cardinal_directions = extract_cardinal_directions(self.state["history"])
        self.log(f"Observation: Cardinal directions extracted: {cardinal_directions}")
        self.log("Thought: Extracting weights from conversation history.")
        weights = extract_weights(self.state["history"])
        self.log(f"Observation: Weights extracted: {weights}")
        self.log("Thought: Extracting anchors from conversation history.")
        anchors = extract_anchors(self.state["history"])
        self.log(f"Observation: Anchors extracted: {anchors}")
        # Store all extracted data
        self.design_data = {
            "spaces": spaces,
            "links": links,
            "positions": positions,
            "cardinal_directions": cardinal_directions,
            "weights": weights,
            "anchors": anchors
        }
        # Step 4: Reason if any data is missing or inconsistent, and fix if needed
        # (For brevity, this is a placeholder. You can add validation/correction logic here.)
        self.log("Thought: All attributes extracted. Proceeding to graph generation.")
        # Step 5: Generate the full courtyard graph
        llm_output = assemble_full_courtyard_graph(self.state["history"])
        self.log(f"Observation: LLM output for graph: {llm_output}")
        # Extract JSON from LLM output
        import re
        match = re.search(r'\{(?:[^{}]|(?R))*\}', llm_output, re.DOTALL)
        if match:
            graph_json = json.loads(match.group(0))
            self.state["graph"] = graph_json
            self.show_graph(graph_json)
        else:
            self.log("No JSON found in LLM output for graph.")

    def show_graph(self, graph_json):
        G = nx.Graph() if not graph_json.get("directed", False) else nx.DiGraph()
        for node in graph_json["nodes"]:
            node_id = node["id"]
            pos = (node["pos"]["x"], node["pos"]["y"])
            G.add_node(node_id, pos=pos, weight=node["weight"], anchor=node["anchor"])
        for link in graph_json["links"]:
            G.add_edge(link["source"], link["target"])
        pos = nx.get_node_attributes(G, "pos")
        weights = nx.get_node_attributes(G, "weight")
        anchors = nx.get_node_attributes(G, "anchor")
        node_colors = ["red" if anchors[n] else "skyblue" for n in G.nodes()]
        node_sizes = [weights[n] * 100 for n in G.nodes()]
        plt.figure(figsize=(10, 8))
        nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=node_sizes, edge_color="gray", font_size=10)
        plt.title("Courtyard Graph")
        plt.axis("equal")
        plt.show()

# Example usage:
if __name__ == "__main__":
    concept = input("Enter concept prompt: ")
    functions = input("Enter functions prompt: ")
    agent = ReactAgent(concept, functions)
    agent.run()
    print("\n--- Agent Reasoning Trace ---")
    for t in agent.thoughts:
        print(t)
