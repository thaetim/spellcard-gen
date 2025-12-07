# Spellcard Generator - Complete Guide

Generates printable D&D 5e spell cards from CSV data exported from 5e.tools or other sources.

## Overview

This tool converts spell data into professionally formatted, print-ready spell cards. It automatically processes spell text, applies abbreviations, colorizes damage types, and intelligently sizes cards based on content length (single, double, or triple width).

![preview](assets/preview.png)

## Features

- **Automatic card sizing**: Single, double, or triple-width cards based on text length
- **Smart attribute display**: Special spell properties shown as badges instead of generic labels
- **Smart text formatting**: Enumerations converted to tables, broken line breaks fixed
- **Damage type colorization**: Damage types highlighted in color
- **Abbreviations**: Common D&D terms shortened (HP, AC, CR, etc.)
- **Duplicate merging**: Combines duplicate spell entries, keeping longest text versions
- **Manual overrides**: `data/Spells-fixed.csv` for correcting problematic spells
- **Print optimization**: Cards arranged for efficient printing
- **Easy setup**: Both executable and Python versions available

### Smart Attribute Display

The attribute table shows spell properties with context-aware labeling:
- **Concentration spells**: "Concentration" badge replaces "Duration" label
- **Ritual spells**: "or Ritual" badge replaces "Casting Time" label  
- **Area effects**: Range shows area type (e.g., "Self Radius", "Touch Cone")

![attr-display-ritual](assets/attr-display-ritual.png)
![attr-display-range](assets/attr-display-range.png)

## Quick Start

### Option 1: Simple Usage (Recommended for Most Users)

