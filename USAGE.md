# Spellcard Generator - User Guide

A tool for D&D players to generate beautiful, printable spell cards from CSV data.

## Quick Start

### Option 1: Simple Usage (Recommended for Most Users)

1. **Get the executable**: Download `spellcard-generator_X.X.X.exe`
2. **Prepare your spell data**: Place your `Spells.csv` file in the same folder as the exe
3. **Run the program**: Double-click `spellcard-generator_X.X.X.exe`
4. **Find your cards**: Open the generated `spell_cards.html` file in the `out/` folder

### Option 2: Drag and Drop

1. **Drag your CSV file** onto the exe
2. Cards will be generated in the `out/` folder next to the exe
3. Press any key to close when done

---

## What You Need

### Required: A Spell CSV File

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

```csv
"Name","Level","School","Casting Time","Range","Components","Duration","Text"
"Fireball","3rd","Evocation","Action","150 feet","V, S, M (a tiny ball of bat guano)","Instantaneous","A bright streak flashes from your pointing finger..."
"Cure Wounds","1st","Evocation","Action","Touch","V, S","Instantaneous","A creature you touch regains hit points..."
```

**Example of proper quoting:**
```csv
"Shield","1st","Abjuration","Reaction","Self","V, S","1 round","An invisible barrier of magical force appears and protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from magic missile."
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

### Advanced Options

```bash
# Developer mode (no waiting for user input)
spellcard-generator_1.0.0.exe --dev

# Loop mode with custom CSV
spellcard-generator_1.0.0.exe "MySpells.csv" --loop
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

## Troubleshooting

### "ERROR: CSV file not found"

**Problem:** The program can't find your spell data.

**Solution:**
1. Make sure `Spells.csv` is in the **same folder** as the exe
2. Or drag your CSV file directly onto the exe
3. Check the file name is exactly `Spells.csv` (case-sensitive)

---

### "ERROR: CSV file validation failed"

**Problem:** Your CSV file has formatting issues.

**Common issues and fixes:**

#### Missing Required Columns
```
Missing required columns: Text, Duration
```
**Fix:** Add the missing columns to your CSV file. All required columns (Name, Level, School, etc.) must be present.

#### Invalid Level Values
```
Level field issues:
  Row 5: Invalid level '3rd level'
```
**Fix:** Level should be:
- `"Cantrip"` (for cantrips)
- `"1st"`, `"2nd"`, `"3rd"`, `"4th"`, `"5th"`, etc. (ordinal numbers)
- `"1"`, `"2"`, `"3"`, etc. (plain numbers also work)

#### CSV Formatting Issues
```
CSV formatting issues (unquoted newlines or commas):
  Row 12: Has 16 columns, expected 14
```
**Fix:** Fields containing commas or newlines must be enclosed in double quotes:

❌ **Wrong:**
```csv
Fireball,3rd,Evocation,Action,150 feet,V, S, M (bat guano),Instantaneous,A bright streak...
```

✅ **Correct:**
```csv
"Fireball","3rd","Evocation","Action","150 feet","V, S, M (bat guano)","Instantaneous","A bright streak..."
```

#### Encoding Issues
```
File encoding error: CSV must be UTF-8 encoded
```
**Fix:** Save your CSV file with UTF-8 encoding:
- **Excel:** Save As → CSV UTF-8 (Comma delimited)
- **Google Sheets:** File → Download → CSV
- **LibreOffice:** Save As → Text CSV → Character set: Unicode (UTF-8)

---

### Cards Look Wrong

**Text is cut off or overlapping:**
- Some spells with very long descriptions may need manual adjustment
- Check the console output for spells that need fixing
- The program will list: `Spells needing manual description fix`

**Colors are wrong:**
- Make sure "Background graphics" is enabled in print settings
- Try a different browser (Chrome recommended)

**Cards don't fit the page:**
- Use Portrait orientation
- Set margins to None or Minimum
- Ensure scale is 100%

