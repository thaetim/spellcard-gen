"""Color styling utilities for spell cards."""
import re


def blend_with_black(hex_color, blend_percent=50):
    """Blend a hex color with black by the given percentage."""
    if not hex_color or hex_color == '#000':
        return hex_color
    
    # Remove # and handle 3-digit shorthand
    hex_color = hex_color.lstrip('#')
    
    # Convert 3-digit to 6-digit hex
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    
    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Blend with black
    factor = 1 - blend_percent / 100
    r_blended = round(r * factor)
    g_blended = round(g * factor)
    b_blended = round(b * factor)
    
    # Convert back to hex
    return f"#{r_blended:02x}{g_blended:02x}{b_blended:02x}"


# Damage type colors
DAMAGE_COLORS_BASE = {
    'necrotic': ('#000',''),

    'fire': ('#f00',''),
    'acid': ('#0f0',''),
    'force': ('#00f',''),

    'radiant': ('#ff0',''),
    'STANDALONE DICE ROLLS': ('#000','#000'),
    'poison': ('#f0f',''),

    'lightning': ('#f80',''),
    'thunder': ('#0f8',''),
    'psychic': ('#f08',''),
    'cold': ('#08f',''),

    'bludgeoning': ('#000','#88f4'),
    'slashing': ('#000','#8f84'),
    'piercing': ('#000','#f884'),
}


DAMAGE_COLORS = {}
for damage_type, colors in DAMAGE_COLORS_BASE.items():
    color, bg_color = colors
    DAMAGE_COLORS[damage_type] = (
        blend_with_black(color, 75) if not bg_color else color,
        f"{color}3" if not bg_color else bg_color
    )

def colorize_text(text):
    """
    Apply coloring to damage expressions:
    - "XdY [+ Z] damage_type" → colored together (e.g., "2d4 + 1 force")
    - "N damage_type" → colored together (e.g., "1 force")
    - "DMG_TYPE damage" → colored (e.g., "fire damage")
    - "DMG_TYPE(and|or|,)DMG_TYPE chains" → each colored individually (e.g., "acid, fire, cold, lightning, or poison damage")
    - "XdY" alone → blue (e.g., "1d4 missiles")
    """
    if not text:
        return text
    
    from text_formatting import sanitize_html
    text = sanitize_html(text)
    
    # Step 1: Color damage type chains FIRST (e.g., "acid, fire, cold, lightning, or poison damage")
    # Match at least 2 damage types separated by conjunctions, followed by " damage"
    damage_types_pattern = '|'.join(re.escape(dmg_type) for dmg_type in DAMAGE_COLORS.keys())
    pattern_chain = rf'\b({damage_types_pattern})(?:\s*,\s*(?:{damage_types_pattern}))+(?:\s*,?\s*(?:and|or)\s*(?:{damage_types_pattern}))?\s+damage\b'
    
    def replace_damage_chain(match):
        full = match.group(0)
        if '<span' in full:
            return full
        
        # Extract the full damage chain (everything except " damage")
        damage_chain = full.rsplit(' damage', 1)[0]
        
        # Color each damage type individually within the chain
        colored_chain = damage_chain
        for dmg_type in DAMAGE_COLORS.keys():
            color, bg_color = DAMAGE_COLORS[dmg_type]
            # Replace each damage type with a colored version
            colored_chain = re.sub(
                rf'\b({re.escape(dmg_type)})\b',
                rf'<span style="color: {color}; background-color: {bg_color}; padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold;">\1</span>',
                colored_chain,
                flags=re.IGNORECASE
            )
        
        return f'{colored_chain} damage'
    
    text = re.sub(pattern_chain, replace_damage_chain, text, flags=re.IGNORECASE)
    
    # Step 2: Color dice expressions with damage type (handles "1d4 + 1 force" as one unit)
    for damage_type in DAMAGE_COLORS.keys():
        color, bg_color = DAMAGE_COLORS[damage_type]
        pattern = rf'((?:\d+d\d+\s*\+\s*)*\d+d\d+(?:\s*\+\s*\d+)*)\s+({re.escape(damage_type)})(?:\s+damage)?'
        
        def replace_dice_damage(match):
            if '<span' in match.group(0):
                return match.group(0)
            
            full_expr = match.group(1)
            damage_part = match.group(2)
            return f'<span style="color: {color}; background-color: {bg_color}; padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold;">{full_expr} {damage_part}</span>'
        
        text = re.sub(pattern, replace_dice_damage, text, flags=re.IGNORECASE)
    
    # Step 3: Color plain number + damage type (like "1 force")
    for damage_type in DAMAGE_COLORS.keys():
        color, bg_color = DAMAGE_COLORS[damage_type]
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
            return f'<span style="color: {color}; background-color: {bg_color}; padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold;">{num_part} {damage_part}</span>'
        
        text = re.sub(pattern, replace_num_damage, text, flags=re.IGNORECASE)
    
    # Step 4: Color standalone dice rolls (not followed by damage type)
    def color_standalone_dice(match):
        dice_text = match.group(0)
        
        # Check if already colored
        start = match.start()
        end = match.end()
        window_before = text[max(0, start - 10):start]
        if '<span' in window_before and '</span>' not in window_before:
            return dice_text
        
        # Check if followed by + N (modifier) or + XdY then damage type
        after_text = text[end:min(len(text), end + 100)]
        for dmg_type in DAMAGE_COLORS.keys():
            if re.match(rf'^\s*(?:(?:\+\s*(?:\d+|\d+d\d+)\s*)*){re.escape(dmg_type)}\b', after_text, re.IGNORECASE):
                return dice_text
        
        # color, bg_color = DAMAGE_COLORS['STANDALONE DICE ROLLS']
        # color = blend_with_black(color, 50)
        return f'<span style="color: #fff; background-color: var(--header-color); padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold;">{dice_text}</span>'
    
    text = re.sub(r'\b\d+d\d+\b', color_standalone_dice, text)
    
    return sanitize_html(text)
