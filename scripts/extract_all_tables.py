import os
import json
import pymupdf

TABLE_SPECS = [
    {
        'id': 'set_a_q22',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam_Fragen_SET_A_v2.3_germ.pdf',
        'page': 20, # page 21
        'start_text': 'Entscheidungstabelle enthält ausgewählte Testfälle',
        'end_text': 'Welcher der folgenden Testfälle beschreibt',
        'img': 'data/images/set_a_q22_table.png',
        'stem_clean': (
            "Neu eingestellte Mitarbeitende einer Firma können individuelle Ziele mit ihren Vorgesetzten vereinbaren, "
            "an deren Erreichung die Auszahlung einer Prämie gekoppelt ist. Diese Prämie wird ihnen aber erst ausgezahlt, "
            "wenn sie länger als ein Jahr im Unternehmen beschäftigt sind.\n\n"
            "Die folgende Entscheidungstabelle enthält ausgewählte Testfälle zu diesem Sachverhalt:\n\n"
            "Welcher der folgenden Testfälle beschreibt eine in der Praxis gültige, durchführbare Bedingungskombination "
            "mit fachlich korrekter erwarteter Aktion und fehlt in der oben aufgeführten Entscheidungstabelle?"
        )
    },
    {
        'id': 'set_a_q33',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam_Fragen_SET_A_v2.3_germ.pdf',
        'page': 30, # page 31
        'start_text': 'folgende Liste von Testfällen',
        'end_text': 'Welcher der folgenden Testfälle soll als dritter',
        'img': 'data/images/set_a_q33_table.png',
        'stem_clean': (
            "Sie testen eine mobile Applikation, die es Benutzern ermöglicht, ein nahegelegenes Restaurant zu finden, "
            "das die gewünschte Art des Essens anbietet. Gegeben ist die folgende Liste von Testfällen, Prioritäten "
            "(eine kleinere Zahl bedeutet eine höhere Priorität) und logischen Abhängigkeiten:\n\n"
            "Welcher der folgenden Testfälle soll als dritter ausgeführt werden?"
        )
    },
    {
        'id': 'set_b_q22',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Questions_SET_B_v1.3.3_GTB-edition_germ.pdf',
        'page': 19, # page 20
        'start_text': 'folgende Entscheidungstabelle enthält die Regeln',
        'end_text': 'Sie haben die Testfälle mit den folgenden Testdaten',
        'img': 'data/images/set_b_q22_table.png',
        'stem_clean': (
            "Die folgende Entscheidungstabelle enthält die Regeln zur Bestimmung des Risikos für Arteriosklerose "
            "(Arterienverkalkung) auf der Grundlage der Cholesterin- und Blutdruckwerte des Patienten:\n\n"
            "Sie haben die Testfälle mit den folgenden Testdaten entworfen:\n"
            "• TC1: Cholesterin = 125 mg/dl – Blutdruck = 141 mm Hg\n"
            "• TC2: Cholesterin = 200 mg/dl – Blutdruck = 201 mm Hg\n"
            "• TC3: Cholesterin = 124 mg/dl – Blutdruck = 201 mm Hg\n"
            "• TC4: Cholesterin = 109 mg/dl – Blutdruck = 200 mm Hg\n"
            "• TC5: Cholesterin = 201 mg/dl – Blutdruck = 140 mm Hg\n\n"
            "Welche Überdeckung der Entscheidungstabelle wird durch diese Testfälle erreicht?"
        )
    },
    {
        'id': 'set_b_q31',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Questions_SET_B_v1.3.3_GTB-edition_germ.pdf',
        'page': 27, # page 28
        'start_text': 'Die Tabelle zeigt unten diese historischen Daten',
        'end_text': 'Der geschätzte Entwicklungsaufwand',
        'img': 'data/images/set_b_q31_table.png',
        'stem_clean': (
            "Sie möchten den Testaufwand für ein neues Projekt mit Hilfe einer auf Kennzahlen basierenden Schätzung abschätzen. "
            "Sie berechnen das Verhältnis von Testaufwand zu Entwicklungsaufwand, indem Sie die Durchschnittsdaten sowohl für den "
            "Entwicklungs- als auch für den Testaufwand aus vier historischen Projekten verwenden, die dem neuen Projekt ähnlich sind.\n\n"
            "Die folgende Tabelle zeigt diese historischen Daten:\n\n"
            "Der geschätzte Entwicklungsaufwand für das neue Projekt beträgt 800.000 €.\n"
            "Wie hoch schätzen Sie den Testaufwand in diesem Projekt ein?"
        )
    },
    {
        'id': 'set_b_q32',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Questions_SET_B_v1.3.3_GTB-edition_germ.pdf',
        'page': 28, # page 29
        'start_text': 'Ausführungsreihenfolge der folgenden Testfälle festzulegen',
        'end_text': 'Priorität 1 ist dringlicher als Priorität 2',
        'img': 'data/images/set_b_q32_table.png',
        'stem_clean': (
            "Sie wurden gebeten, eine optimale, risikobasierte Ausführungsreihenfolge der folgenden Testfälle festzulegen, "
            "die bereits priorisiert und auf mögliche Abhängigkeiten hin untersucht wurden:\n\n"
            "Hinweis: Priorität 1 ist dringlicher als Priorität 2 usw.\n\n"
            "Welcher der folgenden Testabläufe berücksichtigt die oben genannten Abhängigkeiten und Prioritäten?"
        )
    },
    {
        'id': 'set_c_q22',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam_Fragen_SET_C_v2.4.0_germ.pdf',
        'page': 18, # page 19
        'start_text': 'folgenden Regeln wurden in einer Entscheidungstabelle formuliert',
        'end_text': 'Welche Kombination von Eingabedaten zeigt',
        'img': 'data/images/set_c_q22_table.png',
        'stem_clean': (
            "Gegeben ist ein System zur Analyse von Fahrprüfungsergebnissen. "
            "Die folgenden Regeln wurden in einer Entscheidungstabelle formuliert:\n\n"
            "Welche Kombination von Eingabedaten zeigt, dass die Entscheidungstabelle widersprüchliche Regeln enthält?"
        )
    },
    {
        'id': 'set_d_q22',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Question_SET_D_v1.5.0_germ.pdf',
        'page': 17, # page 18
        'start_text': 'basierend auf der folgenden Entscheidungstabelle',
        'end_text': 'Bisher haben Sie die folgenden Testfälle entworfen',
        'img': 'data/images/set_d_q22_table.png',
        'stem_clean': (
            "Sie entwerfen Testfälle basierend auf der folgenden Entscheidungstabelle:\n\n"
            "Bisher haben Sie die folgenden Testfälle entworfen:\n"
            "• TC1: 19-jähriger, nicht registrierter Mann ohne Erfahrung; erwartetes Ergebnis: Kategorie A\n"
            "• TC2: 65-jährige, nicht registrierte Frau mit 5 Jahren Erfahrung; erwartetes Ergebnis: Kategorie B\n"
            "• TC3: 66-jähriger, registrierter Mann ohne Erfahrung; erwartetes Ergebnis: Kategorie C\n"
            "• TC4: 65-jährige, registrierte Frau mit 4 Jahren Erfahrung; erwartetes Ergebnis: Kategorie D\n\n"
            "Welcher der folgenden Testfälle erhöht die Überdeckung der Entscheidungstabelle, wenn er zu den bestehenden Testfällen hinzugefügt wird?"
        )
    },
    {
        'id': 'set_d_q23',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Question_SET_D_v1.5.0_germ.pdf',
        'page': 18, # page 19
        'start_text': 'folgende Zustandsübergangstabelle mit vier Zuständen',
        'end_text': 'Angenommen, alle Testfälle beginnen im Zustand',
        'img': 'data/images/set_d_q23_table.png',
        'stem_clean': (
            "Sie wenden den Zustandsübergangstest auf das Zimmerreservierungssystem an, das durch die folgende "
            "Zustandsübergangstabelle mit vier Zuständen und fünf Ereignissen modelliert wird:\n\n"
            "Angenommen, alle Testfälle beginnen im Zustand „Anfordern“.\n"
            "Welcher der folgenden Testfälle (Abfolge von Ereignissen) erreicht die GRÖSSTMÖGLICHE ÜBERDECKUNG GÜLTIGER ÜBERGÄNGE?"
        )
    },
    {
        'id': 'set_d_q32',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Question_SET_D_v1.5.0_germ.pdf',
        'page': 25, # page 26
        'start_text': 'Nachverfolgbarkeitsmatrix zwischen Testfällen und',
        'end_text': 'Die Testfälle sollen mithilfe des Verfahrens',
        'img': 'data/images/set_d_q32_table.png',
        'stem_clean': (
            "Die Tabelle zeigt die Nachverfolgbarkeitsmatrix zwischen Testfällen und Anforderungen. "
            "Ein „X“ bedeutet, dass ein Testfall die Anforderung überdeckt:\n\n"
            "Die Testfälle sollen mithilfe des Verfahrens der zusätzlichen Überdeckung priorisiert und anschließend alle ausgeführt werden.\n\n"
            "Welcher Testfall sollte gemäß diesem Verfahren ALS LETZTER ausgeführt werden?"
        )
    },
    {
        'id': 'set_e_q20',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Questions_SET-E_v1.3_GTB-edition_germ.pdf',
        'page': 16, # page 17
        'start_text': 'Die folgenden Testfälle existieren bereits',
        'end_text': 'Wie viele Testfälle müssen mindestens noch erzeugt werden',
        'img': 'data/images/set_e_q20_table.png',
        'stem_clean': (
            "Ein Gerät zur Messung des täglichen Strahlungseinfalls für Pflanzen ermittelt einen Einstrahlungswert für Sonnenschein. "
            "Dieser ergibt sich aus der Kombination der Anzahl der Stunden, in denen eine Pflanze der Sonne ausgesetzt ist "
            "(unter 3 Stunden, 3 bis 6 Stunden, über 6 Stunden), und der durchschnittlichen Intensität des Sonnenscheins "
            "(sehr niedrig, niedrig, mittel, hoch).\n\n"
            "Die folgenden Testfälle existieren bereits:\n\n"
            "Wie viele Testfälle müssen mindestens noch erzeugt werden, um eine vollständige Überdeckung ALLER GÜLTIGEN Eingabe-Äquivalenzklassen zu gewährleisten?"
        )
    },
    {
        'id': 'set_e_q22',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Questions_SET-E_v1.3_GTB-edition_germ.pdf',
        'page': 18, # page 19
        'start_text': 'folgender Entscheidungstabelle spezifiziert',
        'end_text': 'Ihnen liegen bereits die folgenden Testfälle',
        'img': 'data/images/set_e_q22_table.png',
        'stem_clean': (
            "Ein System zur Berechnung der Strafe für Geschwindigkeitsübertretungen im Straßenverkehr wird mit folgender Entscheidungstabelle spezifiziert:\n\n"
            "Ihnen liegen bereits die folgenden Testfälle und deren Eingaben vor:\n"
            "• TF1: Geschwindigkeit = 65, Schulzone = Ja\n"
            "• TF2: Geschwindigkeit = 45, Schulzone = Ja\n"
            "• TF3: Geschwindigkeit = 50, Schulzone = Nein\n"
            "• TF4: Geschwindigkeit = 49, Schulzone = Nein\n\n"
            "Welche der Regeln der Entscheidungstabelle ist (noch) NICHT durch einen Testfall überdeckt?"
        )
    },
    {
        'id': 'set_e_q33',
        'file': 'Beispiele/ISTQB_CTFL40_Sample-Exam-Questions_SET-E_v1.3_GTB-edition_germ.pdf',
        'page': 28, # page 29
        'start_text': 'Ausführungsreihenfolge nachfolgender Testfälle festzulegen',
        'end_text': 'Priorität 1 ist dringlicher als Priorität 2',
        'img': 'data/images/set_e_q33_table.png',
        'stem_clean': (
            "Sie wurden gebeten, eine optimale, risikobasierte Ausführungsreihenfolge nachfolgender Testfälle festzulegen, "
            "die bereits priorisiert und auf etwaige Abhängigkeiten hin untersucht wurden:\n\n"
            "Hinweis: Priorität 1 ist dringlicher als Priorität 2 usw.\n\n"
            "Welche der folgenden Testabläufe berücksichtigt die oben genannten Abhängigkeiten und Prioritäten?"
        )
    },
    {
        'id': 'set_f_q21',
        'file': 'Beispiele/ISTQB_CTFL_Sample-Exam-Questions_SET-F_v1.2_-GTB-edition_germ.pdf',
        'page': 16, # page 17
        'start_text': 'Sie haben die folgenden Testfälle vorbereitet',
        'end_text': 'Wie hoch ist die Überdeckung der 2-Wert-Grenzwertanalyse',
        'img': 'data/images/set_f_q21_table.png',
        'stem_clean': (
            "Sie testen ein System, das die Endnote für die Kursteilnehmer berechnet. "
            "Die Endnote wird auf der Grundlage der Gesamtpunktzahl zwischen 0 und 100 nach den folgenden Regeln ermittelt:\n"
            "• 0 - 50 Punkte: nicht bestanden\n"
            "• 51 - 70 Punkte: ausreichend\n"
            "• 71 - 90 Punkte: gut\n"
            "• 91 - 100 Punkte: sehr gut\n\n"
            "Sie haben die folgenden Testfälle vorbereitet:\n\n"
            "Wie hoch ist die Überdeckung der 2-Wert-Grenzwertanalyse, die mit den vorhandenen Testfällen erreicht wird?"
        )
    },
    {
        'id': 'set_f_q22',
        'file': 'Beispiele/ISTQB_CTFL_Sample-Exam-Questions_SET-F_v1.2_-GTB-edition_germ.pdf',
        'page': 17, # page 18
        'start_text': 'folgende Entscheidungstabelle entworfen',
        'end_text': 'Welche Regel (Kombination von Bedingungen und Aktionen)',
        'img': 'data/images/set_f_q22_table.png',
        'stem_clean': (
            "Sie testen ein neues Customer-Relationship-Management-System für einen Fahrrad-Tagesverleih. "
            "Die Anforderungen an das System lauten wie folgt:\n"
            "• Jeder kann ein Fahrrad ausleihen, aber nur Mitglieder erhalten einen Rabatt von 20 %.\n"
            "• Wird die Rückgabefrist jedoch versäumt, kann der Rabatt nicht mehr in Anspruch genommen werden.\n"
            "• Nach 15 Ausleihen erhalten die Mitglieder ein T-Shirt geschenkt.\n\n"
            "Ein Tester hat die folgende Entscheidungstabelle entworfen, um die implementierten Funktionen zu testen (J=Wahr, N=Falsch, X=Aktion ausführen):\n\n"
            "Welche Regel (Kombination von Bedingungen und Aktionen) entspricht NICHT den oben angegebenen Anforderungen?"
        )
    },
    {
        'id': 'set_f_q33',
        'file': 'Beispiele/ISTQB_CTFL_Sample-Exam-Questions_SET-F_v1.2_-GTB-edition_germ.pdf',
        'page': 26, # page 27
        'start_text': 'Prioritäten und Abhängigkeiten der Testfälle sind gegeben',
        'end_text': 'Welcher der folgenden Testausführungspläne berücksichtigt',
        'img': 'data/images/set_f_q33_table.png',
        'stem_clean': (
            "Folgende Prioritäten und Abhängigkeiten der Testfälle sind gegeben:\n\n"
            "Welcher der folgenden Testausführungspläne berücksichtigt AM BESTEN die Prioritäten sowie die technischen und logischen Abhängigkeiten?"
        )
    }
]

