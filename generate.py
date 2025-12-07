"""Main script for generating spell cards."""
import argparse
import keyboard
import sys
from card_generator import generate_spell_card
from spell_processing import load_spells, merge_spell_duplicates, load_fixed_spells, detect_broken_elements
from pathlib import Path
VERSION = '1.0.0'


def load_file(path):
    """Load file content as text."""
    return Path(path).read_text(encoding='utf-8')


def get_base_path():
    """Get the base path for resources (templates, data).
    When running as compiled EXE, use sys._MEIPASS (temporary extraction directory).
    Otherwise, use the script's directory."""
    if hasattr(sys, '_MEIPASS'):
        # Running as compiled EXE - resources are in temp extraction directory
        # Nuitka extracts bundled files to a temp folder like: C:\Users\...\AppData\Local\Temp\_MEI103162
        return Path(sys._MEIPASS)
    else:
        # Running as script - resources are in script's directory
        return Path(__file__).parent.absolute()


def get_exe_directory():
    """Get the directory where the EXE is located (or script directory).
    This is where user-provided files like Spells.csv should be placed."""
    if hasattr(sys, '_MEIPASS'):
        # Running as compiled EXE - sys.argv[0] points to the original EXE location
        return Path(sys.argv[0]).parent.absolute()
    else:
        # Running as script - use script's directory
        return Path(__file__).parent.absolute()


def get_csv_path(csv_path_arg=None):
    """Get the path to the CSV file.
    Priority:
    1. File dragged onto EXE (csv_path_arg)
    2. Spells.csv in the same folder as EXE
    """
    exe_dir = get_exe_directory()

    # If file was dragged onto EXE, use that
    if csv_path_arg:
        csv_path = Path(csv_path_arg).absolute()
        if csv_path.exists():
            return csv_path
        else:
            print(f"Warning: Specified CSV file not found: {csv_path}")
            print(f"Falling back to default location...")

    # Default: Spells.csv in the same folder as EXE
    return exe_dir / "Spells.csv"


def main(csv_path_arg=None):
    # Get base path for resources (templates, data files bundled with EXE)
    # In EXE mode: points to temp extraction directory (sys._MEIPASS)
    # In script mode: points to script directory
    base_path = get_base_path()

    # Get EXE/script directory - where user-provided files should be
    exe_dir = get_exe_directory()

    # Templates and data files are bundled with EXE (in base_path)
    base = base_path / "templates"

    # Get CSV path (prefer dragged file, fallback to default location)
    csv_path = get_csv_path(csv_path_arg)

    # Inform user which CSV file is being used
    if csv_path_arg:
        print(f"Using CSV file: {csv_path} (dragged onto EXE)")
    else:
        print(f"Using CSV file: {csv_path} (default location)")

    paths = {
        # CSV file - prefer dragged file, otherwise in same folder as EXE
        "csv": csv_path,
        # Fixed CSV is bundled in data/ folder (in base_path)
        "fixed_csv": base_path / "data" / "Spells-fixed.csv",
        # Templates are bundled (in base_path)
        "css": base / "style.css",
        "page": base / "page.html",
        "card_single": base / "card-single.html",
        "card_double": base / "card-double.html",
        "card_triple": base / "card-triple.html",
        "js": base / "autosize.js",
        # Output files go to current working directory (where user runs the EXE)
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
        print(
            f"\nSpells needing manual description fix ({len(broken_spell_texts)}):")
        for name, headers in sorted(set(broken_spell_texts)):
            print(f"  - {name}")  # : {headers}")

    html = page.replace(
        '/*{{STYLES}}*/', css).replace('<!--{{CARDS}}-->', ''.join(cards))
    Path("out").mkdir(exist_ok=True)
    paths["out_html"].write_text(html, encoding='utf-8')
    paths["out_js"].write_text(js, encoding='utf-8')

    print(f"Exported {len(cards)} cards to {paths['out_html']}")


if __name__ == "__main__":
    # # DEBUG #
    # import os
    # from pathlib import Path
    # print(f"Current working directory: {os.getcwd()}")
    # print(f"Script location: {__file__}")

    # if hasattr(sys, '_MEIPASS'):
    #     print(f"MEIPASS location: {sys._MEIPASS}")
    #     base_path = Path(sys._MEIPASS)
    # else:
    #     base_path = Path(__file__).parent

    # print(f"Base path: {base_path}")
    # print(f"templates/style.css exists: {(base_path / 'templates' / 'style.css').exists()}")
    # ##

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Spellcard Generator',
        # Allow positional arguments for drag & drop
        allow_abbrev=False
    )
    parser.add_argument('csv_file', nargs='?',
                        help='CSV file to process (can be dragged onto EXE)')
    parser.add_argument('--dev', '-d', action='store_true',
                        help='Developer mode: run once and exit (no interactive input)')
    args = parser.parse_args()

    # Get CSV path from command line (drag & drop) or None
    csv_path_arg = args.csv_file if args.csv_file else None

    # If dev mode, run main once and exit
    if args.dev:
        main(csv_path_arg)
        sys.exit(0)

    def user_input():
        print("\nPress ENTER to (re)generate or ESC to exit...", flush=True)
        return keyboard.read_key(suppress=True)
    try:
        # Create closure to capture csv_path_arg
        def main_with_csv():
            main(csv_path_arg)

        options = {
            'enter': main_with_csv,
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

# TODO: check Chaos Bolt, Clone, Conjure Giant, Control Flames, Creation, Divine Word, Doom of Stacked Stones, Greater Restoration, Guardian of Nature
# TODO: fix damage type coloring on Tasha's Otherworldly Guise text
# TODO: fix Arcane Lock attr labels overlaps (why do they even happen?)
# TODO: Lunar Transfer i Octarine Spray font size
# TODO: Lunar Transfer table
# TODO: better contrast damage type colors
# TODO: no dmg type coloring in Animate Objects
# TODO: Druid Grove vs. Augury "►" listings

# TODO # DEV print test
