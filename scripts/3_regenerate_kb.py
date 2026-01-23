"""Скрипт 3: Регенерация базы знаний с заменой терминов"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
KB_DIR = Path(__file__).parent.parent / 'knowledge_base'


def normalize_spacing(text):
    if not text:
        return text
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\d)([A-Z])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def fix_duplicate_names(text):
    if not text:
        return text
    text = re.sub(r'Nyxkren Synzan\s+Mc\s+Cormick', 'Nyxkren Synzan', text, flags=re.IGNORECASE)
    text = re.sub(r'Thalkor Zangor\s+"(?:Chef|Thalkor Zangor)"\s+Mc\s+Elroy', 'Thalkor Zangor', text, flags=re.IGNORECASE)
    text = re.sub(r'Thalkor Zangor\s+Thalkor Zangor\s+Mc\s+Elroy', 'Thalkor Zangor', text, flags=re.IGNORECASE)
    text = re.sub(r'Thalkor Zangor\s+Mc\s+Elroy', 'Thalkor Zangor', text, flags=re.IGNORECASE)
    text = re.sub(r'Thalkor[_ ]Zangor[_ ]Thalkor[_ ]Zangor', 'Thalkor_Zangor', text, flags=re.IGNORECASE)
    return text


def replace_terms_in_text(text, terms_map):
    if not text:
        return text

    text = normalize_spacing(text)

    all_replacements = {}
    for category in ['characters', 'locations', 'entities', 'events']:
        all_replacements.update(terms_map.get(category, {}))

    sorted_terms = sorted(all_replacements.items(), key=lambda x: len(x[0]), reverse=True)

    for original, replacement in sorted_terms:
        pattern = re.compile(r'\b' + re.escape(original) + r"(?:'s|s)?\b", flags=re.IGNORECASE)

        def replace_match(match):
            matched = match.group(0)
            result = replacement if matched[0].isupper() else replacement.lower()
            if matched.endswith("'s"):
                result += "'s"
            elif matched.endswith("s") and not original.endswith("s"):
                result += "s"
            return result

        text = pattern.sub(replace_match, text)

    text = fix_duplicate_names(text)
    return text


def create_markdown(data, terms_map):
    lines = []

    replaced_title = replace_terms_in_text(data['title'], terms_map)
    lines.append(f"# {replaced_title}\n")
    lines.append(f"**Category:** {data['category'].title()}\n")

    if data.get('infobox') and isinstance(data['infobox'], dict) and data['infobox']:
        lines.append("## Information\n")
        for key, value in data['infobox'].items():
            if value:
                replaced_key = replace_terms_in_text(key, terms_map)
                replaced_value = replace_terms_in_text(str(value), terms_map)
                lines.append(f"**{replaced_key}:** {replaced_value}")
        lines.append("")

    if data.get('sections') and isinstance(data['sections'], dict):
        for section_title, section_content in data['sections'].items():
            if section_title and section_content:
                if isinstance(section_content, list):
                    content_text = '\n'.join(str(item) for item in section_content if item)
                else:
                    content_text = str(section_content)

                if content_text.strip():
                    replaced_title = replace_terms_in_text(section_title, terms_map)
                    replaced_content = replace_terms_in_text(content_text, terms_map)
                    lines.append(f"## {replaced_title}\n")
                    lines.append(replaced_content)
                    lines.append("")

    return '\n'.join(lines)


def sanitize_filename(title):
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = safe.replace(' ', '_')
    return safe[:100]


def main():
    print("[*] Starting knowledge base regeneration...")

    terms_map_path = DATA_DIR / 'terms_map.json'
    with open(terms_map_path, 'r', encoding='utf-8') as f:
        terms_map = json.load(f)

    print(f"[OK] Loaded terms map with {terms_map['metadata']['total_terms']} terms")

    for category in ['character', 'location', 'event']:
        category_dir = KB_DIR / category
        if category_dir.exists():
            for md_file in category_dir.glob('*.md'):
                md_file.unlink()
            print(f"[OK] Cleaned old {category} files")

    json_files = list(RAW_DIR.rglob('*.json'))
    print(f"[*] Found {len(json_files)} JSON files to process")

    processed = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            markdown_content = create_markdown(data, terms_map)
            replaced_title = replace_terms_in_text(data['title'], terms_map)
            safe_filename = sanitize_filename(replaced_title)

            category = data['category'].lower()
            if category not in ['character', 'location', 'event']:
                category = 'character'

            output_dir = KB_DIR / category
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / f"{safe_filename}.md"
            output_path.write_text(markdown_content, encoding='utf-8')

            processed += 1
            print(f"[OK] {processed}/{len(json_files)}: {replaced_title}")

        except Exception as e:
            print(f"[ERROR] Failed to process {json_file.name}: {e}")

    print(f"\n[SUCCESS] Regenerated {processed} documents")


if __name__ == '__main__':
    main()
