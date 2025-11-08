import re, random
from pathlib import Path
import pandas as pd
from html import escape

# Constants
N_SAMPLE_THRESH = 200
N_SAMPLE = 69
N_SAMPLE_PHRASES = [
    # 'Aura of Desecration',
    # 'advantage',
    # 'disadvantage'
]

# Precompile commonly used regex patterns for performance
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_CAPITAL_SPLIT = re.compile(r'(?<![A-Z\s])(?=[A-Z])')
RE_SENTENCE_END = re.compile(r'[.;]\s+')
RE_WHITESPACE = re.compile(r'\s+')
RE_HTML_TAG_PAIRS = re.compile(r'<(\w+)[^>]*>.*?</\1>')

def balance_html_tags(text):
    """Ensure HTML tags are properly balanced when splitting text."""
    if not text or '<' not in text:
        return text
    
    # Count opening and closing tags
    open_tags = re.findall(r'<(\w+)[^>]*>', text)
    close_tags = re.findall(r'</(\w+)>', text)
    
    # Create stack to track tag balancing
    stack = []
    for tag in open_tags:
        stack.append(tag)
    
    for tag in close_tags:
        if stack and stack[-1] == tag:
            stack.pop()
        else:
            # Unmatched closing tag, remove it
            text = re.sub(f'</{tag}>', '', text, count=1)
    
    # Close any remaining open tags
    while stack:
        tag = stack.pop()
        text += f'</{tag}>'
    
    return text

def fix_text(text):
    if not text: 
        return text

    text = re.sub(r'\.([A-Z])', r'. \1', text)
    if ':' not in text:
        return text

    m = re.match(r'^(.*?):([A-Z].*)', text)
    if not m:
        return text
    before_colon, after_colon = m.groups()

    matches = list(filter(None, RE_CAPITAL_SPLIT.split(after_colon)))
    processed = []
    for i, segment in enumerate(matches):
        if i != len(matches) - 1:
            if ',' in segment:
                head, rest = segment.split(',', 1)
                segment = f'<b>{head}</b>,{rest}'
            segment += '; '
        processed.append(segment)
    return before_colon + ': ' + ''.join(processed)

def generate_card_id(name):
    return re.sub(r'[^a-zA-Z0-9]', '', name.lower())[:10]

def parse_classes(classes_str):
    if not classes_str:
        return ""
    first = classes_str.split(',')[0].strip()
    return re.sub(r'\([^)]*\)', '', first).strip().lower()

def load_file(path):
    return Path(path).read_text(encoding='utf-8')

def replace_placeholders(template, mapping):
    for k, v in mapping.items():
        template = template.replace(f'<!--{{{{{k}}}}}-->', v)
    return template

def merge_spell_duplicates(spells_df):
    """Efficiently merge duplicate spells using pandas operations."""
    # Define helper to merge string fields safely
    def merge_texts(series):
        longest = max(series, key=lambda s: len(s or ""), default="")
        return longest.strip()

    def merge_sources(series):
        core = {'PHB', 'SRD', 'DMG'}
        parts = [s for s in series.dropna() if s and s not in core]
        seen, uniq = set(), []
        for s in parts:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        return ', '.join(uniq) if uniq else (series.dropna().iloc[0] if not series.empty else "")

    def merge_lists(series):
        all_items = []
        for v in series.dropna():
            all_items.extend([x.strip() for x in v.split(',') if x.strip()])
        seen, uniq = set(), []
        for x in all_items:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        return ', '.join(uniq)

    # Sort by Name to ensure consistent ordering before grouping
    spells_df = spells_df.sort_values('Name')
    
    merged = (
        spells_df.groupby("Name", dropna=False, sort=False)
        .agg({
            "Source": merge_sources,
            "Classes": merge_lists,
            "Optional/Variant Classes": merge_lists,
            "Subclasses": merge_lists,
            "Text": merge_texts,
            "At Higher Levels": merge_texts,
            **{col: "first" for col in spells_df.columns if col not in {
                "Name", "Source", "Classes", "Optional/Variant Classes", "Subclasses", "Text", "At Higher Levels"
            }}
        })
        .reset_index()
    )
    
    # Ensure consistent final ordering
    merged = merged.sort_values('Name').reset_index(drop=True)
    return merged.to_dict(orient="records")

def estimate_text_length(text):
    return len(RE_HTML_TAGS.sub('', text or ''))

