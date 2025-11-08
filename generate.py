import csv, re, os
from collections import defaultdict

SYMBOL_CONCENTRATION = '<span class="diamond"><span class="c">C</span></span>'

def fix_text(text):
    if not text: 
        return text
    
    # Additional cosmetics
    text = re.sub(r'\.([A-Z])', r'. \1', text)

    if ':' not in text:
        return text

    # Split the text into two parts at the first ':' followed immediately with a letter
    content = re.match(r'^(.*?):([A-Z].*)', text)
    if not content:
        return text

    before_colon, after_colon = content.group(1), content.group(2)

    # Split at capital letters not preceded by another capital letter or whitespace
    pattern = r'(?<![A-Z\s])(?=[A-Z])'
    matches = re.split(pattern, after_colon)
    matches = list(filter(None, matches))

    # Process matches
    processed_matches = []
    for i, content in enumerate(matches):

        # Boldify the paratitle and append ';' (except the last match)
        if i != len(matches) - 1:
            if ',' in content:
                # Boldify the match
                paratitle, rest = content.split(',', 1)
                content = '<b>' + paratitle + '</b>,' + rest
            content += '; '

        processed_matches.append(content)

    # Combine
    result = before_colon + ': ' + ''.join(processed_matches)

    return result

def generate_card_id(name):
    return re.sub(r'[^a-zA-Z0-9]', '', name.lower())[:10]

def parse_classes(classes_str):
    if not classes_str:
        return ""
    first = classes_str.split(',')[0].strip()
    first = re.sub(r'\([^)]*\)', '', first).strip()
    return first.lower()

