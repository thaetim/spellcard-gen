"""Main script for generating spell cards."""
from pathlib import Path
from spell_processing import load_spells, merge_spell_duplicates, load_fixed_spells, detect_broken_elements
from card_generator import generate_spell_card
import sys, keyboard, argparse

def load_file(path):
    """Load file content as text."""
    return Path(path).read_text(encoding='utf-8')


def main():
    base = Path("templates")
    paths = {
        "csv": Path("Spells-various.csv"),
        "fixed_csv": Path("data/Spells-fixed.csv"),
        "css": base / "style.css",
        "page": base / "page.html",
        "card_single": base / "card-single.html",
        "card_double": base / "card-double.html",
        "card_triple": base / "card-triple.html",
        "js": base / "autosize.js",
        "out_html": Path("spell_cards.html"),
        "out_js": Path("autosize.js")
    }

    css, page, card_single, card_double, card_triple, js = [
        load_file(p) for p in (paths["css"], paths["page"], paths["card_single"], paths["card_double"], paths["card_triple"], paths["js"])
    ]

    fixed_spells = load_fixed_spells(paths["fixed_csv"])
    spells_df = load_spells(paths["csv"])
    merged_spells = merge_spell_duplicates(spells_df)
    print(f"Merged {len(spells_df)} → {len(merged_spells)} unique spells")

    broken_spell_texts = []
    
    # Separate wide cards from single cards
    l_cards_double = []
    l_cards_triple = []
    l_cards_single = []
    
    def generate_and_track(spell):
        spell_name = spell['Name']
        if spell_name in fixed_spells:
            spell = fixed_spells[spell_name]
        

        card_html = generate_spell_card(spell, {
            'single': card_single,
            'double': card_double,
            'triple': card_triple,
        })
        
        text = spell.get('Text', '')
        info = detect_broken_elements(text)
        if info and spell_name not in fixed_spells:
            broken_spell_texts.append((spell_name, info))

        return card_html
    
    # Generate all cards and categorize
    for spell in merged_spells:
        card_html = generate_and_track(spell)
        if 'card-triple' in card_html:
            l_cards_triple.append(card_html)
        elif 'card-double' in card_html:
            l_cards_double.append(card_html)
        else:
            l_cards_single.append(card_html)
    
    # Interleave for efficient printing:
    # - Triple-wide (3 slots) = full row
    # - Double-wide (2 slots) + Single (1 slot) = full row  
    # - Remaining singles fill final rows
    cards = []
    
    # Add all triple-wide cards first (they take full rows)
    cards.extend(l_cards_triple)
    
    # Interleave doubles with singles (each double gets exactly one single)
    num_pairs = min(len(l_cards_double), len(l_cards_single))
    for i in range(num_pairs):
        cards.append(l_cards_double[i])
        cards.append(l_cards_single[i])
    
    # Add remaining doubles without singles
    cards.extend(l_cards_double[num_pairs:])
    
    # Add remaining singles
    cards.extend(l_cards_single[num_pairs:])
    
    if broken_spell_texts:
        print(f"\nSpells needing manual description fix ({len(broken_spell_texts)}):")
        for name, headers in sorted(set(broken_spell_texts)):
            print(f"  - {name}") # : {headers}")

    html = page.replace('/*{{STYLES}}*/', css).replace('<!--{{CARDS}}-->', ''.join(cards))
    Path("out").mkdir(exist_ok=True)
    paths["out_html"].write_text(html, encoding='utf-8')
    paths["out_js"].write_text(js, encoding='utf-8')

    print(f"Exported {len(cards)} cards to {paths['out_html']}")

if __name__ == "__main__":
    # DEBUG #
    import os
    from pathlib import Path
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {__file__}")
    
    if hasattr(sys, '_MEIPASS'):
        print(f"MEIPASS location: {sys._MEIPASS}")
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    
    print(f"Base path: {base_path}")
    print(f"templates/style.css exists: {(base_path / 'templates' / 'style.css').exists()}")
    ##

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Spellcard Generator')
    parser.add_argument('--dev', '-d', action='store_true', 
                       help='Developer mode: run once and exit (no interactive input)')
    args = parser.parse_args()

    # If dev mode, run main once and exit
    if args.dev:
        main()
        sys.exit(0)

    def user_input():
        print("\nPress ENTER to (re)generate or ESC to exit...", flush=True)
        return keyboard.read_key(suppress=True)
    try:
        options = {
            'enter': main,
            'esc': lambda: sys.exit(0)
        }
    
        while True:
            try:
                options[user_input()]()
            except KeyboardInterrupt:
                sys.exit(0)
            except KeyError as e:
                pass
    finally:
        keyboard.unhook_all()