def blend_with_black(hex_color, blend_percent=50):
    if not hex_color or hex_color.lower() == '#000000':
        return hex_color
    r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
    factor = 1 - blend_percent / 100
    return f'#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}'

def load_spells(csv_path):
    df = pd.read_csv(csv_path, encoding='utf-8').fillna("")
    
    # Ensure we include rows containing any of the sample phrases
    if len(df) > N_SAMPLE_THRESH:
        # Find rows that contain any of the sample phrases
        phrase_mask = pd.Series(False, index=df.index)
        for phrase in N_SAMPLE_PHRASES:
            # Check all text columns for the phrase
            text_columns = ['Text', 'At Higher Levels', 'Name', 'Description']
            for col in text_columns:
                if col in df.columns:
                    phrase_mask = phrase_mask | df[col].str.contains(phrase, case=False, na=False)
        
        # Get the phrase-matching rows
        phrase_rows = df[phrase_mask]
        
        # Calculate how many more rows we need for the sample
        remaining_sample = max(0, N_SAMPLE - len(phrase_rows))
        
        # Get random sample from the remaining rows (excluding phrase rows)
        if remaining_sample > 0:
            remaining_df = df[~phrase_mask]
            if len(remaining_df) > remaining_sample:
                random_sample = remaining_df.sample(n=remaining_sample, random_state=random.randint(0, 9999))
            else:
                random_sample = remaining_df
        else:
            random_sample = pd.DataFrame()
        
        # Combine phrase rows with random sample
        df = pd.concat([phrase_rows, random_sample], ignore_index=True)
        
        print(f"Loaded sample of {len(df)} spells from {csv_path} (including {len(phrase_rows)} with sample phrases)")
    else:
        print(f"Loaded all {len(df)} spells from {csv_path}")
    
    return df

