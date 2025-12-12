def is_description_field(name: str, field_id: str) -> bool:
    """
    Detect if a field is likely a description/metadata field.
    Returns True if field should be deprioritized.
    """
    name_lower = name.lower()
    id_lower = field_id.lower()
    
    # Pattern 1: Contains "desc", "description", "label", "name" at end
    desc_patterns = ['desc', 'description', 'label', '_name', ' name']
    for pattern in desc_patterns:
        if name_lower.endswith(pattern) or id_lower.endswith(pattern):
            return True
    
    # Pattern 2: Contains "description" anywhere
    if 'description' in name_lower or 'description' in id_lower:
        return True
    
    # Pattern 3: Standalone "Description" field
    if name_lower == 'description':
        return True
    
    return False
