"""Main script for generating spell cards."""
from pathlib import Path
from spell_processing import load_spells, merge_spell_duplicates, load_fixed_spells, detect_broken_elements
from card_generator import generate_spell_card


def load_file(path):
    """Load file content as text."""
    return Path(path).read_text(encoding='utf-8')


def main():
    base = Path("templates")
    paths = {
        "csv": Path("data/Spells-various.csv"),
        "fixed_csv": Path("data/Spells-fixed.csv"),
        "css": base / "style.css",
        "page": base / "page.html",
        "card": base / "card.html",
        "card_cont": base / "card-continuation.html",
        "js": base / "autosize.js",
        "out_html": Path("out/spell_cards.html"),
        "out_js": Path("out/autosize.js")
    }

    css, page, card, card_cont, js = [
        load_file(p) for p in (paths["css"], paths["page"], paths["card"], paths["card_cont"], paths["js"])
    ]

    # Fix CSS syntax error
    css = css.replace("display: ver('-webkit-box');", "display: -webkit-box;")

    fixed_spells = load_fixed_spells(paths["fixed_csv"])
    spells_df = load_spells(paths["csv"])
    merged_spells = merge_spell_duplicates(spells_df)
    print(f"Merged {len(spells_df)} → {len(merged_spells)} unique spells")

    broken_spell_texts = []
    paired_cards = {}
    
    def generate_and_track(spell):
        spell_name = spell['Name']
        if spell_name in fixed_spells:
            print(f"Using fixed data for {spell_name}")
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
    main()