def detect_broken_table(text):
    """Detect if text contains broken table with joined headers (e.g., 'aaaAaaBbb')."""
    if not text:
        return None
    
    # Multiple patterns to catch different types of broken tables
    patterns = [
        # Pattern for sequences like "CreatureDamageHealingExtra"
        r'\b[a-z]+(?:[A-Z][a-z]+){2,}\b',
        # Pattern for sequences with numbers mixed in like "d8DamageType1Acid"
        r'\b(?:[a-z]+[A-Z]|[A-Z][a-z]+|\d+){4,}\b',
        # Pattern for table-like structures with consecutive capitalized words
        r'\b(?:[A-Z][a-z]*){3,}(?:\d+[A-Z][a-z]*)*\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Find the longest match (likely the header row)
            longest_match = max(matches, key=len)
            # Extract potential table title (text before the broken headers)
            title_match = re.search(rf'([^.]*?){re.escape(longest_match)}', text)
            if title_match:
                title = title_match.group(1).strip()
                return {'headers': longest_match, 'title': title}
    return None

def sanitize_html(text):
    """Ensure text doesn't contain malformed HTML that could break the document."""
    if not text:
        return text
    
    # Fix common HTML issues
    text = re.sub(r'</br>', '<br/>', text)  # Fix incorrect </br> closing tags
    text = re.sub(r'<br\s*/?>', '<br/>', text)  # Ensure proper self-closing br tags
    
    # Fix unclosed span tags by balancing them
    open_spans = text.count('<span')
    close_spans = text.count('</span>')
    
    if open_spans > close_spans:
        # Add missing closing spans
        text += '</span>' * (open_spans - close_spans)
    elif close_spans > open_spans:
        # Remove extra closing spans
        for _ in range(close_spans - open_spans):
            text = text.replace('</span>', '', 1)
    
    # Remove any span tags that contain broken content
    text = re.sub(r'<span[^>]*>.*?</br>.*?</span>', lambda m: m.group(0).replace('</br>', '<br/>'), text)
    
    return text

def split_spell_text(text, target_length=800):
    """Split text while preserving HTML tag integrity and not breaking tables."""
    if estimate_text_length(text) < target_length:
        return sanitize_html(text), None

    # First, sanitize the input text
    text = sanitize_html(text)
    
    clean_text = RE_HTML_TAGS.sub('', text)
    total_len = len(clean_text)
    target_pos = int(total_len * 0.35)

    def find_safe_breakpoint(text, target_clean_pos):
        """Find a safe breakpoint that doesn't split HTML tags or tables."""
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
                
                # Check if we're entering or leaving a table
                if tag_buffer.startswith('<table'):
                    in_table = True
                elif tag_buffer.startswith('</table'):
                    in_table = False
                    
                # Skip tag content for clean text positioning
                continue
            elif in_tag:
                tag_buffer += char
                continue
            else:
                current_clean_pos += 1
                
            # If we're in a table, don't break until we're out of it
            if current_clean_pos >= target_clean_pos and not in_tag and not in_table:
                # Look for sentence end or whitespace, but avoid breaking tables
                for lookahead in range(i, min(len(text), i + 100)):
                    # Check if we're about to enter a table
                    if text[lookahead:lookahead+7] == '<table>':
                        # Don't break right before a table, include it in part1
                        continue
                    
                    # Look for good break points
                    if text[lookahead] in '.;' and lookahead + 1 < len(text) and text[lookahead + 1] in ' \t\n':
                        # Make sure we're not breaking a table
                        window = text[max(0, lookahead-20):min(len(text), lookahead+50)]
                        if '<table' not in window and '</table>' not in window:
                            return lookahead + 2  # Include the space after punctuation
                    elif text[lookahead] in ' \t\n' and not in_tag:
                        # Make sure we're not breaking a table
                        window = text[max(0, lookahead-20):min(len(text), lookahead+50)]
                        if '<table' not in window and '</table>' not in window:
                            return lookahead + 1
        
        # If we couldn't find a safe breakpoint, try to break after the next table if we're in one
        if in_table:
            table_end = text.find('</table>', i)
            if table_end != -1:
                return table_end + 8  # Include the </table> tag
        
        return min(len(text), target_clean_pos)

    html_break = find_safe_breakpoint(text, target_pos)
    
    # If the breakpoint would split a table, move it to after the table
    if html_break < len(text):
        # Check if we're breaking in the middle of a table
        text_before = text[:html_break]
        text_after = text[html_break:]
        
        # Count table tags before and after the break
        tables_before = text_before.count('<table')
        tables_closed_before = text_before.count('</table>')
        
        # If there's an unclosed table before the break, move break to after the table
        if tables_before > tables_closed_before:
            next_table_end = text.find('</table>', html_break)
            if next_table_end != -1:
                html_break = next_table_end + 8  # Position after </table>
    
    if not html_break:
        html_break = min(len(text), target_pos)

    part1 = sanitize_html(text[:html_break].strip())
    part2 = sanitize_html(text[html_break:].strip()) or None
    
    return part1, part2

def colorize_text(text):
    """Apply coloring to dice rolls and damage types in spell text."""
    # Damage type colors based on survey data (before 50% black blending)
    DAMAGE_COLORS_BASE = {
        'acid': '#00FF00',        # green/lime
        'bludgeoning': '#808080', # gray
        'cold': '#00FFFF',        # cyan
        'fire': '#FF0000',        # red
        'force': '#800080',       # purple (most popular)
        'lightning': '#FFFF00',   # yellow
        'necrotic': '#000000',    # black
        'piercing': '#808080',    # gray
        'poison': '#800080',      # purple
        'psychic': '#FFC0CB',     # pink
        'radiant': '#FFFFFF',     # white
        'slashing': '#808080',    # gray
        'thunder': '#808080',     # gray (most popular)
    }
    # Create blended damage colors
    DAMAGE_COLORS = {damage_type: blend_with_black(color, 50) 
                    for damage_type, color in DAMAGE_COLORS_BASE.items()}

    if not text:
        return text
    
    # First, ensure the text is properly sanitized
    text = sanitize_html(text)
    
    def replace_damage_and_dice(match):
        full_match = match.group(0)
        
        # Check if this is already inside a span (avoid double-processing)
        if '<span' in full_match and '</span>' in full_match:
            return full_match
            
        # Try to identify what we're matching
        if 'd' in full_match.lower() and any(dmg_type in full_match.lower() for dmg_type in DAMAGE_COLORS.keys()):
            # This contains both dice and damage type
            for damage_type, color in DAMAGE_COLORS.items():
                # Pattern with optional 'nonmagical' or similar modifiers between dice and damage type
                pattern = rf'(\b\d+d\d+\+?\d*\b)(?:\s+(?:nonmagical|magical))?\s+({re.escape(damage_type)}\s+damage\b)'
                damage_match = re.search(pattern, full_match, re.IGNORECASE)
                if damage_match:
                    dice_part = damage_match.group(1)
                    damage_part = damage_match.group(2)
                    return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{dice_part}</span> <span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{damage_part}</span>'
        
        # If we get here, check for damage type alone (including shorthand versions)
        for damage_type, color in DAMAGE_COLORS.items():
            # Check for both full "fire damage" and shorthand "fire" after replacement
            if damage_type in full_match.lower():
                # Check if it's a shorthand damage type (just the word itself)
                shorthand_pattern = rf'\b{re.escape(damage_type)}\b'
                shorthand_match = re.search(shorthand_pattern, full_match, re.IGNORECASE)
                if shorthand_match:
                    # Make sure this isn't part of a larger word and is likely a damage type
                    context = text[max(0, match.start()-10):min(len(text), match.end()+10)]
                    if re.search(rf'\d+d\d+.*?\b{re.escape(damage_type)}\b', context) or \
                       re.search(rf'\b{re.escape(damage_type)}\b(?:\s|$)', full_match):
                        return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{damage_type}</span>'
        
        return full_match
    
    # Process all potential damage type patterns
    processed_text = text
    
    # Build a comprehensive pattern that catches all cases
    damage_patterns = []
    for damage_type in DAMAGE_COLORS.keys():
        damage_patterns.append(rf'\b\d+d\d+\+?\d*\b(?:\s+(?:nonmagical|magical))?\s+{re.escape(damage_type)}\s+damage\b')
        damage_patterns.append(rf'\b{re.escape(damage_type)}\s+damage\b')
        damage_patterns.append(rf'[a-z]{re.escape(damage_type)}\s+damage\b')
        damage_patterns.append(rf'\b{re.escape(damage_type)}\b')
    
    combined_pattern = '|'.join(damage_patterns)
    
    if combined_pattern:
        def process_match(match):
            return replace_damage_and_dice(match)
        
        processed_text = re.sub(combined_pattern, process_match, processed_text, flags=re.IGNORECASE)
    
    # Color remaining standalone dice rolls
    def color_standalone_dice(match):
        dice_text = match.group(0)
        # Skip if dice are already within or immediately before a colored span
        start = match.start()
        window = processed_text[max(0, start - 50):start + 50]
        if '<span' in window:
            return dice_text
        color = '#0000FF'
        return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace;">{dice_text}</span>'

    processed_text = re.sub(
        r'\b\d+d\d+\+?\d*\b',
        color_standalone_dice,
        processed_text
    )

    # Final sanitization to fix any HTML issues introduced during processing
    return sanitize_html(processed_text)

def fix_broken_line_breaks(text):
    """Fix specific broken HTML patterns like </br> and malformed span tags."""
    if not text:
        return text
    
    # Fix </br> (should be <br/>)
    text = re.sub(r'</br>', '<br/>', text)
    
    # Fix malformed span tags with line breaks inside
    text = re.sub(
        r'<span[^>]*>([^<]*)</br>([^<]*)</span>', 
        r'<span style="display: block; height: 0.5em;"></span><span>\1<br/>\2</span>', 
        text
    )
    
    # Fix span tags that contain display: block with broken content
    text = re.sub(
        r'<span[^>]*display:\s*block[^>]*>.*?</br>', 
        '<span style="display: block; height: 0.5em;"></span>', 
        text
    )
    
    return text

def generate_spell_card(spell, card_template, continuation_template=None, paired_cards=None):
    card_id = generate_card_id(spell['Name'])
    lvl = spell.get('Level', '')
    school_raw = spell.get('School', '')
    
    # Extract ritual from school (e.g., "Abjuration (ritual)")
    IS_RITUAL = '(ritual)' in school_raw.lower()
    
    # FIXED: Clean school name for CSS class - remove parentheses and their contents
    school = re.sub(r'\s*\([^)]*\)', '', school_raw).strip().title()
    
    # Build spell type string with colored school name
    if lvl.lower() in ('cantrip', 0, '0'):
        spell_type = f'<span class="school-name">{school}</span> Cantrip'
    else:
        spell_type = f'{lvl}-level <span class="school-name">{school}</span>'

    # Use the spell data as-is (already replaced with fixed version if available)
    text = spell.get('Text', '')
    hl = spell.get('At Higher Levels', '')

    text = fix_text(text)
    hl = fix_text(hl)

    # main text description enhancements
    if hl:
        hl = hl.replace('At Higher Levels.','<b>At Higher Levels.</b>')
        text += "<br><br>" + hl
    
    # Note: We don't check for broken tables here anymore - that's done in main()
    
    # Replace .. with .
    text = re.sub(r'\.{2,}', '.', text)
    
    # Make empty lines half height by replacing <br><br> with smaller spacing
    text = text.replace('<br><br>', '<br><span style="display: block; height: 0.5em;"></span>')
    
    # Apply the specific fix for broken line breaks
    text = fix_broken_line_breaks(text)
    
    # Apply phrase shorthands BEFORE splitting and colorization
    PHRASE_SHORTHANDS = {
        # Damage types - FIXED: Use regex with word boundaries to ensure complete replacement
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
        # CR
        r'\bchallenge\s+ratings?\b': 'CR',
        # AC
        r'\barmor\s+class\b': 'AC',
        # HP
        r'\btemporary\s+hitpoints?\b': 'temp. HP',
        r'\btemporary\s+HP?\b': 'temp. HP',
        r'\bhitpoints?\b': 'HP',
        r'\bhit\s+points\b': 'HP',
        # Ability Scores
        r'\bStrength\b': 'STR',
        r'\bDexterity\b': 'DEX',
        r'\bConstitution\b': 'CON',
        r'\bIntelligence\b': 'INT',
        r'\bWisdom\b': 'WIS',
        r'\bCharisma\b': 'CHA',
        # Units
        r'\bfeet\b': 'ft.',
        r'\bfoot\b': 'ft.',
        r'\bhours?\b': 'h',
        r'\bminutes?\b': 'min.',
        # d20 rolls
        # r'\bwith\s+advantage\b': '⥣',
        # r'\bwith\s+disadvantage\b': '⥥',
        r'\badvantage\b': 'adv.',
        r'\bdisadvantage\b': 'disadv.',
    }
    
    # Apply all shorthand replacements using regex with case-insensitive flag
    for pattern, replacement in PHRASE_SHORTHANDS.items():
        text = re.sub(pattern, replacement, text)
    
    # Check if spell text needs to be split AFTER shorthand replacements
    text_part1, text_part2 = split_spell_text(text)
    
    # If part1 ends with an incomplete table, move the entire table to part2
    if text_part1 and text_part2:
        # Check if part1 has an unclosed table
        tables_in_part1 = text_part1.count('<table')
        tables_closed_in_part1 = text_part1.count('</table>')
        
        if tables_in_part1 > tables_closed_in_part1:
            # Find where the table starts in part1
            last_table_start = text_part1.rfind('<table')
            if last_table_start != -1:
                # Move everything from the table start to part2
                text_before_table = text_part1[:last_table_start].strip()
                text_with_table = text_part1[last_table_start:] + text_part2
                
                # Only split if we have content before the table
                if text_before_table and len(text_before_table) > 50:
                    text_part1 = text_before_table
                    text_part2 = text_with_table
                else:
                    # If there's not much content before the table, keep table in part1
                    # but don't split at all
                    text_part1 = text
                    text_part2 = None
    
    # Color damage types and dice rolls AFTER splitting and shorthand replacements
    text_part1 = colorize_text(text_part1)
    if text_part2:
        text_part2 = colorize_text(text_part2)
    
    # Sanitize HTML to prevent malformed content
    text_part1 = sanitize_html(text_part1)
    if text_part2:
        text_part2 = sanitize_html(text_part2)
    
    # primary class
    primary_class = parse_classes(spell.get('Classes', '')).title()

    # source
    source = spell.get('Source', '')
    CORE_SOURCES = ['PHB', 'SRD', 'DMG']
    # source = '' if source in CORE_SOURCES else source

    # components + materials
    components_raw = spell.get('Components', '')
    materials_match = re.search(r'\(.*?\)', components_raw)
    materials = materials_match.group(0)[1:-1] if materials_match else ""
    components = re.sub(r'\s*M\s*\(.*?\)', ' M', components_raw).strip()

    # duration + duration info
    IS_CONCENTRATION = False
    duration = spell.get('Duration', '')
    duration_info = ""
    if duration.lower().startswith('concentration'):
        IS_CONCENTRATION = True
        match = re.match(r'Concentration,?\s*(up to .*)', duration, re.IGNORECASE)
        if match:
            duration = match.group(1).strip()
    for k, v in {
        'Instantaneous': 'Instant',
        'up to ': '',
        'minutes': 'min.',
        'minute': 'min.',
        'hours': 'h',
        'hour': 'h',
        'year': 'yr',
        'Until dispelled': 'Permanent',
        '(see below)': '',
        'Instant or': 'Instant /',
        'Concentration': 'Indefinite',
    }.items():
        duration = duration.replace(k,v)

    # range - extract parenthetical content if present
    spell_range = spell.get('Range', '')
    range_label = "Range"
    range_class = ""

    # Extended unit mappings
    UNIT_MAP = {
        'foot': 'ft.', 'feet': 'ft.', 
        'mile': 'mi.', 'miles': 'mi.',
        'yard': 'yd.', 'yards': 'yd.',
        'meter': 'm', 'meters': 'm',
        'kilometer': 'km', 'kilometers': 'km'
    }

    # Special cases for self/other with areas
    special_cases = [
        (r'^Self\s*\((.+)\)$', 'Self'),  # Self (30-foot radius)
        (r'^Touch\s*\((.+)\)$', 'Touch'), # Touch (5-foot radius)
    ]

    # Check for special cases first
    for pattern, base_label in special_cases:
        special_match = re.match(pattern, spell_range)
        if special_match:
            range_label = base_label
            area_detail = special_match.group(1)
            
            # Extract area information
            area_match = re.search(r'(\d+)\s*-?\s*(\w+)(?:\s+(\w+))?', area_detail)
            if area_match:
                distance = area_match.group(1)
                unit = area_match.group(2).lower()
                area_type = area_match.group(3) or "radius"  # default to radius
                
                if unit in UNIT_MAP:
                    spell_range = f"{distance} {UNIT_MAP[unit]}"
                else:
                    spell_range = f"{distance} {unit}"
                
                range_label = f"{range_label} {area_type.title()}"
                range_class = "range-special"
            break
    else:
        # Regular parentheses case
        paren_match = re.match(r'^(.+?)\s*\((.+?)\)$', spell_range)
        if paren_match:
            range_label = paren_match.group(1).strip()
            range_detail = paren_match.group(2).strip()
            
            area_match = re.match(r'(\d+)\s*-?\s*(\w+)(?:\s+(.+))?', range_detail)
            if area_match:
                distance = area_match.group(1)
                unit = area_match.group(2).lower()
                area_type = area_match.group(3) or ""
                
                if unit in UNIT_MAP:
                    spell_range = f"{distance} {UNIT_MAP[unit]}"
                
                if area_type:
                    range_label = f"{range_label} {area_type.title()}"
                    range_class = "range-special"

    # Convert all units in the final string
    for old_unit, new_unit in UNIT_MAP.items():
        patterns = [
            rf'(\d+)-{old_unit}\b',
            rf'(\d+)\s+{old_unit}\b'
        ]
        for pattern in patterns:
            spell_range = re.sub(pattern, rf'\1 {new_unit}', spell_range)

    # Final cleanup
    spell_range = re.sub(r'\s+', ' ', spell_range).strip()
    # range_label = range_label.replace('Self Emanation', 'Emanation')
    range_label = range_label.replace('Self ', '')

    # casting time
    casting_time = spell.get('Casting Time', '')
    casting_time = casting_time.replace('Min','min')
    casting_time = casting_time.replace('Day','day')
    casting_time = casting_time.replace('Year','year')
    casting_time = casting_time.replace('Hr.','h')
    casting_time = casting_time.replace('hours','h')

    # name with smart line breaking
    name_raw = spell['Name']
    name = name_raw  # Remove smart breaking for now, let browser handle it

    # Labels for special attributes
    casting_label = "Ritual" if IS_RITUAL else "Casting Time"
    duration_label = "Concentration" if IS_CONCENTRATION else "Duration"

    # Remove pre-calculated font sizes - will be done by font_adjuster
    
    mapping = {
        "CARD_ID": card_id,
        "PRIMARY_CLASS": '', # primary_class,
    "NAME": name,
        "CASTING": casting_time,
        "CASTING_CLASS": "ritual" if IS_RITUAL else "",
        "CASTING_LABEL": casting_label,
        "RANGE": spell_range,
        "RANGE_CLASS": range_class,
        "RANGE_LABEL": range_label,
        "COMPONENTS": components,
        "DURATION": duration,
        "DURATION_CLASS": "concentration" if IS_CONCENTRATION else "",
        "DURATION_LABEL": duration_label,
        "MATERIAL_COMPONENTS": materials,
        "DURATION_INFO": duration_info,
        "TEXT": text_part1,
        "SOURCE": source,
        "SPELL_TYPE": spell_type,
        "SCHOOL": school
    }

    # Sanitize all mapping values to prevent HTML injection
    for key, value in mapping.items():
        if key not in ["TEXT", "SPELL_TYPE"]:  # These already contain intentional HTML
            mapping[key] = escape(str(value))

    cards = [replace_placeholders(card_template, mapping)]
    
    # Generate continuation card if needed
    if text_part2 and continuation_template:
        continuation_mapping = {
            "CARD_ID": card_id,
            "NAME": name,
            "TEXT": text_part2,
            "PRIMARY_CLASS": '',
            "SOURCE": source,
            "SPELL_TYPE": spell_type,
            "SCHOOL": school
        }
        
        # Sanitize continuation mapping
        for key, value in continuation_mapping.items():
            if key not in ["TEXT", "SPELL_TYPE"]:
                continuation_mapping[key] = escape(str(value))
                
        cards.append(replace_placeholders(continuation_template, continuation_mapping))
    
    return ''.join(cards)

def main():
    base = Path("templates")
    paths = {
        "csv": Path("data/Spells-various.csv"),
        "fixed_csv": Path("data/Spells-fixed.csv"),  # Add fixed spells CSV
        "css": base / "style.css",
        "page": base / "page.html",
        "card": base / "card.html",
        "card_cont": base / "card-continuation.html",
        "js": base / "autosize.js",
        "out_html": Path("out/spell_cards.html"),
        "out_js": Path("out/autosize.js")
    }

    css, page, card, card_cont, js = [load_file(p) for p in (paths["css"], paths["page"], paths["card"], paths["card_cont"], paths["js"])]

    # FIX CSS syntax error
    css = css.replace("display: ver('-webkit-box');", "display: -webkit-box;")

    # Load fixed spells if available
    fixed_spells = {}
    try:
        fixed_df = pd.read_csv(paths["fixed_csv"], encoding='utf-8').fillna("")
        for _, spell in fixed_df.iterrows():
            fixed_spells[spell['Name']] = spell.to_dict()
        print(f"Loaded {len(fixed_spells)} fixed spells from {paths['fixed_csv']}")
    except Exception as e:
        print(f"Could not load fixed spells: {e}")

    spells_df = load_spells(paths["csv"])
    merged_spells = merge_spell_duplicates(spells_df)
    print(f"Merged {len(spells_df)} → {len(merged_spells)} unique spells")

    # Track spells with broken tables that need fixing
    broken_table_spells = []
    paired_cards = {}  # Track continuation pairs for font size consistency
    
    def generate_and_track(spell):
        # Use fixed spell data if available, otherwise use original
        spell_name = spell['Name']
        if spell_name in fixed_spells:
            print(f"Using fixed data for {spell_name}")
            spell = fixed_spells[spell_name]
        
        card_html = generate_spell_card(spell, card, card_cont, paired_cards)
        
        # Check if spell text has broken table and wasn't fixed
        text = spell.get('Text', '')
        table_info = detect_broken_table(text)
        if table_info and spell_name not in fixed_spells:
            broken_table_spells.append((spell_name, table_info['headers']))
            
        return card_html
    
    # Generate cards
    cards = [generate_and_track(spell) for spell in merged_spells]
    
    # Print spells with broken tables that still need fixing
    if broken_table_spells:
        print(f"\nSpells with broken tables needing fixes ({len(broken_table_spells)}):")
        for name, headers in sorted(set(broken_table_spells)):
            print(f"  - {name}: {headers}")

    html = page.replace('/*{{STYLES}}*/', css).replace('<!--{{CARDS}}-->', ''.join(cards))
    Path("out").mkdir(exist_ok=True)
    paths["out_html"].write_text(html, encoding='utf-8')
    paths["out_js"].write_text(js, encoding='utf-8')

    print(f"Exported {len(cards)} cards to {paths['out_html']}")

if __name__ == "__main__":
    main()

# TODO: the last card on in the resulting file seems to be scrambled, an amalgamation of many cards - # FIXME
# TODO: broken tables fixing - detect long words with aaaAaa patterns (joined table headers);