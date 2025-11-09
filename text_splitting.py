"""Improved text splitting with table awareness and multi-card support."""
import re
from text_formatting import RE_HTML_TAGS, sanitize_html


def estimate_text_length(text):
    """Estimate text length without HTML tags."""
    return len(RE_HTML_TAGS.sub('', text or ''))


def contains_complete_table(text):
    """Check if text contains at least one complete table."""
    if not text:
        return False
    return text.count('<table') == text.count('</table>') and '<table' in text


def split_at_table_boundary(text):
    """Split text at table boundaries, preferring to keep tables together."""
    if not text or '<table' not in text:
        return None
    
    # Find all table positions
    tables = []
    pos = 0
    while True:
        start = text.find('<table', pos)
        if start == -1:
            break
        end = text.find('</table>', start)
        if end == -1:
            break
        tables.append((start, end + 8))
        pos = end + 8
    
    if not tables:
        return None
    
    # Find best split point (prefer before tables or after complete tables)
    text_len = estimate_text_length(text)
    target = text_len * 0.4  # Split around 40% mark
    
    best_split = None
    best_distance = float('inf')
    
    # Try before each table
    for table_start, table_end in tables:
        before_len = estimate_text_length(text[:table_start])
        distance = abs(before_len - target)
        if distance < best_distance and before_len > 100:  # Don't split too early
            best_distance = distance
            best_split = table_start
    
    # Try after each complete table
    for table_start, table_end in tables:
        after_len = estimate_text_length(text[:table_end])
        distance = abs(after_len - target)
        if distance < best_distance and after_len > 100:
            best_distance = distance
            best_split = table_end
    
    return best_split


def find_safe_breakpoint(text, target_pos, avoid_tables=True):
    """Find safe text breakpoint avoiding HTML tags and optionally tables."""
    if not text:
        return 0
    
    current_clean_pos = 0
    in_tag = False
    in_table = False
    tag_buffer = ""
    
    for i, char in enumerate(text):
        if char == '<':
            in_tag = True
            tag_buffer = char
        elif char == '>' and in_tag:
            in_tag = False
            tag_buffer += char
            
            if tag_buffer.startswith('<table'):
                in_table = True
            elif tag_buffer.startswith('</table'):
                in_table = False
            continue
        elif in_tag:
            tag_buffer += char
            continue
        else:
            current_clean_pos += 1
        
        if current_clean_pos >= target_pos and not in_tag:
            if avoid_tables and in_table:
                continue
                
            # Look for sentence end or whitespace
            for lookahead in range(i, min(len(text), i + 100)):
                if text[lookahead:lookahead+7] == '<table>':
                    continue
                
                if text[lookahead] in '.;' and lookahead + 1 < len(text) and text[lookahead + 1] in ' \t\n':
                    window = text[max(0, lookahead-20):min(len(text), lookahead+50)]
                    if '<table' not in window and '</table>' not in window:
                        return lookahead + 2
                elif text[lookahead] in ' \t\n' and not in_tag:
                    window = text[max(0, lookahead-20):min(len(text), lookahead+50)]
                    if '<table' not in window and '</table>' not in window:
                        return lookahead + 1
    
    if in_table:
        table_end = text.find('</table>', i)
        if table_end != -1:
            return table_end + 8
    
    return min(len(text), target_pos)


def split_spell_text(text, max_parts=3):
    """
    Split text into 1-3 parts with table awareness.
    Returns tuple of (part1, part2, part3) where part2/part3 may be None.
    """
    if not text:
        return text, None, None
    
    text = sanitize_html(text)
    clean_len = estimate_text_length(text)
    
    # Thresholds for splitting (based on typical card capacity)
    single_card_limit = 800
    double_card_limit = 1800
    
    if clean_len <= single_card_limit:
        return text, None, None
    
    # Check if we need triple split
    if clean_len > double_card_limit:
        # Try table-aware split into 3 parts
        table_split = split_at_table_boundary(text)
        
        if table_split:
            part1 = text[:table_split].strip()
            remainder = text[table_split:].strip()
            
            # Split remainder
            remainder_len = estimate_text_length(remainder)
            if remainder_len > single_card_limit:
                mid_pos = int(remainder_len * 0.5)
                mid_split = find_safe_breakpoint(remainder, mid_pos)
                
                part2 = remainder[:mid_split].strip()
                part3 = remainder[mid_split:].strip()
                
                if part1 and part2 and part3:
                    return sanitize_html(part1), sanitize_html(part2), sanitize_html(part3)
        
        # Fallback: split into thirds
        target1 = int(clean_len * 0.35)
        target2 = int(clean_len * 0.67)
        
        split1 = find_safe_breakpoint(text, target1)
        part1 = text[:split1].strip()
        remainder = text[split1:].strip()
        
        remainder_target = estimate_text_length(remainder) // 2
        split2 = find_safe_breakpoint(remainder, remainder_target)
        part2 = remainder[:split2].strip()
        part3 = remainder[split2:].strip()
        
        return sanitize_html(part1), sanitize_html(part2), sanitize_html(part3)
    
    # Double card split
    table_split = split_at_table_boundary(text)
    
    if table_split:
        part1 = text[:table_split].strip()
        part2 = text[table_split:].strip()
        return sanitize_html(part1), sanitize_html(part2), None
    
    # Regular split at 35% mark
    target_pos = int(clean_len * 0.35)
    split_pos = find_safe_breakpoint(text, target_pos)
    
    part1 = text[:split_pos].strip()
    part2 = text[split_pos:].strip()
    
    # Verify no broken tables
    if part1 and part2:
        tables_in_part1 = part1.count('<table')
        tables_closed_in_part1 = part1.count('</table>')
        
        if tables_in_part1 > tables_closed_in_part1:
            last_table_start = part1.rfind('<table')
            if last_table_start != -1:
                text_before_table = part1[:last_table_start].strip()
                text_with_table = part1[last_table_start:] + part2
                
                if text_before_table and len(text_before_table) > 50:
                    part1 = text_before_table
                    part2 = text_with_table
                else:
                    return text, None, None
    
    return sanitize_html(part1), sanitize_html(part2), None
