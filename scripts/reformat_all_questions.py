import glob
import json
import os
import re
import pymupdf

FILES = {
    'SET A': 'Beispiele/ISTQB_CTFL40_Sample-Exam_Antworten_SET_A_v2.3_germ.pdf',
    'SET B': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Answers_SET_B_v1.3.3_GTB-edition_germ.pdf',
    'SET C': 'Beispiele/ISTQB_CTFL40_Sample-Exam_Antworten_SET_C_v2.4.0_germ.pdf',
    'SET D': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Answer_SET_D_v1.5.0_germ.pdf',
    'SET E': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Answers_SET-E_v1.3_GTB-edition_germ.pdf',
    'SET F': 'Beispiele/ISTQB_CTFL_Sample-Exam-Answers_SET-F_v1.2_-GTB-edition_germ.pdf',
}

HEADER_PATTERNS = [
    'ISTQB® Certified Tester',
    'ISTQB ® Certified',
    'Sample Exam Paper',
    'Status: Final',
    'Status: FINAL',
    'CTFL-Lehrplan',
    'Original freigegeben',
    'Platz für Ihre Notizen',
    'GTB-Edition',
    'GTB edition',
    'GTB Edition',
    'Urheberrecht'
]

def clean_page_lines(page_text):
    """Strip recurring headers and footers from each page."""
    lines = page_text.split('\n')
    cleaned = []
    for l in lines:
        ls = l.strip()
        if any(h in ls for h in HEADER_PATTERNS):
            continue
        if re.search(r'CTFL\s+v[\d\.]+', ls):
            continue
        # Version or date header lines: e.g. "v1.2", "-17.04.2025-", "5/58"
        if re.match(r'^v\d+\.\d+(\.\d+)?$', ls):
            continue
        if re.match(r'^-\d{2}\.\d{2}\.\d{4}-?$', ls):
            continue
        if re.match(r'^\d+/\d+$', ls):
            continue
        cleaned.append(l)
    return '\n'.join(cleaned)

def clean_text_formatting(text):
    """Clean common typographical artifacts and spaces."""
    if not text:
        return ''
    t = text.replace('\xa0', ' ').replace('\u200b', '')
    # Fix hyphenation across linebreaks: word-\nword -> wordword
    t = re.sub(r'([a-zA-ZäöüÄÖÜß])-[\n\r]+\s*([a-zA-ZäöüÄÖÜß])', r'\1\2', t)
    # Spurious spaces within words
    t = t.replace('Fehler zuständen', 'Fehlerzuständen')
    t = t.replace('Fehler zustand', 'Fehlerzustand')
    t = t.replace('Fehler wirkung', 'Fehlerwirkung')
    t = t.replace('Testaktivität en', 'Testaktivitäten')
    t = t.replace('ge eignete', 'geeignete')
    # Standardize multiple spaces
    t = re.sub(r'[ \t]+', ' ', t)
    return t.strip()

def format_stem(stem_raw):
    text = stem_raw.strip()
    # 1. Remove redundant instruction at end
    text = re.sub(r'(?:^|\n)\s*Wählen Sie\s+(?:EINE|ZWEI|DREI|[0-9]+)\s+Option(?:en)?[^\n]*$', '', text, flags=re.IGNORECASE)
    
    # 2. Fix hyphenation
    text = re.sub(r'([a-zA-ZäöüÄÖÜß])-[\n\r]+\s*([a-zA-ZäöüÄÖÜß])', r'\1\2', text)
    
    # 3. Clean header remnants
    lines = text.split('\n')
    filtered_lines = []
    for l in lines:
        ls = l.strip()
        if any(h in ls for h in HEADER_PATTERNS):
            continue
        if re.search(r'CTFL\s+v[\d\.]+', ls):
            continue
        if re.match(r'^v\d+\.\d+(\.\d+)?$', ls):
            continue
        if re.match(r'^-\d{2}\.\d{2}\.\d{4}-?$', ls):
            continue
        if re.match(r'^\d+/\d+$', ls):
            continue
        filtered_lines.append(l)
        
    text = '\n'.join(filtered_lines).strip()
    
    # 4. Process paragraphs & lists
    paragraphs = re.split(r'\n\s*\n', text)
    formatted_paras = []
    
    for para in paragraphs:
        p_lines = [l.strip() for l in para.split('\n') if l.strip()]
        if not p_lines:
            continue
            
        new_items = []
        curr = []
        for line in p_lines:
            is_item_start = bool(re.match(r'^(?:[0-9]+[\.\)]|[A-Z][\.\)]|[•\-\*]|TC\s*[0-9]+|T[0-9]+|TF\s*[0-9]+)\s+', line))
            is_sub_heading = bool(re.match(r'^(?:Betrachten Sie|Beachten Sie|Unter Berücksichtigung|Die existierenden Testfälle|Gegeben sei|Tabelle:|Folgende|Als registrierter Kunde|Ihr Team)\b', line)) and len(line) < 90
            
            if is_item_start or is_sub_heading:
                if curr:
                    new_items.append(clean_text_formatting(' '.join(curr)))
                    curr = []
                curr.append(line)
            else:
                curr.append(line)
                
        if curr:
            new_items.append(clean_text_formatting(' '.join(curr)))
            
        formatted_paras.append('\n'.join(new_items))
        
    result = '\n\n'.join(formatted_paras)
    return clean_text_formatting(result)

