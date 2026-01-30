import difflib
from typing import List, Optional


def generate_diff(old_content: str, new_content: str) -> str:
    """Generate unified diff between old and new content"""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff_lines = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="previous",
        tofile="current",
        lineterm=""
    ))
    
    return "".join(diff_lines)


def apply_diff(original_content: str, diff_patch: str) -> str:
    """Apply a unified diff patch to reconstruct content"""
    if not diff_patch:
        return original_content
    
    # Parse the diff patch
    patch_lines = diff_patch.splitlines()
    
    # Find the actual diff content (skip header lines)
    diff_start = 0
    for i, line in enumerate(patch_lines):
        if line.startswith("@@"):
            diff_start = i
            break
    
    if diff_start == 0 and not any(line.startswith("@@") for line in patch_lines):
        # No valid diff found
        return original_content
    
    # Apply the patch manually
    original_lines = original_content.splitlines()
    result_lines = []
    
    i = 0  # Index in original_lines
    j = diff_start  # Index in patch_lines
    
    while j < len(patch_lines):
        line = patch_lines[j]
        
        if line.startswith("@@"):
            # Parse hunk header: @@ -start,count +start,count @@
            try:
                parts = line.split()
                old_range = parts[1][1:]  # Remove the '-'
                new_range = parts[2][1:]  # Remove the '+'
                
                old_start = int(old_range.split(',')[0]) - 1  # Convert to 0-based
                
                # Copy lines up to the hunk start
                while i < old_start:
                    if i < len(original_lines):
                        result_lines.append(original_lines[i])
                    i += 1
                    
            except (IndexError, ValueError):
                break
                
        elif line.startswith(" "):
            # Context line - copy from original
            if i < len(original_lines):
                result_lines.append(original_lines[i])
            i += 1
            
        elif line.startswith("-"):
            # Deleted line - skip in original
            i += 1
            
        elif line.startswith("+"):
            # Added line - add to result
            result_lines.append(line[1:])  # Remove the '+'
            
        j += 1
    
    # Copy any remaining lines from original
    while i < len(original_lines):
        result_lines.append(original_lines[i])
        i += 1
    
    return "\n".join(result_lines)


def reconstruct_version(snapshots: List[dict], target_version: int) -> str:
    """
    Reconstruct article content for a specific version
    
    snapshots should be a list of dicts with:
    - version_number: int
    - diff_patch: str (optional)
    - full_snapshot: str (optional)
    """
    if not snapshots:
        return ""
    
    # Sort by version number
    snapshots = sorted(snapshots, key=lambda x: x['version_number'])
    
    # Find the latest snapshot at or before target version
    base_snapshot = None
    base_content = ""
    
    for snapshot in snapshots:
        if snapshot['version_number'] <= target_version:
            if snapshot.get('full_snapshot'):
                base_snapshot = snapshot
                base_content = snapshot['full_snapshot']
            elif snapshot['version_number'] == 1:
                # First version should have the initial content in diff_patch or be empty
                base_snapshot = snapshot
                base_content = snapshot.get('diff_patch', '')
    
    if not base_snapshot:
        return ""
    
    # Apply diffs from base snapshot to target version
    current_content = base_content
    
    for snapshot in snapshots:
        if snapshot['version_number'] <= base_snapshot['version_number']:
            continue
        if snapshot['version_number'] > target_version:
            break
            
        if snapshot.get('diff_patch'):
            current_content = apply_diff(current_content, snapshot['diff_patch'])
    
    return current_content


def should_create_snapshot(version_number: int, snapshot_interval: int = 10) -> bool:
    """Determine if a full snapshot should be created for this version"""
    return version_number % snapshot_interval == 0


def create_search_text(content: str, title: str = "") -> str:
    """Create searchable text from article content and title"""
    # Remove markdown formatting for better search
    import re
    
    # Remove markdown headers
    search_text = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    
    # Remove markdown links but keep the text
    search_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', search_text)
    
    # Remove markdown bold/italic
    search_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', search_text)
    search_text = re.sub(r'\*([^\*]+)\*', r'\1', search_text)
    search_text = re.sub(r'__([^_]+)__', r'\1', search_text)
    search_text = re.sub(r'_([^_]+)_', r'\1', search_text)
    
    # Remove code blocks and inline code
    search_text = re.sub(r'```[^`]*```', ' ', search_text, flags=re.DOTALL)
    search_text = re.sub(r'`[^`]+`', ' ', search_text)
    
    # Combine title and content
    if title:
        search_text = f"{title} {search_text}"
    
    # Clean up whitespace
    search_text = ' '.join(search_text.split())
    
    return search_text