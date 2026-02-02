"""Скрипт 2: Генерация словаря замен терминов"""

import json
import random
from pathlib import Path
from datetime import datetime
from faker import Faker

fake = Faker()
random.seed(42)

DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'

SYLLABLES = [
    'zan', 'dor', 'vex', 'kor', 'mel', 'trix', 'vor', 'nyx',
    'kal', 'brix', 'thon', 'mor', 'len', 'rax', 'zeph', 'lum',
    'kren', 'val', 'drax', 'syn', 'thal', 'rix', 'fel', 'gor'
]


def generate_fantasy_name(length=2):
    name = ''.join(random.choice(SYLLABLES) for _ in range(length))
    return name.capitalize()


def generate_character_name():
    return f"{generate_fantasy_name(2)} {generate_fantasy_name(2)}"


def generate_location_name(original):
    original_lower = original.lower()

    if 'elementary' in original_lower or 'school' in original_lower:
        return f"{generate_fantasy_name(2)} Academy"
    elif 'residence' in original_lower or 'house' in original_lower:
        return f"{generate_fantasy_name(2)} Manor"
    elif 'park' in original_lower and 'south' in original_lower:
        return f"{generate_fantasy_name(2)} Vale"
    elif 'playground' in original_lower:
        return f"{generate_fantasy_name(2)} Grounds"
    elif 'hospital' in original_lower:
        return f"{generate_fantasy_name(2)} Infirmary"
    elif 'church' in original_lower:
        return f"{generate_fantasy_name(2)} Temple"
    elif 'center' in original_lower:
        return f"{generate_fantasy_name(2)} Hall"
    elif 'street' in original_lower:
        return f"{generate_fantasy_name(2)} Boulevard"
    elif 'pond' in original_lower:
        return f"{generate_fantasy_name(2)} Lake"
    elif 'wok' in original_lower or 'restaurant' in original_lower:
        return f"{generate_fantasy_name(2)} Eatery"
    elif 'farms' in original_lower or 'farm' in original_lower:
        return f"{generate_fantasy_name(2)} Estates"
    else:
        return generate_fantasy_name(3)


def generate_event_name(original):
    clean = original.replace(',', '').replace('%27', "'")
    words = clean.split()
    new_words = []

    for word in words:
        if len(word) <= 3 or word.lower() in ['the', 'not', 'and', 'are', 'you']:
            new_words.append(word)
        else:
            new_words.append(generate_fantasy_name(1))

    return ' '.join(new_words)


def extract_all_terms():
    terms = {
        'characters': set(),
        'locations': set(),
        'entities': set(),
        'events': set()
    }

    print("[*] Extracting terms from JSON files...\n")

    for json_file in RAW_DIR.rglob('*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        title = data['title']
        category = data['category']

        if category == 'character':
            terms['characters'].add(title)
            if ' ' in title:
                parts = title.split()
                last_name = parts[-1]
                if last_name not in ['Jr.', 'Sr.', 'III']:
                    terms['characters'].add(last_name)
                first_name = parts[0]
                if first_name not in ['Mr.', 'Mrs.', 'Ms.', 'Dr.']:
                    terms['characters'].add(first_name)
        elif category == 'location':
            terms['locations'].add(title)
        elif category == 'event':
            terms['events'].add(title)

    terms['locations'].update(['South Park', 'Colorado', 'USA', 'United States', 'America'])
    terms['entities'].update([
        'Comedy Central', 'God', 'Jesus Christ', 'Jesus',
        'Santa Claus', 'Buddha', 'Mickey Mouse', 'World of Warcraft'
    ])

    print(f"  Characters: {len(terms['characters'])}")
    print(f"  Locations: {len(terms['locations'])}")
    print(f"  Entities: {len(terms['entities'])}")
    print(f"  Events: {len(terms['events'])}")
    print(f"  Total: {sum(len(v) for v in terms.values())}\n")

    return terms


def generate_terms_map():
    print("[*] Generating fantasy names...\n")
    all_terms = extract_all_terms()

    terms_map = {
        'metadata': {
            'source_universe': 'South Park (Comedy Central TV Show)',
            'target_universe': 'Zanvoria Chronicles',
            'generation_date': datetime.now().isoformat(),
            'total_terms': sum(len(v) for v in all_terms.values())
        },
        'characters': {},
        'locations': {},
        'entities': {},
        'events': {}
    }

    for category in ['characters', 'locations', 'entities', 'events']:
        sorted_terms = sorted(all_terms[category], key=len, reverse=True)

        for term in sorted_terms:
            if category == 'characters':
                replacement = generate_character_name()
            elif category == 'locations':
                replacement = generate_location_name(term)
            elif category == 'events':
                replacement = generate_event_name(term)
            else:
                replacement = generate_fantasy_name(2)

            terms_map[category][term] = replacement
            print(f"  {category:12} | {term:40} -> {replacement}")

    return terms_map


def main():
    print("=" * 70)
    print("  Скрипт 2: Генерация словаря замен")
    print("=" * 70 + "\n")

    json_files = list(RAW_DIR.rglob('*.json'))
    if not json_files:
        print("[ERROR] No JSON files found. Run script 1 first.")
        return

    print(f"[*] Found {len(json_files)} JSON files\n")

    terms_map = generate_terms_map()

    output_path = DATA_DIR / 'terms_map.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(terms_map, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Terms map saved to: {output_path}")
    print(f"[*] Total replacements: {terms_map['metadata']['total_terms']}")


if __name__ == "__main__":
    main()
