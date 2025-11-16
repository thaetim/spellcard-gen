"""Text formatting and HTML processing utilities."""
import re

# Precompiled regex patterns
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_CAPITAL_SPLIT = re.compile(r'(?<![A-Z\s])(?=[A-Z])')
RE_SENTENCE_END = re.compile(r'[.;]\s+')
RE_WHITESPACE = re.compile(r'\s+')

def fix_enumeration_formatting(text, print_spell=None):
    """Fix enumeration spacing and formatting in spell text."""
    if not text: 
        return text

    text = re.sub(r'\.([A-Z])', r'. \1', text)
    if ':' not in text:
        return text

    m = re.match(r'^(.*?):([A-Z].*)', text)
    if not m:
        return text
    elif print_spell:
        print(f'Fixing enumeration in {print_spell}')
    before_colon, after_colon = m.groups()

    # Split using RE_CAPITAL_SPLIT to detect enumerations
    matches = list(filter(None, RE_CAPITAL_SPLIT.split(after_colon)))
    
    # Convert to table if we have multiple enumeration items
    if len(matches) > 1:
        table_rows = ''.join(f'<tr><td>► {match.strip()}</td></tr>' for match in matches[:-1])
        return before_colon + ':<table>' + table_rows + '</table>' + matches[-1]
    
    # Original formatting for other cases
    processed = []
    for i, segment in enumerate(matches):
        if i != len(matches) - 1:
            if ',' in segment:
                head, rest = segment.split(',', 1)
                segment = f'<b>{head}</b>,{rest}'
            segment += '; '
        processed.append(segment)
    return before_colon + ': ' + ''.join(processed)

def sanitize_html(text):
    """Ensure HTML tags are properly balanced and formatted."""
    if not text:
        return text
    
    text = re.sub(r'</br>', '<br/>', text)
    text = re.sub(r'<br\s*/?>', '<br/>', text)
    
    open_spans = text.count('<span')
    close_spans = text.count('</span>')
    
    if open_spans > close_spans:
        text += '</span>' * (open_spans - close_spans)
    elif close_spans > open_spans:
        for _ in range(close_spans - open_spans):
            text = text.replace('</span>', '', 1)
    
    text = re.sub(r'<span[^>]*>.*?</br>.*?</span>', lambda m: m.group(0).replace('</br>', '<br/>'), text)
    
    return text


def fix_broken_line_breaks(text):
    """Fix specific broken HTML patterns like </br> and malformed span tags."""
    if not text:
        return text
    
    for pattern, repl in {
        r'<br/>': '<br>',
        r'</br>': '<br>',
        r'<br><br>': '<br>',
        r'<span[^>]*>([^<]*)<br>([^<]*)</span>': r'<span style="display: block; height: 0.5em;"></span><span>\1<br/>\2</span>', 
        r'<br><span style="display: block; height: 0.5em;"></span><br><table': '<span style="display: block; height: 0.5em;"></span><table'
    }.items():
        text = re.sub(pattern, repl, text)

    single = '<span style="display: block; height: 0.5em;"></span>'
    # pattern: match the span, then (?:\s*same span)* to catch repeats with optional whitespace/newlines
    pattern = re.compile(r'(?:' + re.escape(single) + r')(?:\s*(?:' + re.escape(single) + r'))+', flags=re.IGNORECASE)
    # collapse repeats to a single span
    text = pattern.sub(single, text)

    
    return text


def estimate_text_length(text):
    """Estimate text length without HTML tags."""
    return len(RE_HTML_TAGS.sub('', text or ''))

