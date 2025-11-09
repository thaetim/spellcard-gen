"""Color styling utilities for spell cards."""
import re


def blend_with_black(hex_color, blend_percent=50):
    """Blend a hex color with black by the given percentage."""
    if not hex_color or hex_color.lower() == '#000000':
        return hex_color
    r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
    factor = 1 - blend_percent / 100
    return f'#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}'


# Damage type colors (50% blended with black)
DAMAGE_COLORS_BASE = {
    'acid': '#00FF00',
    'bludgeoning': '#808080',
    'cold': '#00FFFF',
    'fire': '#FF0000',
    'force': '#800080',
    'lightning': '#FFFF00',
    'necrotic': '#000000',
    'piercing': '#808080',
    'poison': '#800080',
    'psychic': '#FFC0CB',
    'radiant': '#FFFFFF',
    'slashing': '#808080',
    'thunder': '#808080',
}

DAMAGE_COLORS = {
    damage_type: blend_with_black(color, 50) 
    for damage_type, color in DAMAGE_COLORS_BASE.items()
}


def colorize_text(text):
    """
    Apply coloring to damage expressions:
    - "XdY [+ Z] damage_type" → colored together (e.g., "2d4 + 1 force")
    - "N damage_type" → colored together (e.g., "1 force")
    - "XdY" alone → blue (e.g., "1d4 missiles")
    """
    if not text:
        return text
    
    from text_formatting import sanitize_html
    text = sanitize_html(text)
    
    # Step 1: Color dice expressions with damage type (handles "1d4 + 1 force" as one unit)
    for damage_type, color in DAMAGE_COLORS.items():
        # Pattern: XdY [+ N] [+ N] ... damage_type
        # Matches full expressions like "1d4 + 1 force" or "2d6 + 3 + 1 fire"
        pattern = rf'(\d+d\d+(?:\s*\+\s*\d+)*)\s+({re.escape(damage_type)})(?:\s+damage)?'
        
        def replace_dice_damage(match):
            if '<span' in match.group(0):
                return match.group(0)
            
            full_expr = match.group(1)
            damage_part = match.group(2)
            return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{full_expr} {damage_part}</span>'
        
        text = re.sub(pattern, replace_dice_damage, text, flags=re.IGNORECASE)
    
    # Step 2: Color plain number + damage type (like "1 force")
    for damage_type, color in DAMAGE_COLORS.items():
        pattern = rf'\b(\d+)\s+({re.escape(damage_type)})(?:\s+damage)?'
        
        def replace_num_damage(match):
            full = match.group(0)
            if '<span' in full:
                return full
            
            # Skip if preceded by 'd' (part of dice notation)
            start_pos = match.start()
            if start_pos > 0 and text[start_pos - 1] == 'd':
                return full
            
            # Skip if preceded by '+' and whitespace (part of dice modifier already colored)
            check_before = text[max(0, start_pos - 5):start_pos]
            if re.search(r'\+\s*$', check_before):
                return full
            
            num_part = match.group(1)
            damage_part = match.group(2)
            return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{num_part} {damage_part}</span>'
        
        text = re.sub(pattern, replace_num_damage, text, flags=re.IGNORECASE)
    
    # Step 3: Color standalone dice rolls (not followed by damage type)
    def color_standalone_dice(match):
        dice_text = match.group(0)
        
        # Check if already colored
        start = match.start()
        end = match.end()
        window_before = text[max(0, start - 10):start]
        if '<span' in window_before and '</span>' not in window_before:
            return dice_text
        
        # Check if followed by + N (modifier) then damage type
        after_text = text[end:min(len(text), end + 50)]
        for dmg_type in DAMAGE_COLORS.keys():
            # Check for patterns like "+ 1 force" or "force" after dice
            if re.match(rf'^\s*(?:\+\s*\d+\s+)?{re.escape(dmg_type)}\b', after_text, re.IGNORECASE):
                return dice_text
        
        color = '#0000FF'
        return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace;">{dice_text}</span>'
    
    text = re.sub(r'\b\d+d\d+\b(?!\s*\+)', color_standalone_dice, text)
    
    return sanitize_html(text)
