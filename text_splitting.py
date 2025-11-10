"""Improved text splitting with table awareness and multi-card support."""
from text_formatting import RE_HTML_TAGS, sanitize_html


def estimate_text_length(text):
    """Estimate text length without HTML tags."""
    return len(RE_HTML_TAGS.sub('', text or ''))


def estimate_table_height_factor(text):
    """
    Estimate how much vertical space tables take compared to regular text.
    Tables typically take 1.5-2x more space than equivalent character count.
    """
    if not text or '<table' not in text:
        return 1.0
    
    # Count table rows
    table_content = []
    in_table = False
    current_table = []
    
    for line in text.split('<tr>'):
        if '<table' in line:
            in_table = True
            current_table = []
        if in_table:
            current_table.append(line)
        if '</table>' in line:
            in_table = False
            table_content.extend(current_table)
    
    # Estimate: each table row adds significant height
    row_count = text.count('<tr>')
    if row_count == 0:
        return 1.0
    
    # Tables with more rows need more space per character
    # Single-column tables (enumerations) are even worse
    single_column = text.count('<td>') == row_count
    
    if single_column:
        # Single column enumeration tables need lots of vertical space
        return 1.8 + (row_count * 0.1)  # Scales with row count
    else:
        # Multi-column tables are more space-efficient
        return 1.4 + (row_count * 0.05)


def contains_complete_table(text):
    """Check if text contains at least one complete table."""
    if not text:
        return False
    return text.count('<table') == text.count('</table>') and '<table' in text


def find_table_boundaries(text):
    """Find all table start and end positions."""
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
    return tables


def split_at_table_boundary(text, target_ratio=0.4):
    """
    Split text at table boundaries, preferring to keep tables together.
    Uses weighted length that accounts for table vertical space.
    """
    if not text or '<table' not in text:
        return None
    
    tables = find_table_boundaries(text)
    if not tables:
        return None
    
    # Calculate weighted length (accounts for table height)
    def weighted_length(segment):
        base_len = estimate_text_length(segment)
        table_factor = estimate_table_height_factor(segment)
        return base_len * table_factor
    
    total_weighted = weighted_length(text)
    target_weighted = total_weighted * target_ratio
    
    best_split = None
    best_distance = float('inf')
    
    # Try splitting before each table
    for table_start, table_end in tables:
        before_len = weighted_length(text[:table_start])
        distance = abs(before_len - target_weighted)
        
        # Only consider if there's meaningful content before the table
        if before_len > total_weighted * 0.15 and distance < best_distance:
            best_distance = distance
            best_split = table_start
    
    # Try splitting after each complete table
    for table_start, table_end in tables:
        after_len = weighted_length(text[:table_end])
        distance = abs(after_len - target_weighted)
        
        # Must have meaningful content before and after
        remaining = total_weighted - after_len
        if after_len > total_weighted * 0.15 and remaining > total_weighted * 0.15:
            if distance < best_distance:
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
    
    Uses weighted length calculations that account for the vertical space
    tables consume compared to regular text.
    
    CRITICAL: First card has ~100px less vertical space due to card-attrs table.
    This means for a 2-card split, first card can fit ~40% of content, second ~60%.
    We split at 60% so first card gets 60% of text (to fill its constrained space).
    """
    if not text:
        return text, None, None
    
    text = sanitize_html(text)
    
    # Calculate weighted length (accounts for table display height)
    text_factor = estimate_table_height_factor(text)
    clean_len = estimate_text_length(text)
    weighted_len = clean_len * text_factor
    
    # Adjusted thresholds based on actual testing with spell cards
    # These are more conservative because tables take up more vertical space
    # First card has less space due to card-attrs table (~80-100px)
    single_card_limit = 700  # Reduced from 800
    double_card_limit = 1300  # Reduced significantly for two-card splits (first card constraint)
    
    # Apply table penalty to limits
    effective_single_limit = single_card_limit / text_factor
    effective_double_limit = double_card_limit / text_factor
    
    if weighted_len <= effective_single_limit:
        return text, None, None
    
    # Check if we need triple split
    if weighted_len > effective_double_limit:
        # Try table-aware split into 3 parts
        table_split = split_at_table_boundary(text, target_ratio=0.33)
        
        if table_split:
            part1 = text[:table_split].strip()
            remainder = text[table_split:].strip()
            
            # Split remainder with table awareness
            remainder_factor = estimate_table_height_factor(remainder)
            remainder_weighted = estimate_text_length(remainder) * remainder_factor
            
            if remainder_weighted > effective_single_limit:
                # Try to split remainder at table boundary
                remainder_split = split_at_table_boundary(remainder, target_ratio=0.5)
                
                if remainder_split:
                    part2 = remainder[:remainder_split].strip()
                    part3 = remainder[remainder_split:].strip()
                else:
                    # Fallback to clean text split
                    mid_pos = int(estimate_text_length(remainder) * 0.5)
                    mid_split = find_safe_breakpoint(remainder, mid_pos)
                    part2 = remainder[:mid_split].strip()
                    part3 = remainder[mid_split:].strip()
                
                if part1 and part2 and part3:
                    return sanitize_html(part1), sanitize_html(part2), sanitize_html(part3)
        
        # Fallback: split into thirds with table awareness
        target1 = int(clean_len * 0.32)  # Slightly earlier split for safety
        target2 = int(clean_len * 0.64)
        
        split1 = find_safe_breakpoint(text, target1)
        part1 = text[:split1].strip()
        remainder = text[split1:].strip()
        
        remainder_target = estimate_text_length(remainder) // 2
        split2 = find_safe_breakpoint(remainder, remainder_target)
        part2 = remainder[:split2].strip()
        part3 = remainder[split2:].strip()
        
        return sanitize_html(part1), sanitize_html(part2), sanitize_html(part3)
    
    # Double card split with table awareness
    table_split = split_at_table_boundary(text, target_ratio=0.38)  # Slightly earlier
    
    if table_split:
        part1 = text[:table_split].strip()
        part2 = text[table_split:].strip()
        return sanitize_html(part1), sanitize_html(part2), None
    
    # Regular split - put LESS text in first card since it has LESS vertical space
    # First card: ~180px text area with attrs table
    # Continuation: ~280px text area without attrs  
    # Ratio: 180/280 = 0.64, so first card should get 64% of vertical space
    # But that means it gets 36% of text (inverse ratio)
    target_pos = int(clean_len * 0.6)
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
                    # Table is too early, keep everything together
                    return text, None, None
    
    return sanitize_html(part1), sanitize_html(part2), None