def split_spell_size(text, target_length=800):
    """Return 1, 2, or 3 indicating how many parts split_spell_text would produce.

    Heuristic mirrors original splitting logic:
    - If cleaned length < target_length -> 1
    - Else compute first-part cutoff at ~36% of cleaned length.
      If remainder after a safe breakpoint is short -> 2
    - If remainder is very long (>1.5 * target_length) -> 3
    """
    if not text:
        return 'single'

    txt = sanitize_html(text)
    clean = RE_HTML_TAGS.sub('', txt)
    total_len = len(clean)
    if total_len < target_length:
        return 'single'

    # approximate target positions
    first_target = int(total_len * 0.36)

    def find_safe_breakpoint_cleaned(html, target_clean_pos):
        current_clean = 0
        in_tag = False
        in_table = False
        tag_buf = ""
        for i, ch in enumerate(html):
            if ch == '<':
                in_tag = True
                tag_buf = '<'
            elif ch == '>' and in_tag:
                in_tag = False
                tag_buf += '>'
                if tag_buf.startswith('<table'):
                    in_table = True
                elif tag_buf.startswith('</table'):
                    in_table = False
                tag_buf = ""
                continue
            elif in_tag:
                tag_buf += ch
                continue
            else:
                current_clean += 1

            if current_clean >= target_clean_pos and not in_tag and not in_table:
                # try to return a breakpoint nearby (prefer sentence end or whitespace)
                look_end = min(len(html), i + 100)
                for j in range(i, look_end):
                    if html[j] in '.;' and j + 1 < len(html) and html[j+1] in ' \t\n':
                        window = html[max(0, j-20):min(len(html), j+50)]
                        if '<table' not in window and '</table>' not in window:
                            return j + 2
                    if html[j] in ' \t\n':
                        window = html[max(0, j-20):min(len(html), j+50)]
                        if '<table' not in window and '</table>' not in window:
                            return j + 1
        # fallback: if still inside a table, try to jump to its end
        if in_table:
            end = html.find('</table>', i)
            if end != -1:
                return end + 8
        return min(len(html), target_clean_pos)

    first_break = find_safe_breakpoint_cleaned(txt, first_target)
    if first_break >= len(txt):
        return 'single'

    # estimate lengths of parts by removing tags
    part1_clean_len = len(RE_HTML_TAGS.sub('', txt[:first_break]))
    part2_clean_len = len(RE_HTML_TAGS.sub('', txt[first_break:]))

    # classify some exceptions explicitly
    EXPLICIT_CARD_CLASSIFICATION = {
        'single': {},
        'double': {'octarine spray'},
        'triple': {}
    }
    for card_type, card_titles in EXPLICIT_CARD_CLASSIFICATION.items():
        if any(card_title in text.lower() for card_title in card_titles):
            return card_type

    # if part2 is short enough to fit in one card -> 2
    if part2_clean_len <= target_length:
        return 'double'

    # if part2 is long (>1.5 * target_length) -> 3
    if part2_clean_len > target_length * 1.5:
        return 'triple'

    # default: split into 2 parts
    return 'double'

def split_spell_text(text, target_length=800, max_parts=3):
    """Split text into 1-3 parts while preserving HTML tag integrity.
    
    Returns tuple of (part1, part2, part3) where part2/part3 may be None.
    First card has ~100px less vertical space due to card-attrs table.
    """
    if estimate_text_length(text) < target_length:
        return sanitize_html(text), None, None

    text = sanitize_html(text)
    clean_text = RE_HTML_TAGS.sub('', text)
    total_len = len(clean_text)
    # ADJUST THIS: First card gets 36% of text (has less vertical space)
    # Lower = less text in first card, Higher = more text in first card
    # Range: 0.30-0.42 depending on your content
    target_pos = int(total_len * 0.36)

    def find_safe_breakpoint(text, target_clean_pos):
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
                
            if current_clean_pos >= target_clean_pos and not in_tag and not in_table:
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
        
        return min(len(text), target_clean_pos)

    html_break = find_safe_breakpoint(text, target_pos)
    
    if html_break < len(text):
        text_before = text[:html_break]
        tables_in_part1 = text_before.count('<table')
        tables_closed_in_part1 = text_before.count('</table>')
        
        if tables_in_part1 > tables_closed_in_part1:
            next_table_end = text.find('</table>', html_break)
            if next_table_end != -1:
                html_break = next_table_end + 8
    
    if not html_break:
        html_break = min(len(text), target_pos)

    part1 = sanitize_html(text[:html_break].strip())
    part2 = sanitize_html(text[html_break:].strip()) or None
    
    # Move entire tables to part2 if split mid-table
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
                    part1 = text
                    part2 = None
    
    # Check if part2 needs further splitting for triple card
    part3 = None
    if part2 and estimate_text_length(part2) > target_length * 1.5:
        # Split part2 roughly in half
        part2_clean = RE_HTML_TAGS.sub('', part2)
        part2_len = len(part2_clean)
        part2_split_pos = int(part2_len * 0.5)
        
        part2_break = find_safe_breakpoint(part2, part2_split_pos)
        if part2_break and part2_break < len(part2):
            part3 = sanitize_html(part2[part2_break:].strip())
            part2 = sanitize_html(part2[:part2_break].strip())
    
    return part1, part2, part3


