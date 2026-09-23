import glob
import json
import os
import re
from PIL import Image
import pypdf

FILES = {
    'SET A': 'Beispiele/ISTQB_CTFL40_Sample-Exam_Antworten_SET_A_v2.3_germ.pdf',
    'SET B': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Answers_SET_B_v1.3.3_GTB-edition_germ.pdf',
    'SET C': 'Beispiele/ISTQB_CTFL40_Sample-Exam_Antworten_SET_C_v2.4.0_germ.pdf',
    'SET D': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Answer_SET_D_v1.5.0_germ.pdf',
    'SET E': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Answers_SET-E_v1.3_GTB-edition_germ.pdf',
    'SET F': 'Beispiele/ISTQB_CTFL_Sample-Exam-Answers_SET-F_v1.2_-GTB-edition_germ.pdf',
}

def clean_page_text(page_text):
    """Strip standard top header lines (first 4 lines) from page text."""
    lines = page_text.split('\n')
    # If the first line starts with ISTQB header, remove header lines
    start_idx = 0
    if len(lines) > 0 and ('ISTQB' in lines[0] or 'Sample Exam' in lines[0]):
        # typically 4 header lines
        start_idx = 4
        while start_idx < len(lines) and not lines[start_idx].strip():
            start_idx += 1
    return '\n'.join(lines[start_idx:])

def extract_images_from_page(page, set_slug, q_num):
    saved_images = []
    try:
        for idx, img_file in enumerate(page.images):
            # filter standard logos
            if img_file.image.size in [(271, 203), (220, 181), (408, 306), (271, 202)]:
                continue
            w, h = img_file.image.size
            if w < 60 or h < 60:
                continue
            img_name = f"{set_slug}_q{q_num}_{idx}_{img_file.name}"
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_name += '.png'
            out_path = os.path.join('data/images', img_name)
            img_file.image.save(out_path)
            saved_images.append(f"data/images/{img_name}")
    except Exception as e:
        print(f"Image extract error on {set_slug} Q{q_num}: {e}")
    return saved_images

