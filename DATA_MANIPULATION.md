# Data Manipulation Guide: spells-fixed.csv

## Overview

`data/Spells-fixed.csv` contains manually corrected spell data that overrides automatic processing. The script checks this file for each spell name and uses the fixed version if found.

## Location

**Expected path**: `data/Spells-fixed.csv`

The script looks for this file relative to the project root directory.

## CSV Structure

Use the same columns as the main spell CSV:
- Name *(required, used as lookup key)*
- Level
- School
- Casting Time
- Range
- Components
- Duration
- Classes
- Optional/Variant Classes
- Subclasses
- Text
- At Higher Levels
- Source

## Manipulation Options

### 1. Text Corrections
Fix broken enumeration formatting, malformed HTML, or incorrect spell descriptions.

**Common fixes:**
- Broken table headers (e.g., `SpellSlotLevelSpacesAvailable` → proper table markup)
- Missing line breaks
- Incorrect damage dice
- Malformed HTML tags

### 2. HTML Formatting
Add or correct HTML elements:
- `<br>` for line breaks
- `<table><tr><td>content</td></tr></table>` for structured data
- `<b>text</b>` for emphasis

### 3. Field Overrides
Override any column:
- **Duration**: Fix concentration duration format
- **Range**: Correct area of effect descriptions
- **Components**: Fix material component text
- **Classes**: Correct class availability

### 4. Complete Rewrites
Replace entire spell entries for heavily malformed data. Simply add a row with the spell's Name and corrected values for all relevant columns.

## Workflow

1. Run generator and check terminal output for "Spells needing manual description fix"
2. Export problematic spells from main CSV
3. Correct data in `data/Spells-fixed.csv`
4. Re-run generator - fixed versions override originals

## Example Entry

```csv
Name,Level,School,Text,...
"Chaos Bolt",1,Evocation,"You hurl a bolt of chaotic energy. Make a ranged spell attack...<br><table><tr><td>► 1-2 Acid</td></tr><tr><td>► 3-4 Cold</td></tr></table>...",...
```

## Notes

- Fixed spells don't receive automatic text processing (enumeration fixes, abbreviations, etc.)
- Apply manual formatting as needed
- Script reports number of loaded fixed spells at startup
