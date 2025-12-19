"""Main script for generating spell cards."""
import argparse
import keyboard
import sys
import pandas as pd
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
    # Always use the directory where the exe/script is actually located
    # sys.executable for compiled exe, __file__ for script
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE (PyInstaller sets sys.frozen)
        return Path(sys.executable).parent.absolute()
    else:
        # Running as script - use script's directory
        return Path(__file__).parent.absolute()


def get_csv_path(csv_path_arg=None):
    """Get the path to the CSV file.
    Priority:
    1. File dragged onto EXE (csv_path_arg)
    2. Spells.csv in the same folder as EXE

    Returns None if CSV not found.
    """
    exe_dir = get_exe_directory()

    # If file was dragged onto EXE, use that
    if csv_path_arg:
        csv_path = Path(csv_path_arg).absolute()
        if csv_path.exists():
            return csv_path
        else:
            return None

    # Default: Spells.csv in the same folder as EXE
    default_csv = exe_dir / "Spells.csv"
    if default_csv.exists():
        return default_csv

    return None


def validate_csv(csv_path):
    """Validate CSV file structure and content.
    Returns (is_valid, error_messages) tuple.
    """
    errors = []

    try:
        # Try to read the CSV
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        errors.append("File encoding error: CSV must be UTF-8 encoded")
        return False, errors
    except pd.errors.EmptyDataError:
        errors.append("CSV file is empty")
        return False, errors
    except Exception as e:
        errors.append(f"Failed to read CSV: {str(e)}")
        return False, errors

    # Check for required columns
    required_columns = ['Name', 'Level', 'School',
                        'Casting Time', 'Range', 'Components', 'Duration', 'Text']
    missing_columns = [
        col for col in required_columns if col not in df.columns]

    if missing_columns:
        errors.append(
            f"Missing required columns: {', '.join(missing_columns)}")
        errors.append(f"Found columns: {', '.join(df.columns.tolist())}")
        return False, errors

    # Check if CSV has any data
    if len(df) == 0:
        errors.append("CSV file contains no spell data")
        return False, errors

    # Check for critical empty fields
    critical_fields = ['Name', 'Level', 'School']
    for field in critical_fields:
        null_count = df[field].isna().sum()
        if null_count > 0:
            errors.append(
                f"Warning: {null_count} spells have missing '{field}' field")

    # Check for newlines and proper quoting in CSV
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()

        # Check if there are unquoted newlines (newlines outside of quoted fields)
        lines = csv_content.split('\n')
        expected_columns = len(df.columns)

        # Read raw CSV to check for quoting issues
        import csv
        quote_issues = []
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            row_num = 2  # Start from row 2 (after header)

            for row in reader:
                # Check if row has correct number of columns
                if len(row) != expected_columns:
                    quote_issues.append(
                        f"Row {row_num}: Has {len(row)} columns, expected {expected_columns}. "
                        f"This may indicate unquoted newlines or commas in cell values."
                    )

                # Check for newlines in values
                for col_idx, cell in enumerate(row):
                    if cell and '\n' in cell:
                        # This is fine - newlines are allowed in quoted fields
                        pass

                row_num += 1

        if quote_issues:
            errors.append(
                "CSV formatting issues (unquoted newlines or commas):")
            errors.extend(quote_issues[:5])  # Show first 5 issues
            if len(quote_issues) > 5:
                errors.append(
                    f"... and {len(quote_issues) - 5} more formatting issues")
            errors.append(
                "\nTip: Fields containing commas or newlines must be enclosed in double quotes.")
    except Exception as e:
        # Don't fail validation on this check, just warn
        pass

    # Check data types
    try:
        # Level should be: "Cantrip", a number (0-9), or ordinal (1st, 2nd, 3rd, etc.)
        level_issues = []
        for idx, val in df['Level'].items():
            if pd.notna(val):
                val_str = str(val).strip()
                # Check if valid: Cantrip, digit(s), or ordinal (1st, 2nd, 3rd, 4th, etc.)
                if not (val_str.lower() == 'cantrip' or
                        val_str.isdigit() or
                        (val_str[-2:] in ['st', 'nd', 'rd', 'th'] and val_str[:-2].isdigit())):
                    level_issues.append(
                        f"Row {idx + 2}: Invalid level '{val}'")

        if level_issues:
            errors.append("Level field issues:")
            errors.extend(level_issues[:5])  # Show first 5 issues
            if len(level_issues) > 5:
                errors.append(
                    f"... and {len(level_issues) - 5} more level issues")
    except Exception as e:
        errors.append(f"Error validating Level field: {str(e)}")

    # Return results
    if errors:
        return False, errors

    return True, []


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

    # Check if CSV exists
    if csv_path is None:
        print("\n" + "=" * 70)
        print("ERROR: CSV file not found")
        print("=" * 70)

        if csv_path_arg:
            print(f"\nThe file you specified was not found:")
            print(f"  {Path(csv_path_arg).absolute()}")
        else:
            print(f"\nNo Spells.csv file found in the expected location:")
            print(f"  {exe_dir / 'Spells.csv'}")

        print("\nTo use this tool:")
        print("  1. Place a file named 'Spells.csv' in the same folder as this executable")
        print("  2. OR drag and drop your CSV file onto this executable")
        print("\nThe CSV file must contain spell data with the following columns:")
        print("  Name, Level, School, Casting Time, Range, Components, Duration, Text")
        print("=" * 70)
        return False

    # Validate CSV structure
    print(f"Validating CSV file: {csv_path.name}...")
    is_valid, validation_errors = validate_csv(csv_path)

    if not is_valid:
        print("\n" + "=" * 70)
        print("ERROR: CSV file validation failed")
        print("=" * 70)
        print(f"\nFile: {csv_path}")
        print("\nProblems found:")
        for i, error in enumerate(validation_errors, 1):
            print(f"  {i}. {error}")
        print("\nPlease fix these issues and try again.")
        print("=" * 70)
        return False

    print("✓ CSV validation passed")

    # Determine output directory: same as exe if CSV was dragged, otherwise current directory
    if csv_path_arg:
        output_dir = exe_dir / "out"
        print(f"Using CSV file: {csv_path} (dragged onto EXE)")
        print(f"Output directory: {output_dir}")
    else:
        output_dir = Path.cwd() / "out"
        print(f"Using CSV file: {csv_path} (default location)")
        print(f"Output directory: {output_dir}")

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
        # Output files go to output directory
        "out_html": output_dir / "spell_cards.html",
        "out_js": output_dir / "autosize.js"
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
    # Wrap every 9 slots in a page div with top padding
    all_cards_raw = []

    # Add all triple-wide cards first (they take full rows)
    all_cards_raw.extend(l_cards_triple)

    # Interleave doubles with singles (each double gets exactly one single)
    num_pairs = min(len(l_cards_double), len(l_cards_single))
    for i in range(num_pairs):
        all_cards_raw.append(l_cards_double[i])
        all_cards_raw.append(l_cards_single[i])

    # Add remaining doubles without singles
    all_cards_raw.extend(l_cards_double[num_pairs:])

    # Add remaining singles
    all_cards_raw.extend(l_cards_single[num_pairs:])

    # Now wrap cards in page divs (9 slots per page)
    cards = []
    current_page_cards = []
    current_page_slots = 0
    page_num = 0

    for card_html in all_cards_raw:
        # Determine how many slots this card takes
        if 'card-triple' in card_html:
            slots = 3
        elif 'card-double' in card_html:
            slots = 2
        else:
            slots = 1

        # Check if adding this card would exceed 9 slots
        if current_page_slots > 0 and current_page_slots + slots > 9:
            # Wrap current page cards and start new page
            page_div = f'<div class="page-div">{"".join(current_page_cards)}</div>'
            cards.append(page_div)
            current_page_cards = []
            current_page_slots = 0
            page_num += 1

        current_page_cards.append(card_html)
        current_page_slots += slots

        # If we've exactly filled 9 slots, wrap and start new page
        if current_page_slots >= 9:
            page_div = f'<div class="page-div">{"".join(current_page_cards)}</div>'
            cards.append(page_div)
            current_page_cards = []
            current_page_slots = 0
            page_num += 1

    # Add remaining cards if any
    if current_page_cards:
        page_div = f'<div class="page-div">{"".join(current_page_cards)}</div>'
        cards.append(page_div)

    if broken_spell_texts:
        print(
            f"\nSpells needing manual description fix ({len(broken_spell_texts)}):")
        for name, headers in sorted(set(broken_spell_texts)):
            print(f"  - {name}")  # : {headers}")

    html = page.replace(
        '/*{{STYLES}}*/', css).replace('<!--{{CARDS}}-->', ''.join(cards))

    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)

    paths["out_html"].write_text(html, encoding='utf-8')
    paths["out_js"].write_text(js, encoding='utf-8')

    print(f"\n✓ Successfully exported {len(cards)} cards")
    print(f"  HTML: {paths['out_html']}")
    print(f"  JS:   {paths['out_js']}")

    return True


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
    parser.add_argument('--loop', '-l', action='store_true',
                        help='Run in regeneration loop (press ENTER to regenerate, ESC to exit)')
    parser.add_argument('--dev', '-d', action='store_true',
                        help='Developer mode: run once and exit immediately (no user input)')
    args = parser.parse_args()

    # Get CSV path from command line (drag & drop) or None
    csv_path_arg = args.csv_file if args.csv_file else None

    # If dev mode, run main once and exit immediately
    if args.dev:
        success = main(csv_path_arg)
        sys.exit(0 if success else 1)

    # Run main once
    success = main(csv_path_arg)

    # If main failed, wait for user input and exit
    if not success:
        print("\nPress any key to exit...")
        input()
        sys.exit(1)

    # If loop mode, enter regeneration loop
    if args.loop:
        def user_input():
            print("\nPress ENTER to (re)generate or ESC to exit...", flush=True)
            return keyboard.read_key(suppress=True)

        try:
            def main_with_csv():
                success = main(csv_path_arg)
                if not success:
                    print(
                        "\nGeneration failed. Press ESC to exit or ENTER to try again...")

            options = {
                'enter': main_with_csv,
                'esc': lambda: sys.exit(0)
            }

            while True:
                try:
                    options[user_input()]()
                except KeyboardInterrupt:
                    sys.exit(0)
                except KeyError:
                    pass
        finally:
            keyboard.unhook_all()
    else:
        # Default: wait for user input before closing
        print("\nPress any key to exit...")
        input()

# TODO: check Chaos Bolt, Clone, Conjure Giant, Control Flames, Creation, Divine Word, Doom of Stacked Stones, Greater Restoration, Guardian of Nature
# TODO: fix damage type coloring on Tasha's Otherworldly Guise text
# TODO: fix Arcane Lock attr labels overlaps (why do they even happen?)
# TODO: Lunar Transfer i Octarine Spray font size
# TODO: Lunar Transfer table
# TODO: better contrast damage type colors
# TODO: no dmg type coloring in Animate Objects
# TODO: Druid Grove vs. Augury "►" listings

# TODO # DEV print test