def apply_phrase_shorthands(text):
    """Apply abbreviations to common D&D phrases. Damage-type words are
    replaced only when preceded by a dice roll (e.g., '1d8 fire' or
    '2d6 + 14 cold'). Supports dice sequences with optional +/− numeric modifiers."""
    # Damage-type replacements — only when preceded by a dice sequence
    damage_patterns = {
        r'\bacids?\s+damage\b': 'acid',
        r'\bbludgeonings?\s+damage\b': 'bludgeoning',
        r'\bcolds?\s+damage\b': 'cold',
        r'\bfires?\s+damage\b': 'fire',
        r'\bforces?\s+damage\b': 'force',
        r'\blightnings?\s+damage\b': 'lightning',
        r'\bnecrotics?\s+damage\b': 'necrotic',
        r'\bpiercings?\s+damage\b': 'piercing',
        r'\bpoisons?\s+damage\b': 'poison',
        r'\bpsychics?\s+damage\b': 'psychic',
        r'\bradiants?\s+damage\b': 'radiant',
        r'\bslashings?\s+damage\b': 'slashing',
        r'\bthunders?\s+damage\b': 'thunder',
    }

    # Other global shorthand replacements (applied anywhere)
    PHRASE_SHORTHANDS = {
        r'\bchallenge\s+ratings?\b': 'CR',
        r'\barmor\s+class\b': 'AC',
        r'\btemporary\s+hitpoints?\b': 'temp. HP',
        r'\btemporary\s+HP?\b': 'temp. HP',
        r'\bhitpoints?\b': 'HP',
        r'\bhit\s+points\b': 'HP',
        r'\bStrength\b': 'STR',
        r'\bDexterity\b': 'DEX',
        r'\bConstitution\b': 'CON',
        r'\bIntelligence\b': 'INT',
        r'\bWisdom\b': 'WIS',
        r'\bCharisma\b': 'CHA',
        r'\bfeet\b': 'ft.',
        r'\bfoot\b': 'ft.',
        r'\bhours?\b': 'h',
        r'\bminutes?\b': 'min.',
        r'\badvantage\b': 'adv.',
        r'\bdisadvantage\b': 'disadv.',
        r'\bcritical hit\b': 'crit',
        r'__INSET_0__': '',
    }

    # Dice-sequence pattern that allows:
    # - one or more dice terms: \d+d\d+
    # - optionally followed by zero or more "+ 3d6" or "- 14" style modifiers
    # This merges your broader modifier support so flat integers like "+ 14" are allowed.
    dice_seq = r'(?:\s*\d+d\d+\s*(?:[+-]\s*(?:\d+d\d+|\d+)\s*)*)'

    # For each damage pattern, only replace when it is immediately preceded by a dice sequence.
    # We capture the dice sequence and replace the whole match with "dice-seq <abbr>".
    for pattern, replacement in damage_patterns.items():
        combined_re = re.compile(r'(' + dice_seq + r')' + r'(' + pattern + r')', flags=re.IGNORECASE)
        def _repl(m):
            # Preserve original spacing of the captured dice sequence, then append a single space + replacement
            dice_part = m.group(1).rstrip()
            return dice_part + ' ' + replacement
        text = combined_re.sub(_repl, text)

    # Apply the other global replacements case-insensitively
    for pattern, replacement in PHRASE_SHORTHANDS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text
