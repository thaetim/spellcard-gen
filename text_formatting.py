"""Text formatting and HTML processing utilities."""
import re

# Precompiled regex patterns
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_CAPITAL_SPLIT = re.compile(r'(?<![A-Z\s])(?=[A-Z])')
RE_SENTENCE_END = re.compile(r'[.;]\s+')
RE_WHITESPACE = re.compile(r'\s+')

def fix_text(text, print_spell = None):
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
        table_rows = ''.join(f'<tr><td>- {match.strip()}</td></tr>' for match in matches[:-1])
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
    
    text = re.sub(r'</br>', '<br/>', text)
    text = re.sub(
        r'<span[^>]*>([^<]*)</br>([^<]*)</span>', 
        r'<span style="display: block; height: 0.5em;"></span><span>\1<br/>\2</span>', 
        text
    )
    text = re.sub(
        r'<span[^>]*display:\s*block[^>]*>.*?</br>', 
        '<span style="display: block; height: 0.5em;"></span>', 
        text
    )
    
    return text


def estimate_text_length(text):
    """Estimate text length without HTML tags."""
    return len(RE_HTML_TAGS.sub('', text or ''))


def split_spell_text(text, target_length=800):
    """Split text while preserving HTML tag integrity and not breaking tables.
    
    First card has ~100px less vertical space due to card-attrs table,
    so it needs LESS text to fill properly. Split at 36% to balance density.
    """
    if estimate_text_length(text) < target_length:
        return sanitize_html(text), None

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
    
    return part1, part2


def apply_phrase_shorthands(text):
    """Apply abbreviations to common D&D phrases."""
    PHRASE_SHORTHANDS = {
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
    
    for pattern, replacement in PHRASE_SHORTHANDS.items():
        text = re.sub(pattern, replacement, text)
    
    return text
