/**
 * comparison-table.js — Interactive comparison table component
 *
 * Features:
 * - Column sorting (click header)
 * - Row click → navigate to detail page
 * - Client-side filtering and search
 * - Group highlighting on hover
 */
(function () {
  'use strict';

  function safeStr(value, lang) {
    lang = lang || window.TutorHunterI18n ? window.TutorHunterI18n.getLanguage() : 'zh';
    if (value === null || value === undefined) return '';
    if (typeof value === 'object' && value.zh !== undefined) {
      return value[lang] || value.en || '';
    }
    if (Array.isArray(value)) {
      return value.map(function (v) { return safeStr(v, lang); }).join(', ');
    }
    return String(value);
  }

  function renderTable(professors, containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;

    if (!professors || professors.length === 0) {
      container.innerHTML =
        '<div class="empty-state">' +
        '<h3 data-zh="暂无导师数据" data-en="No Professor Data"></h3>' +
        '<p data-zh="请先在 Claude Code 中运行 hunt 命令添加导师" data-en="Run the hunt command in Claude Code to add professors"></p>' +
        '</div>';
      return;
    }

    var html = '<div class="table-container"><table class="professor-table"><thead><tr>';
    var headers = [
      { key: 'display_name', zh: '姓名', en: 'Name', sortable: true },
      { key: 'display_university', zh: '院校', en: 'University', sortable: true },
      { key: 'display_department', zh: '学院', en: 'Department', sortable: true },
      { key: 'title', zh: '职称', en: 'Title', sortable: false },
      { key: 'homepage_dirs', zh: '研究方向', en: 'Research', sortable: false },
      { key: 'display_group', zh: '课题组', en: 'Group', sortable: true },
      { key: 'is_recruiting', zh: '招生', en: 'Recruiting', sortable: true },
      { key: 'quality_overall', zh: '数据质量', en: 'Quality', sortable: true }
    ];

    headers.forEach(function (h) {
      html += '<th data-sort="' + h.key + '"' + (h.sortable ? ' class="sortable"' : '') + '>';
      html += '<span data-zh="' + h.zh + '" data-en="' + h.en + '">' + h.zh + '</span>';
      if (h.sortable) html += '<span class="sort-arrow">↕</span>';
      html += '</th>';
    });
    html += '</tr></thead><tbody>';

    professors.forEach(function (prof) {
      html += '<tr data-id="' + prof.id + '" data-group="' + safeStr(prof.display_group) + '">';

      // Name
      html += '<td><span class="professor-name">' + safeStr(prof.name) + '</span>';
      if (prof.display_name_en) {
        html += '<br><small style="color:#999;">' + prof.display_name_en + '</small>';
      }
      html += '</td>';

      // University
      html += '<td>' + safeStr(prof.university) + '</td>';

      // Department
      html += '<td>' + safeStr(prof.department) + '</td>';

      // Title
      html += '<td>' + (prof.title || '') + '</td>';

      // Research directions
      html += '<td><div class="tag-list">';
      var dirs = prof.homepage_dirs || [];
      var tags = prof.tags || [];
      var tagColors = ['tag-blue', 'tag-green', 'tag-purple', 'tag-orange'];
      tags.forEach(function (tag, i) {
        html += '<span class="tag ' + (tagColors[i % tagColors.length]) + '">' + tag + '</span>';
      });
      html += '</div></td>';

      // Group
      html += '<td>' + (prof.display_group ?
        '<span class="group-badge" style="font-size:0.78rem;padding:0.15rem 0.5rem;">' + prof.display_group + '</span>' :
        '<span style="color:#ccc;">—</span>') + '</td>';

      // Recruiting
      html += '<td>';
      if (prof.is_recruiting === true) {
        html += '<span class="status-dot status-recruiting"></span><span data-zh="招生中" data-en="Yes"></span>';
      } else if (prof.is_recruiting === false) {
        html += '<span class="status-dot status-not-recruiting"></span><span data-zh="暂不招生" data-en="No"></span>';
      } else {
        html += '<span class="status-dot status-unknown"></span><span data-zh="未知" data-en="Unknown"></span>';
      }
      html += '</td>';

      // Quality
      html += '<td><span class="quality-badge quality-' + (prof.quality_overall || 'low') + '">' +
        (prof.quality_overall || 'low') + '</span></td>';

      html += '</tr>';
    });

    html += '</tbody></table></div>';
    container.innerHTML = html;
    attachEvents(professors);
  }

  function attachEvents(professors) {
    // Sort on header click
    document.querySelectorAll('.professor-table th.sortable').forEach(function (th) {
      th.addEventListener('click', function () {
        var key = th.getAttribute('data-sort');
        sortTable(key, professors);
      });
    });

    // Navigate on row click
    document.querySelectorAll('.professor-table tbody tr').forEach(function (tr) {
      tr.addEventListener('click', function () {
        var id = tr.getAttribute('data-id');
        if (id) {
          window.location.href = 'professors/' + id + '.html';
        }
      });
    });

    // Group highlighting
    document.querySelectorAll('.group-badge').forEach(function (badge) {
      badge.addEventListener('mouseenter', function () {
        var groupName = badge.textContent.trim();
        document.querySelectorAll('.professor-table tbody tr').forEach(function (tr) {
          if (tr.getAttribute('data-group') === groupName) {
            tr.classList.add('group-highlight');
          }
        });
      });
      badge.addEventListener('mouseleave', function () {
        document.querySelectorAll('.professor-table tbody tr').forEach(function (tr) {
          tr.classList.remove('group-highlight');
        });
      });
    });
  }

  function sortTable(key, professors) {
    var th = document.querySelector('.professor-table th[data-sort="' + key + '"]');
    var isAsc = th.classList.contains('sorted-asc');

    // Reset all sort indicators
    document.querySelectorAll('.professor-table th').forEach(function (h) {
      h.classList.remove('sorted', 'sorted-asc', 'sorted-desc');
    });

    var sorted = professors.slice().sort(function (a, b) {
      var va = safeStr(getNestedValue(a, key));
      var vb = safeStr(getNestedValue(b, key));
      if (va < vb) return isAsc ? 1 : -1;
      if (va > vb) return isAsc ? -1 : 1;
      return 0;
    });

    th.classList.add('sorted', isAsc ? 'sorted-desc' : 'sorted-asc');
    renderTable(sorted, 'table-container');
  }

  function getNestedValue(obj, key) {
    if (obj[key] !== undefined) return obj[key];
    // Try nested paths
    var parts = key.split('.');
    var val = obj;
    for (var i = 0; i < parts.length; i++) {
      if (val === null || val === undefined) return '';
      val = val[parts[i]];
    }
    return val;
  }

  function filterProfessors(professors, filters) {
    return professors.filter(function (prof) {
      // Search text
      if (filters.search) {
        var searchText = filters.search.toLowerCase();
        var searchable = [
          safeStr(prof.name), safeStr(prof.name, 'en'),
          safeStr(prof.university), safeStr(prof.university, 'en'),
          safeStr(prof.department), prof.title || '',
          (prof.homepage_dirs || []).join(' '),
          (prof.tags || []).join(' ')
        ].join(' ').toLowerCase();
        if (searchable.indexOf(searchText) === -1) return false;
      }

      // Region filter
      if (filters.region && filters.region !== 'all' && prof.region !== filters.region) return false;

      // University filter
      if (filters.university && filters.university !== 'all') {
        if (safeStr(prof.university) !== filters.university) return false;
      }

      // Tag filter
      if (filters.tag && filters.tag !== 'all') {
        if (!(prof.tags || []).includes(filters.tag)) return false;
      }

      // Recruiting filter
      if (filters.recruiting === 'yes' && prof.is_recruiting !== true) return false;
      if (filters.recruiting === 'no' && prof.is_recruiting !== false) return false;

      return true;
    });
  }

  window.TutorHunterTable = {
    renderTable: renderTable,
    filterProfessors: filterProfessors
  };
})();