1. **Download the executable**: Get `spellcard-generator_X.X.X.exe` from [GitHub Releases](https://github.com/thaetim/spellcard-gen/releases/latest)
2. **Get your spell data** (see below for how to get CSV from 5e.tools)
3. **Place your CSV file** in the same folder as the exe (default: `Spells.csv`)
4. **Run the program**: Double-click `spellcard-generator_X.X.X.exe`
5. **Find your cards**: Open `out/spell_cards.html` in your browser

### Option 2: Drag and Drop

1. **Drag your CSV file** onto the exe
2. Cards will be generated in the `out/` folder next to the exe
3. Press any key to close when done

---

## Getting Spell Data from 5e.tools

### Step-by-Step Guide

1. **Go to 5e.tools Spells Table**: [https://2014.5e.tools/spells.html](https://2014.5e.tools/spells.html)

2. **Set up your spell list:**
   - **Utilities / Load All Partnered Content** (optional, to see all available sources)
   - **Utilities / Homebrew Manager** > Get Homebrew (blue button) > Select desired > Add Selected (blue ⤓ download button)
   - Adjust the Filters to find spells you want

3. **Select spells:**
   - **Option A (Filtered list)**: Use filters and take all visible spells
   - **Option B (Pinned list)**: Press `P` on individual spells to pin them (takes precedence over filters)

4. **Export to CSV:**
   - Open the **Table View** (look for table icon/button)
   - Click **Export to CSV** button
   - Save as `Spells.csv` in your working directory

### Sampling for Large Lists

By default, if your CSV contains more than **200 spells**, the script generates only a **sample of 69 spells** to speed up development. The sample includes:
- All spells matching specific test phrases
- Random spells to fill up to 69 total

**To generate all spells**, you'll need to edit the source code or use the executable version which doesn't have this limitation.

> **Warning**: Generating large spell lists (200+ spells) can cause the browser's font autosizing JavaScript to take several minutes to complete.

---

## Input Data Requirements

Your CSV file must contain spell data with these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Name** | Spell name | `"Fireball"` |
| **Level** | Spell level | `"3rd"` or `"3"` or `"Cantrip"` |
| **School** | School of magic | `"Evocation"` |
| **Casting Time** | Time to cast | `"Action"` or `"1 Action"` |
| **Range** | Spell range | `"150 feet"` or `"Self"` |
| **Components** | V, S, M components | `"V, S, M (a tiny ball of bat guano)"` |
| **Duration** | How long it lasts | `"Instantaneous"` or `"Concentration, up to 1 minute"` |
| **Text** | Spell description | Full spell text with formatting |

**Optional columns** (will be included if present):
- `Source` - Book abbreviation (e.g., "PHB", "XGE")
- `Page` - Page number
- `Classes` - Who can cast it
- `At Higher Levels` - Upcasting effects
- `Subclasses` - Subclass-specific availability

### CSV Format Requirements

✅ **Correct formatting:**
- Save file as UTF-8 encoding
- Use double quotes `""` around fields containing commas or newlines
- Fields with special characters must be quoted

**Example of proper CSV:**
```csv
"Name","Level","School","Casting Time","Range","Components","Duration","Text"
"Fireball","3rd","Evocation","Action","150 feet","V, S, M (a tiny ball of bat guano)","Instantaneous","A bright streak flashes from your pointing finger..."
"Cure Wounds","1st","Evocation","Action","Touch","V, S","Instantaneous","A creature you touch regains hit points..."
```

---

## Running the Program

### Basic Usage (No Loop Mode)

```bash
# Windows: Double-click the exe, or run from command line
spellcard-generator_1.0.0.exe
```

**What happens:**
1. Program looks for `Spells.csv` in the same folder
2. Validates the CSV file
3. Generates spell cards
4. Saves output to `out/spell_cards.html`
5. Waits for you to press any key before closing

### Loop Mode (For Development/Testing)

```bash
spellcard-generator_1.0.0.exe --loop
```

**What happens:**
1. Generates cards once
2. Shows: `Press ENTER to (re)generate or ESC to exit...`
3. Press **ENTER** to regenerate (useful when editing CSV)
4. Press **ESC** to exit

### Using a Different CSV File

**Option A: Drag and Drop**
- Drag your CSV file onto the exe icon
- Output goes to `out/` folder next to the exe

**Option B: Command Line**
```bash
spellcard-generator_1.0.0.exe "path/to/your/spells.csv"
```

### For Developers (Run from Source)

If you're running from Python source code:

```bash
# Basic usage
python generate.py
# Press ENTER to regenerate, ESC to exit

# Developer mode (single run)
python generate.py --dev

# Watch mode (auto-regenerate on changes)
python runwatch.py
```

---

## Understanding the Output

### Generated Files

After running, you'll find these files in the `out/` folder:

```
out/
├── spell_cards.html    # Open this in your web browser
└── autosize.js         # Required JavaScript (don't delete)
```

### Opening Your Spell Cards

1. Navigate to the `out/` folder
2. Double-click `spell_cards.html`
3. Your default browser will open showing all your spell cards

### Card Layout

Cards are automatically organized for efficient printing:
- **Triple-wide cards** (very long spells) take a full row (3 slots)
- **Double-wide cards** (long spells) take 2 slots
- **Single cards** (normal spells) take 1 slot
- Double-wide and single cards are interleaved to minimize wasted space

### Printing Your Cards

1. Open `spell_cards.html` in your browser
2. Press **Ctrl+P** (or Cmd+P on Mac)
3. **Print settings:**
   - Layout: **Portrait**
   - Margins: **None** or **Minimum**
   - Scale: **100%**
   - Background graphics: **Enabled** (to show colors)
4. Print or save as PDF

**Recommended paper:**
- Standard letter size (8.5" × 11")
- Cardstock (for durability)
- Print double-sided if possible

---

## Manual Corrections

### `data/Spells-fixed.csv`

Contains manually corrected spell data to override automatic processing. The script checks this file first for each spell. Use this to fix problematic spells with broken formatting, incorrect data, or special requirements.

---

## Troubleshooting

### Common Errors and Solutions

**"ERROR: CSV file not found"**
- Make sure `Spells.csv` is in the **same folder** as the exe
- Or drag your CSV file directly onto the exe

**"ERROR: CSV file validation failed"**

**Missing columns:**
- Ensure all required columns (Name, Level, School, etc.) are present

**Invalid Level Values:**
- Use `"Cantrip"`, `"1st"`, `"2nd"`, `"3rd"`, etc.
- Or plain numbers: `"1"`, `"2"`, `"3"`, etc.

**CSV Formatting Issues:**
- Fields containing commas or newlines MUST be enclosed in double quotes:
  ✅ `"V, S, M (bat guano)"`
  ❌ `V, S, M (bat guano)`

**Encoding Issues:**
- Save your CSV file with UTF-8 encoding
- **Excel:** Save As → CSV UTF-8 (Comma delimited)
- **Google Sheets:** File → Download → CSV

**Cards Look Wrong**
- Enable "Background graphics" in print settings
- Use Portrait orientation with minimum margins
- Try Chrome browser for best compatibility

**Antivirus Warnings** (False Positives)
- Add exception for the exe in your antivirus
- Or run from Python source code if concerned

---

## Tips and Best Practices

### Organizing Your Spells

**Create separate CSV files for different purposes:**
```
MySpells/
├── Wizard_Prepared.csv      # Spells you have prepared
├── Wizard_Spellbook.csv     # All spells in your spellbook
├── Party_Ritual.csv         # Ritual spells for the party
└── Backup_Scrolls.csv       # Scrolls you're carrying
```

### Updating Your Cards

**Quick workflow for frequent updates:**
1. Run with `--loop` flag
2. Edit your CSV in Excel/Google Sheets
3. Save the CSV
4. Press **ENTER** in the program window
5. Refresh your browser to see changes

### Preparing for Game Session

1. Generate cards for your prepared spells
2. Print on cardstock
3. Cut out the cards
4. Organize by spell level
5. Keep in a deck box or binder

### Multiple Characters Setup

```
D&D/
├── Wizard/
│   ├── spellcard-generator.exe
│   ├── Spells.csv (wizard spells)
│   └── out/spell_cards.html
└── Cleric/
    ├── spellcard-generator.exe (copy)
    ├── Spells.csv (cleric spells)
    └── out/spell_cards.html
```

---

## File Structure

- `generate.py` - Main entry point
- `runwatch.py` - File watcher for auto-regeneration
- `card_generator.py` - Card HTML generation
- `spell_processing.py` - CSV loading, merging, sampling
- `text_formatting.py` - Text processing, splitting, abbreviations
- `spell_styling.py` - Damage type colorization
- `templates/` - HTML/CSS templates for cards
- `data/Spells-fixed.csv` - Manual spell corrections
- `data/Spells.csv` - Input data (place your CSV here)

## Requirements for Python Version

```
pandas==2.3.3
watchdog==6.0.0
```

Install with: `pip install -r requirements.txt`

## License

See LICENSE file.

## Support

**Found a bug?** Open an issue on the project's GitHub repository.

**Need help?** Check the error messages - they usually tell you exactly what's wrong and how to fix it.

**Want to contribute?** See the source code for development setup instructions.

---

## Credits

Spellcard Generator - A tool for D&D players

**Note:** This tool generates spell cards for personal use. All spell data is copyright Wizards of the Coast. Use responsibly and respect intellectual property rights.