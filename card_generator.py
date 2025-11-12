"""Spell card generation and formatting."""
import re
from html import escape
from text_formatting import fix_text, sanitize_html, split_spell_text, apply_phrase_shorthands, fix_broken_line_breaks
from spell_styling import colorize_text


def generate_card_id(name):
    """Generate a unique HTML-safe ID from spell name."""
    return re.sub(r'[^a-zA-Z0-9]', '', name.lower())[:10]


def parse_classes(classes_str):
    """Extract primary class from classes string."""
    if not classes_str:
        return ""
    first = classes_str.split(',')[0].strip()
    return re.sub(r'\([^)]*\)', '', first).strip().lower()


def parse_duration(duration):
    """Parse duration string and extract concentration flag."""
    is_concentration = False
    duration_text = duration
    
    if duration.lower().startswith('concentration'):
        is_concentration = True
        match = re.match(r'Concentration,?\s*(up to .*)', duration, re.IGNORECASE)
        if match:
            duration_text = match.group(1).strip()
    
    replacements = {
        'Instantaneous': 'Instant',
        'up to ': '',
        'Up to ': '',
        'minutes': 'min.',
        'minute': 'min.',
        'hours': 'h',
        'hour': 'h',
        'year': 'yr',
        'Until dispelled': 'Permanent',
        '(see below)': '',
        # 'Instant or': 'Instant /',
        'Instant or': 'In. /', # FIXME
        'Concentration': 'Indefinite',
    }
    
    for old, new in replacements.items():
        duration_text = duration_text.replace(old, new)
    
    return duration_text, is_concentration


def parse_range(spell_range):
    """Parse range string and extract area information."""
    range_label = "Range"
    range_class = ""
    range_text = spell_range
    
    UNIT_MAP = {
        'foot': 'ft.', 'feet': 'ft.', 
        'mile': 'mi.', 'miles': 'mi.',
        'yard': 'yd.', 'yards': 'yd.',
        'meter': 'm', 'meters': 'm',
        'kilometer': 'km', 'kilometers': 'km'
    }
    
    special_cases = [
        (r'^Self\s*\((.+)\)$', 'Self'),
        (r'^Touch\s*\((.+)\)$', 'Touch'),
    ]
    
    for pattern, base_label in special_cases:
        special_match = re.match(pattern, spell_range)
        if special_match:
            range_label = base_label
            area_detail = special_match.group(1)
            
            area_match = re.search(r'(\d+)\s*-?\s*(\w+)(?:\s+(\w+))?', area_detail)
            if area_match:
                distance = area_match.group(1)
                unit = area_match.group(2).lower()
                area_type = area_match.group(3) or "radius"
                
                range_text = f"{distance} {UNIT_MAP.get(unit, unit)}"
                range_label = f"{range_label} {area_type.title()}"
                range_class = "range-special"
            break
    else:
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
                    range_text = f"{distance} {UNIT_MAP[unit]}"
                
                if area_type:
                    range_label = f"{range_label} {area_type.title()}"
                    range_class = "range-special"
    
    for old_unit, new_unit in UNIT_MAP.items():
        patterns = [rf'(\d+)-{old_unit}\b', rf'(\d+)\s+{old_unit}\b']
        for pattern in patterns:
            range_text = re.sub(pattern, rf'\1 {new_unit}', range_text)
    
    range_text = re.sub(r'\s+', ' ', range_text).strip()
    range_label = range_label.replace('Self ', '')
    
    return range_text, range_label, range_class


def parse_components(components_raw):
    """Extract components and materials from components string."""
    materials_match = re.search(r'\(.*?\)', components_raw)
    materials = materials_match.group(0)[1:-1] if materials_match else ""
    components = re.sub(r'\s*M\s*\(.*?\)', ' M', components_raw).strip()
    return components, materials


def replace_placeholders(template, mapping):
    """Replace placeholders in template with values from mapping."""
    for k, v in mapping.items():
        template = template.replace(f'<!--{{{{{k}}}}}-->', v)
    return template