def parse_question(set_name, q_num, raw_text, images):
    text = raw_text

    # Extract footer info: e.g. Frage 1 FL-1.1.1 K1 Punkte 1.0
    f_match = re.search(r'Frage\s+(\d+)\s+([A-Z0-9\.\-\s]+?)\s+Punkte\s*([0-9\.]+)', text)
    lo_meta = f_match.group(2).strip() if f_match else ''
    points = float(f_match.group(3)) if f_match else 1.0

    # Extract K-Level (K1, K2, K3)
    k_level_m = re.search(r'\b(K[1-4])\b', lo_meta)
    if not k_level_m:
        k_level_m = re.search(r'\((K[1-4])\)', text)
    k_level = k_level_m.group(1) if k_level_m else 'K1'

    # Remove all footer occurrences from text cleanly
    text_clean = re.sub(r'Frage\s+\d+\s+FL-[^\n]+?Punkte\s*[0-9\.]+', '', text).strip()

    # Begründung separator
    # Can be preceded by LO title e.g. FL-1.4.1 (K2) Der Lernende ...
    lo_title = lo_meta
    lo_match = re.search(r'(?:^|\n)\s*(FL-[\d\.]+\s*\([^\)]+\)[^\n]+(?:\n[^\n]+)?)\s*\n\s*Begründung[^\n]*:\s*', text_clean)
    if lo_match:
        q_part = text_clean[:lo_match.start()].strip()
        ans_part = text_clean[lo_match.end():].strip()
        lo_title = lo_match.group(1).replace('\n', ' ').strip()
    else:
        begr_match = re.search(r'(?:^|\n)\s*Begründung[^\n]*:\s*', text_clean)
        if begr_match:
            q_part = text_clean[:begr_match.start()].strip()
            ans_part = text_clean[begr_match.end():].strip()
        else:
            q_part = text_clean.strip()
            ans_part = ''

    # Clean any trailing FL-... from q_part if it was not caught
    trailing_lo = re.search(r'\n\s*FL-[\d\.]+\s*\(K\d\).*$', q_part, re.DOTALL)
    if trailing_lo:
        q_part = q_part[:trailing_lo.start()].strip()

    # Instruction: e.g. Wählen Sie EINE Option! (1 aus 4)
    instr_m = re.search(r'(Wählen Sie\s+(?:EINE|ZWEI|DREI|[0-9]+)\s+Option(?:en)?[^\n]*)', q_part, re.IGNORECASE)
    instruction = instr_m.group(1).strip() if instr_m else 'Wählen Sie EINE Option!'
    is_multi = bool(re.search(r'ZWEI|DREI|[2-9]\s+Option', instruction, re.IGNORECASE))

    # Options in q_part: lines starting with a), b), c), d), e) or a., b., c.
    opt_matches = list(re.finditer(r'(?:^|\n)\s*([a-e])[\)\.]\s*', q_part))
    options = {}
    if opt_matches:
        stem = q_part[:opt_matches[0].start()].strip()
        for i in range(len(opt_matches)):
            letter = opt_matches[i].group(1).lower()
            start = opt_matches[i].end()
            end = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(q_part)
            opt_content = q_part[start:end].strip()
            # Clean possible trailing LO from last option
            opt_content = re.sub(r'\n\s*FL-[\d\.]+\s*\(K\d\).*$', '', opt_content, flags=re.DOTALL).strip()
            options[letter] = opt_content
    else:
        stem = q_part

    # Explanations in ans_part: lines starting with a), b), c), d), e)
    exp_matches = list(re.finditer(r'(?:^|\n)\s*([a-e])[\)\.]\s*', ans_part))
    explanations = {}
    correct_answers = []

    if exp_matches:
        for i in range(len(exp_matches)):
            letter = exp_matches[i].group(1).lower()
            start = exp_matches[i].end()
            end = exp_matches[i+1].start() if i+1 < len(exp_matches) else len(ans_part)
            exp_text = ans_part[start:end].strip()

            # Check correctness: KORREKT / RICHTIG
            is_correct = bool(re.search(r'^(?:KORREKT|RICHTIG)\b', exp_text, re.IGNORECASE))
            if not is_correct:
                first_line = exp_text.split('\n')[0]
                if 'KORREKT' in first_line.upper() and 'FALSCH' not in first_line.upper():
                    is_correct = True

            if is_correct:
                correct_answers.append(letter)

            explanations[letter] = {
                'status': 'KORREKT' if is_correct else 'FALSCH',
                'text': exp_text
            }

    # Fallback correct answers detection
    # 1. Pattern like "Folglich ist a) KORREKT" or "Daher ist die Option d) KORREKT" or "Folglich ist Antwort b) KORREKT"
    folglich = re.findall(r'(?:Folglich|Daher|Somit|Deshalb|Damit)\s+ist\s+(?:die\s+)?(?:Option\s+|Antwort\s+)?([a-e])[\)\.]?\s*(?:\[[^\]]*\]\s*)?KORREKT', ans_part, re.IGNORECASE)
    for c in folglich:
        c_low = c.lower()
        if c_low not in correct_answers:
            correct_answers.append(c_low)
        if c_low in explanations:
            explanations[c_low]['status'] = 'KORREKT'

    # 2. Check if specific option has KORREKT marker
    for l in options.keys():
        if l not in correct_answers:
            if re.search(r'(?:^|\n)\s*' + l + r'[\)\.]\s*KORREKT\b', ans_part, re.IGNORECASE):
                correct_answers.append(l)
                if l in explanations:
                    explanations[l]['status'] = 'KORREKT'

    # 3. Deduction: If all other options are explicitly marked FALSCH
    if not correct_answers and options:
        falsch_opts = [l for l, exp in explanations.items() if exp['status'] == 'FALSCH']
        remaining = [l for l in options.keys() if l not in falsch_opts]
        if len(remaining) == 1 and not is_multi:
            correct_answers.append(remaining[0])
            if remaining[0] in explanations:
                explanations[remaining[0]]['status'] = 'KORREKT'

    # Special known question resolutions if needed
    if not correct_answers:
        if set_name == 'SET E' and q_num == 39:
            correct_answers = ['c']
            if 'c' in explanations:
                explanations['c']['status'] = 'KORREKT'
        elif set_name == 'SET F' and q_num == 3:
            correct_answers = ['d']
            if 'd' in explanations:
                explanations['d']['status'] = 'KORREKT'

    return {
        'id': f"{set_name.replace(' ', '_').lower()}_q{q_num}",
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
        'raw_explanation': ans_part,
        'images': images
    }

def main():
    os.makedirs('data/images', exist_ok=True)
    all_questions = []

    for set_name, pdf_path in FILES.items():
        set_slug = set_name.replace(' ', '_').lower()
        print(f"Processing {set_name} from {pdf_path}...")
        reader = pypdf.PdfReader(pdf_path)

        # Map pages to question numbers
        q_pages = {i: [] for i in range(1, 41)}
        curr_q = 0
        for p_idx in range(len(reader.pages)):
            txt = reader.pages[p_idx].extract_text() or ''
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

        set_questions = []
        for q_num in range(1, 41):
            pages_idx = q_pages[q_num]
            # Clean each page before combining
            combined_text = '\n'.join([clean_page_text(reader.pages[p].extract_text() or '') for p in pages_idx])

            # Extract diagrams
            images = []
            for p in pages_idx:
                imgs = extract_images_from_page(reader.pages[p], set_slug, q_num)
                images.extend(imgs)

            q_data = parse_question(set_name, q_num, combined_text, images)
            set_questions.append(q_data)

        # Validate set questions
        missing_opts = [q['question_number'] for q in set_questions if len(q['options']) < 3]
        missing_corr = [q['question_number'] for q in set_questions if len(q['correct_answers']) == 0]
        print(f"  {set_name}: {len(set_questions)} questions parsed.")
        if missing_opts:
            print(f"  WARNING: Questions with <3 options: {missing_opts}")
        if missing_corr:
            print(f"  WARNING: Questions with no correct answer: {missing_corr}")

        all_questions.extend(set_questions)

    print(f"\nTotal questions collected: {len(all_questions)}")
    out_file = 'data/questions.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved to {out_file}")

    with_images = [q['id'] for q in all_questions if len(q['images']) > 0]
    print(f"Questions with diagrams: {len(with_images)} -> {with_images}")

if __name__ == '__main__':
    main()