def load_file(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def replace_placeholders(template, mapping):
    for key, value in mapping.items():
        template = template.replace(f'<!--{{{{{key}}}}}-->', value)
    return template

def merge_spell_duplicates(spell_rows):
    """
    Merge duplicate spells by name. Combines metadata from multiple sources.
    Returns a list of merged spell dictionaries.
    """
    spells_by_name = defaultdict(list)
    
    # Group spells by name
    for spell in spell_rows:
        spells_by_name[spell['Name']].append(spell)
    
    merged_spells = []
    
    for spell_name, occurrences in spells_by_name.items():
        if len(occurrences) == 1:
            # No duplicates, use as-is
            merged_spells.append(occurrences[0])
            continue
        
        # Multiple occurrences - merge them
        primary = occurrences[0].copy()
        
        # Collect all sources
        sources = [occ.get('Source', '') for occ in occurrences if occ.get('Source')]
        # Remove duplicates and core sources
        CORE_SOURCES = {'PHB', 'SRD', 'DMG'}
        unique_sources = []
        for src in sources:
            if src not in unique_sources and src not in CORE_SOURCES:
                unique_sources.append(src)
        primary['Source'] = ', '.join(unique_sources) if unique_sources else sources[0]
        
        # Merge additive fields (classes, subclasses, etc.)
        def merge_list_field(field_name):
            all_items = []
            for occ in occurrences:
                field_val = occ.get(field_name, '')
                if field_val:
                    # Split by comma and clean
                    items = [item.strip() for item in field_val.split(',')]
                    all_items.extend(items)
            # Deduplicate while preserving order
            seen = set()
            unique = []
            for item in all_items:
                if item and item not in seen:
                    seen.add(item)
                    unique.append(item)
            return ', '.join(unique)
        
        primary['Classes'] = merge_list_field('Classes')
        primary['Optional/Variant Classes'] = merge_list_field('Optional/Variant Classes')
        primary['Subclasses'] = merge_list_field('Subclasses')
        
        # For text content, use the longest/most detailed version
        best_text = primary.get('Text', '')
        best_hl = primary.get('At Higher Levels', '')
        
        for occ in occurrences:
            occ_text = occ.get('Text', '')
            occ_hl = occ.get('At Higher Levels', '')
            
            # Prefer longer text (more detailed)
            if len(occ_text) > len(best_text):
                best_text = occ_text
            if len(occ_hl) > len(best_hl):
                best_hl = occ_hl
        
        primary['Text'] = best_text
        primary['At Higher Levels'] = best_hl
        
        merged_spells.append(primary)
    
    return merged_spells

def estimate_text_length(text):
    """Rough estimate of how much space text will take."""
    # Remove HTML tags for counting
    clean_text = re.sub(r'<[^>]+>', '', text)
    return len(clean_text)

def split_spell_text(text, target_length=800):
    """
    Split long spell text into two parts at a reasonable break point.
    Aims for 45%/55% split, preferring sentence endings (. or ;) over other whitespace.
    Returns (part1, part2) or (text, None) if no split needed.
    """
    if estimate_text_length(text) < target_length:
        return text, None
    
    # Remove HTML tags to work with clean text
    clean_text = re.sub(r'<[^>]+>', '', text)
    total_length = len(clean_text)
    target_pos = int(total_length * 0.45)
    
    # Find all potential break points with priorities
    sentence_ends = []  # Priority: sentence endings (. or ;)
    whitespaces = []     # Fallback: any whitespace
    
    # Find sentence endings
    for match in re.finditer(r'[.;]\s+', text):
        # Map position from original text (with HTML) to clean text position
        html_pos = match.end()
        clean_pos = len(re.sub(r'<[^>]+>', '', text[:html_pos]))
        sentence_ends.append((html_pos, clean_pos))
    
    # Find all whitespace positions
    for match in re.finditer(r'\s+', text):
        html_pos = match.end()
        clean_pos = len(re.sub(r'<[^>]+>', '', text[:html_pos]))
        whitespaces.append((html_pos, clean_pos))
    
    # First try to find best sentence ending near 45%
    best_break = None
    best_distance = float('inf')
    
    for html_pos, clean_pos in sentence_ends:
        distance = abs(clean_pos - target_pos)
        if distance < best_distance:
            best_distance = distance
            best_break = html_pos
    
    # If no sentence ending found within reasonable range, use any whitespace
    if best_break is None or best_distance > total_length * 0.2:  # If >20% away from target
        best_distance = float('inf')
        for html_pos, clean_pos in whitespaces:
            distance = abs(clean_pos - target_pos)
            if distance < best_distance:
                best_distance = distance
                best_break = html_pos
    
    # If still no break found, just split at target
    if best_break is None:
        # Map target position back to HTML
        char_count = 0
        html_pos = 0
        in_tag = False
        
        while html_pos < len(text) and char_count < target_pos:
            if text[html_pos] == '<':
                in_tag = True
            elif text[html_pos] == '>':
                in_tag = False
            elif not in_tag:
                char_count += 1
            html_pos += 1
        
        best_break = html_pos
    
    part1 = text[:best_break].strip()
    part2 = text[best_break:].strip()
    
    return part1, part2 if part2 else None

def generate_spell_card(spell, card_template, continuation_template=None):
    card_id = generate_card_id(spell['Name'])
    lvl = spell.get('Level', '')
    school_raw = spell.get('School', '')
    
    # Extract ritual from school (e.g., "Abjuration (ritual)")
    IS_RITUAL = '(ritual)' in school_raw.lower()
    school = school_raw.replace('(ritual)', '').replace('(Ritual)', '').strip().title()
    
    # Build spell type string with colored school name
    if lvl.lower() in ('cantrip', 0, '0'):
        spell_type = f'<span class="school-name">{school}</span> Cantrip'
    else:
        spell_type = f'{lvl}-level <span class="school-name">{school}</span>'

    text = fix_text(spell.get('Text', ''))
    hl = fix_text(spell.get('At Higher Levels', ''))
    if hl:
        hl = hl.replace('At Higher Levels.','<b>At Higher Levels.</b>')
        text += "<br><br>" + hl
    
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

    # casting time
    casting_time = spell.get('Casting Time', '')
    casting_time = casting_time.replace('Min','min')
    casting_time = casting_time.replace('Day','day')
    casting_time = casting_time.replace('Year','year')
    casting_time = casting_time.replace('Hr.','hours')

    # name
    name = spell['Name']

    # Labels for special attributes
    casting_label = "Ritual" if IS_RITUAL else "Casting Time"
    duration_label = "Concentration" if IS_CONCENTRATION else "Duration"

    # Check if spell text needs to be split
    text_part1, text_part2 = split_spell_text(text)

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
        cards.append(replace_placeholders(continuation_template, continuation_mapping))
    
    return ''.join(cards)

def main():
    csv_path = 'data/Spells-various.csv'
    css_path = 'templates/style.css'
    page_path = 'templates/page.html'
    card_path = 'templates/card.html'
    card_continuation_path = 'templates/card-continuation.html'
    js_path = 'templates/autosize.js'
    out_path = 'out/spell_cards.html'
    out_js_path = 'out/autosize.js'

    css = load_file(css_path)
    page_template = load_file(page_path)
    card_template = load_file(card_path)
    continuation_template = load_file(card_continuation_path)
    js_content = load_file(js_path)

    # Read and merge spell data
    spell_rows = []
    with open(csv_path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            cleaned = {k: v.strip() if v else "" for k, v in row.items()}
            spell_rows.append(cleaned)
    
    # Merge duplicates
    merged_spells = merge_spell_duplicates(spell_rows)
    print(f"Merged {len(spell_rows)} spell entries into {len(merged_spells)} unique spells")
    
    # Generate cards
    cards = [generate_spell_card(spell, card_template, continuation_template) for spell in merged_spells]

    html_output = (page_template
        .replace('/*{{STYLES}}*/', css)
        .replace('<!--{{CARDS}}-->', ''.join(cards)))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # Write HTML
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    # Copy JS to output
    with open(out_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"Generated {len(cards)} cards → {out_path}")

if __name__ == "__main__":
    main()
