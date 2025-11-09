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
    """Apply coloring to dice rolls and damage types in spell text."""
    if not text:
        return text
    
    from text_formatting import sanitize_html
    text = sanitize_html(text)
    
    def replace_damage_and_dice(match):
        full_match = match.group(0)
        
        if '<span' in full_match and '</span>' in full_match:
            return full_match
            
        if 'd' in full_match.lower() and any(dmg_type in full_match.lower() for dmg_type in DAMAGE_COLORS.keys()):
            for damage_type, color in DAMAGE_COLORS.items():
                pattern = rf'(\b\d+d\d+\+?\d*\b)(?:\s+(?:nonmagical|magical))?\s+({re.escape(damage_type)}\s+damage\b)'
                damage_match = re.search(pattern, full_match, re.IGNORECASE)
                if damage_match:
                    dice_part = damage_match.group(1)
                    damage_part = damage_match.group(2)
                    return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{dice_part}</span> <span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{damage_part}</span>'
        
        for damage_type, color in DAMAGE_COLORS.items():
            if damage_type in full_match.lower():
                shorthand_pattern = rf'\b{re.escape(damage_type)}\b'
                shorthand_match = re.search(shorthand_pattern, full_match, re.IGNORECASE)
                if shorthand_match:
                    context = text[max(0, match.start()-10):min(len(text), match.end()+10)]
                    if re.search(rf'\d+d\d+.*?\b{re.escape(damage_type)}\b', context) or \
                       re.search(rf'\b{re.escape(damage_type)}\b(?:\s|$)', full_match):
                        return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace; font-weight: bold;">{damage_type}</span>'
        
        return full_match
    
    processed_text = text
    
    damage_patterns = []
    for damage_type in DAMAGE_COLORS.keys():
        damage_patterns.extend([
            rf'\b\d+d\d+\+?\d*\b(?:\s+(?:nonmagical|magical))?\s+{re.escape(damage_type)}\s+damage\b',
            rf'\b{re.escape(damage_type)}\s+damage\b',
            rf'[a-z]{re.escape(damage_type)}\s+damage\b',
            rf'\b{re.escape(damage_type)}\b'
        ])
    
    combined_pattern = '|'.join(damage_patterns)
    
    if combined_pattern:
        processed_text = re.sub(combined_pattern, replace_damage_and_dice, processed_text, flags=re.IGNORECASE)
    
    def color_standalone_dice(match):
        dice_text = match.group(0)
        start = match.start()
        window = processed_text[max(0, start - 50):start + 50]
        if '<span' in window:
            return dice_text
        color = '#0000FF'
        return f'<span style="color: {color}; background-color: {color}20; padding: 0 2px; border-radius: 2px; font-family: monospace;">{dice_text}</span>'

    processed_text = re.sub(r'\b\d+d\d+\+?\d*\b', color_standalone_dice, processed_text)

    return sanitize_html(processed_text)
