import csv, re, os
from collections import defaultdict

SYMBOL_CONCENTRATION = '<span class="diamond"><span class="c">C</span></span>'

def clean_html_text(text):
    if not text:
        return ""
    text = text.replace('\n', '<br>')
    text = re.sub(r'<[^>]+>', '', text)
    return text

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

def generate_spell_card(spell, card_template):
    card_id = generate_card_id(spell['Name'])
    lvl = spell.get('Level', '')
    school = spell.get('School', '').title()
    spell_type = f"{school} Cantrip" if lvl.lower() in ('cantrip', 0, '0') else f"{lvl}-level {school}"

    text = clean_html_text(spell.get('Text', ''))
    hl = clean_html_text(spell.get('At Higher Levels', ''))
    if hl:
        text += f"<br><br><b>At Higher Levels:</b> {hl}"
    
    # primary class
    primary_class = parse_classes(spell.get('Classes', '')).title()

    # source
    source = spell.get('Source', '')
    CORE_SOURCES = ['PHB', 'SRD', 'DMG']
    source = '' if source in CORE_SOURCES else f"[{source}]"

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
            # duration_info = "concentration" # 🌀⚪×🔆 
            duration = match.group(1).strip() # + '&nbsp;' + SYMBOL_CONCENTRATION
    duration = duration.replace('Instantaneous','Instant')
    duration = duration.replace('up to ','')
    duration = duration.replace('minutes','mins')
    duration = duration.replace('minute','min.')
    duration = duration.replace('year','yr')

    # range
    spell_range = spell.get('Range', '')
    spell_range = spell_range.replace('feet','ft.')
    spell_range = spell_range.replace(' (','<br>(')

    # casting time + ritual
    IS_RITUAL = False
    casting_time = spell.get('Casting Time', '')
    ritual_field = spell.get('Ritual', '').lower()
    if ritual_field in ('yes', 'true', '1'):
        IS_RITUAL = True
    casting_time = casting_time.replace('Min','min')
    casting_time = casting_time.replace('Day','day')
    casting_time = casting_time.replace('Year','year')
    casting_time = casting_time.replace('Hr.','hours')

    # name
    name = spell['Name']
    # if IS_CONCENTRATION:
    #     name += '&nbsp;' + SYMBOL_CONCENTRATION

    # Labels for special attributes
    casting_label = "Ritual" if IS_RITUAL else "Casting Time"
    duration_label = "Concentration" if IS_CONCENTRATION else "Duration"

    mapping = {
        "CARD_ID": card_id,
        "PRIMARY_CLASS": '', # primary_class,
        "NAME": name,
        "CASTING": casting_time,
        "CASTING_CLASS": "ritual" if IS_RITUAL else "",
        "CASTING_LABEL": casting_label,
        "RANGE": spell_range,
        "COMPONENTS": components,
        "DURATION": duration,
        "DURATION_CLASS": "concentration" if IS_CONCENTRATION else "",
        "DURATION_LABEL": duration_label,
        "MATERIAL_COMPONENTS": materials,
        "DURATION_INFO": duration_info,
        "TEXT": text,
        "SOURCE": '', # source,
        "SPELL_TYPE": spell_type,
        "SCHOOL": school
    }

    return replace_placeholders(card_template, mapping)

def main():
    csv_path = 'data/Spells-various.csv'
    css_path = 'templates/style.css'
    page_path = 'templates/page.html'
    card_path = 'templates/card.html'
    js_path = 'templates/autosize.js'
    out_path = 'out/spell_cards.html'
    out_js_path = 'out/autosize.js'

    css = load_file(css_path)
    page_template = load_file(page_path)
    card_template = load_file(card_path)
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
    cards = [generate_spell_card(spell, card_template) for spell in merged_spells]

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
