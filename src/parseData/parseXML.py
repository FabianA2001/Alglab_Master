import xml.etree.ElementTree as ET
from pathlib import Path


def parse_xml(xml_file_path: Path):
    """
    Parse an XML file and return the root element.

    Args:
        xml_file_path: Path to the XML file (default: Instance1.ros)

    Returns:
        Root element of the XML tree
    """
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    return root


def print_xml_structure(path: Path):
    # Parse die XML-Datei
    root = parse_xml(path)

    # Gebe Root-Tag und Attribute aus
    print(f"Root tag: {root.tag}")
    print(f"Root attributes: {root.attrib}")
    print("\n" + "=" * 50 + "\n")

    # Gebe die XML-Struktur formatiert aus
    ET.indent(root, space="  ")
    print(ET.tostring(root, encoding="unicode"))

    print("\n" + "=" * 50 + "\n")

    # Gebe alle direkten Kinder aus
    print("Direct children:")
    for child in root:
        print(f"  - {child.tag}: {child.attrib}")
        if child.text and child.text.strip():
            print(f"    Text: {child.text.strip()}")
