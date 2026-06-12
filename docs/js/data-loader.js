/**
 * data-loader.js — Load professor JSON data for client-side rendering
 *
 * On the index page: loads index.json, then optionally individual professor JSONs
 * On detail pages: loads the specific professor JSON
 */
(function () {
  'use strict';

  const DATA_BASE = 'data/professors/';

  async function loadIndex() {
    const resp = await fetch(DATA_BASE + 'index.json');
    if (!resp.ok) throw new Error('Failed to load index: ' + resp.status);
    return resp.json();
  }

  async function loadProfessor(id) {
    const resp = await fetch(DATA_BASE + id + '.json');
    if (!resp.ok) throw new Error('Failed to load professor ' + id + ': ' + resp.status);
    return resp.json();
  }

  async function loadAllProfessors() {
    const index = await loadIndex();
    const professors = await Promise.all(
      index.map(function (entry) { return loadProfessor(entry.id); })
    );
    return professors;
  }

  window.TutorHunterData = {
    loadIndex: loadIndex,
    loadProfessor: loadProfessor,
    loadAllProfessors: loadAllProfessors
  };
})();
