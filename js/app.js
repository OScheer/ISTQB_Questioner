/**
 * ISTQB® CTFL 4.0 Fragenautomat
 * Modern, interactive quiz trainer with 240 official questions.
 */

(function () {
  'use strict';

  // State
  let allQuestions = [];
  let currentQuestion = null;
  let selectedOptions = new Set();
  let isChecked = false;

  let activeMode = 'ALL'; // 'ALL', 'WRONG', 'BOOKMARKS'
  let activeFilterSet = 'ALL';
  let activeFilterK = 'ALL';

  let soundEnabled = true;
  let audioCtx = null;

  // Persistence keys
  const STORAGE_KEY_STATS = 'istqb_stats_v1';
  const STORAGE_KEY_BOOKMARKS = 'istqb_bookmarks_v1';
  const STORAGE_KEY_WRONG = 'istqb_wrong_v1';
  const STORAGE_KEY_THEME = 'istqb_theme_v1';
  const STORAGE_KEY_SOUND = 'istqb_sound_v1';

  let userStats = {
    answered: 0,
    correct: 0,
    wrong: 0,
    streak: 0,
    answeredIds: []
  };

  let bookmarks = new Set();
  let wrongQuestions = new Set();

  // DOM Elements
  const dom = {
    // Stats
    statProgress: document.getElementById('stat-progress'),
    statCorrect: document.getElementById('stat-correct'),
    statWrong: document.getElementById('stat-wrong'),
    statRate: document.getElementById('stat-rate'),
    statStreak: document.getElementById('stat-streak'),

    // Badges & Meta
    badgeSet: document.getElementById('badge-set'),
    badgeQNum: document.getElementById('badge-qnum'),
    badgeKLevel: document.getElementById('badge-klevel'),
    badgePoints: document.getElementById('badge-points'),
    btnBookmarkCurrent: document.getElementById('btn-bookmark-current'),
    bookmarkIcon: document.getElementById('bookmark-icon'),

    // Question content
    questionStem: document.getElementById('question-stem'),
    diagramContainer: document.getElementById('diagram-container'),
    diagramImage: document.getElementById('diagram-image'),
    instructionBanner: document.getElementById('instruction-banner'),
    instructionText: document.getElementById('instruction-text'),
    optionsContainer: document.getElementById('options-container'),

    // Actions
    btnCheck: document.getElementById('btn-check'),
    btnNext: document.getElementById('btn-next'),
    btnRandom: document.getElementById('btn-random'),

    // Explanations
    explanationContainer: document.getElementById('explanation-container'),
    loMetaBadge: document.getElementById('lo-meta-badge'),
    explanationItems: document.getElementById('explanation-items'),

    // Sidebar & Filters
    modeAll: document.getElementById('mode-all'),
    modeWrong: document.getElementById('mode-wrong'),
    modeBookmarks: document.getElementById('mode-bookmarks'),
    countWrong: document.getElementById('count-wrong'),
    countBookmarks: document.getElementById('count-bookmarks'),
    filterSet: document.getElementById('filter-set'),
    klevelPills: document.querySelectorAll('.filter-pill'),

    // Header buttons
    btnToggleTheme: document.getElementById('btn-toggle-theme'),
    btnToggleSound: document.getElementById('btn-toggle-sound'),
    btnResetStats: document.getElementById('btn-reset-stats'),
    btnOpenSearch: document.getElementById('btn-open-search'),

    // Modal Search
    modalSearch: document.getElementById('modal-search'),
    modalSearchInput: document.getElementById('modal-search-input'),
    modalSearchResults: document.getElementById('modal-search-results'),
    btnCloseSearch: document.getElementById('btn-close-search')
  };

  // Init App
  async function init() {
    loadStorage();
    setupEventListeners();
    updateTheme(localStorage.getItem(STORAGE_KEY_THEME) || 'dark');
    updateStatsUI();

    try {
      dom.questionStem.textContent = 'Lade Prüfungsfragen (240 Fragen)...';
      const response = await fetch('data/questions.json');
      if (!response.ok) throw new Error('Netzwerkfehler beim Laden von questions.json');
      allQuestions = await response.json();
      
      updateCounts();
      loadNextQuestion();
    } catch (err) {
      console.error(err);
      dom.questionStem.textContent = 'Fehler beim Laden der Fragen. Bitte stelle sicher, dass questions.json vorhanden ist.';
    }
  }

  // Load state from localStorage
  function loadStorage() {
    try {
      const savedStats = localStorage.getItem(STORAGE_KEY_STATS);
      if (savedStats) userStats = Object.assign(userStats, JSON.parse(savedStats));

      const savedBookmarks = localStorage.getItem(STORAGE_KEY_BOOKMARKS);
      if (savedBookmarks) bookmarks = new Set(JSON.parse(savedBookmarks));

      const savedWrong = localStorage.getItem(STORAGE_KEY_WRONG);
      if (savedWrong) wrongQuestions = new Set(JSON.parse(savedWrong));

      const savedSound = localStorage.getItem(STORAGE_KEY_SOUND);
      if (savedSound !== null) soundEnabled = savedSound === 'true';
      updateSoundUI();
    } catch (e) {
      console.warn('Storage read error:', e);
    }
  }

  function saveStorage() {
    try {
      localStorage.setItem(STORAGE_KEY_STATS, JSON.stringify(userStats));
      localStorage.setItem(STORAGE_KEY_BOOKMARKS, JSON.stringify([...bookmarks]));
      localStorage.setItem(STORAGE_KEY_WRONG, JSON.stringify([...wrongQuestions]));
      localStorage.setItem(STORAGE_KEY_SOUND, soundEnabled.toString());
    } catch (e) {
      console.warn('Storage save error:', e);
    }
  }

  // Filter questions based on current settings
  function getFilteredQuestions() {
    return allQuestions.filter(q => {
      // Mode filter
      if (activeMode === 'WRONG' && !wrongQuestions.has(q.id)) return false;
      if (activeMode === 'BOOKMARKS' && !bookmarks.has(q.id)) return false;

      // Set filter
      if (activeFilterSet !== 'ALL' && q.set !== activeFilterSet) return false;

      // K-Level filter
      if (activeFilterK !== 'ALL' && q.k_level !== activeFilterK) return false;

      return true;
    });
  }

  // Load random question from pool
  function loadNextQuestion(preferredQuestionId = null) {
    isChecked = false;
    selectedOptions.clear();

    const pool = getFilteredQuestions();

    if (pool.length === 0) {
      dom.questionStem.textContent = 'Keine Fragen für die aktuellen Filtereinstellungen gefunden.';
      dom.optionsContainer.innerHTML = '';
      dom.instructionBanner.style.display = 'none';
      dom.diagramContainer.style.display = 'none';
      dom.explanationContainer.style.display = 'none';
      dom.btnCheck.style.display = 'inline-flex';
      dom.btnCheck.disabled = true;
      dom.btnNext.style.display = 'none';
      return;
    }

    if (preferredQuestionId) {
      currentQuestion = pool.find(q => q.id === preferredQuestionId) || pool[0];
    } else {
      // Pick random question, preferably one different from currentQuestion
      if (pool.length > 1 && currentQuestion) {
        const remaining = pool.filter(q => q.id !== currentQuestion.id);
        const idx = Math.floor(Math.random() * remaining.length);
        currentQuestion = remaining[idx];
      } else {
        const idx = Math.floor(Math.random() * pool.length);
        currentQuestion = pool[idx];
      }
    }

    renderQuestion(currentQuestion);
  }

  // Render question UI
  function renderQuestion(q) {
    // Badges
    dom.badgeSet.textContent = q.set;
    dom.badgeQNum.textContent = `Frage ${q.question_number} / 40`;
    dom.badgeKLevel.textContent = q.k_level;
    dom.badgeKLevel.setAttribute('data-k', q.k_level);
    dom.badgePoints.textContent = `${q.points.toFixed(1)} ${q.points === 1 ? 'Punkt' : 'Punkte'}`;

    // Bookmark button
    updateBookmarkButton();

    // Stem
    dom.questionStem.textContent = q.stem;

    // Diagram
    if (q.images && q.images.length > 0) {
      dom.diagramContainer.style.display = 'block';
      dom.diagramImage.src = q.images[0];
    } else {
      dom.diagramContainer.style.display = 'none';
      dom.diagramImage.src = '';
    }

    // Instruction Banner
    dom.instructionBanner.style.display = 'flex';
    dom.instructionText.textContent = q.instruction || (q.is_multi_select ? 'Wählen Sie ZWEI Optionen!' : 'Wählen Sie EINE Option!');

    // Options
    dom.optionsContainer.innerHTML = '';
    const letters = Object.keys(q.options).sort();

    letters.forEach(letter => {
      const text = q.options[letter];
      const optEl = document.createElement('div');
      optEl.className = 'option-item';
      optEl.dataset.letter = letter;

      optEl.innerHTML = `
        <div class="option-letter">${letter.toUpperCase()}</div>
        <div class="option-text">${escapeHtml(text)}</div>
        <span class="option-badge-status" style="display: none;"></span>
      `;

      optEl.addEventListener('click', () => handleOptionClick(letter, optEl));
      dom.optionsContainer.appendChild(optEl);
    });

    // Reset controls
    dom.btnCheck.style.display = 'inline-flex';
    dom.btnCheck.disabled = true;
    dom.btnNext.style.display = 'none';
    dom.explanationContainer.style.display = 'none';

    // Scroll question into view smoothly
    document.getElementById('question-card').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Handle Option selection
  function handleOptionClick(letter, element) {
    if (isChecked) return; // Locked once checked

    playAudio('click');

    if (currentQuestion.is_multi_select) {
      // Multi-select toggle
      if (selectedOptions.has(letter)) {
        selectedOptions.delete(letter);
        element.classList.remove('selected');
      } else {
        selectedOptions.add(letter);
        element.classList.add('selected');
      }
    } else {
      // Single-select: Clear previous
      selectedOptions.clear();
      dom.optionsContainer.querySelectorAll('.option-item').forEach(el => el.classList.remove('selected'));
      selectedOptions.add(letter);
      element.classList.add('selected');
    }

    // Enable / disable check button
    dom.btnCheck.disabled = selectedOptions.size === 0;
  }

  // Evaluate Answer
  function checkAnswer() {
    if (isChecked || selectedOptions.size === 0) return;
    isChecked = true;

    const correctAnswers = new Set(currentQuestion.correct_answers);
    const selectedArr = Array.from(selectedOptions);

    // Is totally correct?
    const isCorrect = selectedArr.length === correctAnswers.size &&
                      selectedArr.every(l => correctAnswers.has(l));

    // Update stats
    userStats.answered += 1;
    if (!userStats.answeredIds.includes(currentQuestion.id)) {
      userStats.answeredIds.push(currentQuestion.id);
    }

    if (isCorrect) {
      userStats.correct += 1;
      userStats.streak += 1;
      wrongQuestions.delete(currentQuestion.id);
      playAudio('success');
    } else {
      userStats.wrong += 1;
      userStats.streak = 0;
      wrongQuestions.add(currentQuestion.id);
      playAudio('error');
    }

    saveStorage();
    updateStatsUI();
    updateCounts();

    // Style option items
    dom.optionsContainer.querySelectorAll('.option-item').forEach(optEl => {
      const letter = optEl.dataset.letter;
      const isLetterCorrect = correctAnswers.has(letter);
      const isLetterSelected = selectedOptions.has(letter);
      const badge = optEl.querySelector('.option-badge-status');

      optEl.classList.add('locked');

      if (isLetterSelected) {
        if (isLetterCorrect) {
          optEl.classList.add('correct');
          badge.textContent = '✓ Richtig';
          badge.style.display = 'inline-block';
        } else {
          optEl.classList.add('incorrect');
          badge.textContent = '✕ Falsch';
          badge.style.display = 'inline-block';
        }
      } else {
        if (isLetterCorrect) {
          optEl.classList.add('missed');
          badge.textContent = 'Richtige Antwort';
          badge.style.display = 'inline-block';
        }
      }
    });

    // Render Explanation Card
    renderExplanations();

    // Switch action buttons
    dom.btnCheck.style.display = 'none';
    dom.btnNext.style.display = 'inline-flex';
  }

  // Render Explanations
  function renderExplanations() {
    dom.loMetaBadge.textContent = currentQuestion.lo_title || currentQuestion.meta || '';
    dom.explanationItems.innerHTML = '';

    const letters = Object.keys(currentQuestion.options).sort();

    letters.forEach(letter => {
      const expData = currentQuestion.explanations[letter];
      const isCorrect = currentQuestion.correct_answers.includes(letter);
      const itemEl = document.createElement('div');
      itemEl.className = `exp-item ${isCorrect ? 'status-korrekt' : 'status-falsch'}`;

      let expText = expData ? expData.text : '';
      if (!expText && currentQuestion.raw_explanation) {
        expText = currentQuestion.raw_explanation;
      }

      itemEl.innerHTML = `
        <div class="exp-item-label">
          <span>${letter.toUpperCase()})</span>
          <span>${isCorrect ? 'KORREKT' : 'FALSCH'}</span>
        </div>
        <div class="exp-item-text">${escapeHtml(expText)}</div>
      `;

      dom.explanationItems.appendChild(itemEl);
    });

    dom.explanationContainer.style.display = 'block';
  }

  // Toggle Bookmark
  function toggleBookmark() {
    if (!currentQuestion) return;
    if (bookmarks.has(currentQuestion.id)) {
      bookmarks.delete(currentQuestion.id);
    } else {
      bookmarks.add(currentQuestion.id);
    }
    saveStorage();
    updateBookmarkButton();
    updateCounts();
  }

  function updateBookmarkButton() {
    if (!currentQuestion) return;
    const isBookmarked = bookmarks.has(currentQuestion.id);
    if (isBookmarked) {
      dom.btnBookmarkCurrent.classList.add('bookmarked');
      dom.bookmarkIcon.textContent = '★';
      dom.btnBookmarkCurrent.innerHTML = '<span id="bookmark-icon">★</span> Gemerkt';
    } else {
      dom.btnBookmarkCurrent.classList.remove('bookmarked');
      dom.btnBookmarkCurrent.innerHTML = '<span id="bookmark-icon">☆</span> Merken';
    }
  }

  // Update Stats UI
  function updateStatsUI() {
    const total = 240;
    const answeredCount = userStats.answeredIds.length;
    dom.statProgress.textContent = `${answeredCount} / ${total}`;
    dom.statCorrect.textContent = userStats.correct;
    dom.statWrong.textContent = userStats.wrong;

    const rate = userStats.answered > 0
      ? Math.round((userStats.correct / userStats.answered) * 100)
      : 0;
    dom.statRate.textContent = `${rate}%`;
    dom.statStreak.textContent = `🔥 ${userStats.streak}`;
  }

  function updateCounts() {
    dom.countWrong.textContent = wrongQuestions.size;
    dom.countBookmarks.textContent = bookmarks.size;
  }

  // Audio synthesis using Web Audio API
  function playAudio(type) {
    if (!soundEnabled) return;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }

      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);

      if (type === 'click') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(600, now);
        osc.frequency.exponentialRampToValueAtTime(800, now + 0.05);
        gain.gain.setValueAtTime(0.04, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now);
        osc.stop(now + 0.05);
      } else if (type === 'success') {
        // Joyful chord (C5 - E5 - G5)
        [523.25, 659.25, 783.99].forEach((freq, i) => {
          const chordOsc = audioCtx.createOscillator();
          const chordGain = audioCtx.createGain();
          chordOsc.connect(chordGain);
          chordGain.connect(audioCtx.destination);
          chordOsc.type = 'triangle';
          chordOsc.frequency.setValueAtTime(freq, now + i * 0.08);
          chordGain.gain.setValueAtTime(0.08, now + i * 0.08);
          chordGain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.25);
          chordOsc.start(now + i * 0.08);
          chordOsc.stop(now + i * 0.08 + 0.25);
        });
      } else if (type === 'error') {
        // Soft low tone
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(220, now);
        osc.frequency.exponentialRampToValueAtTime(140, now + 0.2);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.2);
      }
    } catch (e) {
      // Audio not supported or blocked
    }
  }

  // Theme Handling
  function updateTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY_THEME, theme);
    const moonIcon = document.getElementById('icon-moon');
    if (theme === 'light') {
      moonIcon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    } else {
      moonIcon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    }
  }

  function updateSoundUI() {
    const soundBtn = dom.btnToggleSound;
    if (soundEnabled) {
      soundBtn.style.color = 'var(--accent-primary)';
      soundBtn.title = 'Sound aktiviert (Klick zum Stummschalten)';
    } else {
      soundBtn.style.color = 'var(--text-muted)';
      soundBtn.title = 'Sound stummgeschaltet (Klick zum Aktivieren)';
    }
  }

  // Setup Event Listeners
  function setupEventListeners() {
    // Check answer
    dom.btnCheck.addEventListener('click', checkAnswer);

    // Next question
    dom.btnNext.addEventListener('click', () => loadNextQuestion());

    // Random question
    dom.btnRandom.addEventListener('click', () => loadNextQuestion());

    // Bookmark
    dom.btnBookmarkCurrent.addEventListener('click', toggleBookmark);

    // Modes in sidebar
    dom.modeAll.addEventListener('click', () => {
      setMode('ALL', dom.modeAll);
    });

    dom.modeWrong.addEventListener('click', () => {
      if (wrongQuestions.size === 0) {
        alert('Aktuell sind keine falsch beantworteten Fragen gespeichert.');
        return;
      }
      setMode('WRONG', dom.modeWrong);
    });

    dom.modeBookmarks.addEventListener('click', () => {
      if (bookmarks.size === 0) {
        alert('Ihre Merkliste ist aktuell leer. Sie können Fragen mit dem Sternchen-Button oben rechts merken.');
        return;
      }
      setMode('BOOKMARKS', dom.modeBookmarks);
    });

    // Filters
    dom.filterSet.addEventListener('change', (e) => {
      activeFilterSet = e.target.value;
      loadNextQuestion();
    });

    dom.klevelPills.forEach(pill => {
      pill.addEventListener('click', () => {
        dom.klevelPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        activeFilterK = pill.dataset.klevel;
        loadNextQuestion();
      });
    });

    // Header actions
    dom.btnToggleTheme.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      updateTheme(current === 'dark' ? 'light' : 'dark');
    });

    dom.btnToggleSound.addEventListener('click', () => {
      soundEnabled = !soundEnabled;
      saveStorage();
      updateSoundUI();
    });

    dom.btnResetStats.addEventListener('click', () => {
      if (confirm('Möchten Sie Ihren gesamten Fortschritt und die Statistiken wirklich zurücksetzen?')) {
        userStats = { answered: 0, correct: 0, wrong: 0, streak: 0, answeredIds: [] };
        wrongQuestions.clear();
        bookmarks.clear();
        saveStorage();
        updateStatsUI();
        updateCounts();
        updateBookmarkButton();
        alert('Fortschritt wurde erfolgreich zurückgesetzt.');
      }
    });

    // Search modal
    dom.btnOpenSearch.addEventListener('click', openSearchModal);
    dom.btnCloseSearch.addEventListener('click', closeSearchModal);
    dom.modalSearch.addEventListener('click', (e) => {
      if (e.target === dom.modalSearch) closeSearchModal();
    });

    dom.modalSearchInput.addEventListener('input', (e) => {
      renderSearchResults(e.target.value);
    });

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      // Don't trigger if inside modal input
      if (document.activeElement === dom.modalSearchInput) {
        if (e.key === 'Escape') closeSearchModal();
        return;
      }

      if (e.key === 'Escape') {
        closeSearchModal();
        return;
      }

      // Open search: Ctrl+K or /
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openSearchModal();
        return;
      }

      // Enter
      if (e.key === 'Enter') {
        if (!isChecked && !dom.btnCheck.disabled) {
          e.preventDefault();
          checkAnswer();
        } else if (isChecked) {
          e.preventDefault();
          loadNextQuestion();
        }
      }

      // Random / Next: R or Z
      if (!isChecked && (e.key.toLowerCase() === 'r' || e.key.toLowerCase() === 'z')) {
        loadNextQuestion();
      }

      // Bookmark: M
      if (e.key.toLowerCase() === 'm') {
        toggleBookmark();
      }

      // Options 1-5 or A-E
      const key = e.key.toLowerCase();
      let targetLetter = null;
      if (['1', '2', '3', '4', '5'].includes(key)) {
        const letters = ['a', 'b', 'c', 'd', 'e'];
        targetLetter = letters[parseInt(key) - 1];
      } else if (['a', 'b', 'c', 'd', 'e'].includes(key)) {
        targetLetter = key;
      }

      if (targetLetter && currentQuestion && currentQuestion.options[targetLetter]) {
        const optEl = dom.optionsContainer.querySelector(`.option-item[data-letter="${targetLetter}"]`);
        if (optEl) handleOptionClick(targetLetter, optEl);
      }
    });
  }

  function setMode(mode, activeBtn) {
    activeMode = mode;
    [dom.modeAll, dom.modeWrong, dom.modeBookmarks].forEach(btn => btn.classList.remove('active'));
    activeBtn.classList.add('active');
    loadNextQuestion();
  }

  // Search Modal Functions
  function openSearchModal() {
    dom.modalSearch.classList.add('active');
    dom.modalSearchInput.value = '';
    renderSearchResults('');
    setTimeout(() => dom.modalSearchInput.focus(), 50);
  }

  function closeSearchModal() {
    dom.modalSearch.classList.remove('active');
  }

  function renderSearchResults(query) {
    const qTrim = query.trim().toLowerCase();
    const results = allQuestions.filter(q => {
      if (!qTrim) return true;
      return (
        q.stem.toLowerCase().includes(qTrim) ||
        (q.lo_title && q.lo_title.toLowerCase().includes(qTrim)) ||
        (q.meta && q.meta.toLowerCase().includes(qTrim)) ||
        q.set.toLowerCase().includes(qTrim)
      );
    }).slice(0, 30); // show top 30 matches

    dom.modalSearchResults.innerHTML = '';
    if (results.length === 0) {
      dom.modalSearchResults.innerHTML = '<div style="color: var(--text-muted); padding: 1rem; text-align: center;">Keine passenden Fragen gefunden.</div>';
      return;
    }

    results.forEach(q => {
      const item = document.createElement('div');
      item.className = 'modal-q-item';
      item.innerHTML = `
        <span class="badge badge-set" style="flex-shrink:0;">${q.set} Q${q.question_number}</span>
        <span class="modal-q-title">${escapeHtml(q.stem)}</span>
        <span class="badge badge-klevel" style="flex-shrink:0;">${q.k_level}</span>
      `;
      item.addEventListener('click', () => {
        closeSearchModal();
        loadNextQuestion(q.id);
      });
      dom.modalSearchResults.appendChild(item);
    });
  }

  // Utility to escape HTML
  function escapeHtml(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Start the application
  window.addEventListener('DOMContentLoaded', init);
})();
