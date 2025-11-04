import csv, re, os

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
    primary_class = parse_classes(spell.get('Classes', ''))
    lvl = spell.get('Level', '')
    school = spell.get('School', '')
    spell_type = f"{school} cantrip" if lvl.lower() == 'cantrip' else f"{lvl}-level {school.lower()}"

    text = clean_html_text(spell.get('Text', ''))
    hl = clean_html_text(spell.get('At Higher Levels', ''))
    if hl:
        text += f"<br><br><b>At Higher Levels:</b> {hl}"

    # source
    source = spell.get('Source', '')
    CORE_SOURCES = ['PHB', 'SRD', 'DMG']
    source = '' if source in CORE_SOURCES else f"({source})"

    # components
    components = spell.get('Components', '')
    if ' M (' in components:
        components = components.replace(' M (','\nM (')

    # duration
    duration = spell.get('Duration', '')
    if 'up to' in duration:
        duration = duration.replace(', ',',\n')

    mapping = {
        "CARD_ID": card_id,
        "PRIMARY_CLASS": primary_class,
        "NAME": spell['Name'],
        "CASTING": spell.get('Casting Time', ''),
        "RANGE": spell.get('Range', ''),
        "COMPONENTS": components,
        "DURATION": duration,
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