def crop_table(spec):
    doc = pymupdf.open(spec['file'])
    page = doc[spec['page']]
    blocks = page.get_text('blocks')
    
    y0 = None
    y1 = None
    
    # Match block text ignoring whitespace and case
    def norm(s):
        return ''.join(s.lower().split())
        
    s_target = norm(spec['start_text'])
    e_target = norm(spec['end_text'])
    
    for b in blocks:
        b_txt = norm(b[4])
        if s_target in b_txt:
            y0 = b[3]
        if e_target in b_txt:
            if y1 is None:
                y1 = b[1]
                
    if y0 is None or y1 is None:
        print(f"Fallback coordinates for {spec['id']}: y0={y0}, y1={y1}")
        # Try table finder
        tabs = page.find_tables()
        cand = [t for t in tabs.tables if t.row_count > 2 and t.col_count > 2 and (t.row_count, t.col_count) not in [(4, 3), (1, 8), (5, 3), (4, 2)]]
        if cand:
            bbox = cand[0].bbox
            y0 = bbox[1] - 4
            y1 = bbox[3] + 4
        else:
            print(f"FAILED to find table bounds for {spec['id']}")
            return False
            
    rect = pymupdf.Rect(page.rect.x0 + 35, y0 + 3, page.rect.x1 - 35, y1 - 3)
    pix = page.get_pixmap(dpi=220, clip=rect)
    pix.save(spec['img'])
    print(f"Rendered {spec['img']}: {pix.width}x{pix.height} (y={y0:.1f} to {y1:.1f})")
    return True

def main():
    os.makedirs('data/images', exist_ok=True)
    with open('data/questions.json') as f:
        questions = json.load(f)
        
    q_map = {q['id']: q for q in questions}
    
    for spec in TABLE_SPECS:
        success = crop_table(spec)
        if success and spec['id'] in q_map:
            q = q_map[spec['id']]
            q['stem'] = spec['stem_clean']
            if spec['img'] not in q['images']:
                q['images'] = [spec['img']]
                
    with open('data/questions.json', 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
        
    print("\nUpdated all questions with clean tables and clean stems in data/questions.json!")

if __name__ == '__main__':
    main()
