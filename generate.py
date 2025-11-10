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
        "csv": Path("Spells-many.csv"),
        "fixed_csv": Path("data/Spells-fixed.csv"),
        "css": base / "style.css",
        "page": base / "page.html",
        "card": base / "card.html",
        "card_cont": base / "card-continuation.html",
        "js": base / "autosize.js",
        "out_html": Path("spell_cards.html"),
        "out_js": Path("autosize.js")
    }

    css, page, card, card_cont, js = [
        load_file(p) for p in (paths["css"], paths["page"], paths["card"], paths["card_cont"], paths["js"])
    ]

    fixed_spells = load_fixed_spells(paths["fixed_csv"])
    spells_df = load_spells(paths["csv"])
    merged_spells = merge_spell_duplicates(spells_df)
    print(f"Merged {len(spells_df)} → {len(merged_spells)} unique spells")

    broken_spell_texts = []
    paired_cards = {}
    
    def generate_and_track(spell):
        spell_name = spell['Name']
        if spell_name in fixed_spells:
            # print(f"Using fixed data for {spell_name}")
            spell = fixed_spells[spell_name]
        
        card_html = generate_spell_card(spell, card, card_cont, paired_cards)
        
        text = spell.get('Text', '')
        info = detect_broken_elements(text)
        if info and spell_name not in fixed_spells:
            broken_spell_texts.append((spell_name, info))
            
        return card_html
    
    cards = [generate_and_track(spell) for spell in merged_spells]
    
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

# TODO: fix Tasha's Otherworldly Guise
# TODO: better contrast damage type colors
# TODO: better text split and font autosizing (text_splitting.py changes in ratio do not seem to be effective, e.g. Wish spell)
# TODO: triple split cards
# TODO: continuous split cards