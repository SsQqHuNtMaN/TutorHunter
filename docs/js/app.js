/**
 * app.js — Main application logic for TutorHunter
 *
 * Coordinates: data loading → filtering → table rendering
 * Used on the index page.
 */
(function () {
  'use strict';

  var allProfessors = [];
  var currentFilters = {
    search: '',
    region: 'all',
    university: 'all',
    tag: 'all',
    recruiting: 'all',
    sort: { field: 'display_name', direction: 'asc' }
  };

  async function init() {
    try {
      // Try to load from embedded data first (server-rendered)
      var embeddedData = document.getElementById('embedded-data');
      if (embeddedData) {
        try {
          allProfessors = JSON.parse(embeddedData.textContent);
        } catch (e) {
          console.warn('Failed to parse embedded data, loading from JSON...');
        }
      }

      // Fallback: load from JSON files
      if (!allProfessors || allProfessors.length === 0) {
        if (window.TutorHunterData) {
          allProfessors = await window.TutorHunterData.loadAllProfessors();
        }
      }

      if (window.TutorHunterTable) {
        window.TutorHunterTable.renderTable(allProfessors, 'table-container');
      }
      setupFilters();
      updateStats();
    } catch (err) {
      console.error('Failed to initialize app:', err);
    }
  }

  function setupFilters() {
    // Search box
    var searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', function () {
        currentFilters.search = this.value;
        applyFilters();
      });
    }

    // Filter selects
    ['region-filter', 'university-filter', 'tag-filter', 'recruiting-filter'].forEach(function (id) {
      var select = document.getElementById(id);
      if (select) {
        select.addEventListener('change', function () {
          var key = id.replace('-filter', '');
          currentFilters[key] = this.value;
          applyFilters();
        });
      }
    });

    // Language change re-render
    window.addEventListener('languagechange', function () {
      applyFilters();
    });
  }

  function applyFilters() {
    var filtered = window.TutorHunterTable.filterProfessors(allProfessors, currentFilters);
    window.TutorHunterTable.renderTable(filtered, 'table-container');
    updateStats(filtered.length);
  }

  function updateStats(filteredCount) {
    var countEl = document.getElementById('professor-count');
    if (countEl) {
      if (filteredCount !== undefined) {
        countEl.textContent = filteredCount + ' / ' + allProfessors.length;
      } else {
        countEl.textContent = allProfessors.length;
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
