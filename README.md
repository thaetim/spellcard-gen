# Spellcard Generator

Generates printable D&D 5e spell cards from CSV data exported from 5e.tools Table View.

## Overview

This tool converts spell data into professionally formatted, print-ready spell cards. It automatically processes spell text, applies abbreviations, colorizes damage types, and intelligently sizes cards based on content length (single, double, or triple width).

![alt text](assets/image.png)

## Features

- **Automatic card sizing**: Single, double, or triple-width cards based on text length
- **Smart attribute display**: Special spell properties (Concentration, Ritual, area effects) shown as badges instead of generic labels
- **Smart text formatting**: Enumerations converted to tables, broken line breaks fixed
- **Damage type colorization**: Damage types highlighted in color
- **Abbreviations**: Common D&D terms shortened (HP, AC, CR, etc.)
- **Duplicate merging**: Combines duplicate spell entries, keeping longest text versions
- **Manual overrides**: `data/Spells-fixed.csv` for correcting problematic spells
- **Live reloading**: Auto-regenerate on file changes with `runwatch.py`
- **Print optimization**: Cards arranged for efficient printing (triple cards use full rows, doubles paired with singles)

### Smart Attribute Display

The attribute table shows spell properties with context-aware labeling:

- **Concentration spells**: "Concentration" badge replaces "Duration" label
- **Ritual spells**: "or Ritual" badge replaces "Casting Time" label  
- **Area effects**: Range shows area type (e.g., "Self Radius", "Touch Cone") instead of generic "Range"

This reduces visual clutter while highlighting important spell properties at a glance.

## Usage

### Basic Usage
```bash
python generate.py
```
Press ENTER to regenerate, ESC to exit.

### Developer Mode (Single Run)
```bash
python generate.py --dev
```
Runs once and exits (no interactive prompt).

### Watch Mode (Auto-Regenerate)
```bash
python runwatch.py
```
Automatically regenerates cards when source files change. Monitors:
- Core Python files: `generate.py`, `card_generator.py`, `spell_processing.py`, etc.
- `templates/` directory: HTML/CSS templates
- `data/` directory: `Spells-fixed.csv` corrections

Includes 4-second debounce to prevent rapid rebuilds. Press Ctrl+C to stop.

## Typical Workflow

1. **Initial setup**: Run `python generate.py` to generate initial cards
2. **Development loop** with `runwatch.py`:
   - Start watch mode: `python runwatch.py`
   - Open `spell_cards.html` in browser with auto-reload extension (like [Live Server](https://open-vsx.org/extension/ritwickdey/LiveServer))
   - Edit templates, Python code, or `data/Spells-fixed.csv`
   - Cards auto-regenerate on save
   - \* Refresh browser to see changes
3. **Final generation**: Stop watch mode, run `python generate.py` once more for clean output

This workflow enables rapid iteration on card styling, text formatting, and spell corrections without manual rebuilds.

## Input Data

### Data Source
Go to [5e.tools Spells Table](https://2014.5e.tools/spells.html). To get the list of spells relevant for you, you can:

- Utilities / Load All Partnered Content
- Utilities / Homebrew Manager > Get Homebrew (blue button) > Select desired > Add Selected (blue download button)
- Adjust the Filters
- Pin the spells to a list (shortcut: press `P`); Note that this takes precedence over the filtered list of spells in the Table view

When you have the list ready either (filtered or pinned) open the Table View > Export to CSV.
Finally, place your spell CSV in the root directory (default: `Spells.csv`).

### Sampling for Large Lists

By default, if your CSV contains more than **200 spells**, the script generates only a **sample of 69 spells** to speed up development. The sample includes:
- All spells matching specific test phrases (defined in `N_SAMPLE_PHRASES` in `spell_processing.py`)
- Random spells to fill up to 69 total

**To generate all spells**, edit `spell_processing.py` and change:
```python
N_SAMPLE_THRESH = 200
```
to a large number like:
```python
N_SAMPLE_THRESH = 999999
```

> **⚠️ Warning**: Generating large spell lists (200+ spells) can cause the browser's font autosizing JavaScript to take several minutes to complete. The HTML file will load, but text may appear unsized until the script finishes processing all cards.

### Manual Corrections: `data/Spells-fixed.csv`
Contains manually corrected spell data to override automatic processing. The script checks this file first for each spell. See [DATA_MANIPULATION.md](DATA_MANIPULATION.md) for details on available manipulations.

## Output

Both output files are generated in the root:

- `spell_cards.html` - Print-ready HTML file with all spell cards
- `autosize.js` - JavaScript for card text sizing (copied to root)

## Requirements

```
pandas==2.3.3
watchdog==6.0.0
```

Install with: `pip install -r requirements.txt`

## File Structure

- `generate.py` - Main entry point
- `runwatch.py` - File watcher for auto-regeneration
- `card_generator.py` - Card HTML generation
- `spell_processing.py` - CSV loading, merging, sampling
- `text_formatting.py` - Text processing, splitting, abbreviations
- `spell_styling.py` - Damage type colorization
- `templates/` - HTML/CSS templates for cards
- `data/Spells-fixed.csv` - Manual spell corrections
- `data/Spells.csv` - Input data

## Card Types

- **Single**: Standard spell description (<800 chars)
- **Double**: Long spell split across two cards
- **Triple**: Very long spell split across three cards

## License

See LICENSE file.
