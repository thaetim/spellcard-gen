import os, re, random
from pathlib import Path
from collections import defaultdict
import pandas as pd

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

    merged = (
        spells_df.groupby("Name", dropna=False)
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
    return merged.to_dict(orient="records")

def estimate_text_length(text):
    return len(RE_HTML_TAGS.sub('', text or ''))

def split_spell_text(text, target_length=800):
    if estimate_text_length(text) < target_length:
        return text, None

    clean_text = RE_HTML_TAGS.sub('', text)
    total_len = len(clean_text)
    target_pos = int(total_len * 0.35)

    def best_break(text, regex):
        best, dist = None, float('inf')
        for match in regex.finditer(text):
            html_pos = match.end()
            clean_pos = len(RE_HTML_TAGS.sub('', text[:html_pos]))
            d = abs(clean_pos - target_pos)
            if d < dist:
                dist, best = d, html_pos
        return best, dist

    html_break, dist = best_break(text, RE_SENTENCE_END)
    if html_break is None or dist > total_len * 0.2:
        html_break, _ = best_break(text, RE_WHITESPACE)

    if not html_break:
        html_break = min(len(text), target_pos)

    return text[:html_break].strip(), text[html_break:].strip() or None

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
    
    # We'll process in a single pass using a replacement function
    def replace_damage_and_dice(match):
        full_match = match.group(0)
        
        # Check if this is already inside a span (avoid double-processing)
        if '<span' in full_match and '</span>' in full_match:
            return full_match
            
        # Try to identify what we're matching
        if 'd' in full_match.lower() and any(dmg_type in full_match.lower() for dmg_type in DAMAGE_COLORS.keys()):
            # This contains both dice and damage type
            for damage_type, color in DAMAGE_COLORS.items():
                pattern = rf'(\b\d+d\d+\+?\d*\b)\s+({re.escape(damage_type)}\s+damage\b)'
                damage_match = re.search(pattern, full_match, re.IGNORECASE)
                if damage_match:
                    dice_part = damage_match.group(1)
                    damage_part = damage_match.group(2)
                    return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{dice_part}</span> <span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{damage_part}</span>'
        
        # If we get here, check for damage type alone
        for damage_type, color in DAMAGE_COLORS.items():
            if damage_type in full_match.lower() and 'damage' in full_match.lower():
                # Check if it's a missing whitespace case
                missing_ws_pattern = rf'([a-z])({re.escape(damage_type)}\s+damage\b)'
                missing_ws_match = re.search(missing_ws_pattern, full_match, re.IGNORECASE)
                if missing_ws_match:
                    preceding_char = missing_ws_match.group(1)
                    damage_part = missing_ws_match.group(2)
                    return f'{preceding_char}<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{damage_part}</span>'
                
                # Regular damage type
                damage_pattern = rf'(\b{re.escape(damage_type)}\s+damage\b)'
                damage_match = re.search(damage_pattern, full_match, re.IGNORECASE)
                if damage_match:
                    damage_part = damage_match.group(1)
                    return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{damage_part}</span>'
        
        return full_match
    
    # First pass: process all potential damage type patterns
    processed_text = text
    
    # Build a comprehensive pattern that catches all cases
    damage_patterns = []
    for damage_type in DAMAGE_COLORS.keys():
        # Pattern for dice + damage type
        damage_patterns.append(rf'\b\d+d\d+\+?\d*\b\s+{re.escape(damage_type)}\s+damage\b')
        # Pattern for damage type alone
        damage_patterns.append(rf'\b{re.escape(damage_type)}\s+damage\b')
        # Pattern for missing whitespace
        damage_patterns.append(rf'[a-z]{re.escape(damage_type)}\s+damage\b')
    
    # Combine patterns with OR
    combined_pattern = '|'.join(damage_patterns)
    
    if combined_pattern:
        # Use a function to process matches and avoid overlaps
        def process_match(match):
            return replace_damage_and_dice(match)
        
        processed_text = re.sub(combined_pattern, process_match, processed_text, flags=re.IGNORECASE)
    
    # Second pass: color remaining standalone dice rolls
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

    return processed_text

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

    # main text description enhancements
    if hl:
        hl = hl.replace('At Higher Levels.','<b>At Higher Levels.</b>')
        text += "<br><br>" + hl
    
    # Color damage types and dice rolls FIRST (while full "damage type damage" exists)
    text = colorize_text(text)
    
    # Apply phrase shorthands
    PHRASE_SHORTHANDS = {
        # Damage types
        'acid damage': 'acid',
        'bludgeoning damage': 'bludgeoning',
        'cold damage': 'cold',
        'fire damage': 'fire',
        'force damage': 'force',
        'lightning damage': 'lightning',
        'necrotic damage': 'necrotic',
        'piercing damage': 'piercing',
        'poison damage': 'poison',
        'psychic damage': 'psychic',
        'radiant damage': 'radiant',
        'slashing damage': 'slashing',
        'thunder damage': 'thunder',
        # HP
        'temporary hitpoints': 'temp. HP',
        'hitpoints': 'HP',
        'hit points': 'HP',
        # CR
        'challenge ratings': 'CR',
        'challenge rating': 'CR',
        # Ability Scores
        'Strength': 'STR',
        'Dexterity': 'DEX',
        'Constitution': 'CON',
        'Intelligence': 'INT',
        'Wisdom': 'WIS',
        'Charisma': 'CHA',
        # Units
        'feet': 'ft.',
        'foot': 'ft.',
        'hours': 'h',
        'hour': 'h',
        'minutes': 'min.',
        'minute': 'min.',
        # d20 rolls
        'with advantage': '⥣',
        'with disadvantage': '⥥',
        'advantage': 'adv.',
        'disadvantage': 'disadv.',
    }
    for k, v in PHRASE_SHORTHANDS.items():
        text = text.replace(k, v)
    
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
    base = Path("templates")
    paths = {
        "csv": Path("data/Spells-many.csv"),
        "css": base / "style.css",
        "page": base / "page.html",
        "card": base / "card.html",
        "card_cont": base / "card-continuation.html",
        "js": base / "autosize.js",
        "out_html": Path("out/spell_cards.html"),
        "out_js": Path("out/autosize.js")
    }

    css, page, card, card_cont, js = [load_file(p) for p in (paths["css"], paths["page"], paths["card"], paths["card_cont"], paths["js"])]

    spells_df = load_spells(paths["csv"])
    merged_spells = merge_spell_duplicates(spells_df)
    print(f"Merged {len(spells_df)} → {len(merged_spells)} unique spells")

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as ex:
        cards = list(ex.map(lambda s: generate_spell_card(s, card, card_cont), merged_spells))

    html = page.replace('/*{{STYLES}}*/', css).replace('<!--{{CARDS}}-->', ''.join(cards))
    Path("out").mkdir(exist_ok=True)
    paths["out_html"].write_text(html, encoding='utf-8')
    paths["out_js"].write_text(js, encoding='utf-8')

    print(f"Exported {len(cards)} cards to {paths['out_html']}")

if __name__ == "__main__":
    main()