---

### Antivirus Warnings

Some antivirus software (like ESET) may flag the exe as suspicious. This is a **false positive**.

**Why this happens:**
- PyInstaller-compiled executables are sometimes flagged
- The exe is perfectly safe and contains no malware

**Solutions:**
1. **Add an exception** in your antivirus for the exe
2. **Temporarily disable** antivirus while running (not recommended)
3. **Run from source code** instead (requires Python - see README.md)
4. **Submit false positive** report to your antivirus vendor

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

Run the program on each file to generate separate card sets.

### Updating Your Cards

**Quick workflow for frequent updates:**
1. Keep the program window open with `--loop` flag
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

### Sharing with Your Party

1. Generate cards for party-wide spells (like rituals)
2. Save `spell_cards.html` as PDF (Ctrl+P → Save as PDF)
3. Share the PDF with your group
4. Everyone prints the same set

---

## Example Workflows

### Workflow 1: First-Time Setup

```
1. Download spellcard-generator_1.0.0.exe
2. Create Spells.csv with your wizard's spells
3. Put both files in a folder: D&D/Spellcards/
4. Double-click the exe
5. Open out/spell_cards.html
6. Print your cards!
```

### Workflow 2: Level Up (Adding New Spells)

```
1. Open your existing Spells.csv
2. Add new spells you learned
3. Save the CSV
4. Run: spellcard-generator_1.0.0.exe
5. Print only the new cards (or print all)
```

### Workflow 3: Multiple Characters

```
D&D/
├── Wizard/
│   ├── spellcard-generator_1.0.0.exe
│   ├── Spells.csv (wizard spells)
│   └── out/spell_cards.html
└── Cleric/
    ├── spellcard-generator_1.0.0.exe (copy)
    ├── Spells.csv (cleric spells)
    └── out/spell_cards.html
```

Each character has their own folder with their own spell cards.

---

## Getting Spell Data

### Option 1: Manual Entry

Create a CSV file in Excel, Google Sheets, or any text editor:

```csv
"Name","Level","School","Casting Time","Range","Components","Duration","Text"
"Magic Missile","1st","Evocation","Action","120 feet","V, S","Instantaneous","You create three glowing darts..."
```

### Option 2: Export from D&D Beyond

1. View your character's spell list
2. Copy spell data
3. Format as CSV

### Option 3: Use Existing Databases

Many D&D spell databases exist online - convert to CSV format.

**Important:** Respect copyright! Only use spell data you have legitimate access to.

---

## FAQ

**Q: Can I customize the card appearance?**  
A: The card styles are defined in the template files. For advanced customization, you'll need to modify the template HTML/CSS files (requires programming knowledge).

**Q: What size are the cards?**  
A: Cards are designed for standard letter size paper (8.5" × 11"). Three cards fit across the page width.

**Q: Can I use this for Pathfinder or other games?**  
A: Yes! As long as you can format your spell data into the required CSV structure, the generator will work.

**Q: Does this work on Mac/Linux?**  
A: The pre-built exe is Windows-only. For Mac/Linux, run from Python source (see README.md).

**Q: Can I distribute the generated cards?**  
A: You can use the cards for personal use. Distributing them may have copyright implications depending on the source of your spell data.

**Q: The program closes immediately!**  
A: Run from command line to see error messages, or check if CSV file is present.

**Q: Can I generate cards for homebrew spells?**  
A: Absolutely! Just add them to your CSV file with all required fields.

---

## Support

**Found a bug?** Open an issue on the project's GitHub repository.

**Need help?** Check the error messages - they usually tell you exactly what's wrong and how to fix it.

**Want to contribute?** See README.md for development setup instructions.

---

## Credits

Spellcard Generator - A tool for D&D players  
Version 1.0.0

**Note:** This tool generates spell cards for personal use. All spell data is copyright Wizards of the Coast. Use responsibly and respect intellectual property rights.
