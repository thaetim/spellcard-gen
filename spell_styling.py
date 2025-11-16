"""Color styling utilities for spell cards."""
import re
from text_formatting import sanitize_html

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
    - "DMG_TYPE damage" → colored (e.g., "fire damage")  <-- controlled by COLORIZE_UNDICED
    - "DMG_TYPE(and|or|,)DMG_TYPE chains" → each colored individually
    - "XdY" alone → blue (e.g., "1d4 missiles")
    """
    if not text:
        return text
    
    # Set this to True to also colorize damage-type phrases that are not explicitly
    # preceded by a dice expression (e.g., "fire damage", "piercing or slashing damage").
    COLORIZE_UNDICED = True

    text = sanitize_html(text)

    # Build damage types pattern from DAMAGE_COLORS keys
    damage_types = list(DAMAGE_COLORS.keys())
    damage_types_escaped = [re.escape(dt) for dt in damage_types]
    damage_types_pattern = '|'.join(damage_types_escaped)

    # Step 1: Color damage type chains FIRST (e.g., "acid, fire, cold, lightning, or poison damage")
    # Also matches patterns like "slashing or piercing damage" without commas
    pattern_chain = rf'\b({damage_types_pattern})(?:(?:\s*,\s*|\s+(?:and|or)\s+)(?:{damage_types_pattern}))+(?:\s*,?\s*(?:and|or)\s*(?:{damage_types_pattern}))?\s+damage\b'

    def replace_damage_chain(match):
        full = match.group(0)
        if '<span' in full:
            return full

        # Extract the chain without the trailing " damage"
        damage_chain = full.rsplit(' damage', 1)[0]

        colored_chain = damage_chain
        for dmg_type in damage_types:
            color, bg_color = DAMAGE_COLORS[dmg_type]
            colored_chain = re.sub(
                rf'\b({re.escape(dmg_type)})\b',
                rf'<span style="color: {color}; background-color: {bg_color}; padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold; border: 1px solid #0003;">\1</span>',
                colored_chain,
                flags=re.IGNORECASE
            )

        return f'{colored_chain} damage'

    # Apply chain coloring regardless of COLORIZE_UNDICED only if we want undiced coloring.
    if COLORIZE_UNDICED:
        text = re.sub(pattern_chain, replace_damage_chain, text, flags=re.IGNORECASE)
    else:
        # Still remove/skip already-colored chains to avoid double-coloring later:
        # If an existing chain already contains a span, leave it alone (no substitution).
        # (No-op here; keeping for clarity.)
        pass

    # Dice-sequence pattern allowing numeric modifiers as well (e.g., "+ 14")
    dice_seq = r'(?:\s*\d+d\d+\s*(?:[+-]\s*(?:\d+d\d+|\d+)\s*)*)'

    # Step 2: Color dice expressions with damage type (handles "1d4 + 1 force" as one unit)
    for damage_type in damage_types:
        color, bg_color = DAMAGE_COLORS[damage_type]
        pattern = rf'((?:\d+d\d+\s*(?:[+-]\s*(?:\d+d\d+|\d+)\s*)*))\s+({re.escape(damage_type)})(?:\s+damage)?'

        def replace_dice_damage(match):
            if '<span' in match.group(0):
                return match.group(0)
            dice_part = match.group(1).strip()
            damage_part = match.group(2)
            return (
                f'<span style="color: {color}; background-color: {bg_color}; '
                f'padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold; border: 1px solid #0003;">'
                f'{dice_part} {damage_part}</span>'
            )

        text = re.sub(pattern, replace_dice_damage, text, flags=re.IGNORECASE)

    # Step 3: Color plain number + damage type (like "1 force")
    for damage_type in damage_types:
        color, bg_color = DAMAGE_COLORS[damage_type]
        pattern = rf'\b(\d+)\s+({re.escape(damage_type)})(?:\s+damage)?'

        def replace_num_damage(match):
            full = match.group(0)
            if '<span' in full:
                return full

            # Skip if preceded by 'd' (part of dice notation)
            start_pos = match.start()
            if start_pos > 0 and text[start_pos - 1].lower() == 'd':
                return full

            # Skip if preceded by '+' (likely part of a dice expression already handled)
            check_before = text[max(0, start_pos - 5):start_pos]
            if re.search(r'\+\s*$', check_before):
                return full

            num_part = match.group(1)
            damage_part = match.group(2)
            return (
                f'<span style="color: {color}; background-color: {bg_color}; '
                f'padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold; border: 1px solid #0003;">'
                f'{num_part} {damage_part}</span>'
            )

        text = re.sub(pattern, replace_num_damage, text, flags=re.IGNORECASE)

    # Step 4: Optionally color plain "DMG_TYPE damage" when COLORIZE_UNDICED is True
    if COLORIZE_UNDICED:
        for damage_type in damage_types:
            color, bg_color = DAMAGE_COLORS[damage_type]
            pattern = rf'\b({re.escape(damage_type)})\s+damage\b'

            def replace_plain_damage(match):
                full = match.group(0)
                if '<span' in full:
                    return full
                dmg = match.group(1)
                return (
                    f'<span style="color: {color}; background-color: {bg_color}; '
                    f'padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold; border: 1px solid #0003;">'
                    f'{dmg}</span> damage'
                )

            text = re.sub(pattern, replace_plain_damage, text, flags=re.IGNORECASE)

    # Step 5: Color standalone dice rolls (not followed by damage type)
    def color_standalone_dice(match):
        dice_text = match.group(0)

        # Avoid recoloring inside an already-open span
        start = match.start()
        window_before = text[max(0, start - 50):start]
        if '<span' in window_before and '</span>' not in window_before:
            return dice_text

        # Check if followed by modifiers and a damage type (already handled)
        end = match.end()
        after_text = text[end:end + 100]
        for dmg_type in damage_types:
            if re.match(rf'^\s*(?:(?:\+\s*(?:\d+|\d+d\d+)\s*)*){re.escape(dmg_type)}\b', after_text, re.IGNORECASE):
                return dice_text

        return (
            f'<span style="color: #fff; background-color: var(--header-color); '
            f'padding: 0 2px; border-radius: 2px; font-family: Courier; font-weight: bold; border: 1px solid #0003;">'
            f'{dice_text}</span>'
        )

    text = re.sub(r'\b\d+d\d+\b', color_standalone_dice, text)

    return sanitize_html(text)

