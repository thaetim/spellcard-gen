"""Spell data processing and text manipulation utilities."""
import re
import pandas as pd


# Constants for sampling
N_SAMPLE_THRESH = 200#00000
N_SAMPLE = 69
N_SAMPLE_PHRASES = [
    "Augury",
    "Bestow Curse",
    "Conjure Animals",
    "Conjure Minor Elementals",
    "Conjure Woodland Beings",
    "Contaminated Power",
    "Control Flames",
    "Draconic Transformation",
    "Druid Grove",
    "Druidcraft",
    "Feathered Reach",
    "Fizban's Platinum Shield",
    "Gust",
    "Investiture of Flame",
    "Investiture of Ice",
    "Investiture of Stone",
    "Investiture of Wind",
    "Magic Circle",
    "Mend Plants",
    "Mold Earth",
    "Mordenkainen's Private Sanctum",
    "Pratfall",
    "Prestidigitation",
    "Shape Water",
    "Swallow Magic",
    "Tasha's Otherworldly Guise",
    "Tenser's Transformation",
    "Thaumaturgy",
    "Warding Wind",
    "Wish",
]


def load_spells(csv_path, sample_phrases=None):
    """Load spells from CSV with optional sampling."""
    df = pd.read_csv(csv_path, encoding='utf-8').fillna("")
    
    if len(df) > N_SAMPLE_THRESH:
        phrases = sample_phrases or N_SAMPLE_PHRASES
        phrase_mask = pd.Series(False, index=df.index)
        
        for phrase in phrases:
            text_columns = ['Name'] # ['Text', 'At Higher Levels', 'Name', 'Description']
            for col in text_columns:
                if col in df.columns:
                    phrase_mask = phrase_mask | df[col].str.contains(phrase, case=False, na=False)
        
        phrase_rows = df[phrase_mask]
        remaining_sample = max(0, N_SAMPLE - len(phrase_rows))
        
        if remaining_sample > 0:
            remaining_df = df[~phrase_mask]
            if len(remaining_df) > remaining_sample:
                import random
                random_sample = remaining_df.sample(n=remaining_sample, random_state=random.randint(0, 9999))
            else:
                random_sample = remaining_df
        else:
            random_sample = pd.DataFrame()
        
        df = pd.concat([phrase_rows, random_sample], ignore_index=True)
        print(f"Loaded sample of {len(df)} spells from {csv_path} (including {len(phrase_rows)} with sample phrases)")
    else:
        print(f"Loaded all {len(df)} spells from {csv_path}")
    
    return df


def merge_spell_duplicates(spells_df):
    """Merge duplicate spell entries, keeping longest text versions."""
    def merge_texts(series):
        longest = max(series, key=lambda s: len(s or ""), default="")
        return longest.strip()

    def merge_sources(series):
        core = {'PHB', 'SRD', 'DMG'}
        parts = [s for s in series.dropna() if s and s not in core]
        seen, uniq = set(), []
        for s in parts:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        return ', '.join(uniq) if uniq else (series.dropna().iloc[0] if not series.empty else "")

    def merge_lists(series):
        all_items = []
        for v in series.dropna():
            all_items.extend([x.strip() for x in v.split(',') if x.strip()])
        seen, uniq = set(), []
        for x in all_items:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        return ', '.join(uniq)

    spells_df = spells_df.sort_values('Name')
    
    merged = (
        spells_df.groupby("Name", dropna=False, sort=False)
        .agg({
            "Source": merge_sources,
            "Classes": merge_lists,
            "Optional/Variant Classes": merge_lists,
            "Subclasses": merge_lists,
            "Text": merge_texts,
            "At Higher Levels": merge_texts,
            **{col: "first" for col in spells_df.columns if col not in {
                "Name", "Source", "Classes", "Optional/Variant Classes", "Subclasses", "Text", "At Higher Levels"
            }}
        })
        .reset_index()
    )
    
    merged = merged.sort_values('Name').reset_index(drop=True)
    return merged.to_dict(orient="records")


def load_fixed_spells(csv_path):
    """Load manually fixed spell data."""
    try:
        fixed_df = pd.read_csv(csv_path, encoding='utf-8').fillna("")
        fixed_spells = {spell['Name']: spell.to_dict() for _, spell in fixed_df.iterrows()}
        print(f"Loaded {len(fixed_spells)} fixed spells from {csv_path}")
        return fixed_spells
    except Exception as e:
        print(f"Could not load fixed spells: {e}")
        return {}


def detect_broken_elements(text):
    if not text:
        return None
    
    patterns = [
        # # broken table headers
        r'\b[a-z]+(?:[A-Z][a-z]+){2,}\b',
        r'\b(?:[a-z]+[A-Z]|[A-Z][a-z]+|\d+){4,}\b',
        r'\b(?:[A-Z][a-z]*){3,}(?:\d+[A-Z][a-z]*)*\b',
        # broken lists
        r'[a-zA-Z][a-zA-Z]\d'
    ]
    
    detected_issues = {}

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            detected_issues = tuple(matches)
            break
    
    return detected_issues if detected_issues else None
