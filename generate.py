import csv
import re

def clean_html_text(text):
    """Clean and format text for HTML display"""
    if not text:
        return ""
    # Replace line breaks with <br> tags
    text = text.replace('\n', '<br>')
    # Remove any existing HTML tags to prevent injection
    text = re.sub(r'<[^>]+>', '', text)
    return text

def generate_card_id(spell_name):
    """Generate a simple ID from spell name"""
    return re.sub(r'[^a-zA-Z0-9]', '', spell_name.lower())[:10]

def parse_classes(classes_str):
    """Parse classes string and return primary class"""
    if not classes_str:
        return ""
    
    # Extract the first class mentioned
    classes = classes_str.split(',')
    if classes:
        first_class = classes[0].strip()
        # Remove source in parentheses if present
        first_class = re.sub(r'\([^)]*\)', '', first_class).strip()
        return first_class
    return ""

def generate_spell_card(spell_data):
    """Generate HTML for a single spell card"""
    card_id = generate_card_id(spell_data['Name'])
    primary_class = parse_classes(spell_data.get('Classes', ''))
    
    # Format casting time
    casting_time = spell_data.get('Casting Time', '')
    if casting_time and not casting_time.startswith('1 '):
        casting_time = '1 ' + casting_time.lower()
    
    # Format components
    components = spell_data.get('Components', '')
    
    # Format duration
    duration = spell_data.get('Duration', '')
    
    # Format range
    range_val = spell_data.get('Range', '')
    
    # Format level and school into type
    level = spell_data.get('Level', '')
    school = spell_data.get('School', '')
    if level.lower() == 'cantrip':
        spell_type = f"{school} cantrip"
    else:
        spell_type = f"{level}-level {school.lower()}"
    
    # Check if weapon component is needed
    need_weapon = "a weapon" if "weapon" in components.lower() else ""
    
    # Prepare text and higher levels
    text = clean_html_text(spell_data.get('Text', ''))
    higher_levels = clean_html_text(spell_data.get('At Higher Levels', ''))
    
    if higher_levels:
        text += f'<br><br><b>At Higher Levels:</b> {higher_levels}'
    
    html = f'''
<div id="{card_id}" class="card cardBlock class-{primary_class}">
  <div class="front">
    <div class="body">
      <h3 class="name lined srname">{spell_data["Name"]} ({spell_data.get("Source", "")})</h3>
      <ul class="status lined">
        <li><em>casting time</em>{casting_time}</li>
        <li class="second"><em>range</em>{range_val}</li>
        <br clear="all">
      </ul>
      <ul class="status lined">
        <li><em>components</em>{components}</li>
        <li class="second small"><em>duration</em>{duration}</li>      
        <br clear="all">
      </ul>'''
    
    if need_weapon:
        html += f'\n              <b class="need">{need_weapon}</b>'
    
    html += f'''
      <p class="text">
        {text}
      </p>                     
      
    </div>        
    <b class="class srclass">{primary_class}</b>
    <b class="type srtype">{spell_type}</b>
  </div>
</div>
'''
    return html

def load_csv_and_generate_cards(csv_file_path):
    """Load CSV and generate spell cards"""
    spells_html = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            # Use DictReader to read CSV as dictionary
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # Clean up the data
                cleaned_row = {key: value.strip() if value else "" for key, value in row.items()}
                card_html = generate_spell_card(cleaned_row)
                spells_html.append(card_html)
                
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []
    
    return spells_html

def save_html_output(spells_html, output_file='spell_cards.html'):
    """Save generated spell cards to HTML file"""
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spell Cards</title>
    <style>
        .card {{
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 15px;
            margin: 10px;
            background: #f9f9f9;
            font-family: Arial, sans-serif;
        }}
        .name {{
            color: #333;
            border-bottom: 1px solid #666;
            padding-bottom: 5px;
        }}
        .status {{
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }}
        .status li {{
            display: inline-block;
            margin-right: 20px;
        }}
        .status em {{
            font-style: italic;
            color: #666;
        }}
        .need {{
            color: #d00;
            font-weight: bold;
        }}
        .text {{
            margin: 10px 0;
            line-height: 1.4;
        }}
        .srclass, .srtype {{
            display: block;
            margin-top: 10px;
            font-weight: bold;
            color: #444;
        }}
        .lined {{
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        .second {{
            float: right;
        }}
        .small {{
            font-size: 0.9em;
        }}
        br.clear {{
            clear: both;
        }}
    </style>
</head>
<body>
{''.join(spells_html)}
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Spell cards saved to {output_file}")

def main():
    # Example usage
    csv_file = 'data/Spells.csv'  # Change this to your CSV file path
    output_file = 'out/spell_cards.html'
    
    # Generate spell cards
    spells_html = load_csv_and_generate_cards(csv_file)
    
    if spells_html:
        # Save to HTML file
        save_html_output(spells_html, output_file)
        print(f"Generated {len(spells_html)} spell cards!")
        
        # Also print first card as example
        print("\nFirst card preview:")
        print(spells_html[0][:500] + "...")
    else:
        print("No spell cards were generated.")

if __name__ == "__main__":
    main()