def generate_spell_card(spell, card_template, continuation_template=None, paired_cards=None, card_double_template=None, card_striple_template=None):
    """Generate HTML for a spell card with optional continuation or wide cards."""
    card_id = generate_card_id(spell['Name'])
    lvl = spell.get('Level', '')
    school_raw = spell.get('School', '')
    
    is_ritual = '(ritual)' in school_raw.lower()
    school = re.sub(r'\s*\([^)]*\)', '', school_raw).strip().title()
    
    if lvl.lower() in ('cantrip', 0, '0'):
        spell_type = f'<span class="school-name">{school}</span> Cantrip'
    else:
        spell_type = f'{lvl}-level <span class="school-name">{school}</span>'

    text = spell.get('Text', '')
    hl = spell.get('At Higher Levels', '')
    
    text = fix_text(text, spell['Name'])
    hl = fix_text(hl)
    
    if hl:
        hl = hl.replace('At Higher Levels.', '<b>At Higher Levels.</b>')
        text += "<br><br>" + hl
    
    text = re.sub(r'\.{2,}', '.', text)
    text = text.replace('<br><br>', '<br><span style="display: block; height: 0.5em;"></span>')
    text = fix_broken_line_breaks(text)
    
    text_part1, text_part2, text_part3 = split_spell_text(text)
    
    if text_part1 and text_part2:
        tables_in_part1 = text_part1.count('<table')
        tables_closed_in_part1 = text_part1.count('</table>')
        
        if tables_in_part1 > tables_closed_in_part1:
            last_table_start = text_part1.rfind('<table')
            if last_table_start != -1:
                text_before_table = text_part1[:last_table_start].strip()
                text_with_table = text_part1[last_table_start:] + text_part2
                
                if text_before_table and len(text_before_table) > 50:
                    text_part1 = text_before_table
                    text_part2 = text_with_table
                else:
                    text_part1 = text
                    text_part2 = None
    
    for proc_func in [colorize_text, apply_phrase_shorthands, sanitize_html]:
        text_part1 = proc_func(text_part1)
        if text_part2:
            text_part2 = proc_func(text_part2) 
    
    primary_class = parse_classes(spell.get('Classes', '')).title()
    source = spell.get('Source', '')
    
    components, materials = parse_components(spell.get('Components', ''))
    duration, is_concentration = parse_duration(spell.get('Duration', ''))
    spell_range, range_label, range_class = parse_range(spell.get('Range', ''))
    
    casting_time = spell.get('Casting Time', '')
    casting_time = casting_time.replace('Min', 'min').replace('Day', 'day').replace('Year', 'year').replace('Hr.', 'h').replace('hours', 'h')
    
    name = spell['Name']
    casting_label = "or Ritual" if is_ritual else "Casting Time"
    duration_label = "Concentration" if is_concentration else "Duration"
    
    mapping = {
        "CARD_ID": card_id,
        "PRIMARY_CLASS": '',
        "NAME": name,
        "CASTING": casting_time,
        "CASTING_CLASS": "ritual" if is_ritual else "",
        "CASTING_LABEL": casting_label,
        "RANGE": spell_range,
        "RANGE_CLASS": range_class,
        "RANGE_LABEL": range_label,
        "COMPONENTS": components,
        "DURATION": duration,
        "DURATION_CLASS": "concentration" if is_concentration else "",
        "DURATION_LABEL": duration_label,
        "MATERIAL_COMPONENTS": materials,
        "DURATION_INFO": "",
        "TEXT": text_part1,
        "SOURCE": source,
        "SPELL_TYPE": spell_type,
        "SCHOOL": school
    }

    for key, value in mapping.items():
        if key not in ["TEXT", "SPELL_TYPE"]:
            mapping[key] = escape(str(value))

    # Decide card type based on number of parts
    if text_part3 and card_striple_template:
        # Use triple-wide card (3 adjacent cards) - all text in first card
        wide_mapping = mapping.copy()
        wide_mapping["TEXT"] = text  # Put ALL text in first card
        wide_mapping["TEXT_PART2"] = ""  # Empty continuation cards
        wide_mapping["TEXT_PART3"] = ""
        return replace_placeholders(card_striple_template, wide_mapping)
    elif text_part2 and card_double_template:
        # Use double-wide card (2 adjacent cards) - all text in first card  
        wide_mapping = mapping.copy()
        wide_mapping["TEXT"] = text  # Put ALL text in first card
        wide_mapping["TEXT_PART2"] = ""  # Empty continuation card
        return replace_placeholders(card_double_template, wide_mapping)
    elif text_part2 and continuation_template:
        # Use vertical continuation cards (legacy)
        cards = [replace_placeholders(card_template, mapping)]
        continuation_mapping = {
            "CARD_ID": card_id,
            "NAME": name,
            "TEXT": text_part2,
            "PRIMARY_CLASS": '',
            "SOURCE": source,
            "SPELL_TYPE": spell_type,
            "SCHOOL": school
        }
        
        for key, value in continuation_mapping.items():
            if key not in ["TEXT", "SPELL_TYPE"]:
                continuation_mapping[key] = escape(str(value))
                
        cards.append(replace_placeholders(continuation_template, continuation_mapping))
        return ''.join(cards)
    else:
        # Single card
        return replace_placeholders(card_template, mapping)
