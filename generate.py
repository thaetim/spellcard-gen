import csv, re, os

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
            duration = match.group(1).strip() + '&nbsp;' + SYMBOL_CONCENTRATION
    duration = duration.replace('Instantaneous','Instant')
    duration = duration.replace('up to ','')
    duration = duration.replace('minutes','mins')
    duration = duration.replace('minute','min.')
    duration = duration.replace('year','yr')

    # range
    spell_range = spell.get('Range', '')
    spell_range = spell_range.replace('feet','ft.')
    spell_range = spell_range.replace(' (','<br>(')

    # casting time
    casting_time = spell.get('Casting Time', '')
    casting_time = casting_time.replace('Min','min')
    casting_time = casting_time.replace('Day','day')
    casting_time = casting_time.replace('Year','year')

    # name
    name = spell['Name']
    # if IS_CONCENTRATION:
    #     name += '&nbsp;' + SYMBOL_CONCENTRATION

    mapping = {
        "CARD_ID": card_id,
        "PRIMARY_CLASS": primary_class,
        "NAME": name,
        "CASTING": casting_time,
        "RANGE": spell_range,
        "COMPONENTS": components,
        "DURATION": duration,
        "MATERIAL_COMPONENTS": materials,
        "DURATION_INFO": duration_info,
        "TEXT": text,
        "SOURCE": source,
        "SPELL_TYPE": spell_type
    }

    return replace_placeholders(card_template, mapping)

def main():
    csv_path = 'data/Spells.csv'
    css_path = 'templates/style.css'
    page_path = 'templates/page.html'
    card_path = 'templates/card.html'
    out_path = 'out/spell_cards.html'

    css = load_file(css_path)
    page_template = load_file(page_path)
    card_template = load_file(card_path)

    cards = []
    with open(csv_path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            cleaned = {k: v.strip() if v else "" for k, v in row.items()}
            cards.append(generate_spell_card(cleaned, card_template))

    html_output = page_template.replace('/*{{STYLES}}*/', css).replace('<!--{{CARDS}}-->', ''.join(cards))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"Generated {len(cards)} cards → {out_path}")

if __name__ == "__main__":
    main()
