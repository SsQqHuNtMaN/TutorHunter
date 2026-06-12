/**
 * i18n.js — Bilingual (zh/en) text switching
 *
 * Convention: all display elements have data-zh and data-en attributes.
 * switchLanguage(lang) swaps text content based on current language.
 * Default: detects from navigator.language; falls back to 'zh' for zh-CN/zh-TW/zh-HK.
 */
(function () {
  'use strict';

  const LANG_KEY = 'tutorhunter-lang';

  function detectLanguage() {
    const saved = localStorage.getItem(LANG_KEY);
    if (saved === 'zh' || saved === 'en') return saved;

    const nav = navigator.language || '';
    if (nav.startsWith('zh')) return 'zh';
    return 'en';
  }

  function switchLanguage(lang) {
    document.querySelectorAll('[data-zh][data-en]').forEach(function (el) {
      var text = el.getAttribute('data-' + lang);
      if (text !== null && text !== '') {
        el.textContent = text;
      }
    });

    // Update placeholder attributes
    document.querySelectorAll('[data-zh-placeholder][data-en-placeholder]').forEach(function (el) {
      var placeholder = el.getAttribute('data-' + lang + '-placeholder');
      if (placeholder !== null) {
        el.placeholder = placeholder;
      }
    });

    // Update lang toggle buttons
    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });

    localStorage.setItem(LANG_KEY, lang);
    document.documentElement.lang = lang;

    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('languagechange', { detail: { lang: lang } }));
  }

  function init() {
    var lang = detectLanguage();

    // Attach toggle handlers
    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        switchLanguage(btn.getAttribute('data-lang'));
      });
    });

    // Apply initial language
    switchLanguage(lang);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose to global scope
  window.TutorHunterI18n = {
    switchLanguage: switchLanguage,
    getLanguage: function () { return localStorage.getItem(LANG_KEY) || detectLanguage(); }
  };
})();
