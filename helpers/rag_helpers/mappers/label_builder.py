def build_label(name: str, field_id: str, description: str = "") -> str:
    """Only add description if it provides new information."""
    label = (name or "").strip().lower()
    
    if description:
        desc_lower = description.strip().lower()
        # Skip if it's just "example column: <name>"
        if not (desc_lower.startswith("example") and name.lower() in desc_lower):
            label += " " + desc_lower
    
    return label