def format_option(opt_raw):
    # Strip any trailing footer or header that leaked after option
    cleaned = re.split(r'\n\s*(?:Frage\s+\d+|FL-[\d\.]+|ISTQB|Sample Exam|CTFL)', opt_raw)[0].strip()
    lines = [clean_text_formatting(l) for l in cleaned.split('\n') if l.strip()]
    if not lines:
        return ''
    # If it's a table row or multiple steps, preserve lines
    if any('|' in l for l in lines) or (len(lines) > 1 and all(re.match(r'^[0-9]+[A-Z]', l) for l in lines)):
        return '\n'.join(lines)
    return clean_text_formatting(' '.join(lines))

def format_explanation(exp_raw):
    # Strip footer from explanation if at end
    cleaned = re.split(r'\n\s*Frage\s+\d+\s+FL-', exp_raw)[0].strip()
    lines = [clean_text_formatting(l) for l in cleaned.split('\n') if l.strip()]
    if not lines:
        return ''
    joined = ' '.join(lines)
    joined = re.sub(r'^(KORREKT|FALSCH|RICHTIG)\s*[-–—:]*\s*', r'\1 – ', joined, flags=re.IGNORECASE)
    return clean_text_formatting(joined)

def parse_set(set_name, pdf_path):
    doc = pymupdf.open(pdf_path)
    
    q_pages = {i: [] for i in range(1, 41)}
    curr_q = 0
    for p_idx in range(len(doc)):
        txt = doc[p_idx].get_text('text')
        f_match = re.search(r'Frage\s+(\d+)\s+FL-', txt)
        is_notes = 'Platz für Ihre Notizen' in txt
        is_front = p_idx < 3 or 'Allgemeine Angaben' in txt or 'Änderungsübersicht' in txt
        if is_front or is_notes:
            continue
        if f_match:
            curr_q = int(f_match.group(1))
            q_pages[curr_q].append(p_idx)
        elif curr_q > 0:
            q_pages[curr_q].append(p_idx)

    parsed_questions = []
    
    for q_num in range(1, 41):
        pages_idx = q_pages[q_num]
        # Clean each page lines before joining
        combined_text = '\n'.join([clean_page_lines(doc[p].get_text('text')) for p in pages_idx])
        
        # Meta & points
        f_match = re.search(r'Frage\s+(\d+)\s+([A-Z0-9\.\-\s]+?)\s+Punkte\s*([0-9\.]+)', combined_text)
        lo_meta = f_match.group(2).strip() if f_match else ''
        points = float(f_match.group(3)) if f_match else 1.0

        k_level_m = re.search(r'\b(K[1-4])\b', lo_meta)
        if not k_level_m:
            k_level_m = re.search(r'\((K[1-4])\)', combined_text)
        k_level = k_level_m.group(1) if k_level_m else 'K1'

        # Remove footer
        text_clean = re.sub(r'Frage\s+\d+\s+FL-[^\n]+?Punkte\s*[0-9\.]+', '', combined_text).strip()

        # Begründung separator
        lo_title = lo_meta
        lo_match = re.search(r'(?:^|\n)\s*(FL-[\d\.]+\s*\([^\)]+\)[^\n]+(?:\n[^\n]+)?)\s*\n\s*Begründung[^\n]*:\s*', text_clean)
        if lo_match:
            q_part = text_clean[:lo_match.start()].strip()
            ans_part = text_clean[lo_match.end():].strip()
            lo_title = clean_text_formatting(lo_match.group(1).replace('\n', ' '))
        else:
            begr_match = re.search(r'(?:^|\n)\s*Begründung[^\n]*:\s*', text_clean)
            if begr_match:
                q_part = text_clean[:begr_match.start()].strip()
                ans_part = text_clean[begr_match.end():].strip()
            else:
                q_part = text_clean.strip()
                ans_part = ''

        # Instruction
        instr_m = re.search(r'(Wählen Sie\s+(?:EINE|ZWEI|DREI|[0-9]+)\s+Option(?:en)?[^\n]*)', q_part, re.IGNORECASE)
        instruction = instr_m.group(1).strip() if instr_m else 'Wählen Sie EINE Option!'
        is_multi = bool(re.search(r'ZWEI|DREI|[2-9]\s+Option', instruction, re.IGNORECASE))

        # Options in q_part
        opt_matches = list(re.finditer(r'(?:^|\n)\s*([a-e])[\)\.]\s*', q_part))
        raw_options = {}
        if opt_matches:
            raw_stem = q_part[:opt_matches[0].start()].strip()
            for i in range(len(opt_matches)):
                letter = opt_matches[i].group(1).lower()
                start = opt_matches[i].end()
                end = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(q_part)
                opt_c = q_part[start:end].strip()
                opt_c = re.sub(r'\n\s*FL-[\d\.]+\s*\(K\d\).*$', '', opt_c, flags=re.DOTALL).strip()
                raw_options[letter] = opt_c
        else:
            raw_stem = q_part

        # Format stem and options
        stem = format_stem(raw_stem)
        options = {k: format_option(v) for k, v in raw_options.items()}

        # Explanations in ans_part
        exp_matches = list(re.finditer(r'(?:^|\n)\s*([a-e])[\)\.]\s*', ans_part))
        explanations = {}
        correct_answers = []

        if exp_matches:
            for i in range(len(exp_matches)):
                letter = exp_matches[i].group(1).lower()
                start = exp_matches[i].end()
                end = exp_matches[i+1].start() if i+1 < len(exp_matches) else len(ans_part)
                exp_text = ans_part[start:end].strip()

                is_correct = bool(re.search(r'^(?:KORREKT|RICHTIG)\b', exp_text, re.IGNORECASE))
                if not is_correct:
                    first_line = exp_text.split('\n')[0]
                    if 'KORREKT' in first_line.upper() and 'FALSCH' not in first_line.upper():
                        is_correct = True

                if is_correct:
                    correct_answers.append(letter)

                explanations[letter] = {
                    'status': 'KORREKT' if is_correct else 'FALSCH',
                    'text': format_explanation(exp_text)
                }

        # Fallbacks for correct answers
        folglich = re.findall(r'(?:Folglich|Daher|Somit|Deshalb|Damit)\s+ist\s+(?:die\s+)?(?:Option\s+|Antwort\s+)?([a-e])[\)\.]?\s*(?:\[[^\]]*\]\s*)?KORREKT', ans_part, re.IGNORECASE)
        for c in folglich:
            c_low = c.lower()
            if c_low not in correct_answers:
                correct_answers.append(c_low)
            if c_low in explanations:
                explanations[c_low]['status'] = 'KORREKT'

        for l in options.keys():
            if l not in correct_answers:
                if re.search(r'(?:^|\n)\s*' + l + r'[\)\.]\s*KORREKT\b', ans_part, re.IGNORECASE):
                    correct_answers.append(l)
                    if l in explanations:
                        explanations[l]['status'] = 'KORREKT'

        if not correct_answers and options:
            falsch_opts = [l for l, exp in explanations.items() if exp['status'] == 'FALSCH']
            remaining = [l for l in options.keys() if l not in falsch_opts]
            if len(remaining) == 1 and not is_multi:
                correct_answers.append(remaining[0])
                if remaining[0] in explanations:
                    explanations[remaining[0]]['status'] = 'KORREKT'

        if not correct_answers:
            if set_name == 'SET E' and q_num == 39:
                correct_answers = ['c']
                if 'c' in explanations:
                    explanations['c']['status'] = 'KORREKT'
            elif set_name == 'SET F' and q_num == 3:
                correct_answers = ['d']
                if 'd' in explanations:
                    explanations['d']['status'] = 'KORREKT'

        qid = f"{set_name.replace(' ', '_').lower()}_q{q_num}"
        
        parsed_questions.append({
            'id': qid,
            'set': set_name,
            'question_number': q_num,
            'k_level': k_level,
            'meta': lo_meta,
            'lo_title': lo_title,
            'points': points,
            'is_multi_select': is_multi,
            'instruction': instruction,
            'stem': stem,
            'options': options,
            'correct_answers': sorted(list(set(correct_answers))),
            'explanations': explanations,
            'raw_explanation': clean_text_formatting(ans_part)
        })

    return parsed_questions

def main():
    existing_images = {}
    if os.path.exists('data/questions.json'):
        with open('data/questions.json') as f:
            old_qs = json.load(f)
            for q in old_qs:
                if q.get('images'):
                    existing_images[q['id']] = q['images']

    all_questions = []
    for set_name, pdf_path in FILES.items():
        print(f"Parsing {set_name}...")
        set_qs = parse_set(set_name, pdf_path)
        for q in set_qs:
            q['images'] = existing_images.get(q['id'], [])
        all_questions.extend(set_qs)

    with open('data/questions.json', 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f"Success! Formatted {len(all_questions)} questions saved to data/questions.json")

if __name__ == '__main__':
    main()
