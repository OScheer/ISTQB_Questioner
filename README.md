# ISTQB® CTFL 4.0 Fragenautomat 🎯

Ein moderner, interaktiver Fragenautomat zur Vorbereitung auf das **ISTQB® Certified Tester Foundation Level (CTFL 4.0)** Zertifikat.

Das Tool enthält den vollständigen Fragenkatalog aller 6 offiziellen GTB-Musterprüfungen (**SET A bis SET F**) mit insgesamt **240 Fragen**, inklusive aller Antwortoptionen, korrekten Lösungen und den **offiziellen GTB-Begründungen für jede einzelne Option**.

---

## ✨ Features

- 🎲 **Zufalls- und Trainingsmodus**: Stellt zufällige Fragen aus dem gesamten Fragenpool oder gefiltert nach Prüfungsset / K-Level.
- ✅ **Sofortige Auswertung**: Direktes visuelles Feedback (Grün = Richtig, Rot = Falsch, Gestrichelt = Verpasste Antwort).
- 💡 **Ausführliche GTB-Begründungen**: Anzeige der offiziellen Erklärungen für jede Option (A bis E) mit Verweis auf den ISTQB-Lehrplanabschnitt.
- 📊 **Fortschritt & Streak-Tracking**: Zählt beantwortete Fragen, Erfolgsquote (%), Serie (Streak) und speichert den Stand automatisch im Browser (`localStorage`).
- 🔁 **Falsche Fragen wiederholen**: Spezieller Modus, um gezielt nur bisher falsch beantwortete Fragen zu trainieren.
- ⭐ **Merkliste**: Fragen zur persönlichen Wiederholung mit einem Klick speichern.
- 🖼️ **Diagramm-Support**: Vollständige Einbindung aller relevanten Prüfungsdiagramme (Zustandsübergänge, Grenzwertanalysen etc.).
- ⌨️ **Tastatursteuerung**:
  - `1`–`5` bzw. `A`–`E`: Option wählen
  - `Enter`: Antwort prüfen / nächste Frage
  - `R` / `Z`: Neue Zufallsfrage
  - `M`: Frage merken (Bookmark)
  - `Strg+K` / `Cmd+K`: Schnelle Volltextsuche
- 🌓 **Dark & Light Mode** + optionale dezente Soundeffekte (Web Audio API).

---

## 🚀 Schnelleinstieg (Lokal ausführen)

Da es sich um eine moderne statische Webanwendung handelt, wird kein komplexer Build-Schritt benötigt.

### Option 1: Mit Python
```bash
python3 -m http.server 8080
```
Öffne anschließend **[http://localhost:8080](http://localhost:8080)** im Browser.

### Option 2: Mit Node / npm
```bash
npm start
```

---

## 🌐 Direktes Hosting auf GitHub Pages

Dieses Repository kann ohne zusätzliche Konfiguration kostenlos über **GitHub Pages** bereitgestellt werden:
1. Gehe in deinem GitHub-Repository auf **Settings** ➔ **Pages**.
2. Wähle unter **Branch** den Branch `main` und Ordner `/(root)`.
3. Klicke auf **Save**. Die Web-App ist nach wenigen Sekunden weltweit über deine GitHub-Pages-URL erreichbar!

---

## 📁 Projektstruktur

```
ISTQB_Question/
├── Beispiele/                  # Offizielle ISTQB / GTB Musterprüfungs-PDFs (SET A bis F)
├── css/
│   └── style.css              # Modernes Stylesheet (Themes, Glassmorphism, Animationen)
├── data/
│   ├── questions.json         # Extrahierte 240 Fragen mit Antworten und Begründungen
│   └── images/                # Extrahierte Diagrammbilder
├── js/
│   └── app.js                 # Anwendungslogik, Audio-Synthese, State Management
├── scripts/
│   └── extract_questions.py   # Automatisches Extraktionsskript aus den PDFs
├── index.html                 # Benutzeroberfläche
├── package.json               # Start-Skripte
└── README.md                  # Dokumentation
```

---

## 📜 Lizenz & Urheberrecht
Die Musterprüfungsfragen und Begründungen basieren auf den öffentlich freigegebenen Unterlagen des **International Software Testing Qualifications Board (ISTQB®)** und des **German Testing Board e.V. (GTB)**.
