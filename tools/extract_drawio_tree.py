"""Extract the editable diagrams.net source embedded in an exported SVG."""

from pathlib import Path
import xml.etree.ElementTree as ET


project = Path(__file__).resolve().parents[1]
source = project / "reference_posg_game_tree.svg"
target = project / "posg_game_tree_aligned.drawio"

svg = ET.parse(source).getroot()
mxfile = svg.attrib["content"]

# Verify that the embedded source is a valid diagrams.net document before saving.
document = ET.fromstring(mxfile)
if document.tag != "mxfile":
    raise ValueError("The SVG does not contain an mxfile diagrams.net payload.")

cells = document.find(".//root").findall("mxCell")
edges = [cell for cell in cells if cell.get("edge") == "1"]
attached = [
    edge for edge in edges
    if edge.get("source") is not None and edge.get("target") is not None
]
if len(edges) != 89 or len(attached) != 27:
    raise ValueError(
        f"Unexpected source structure: {len(edges)} edges; {len(attached)} fully attached."
    )

ET.ElementTree(document).write(target, encoding="utf-8", xml_declaration=True)
print(f"Wrote {target}")
print(f"Preserved {len(edges)} connectors and {len(attached)} fully attached connectors.")
