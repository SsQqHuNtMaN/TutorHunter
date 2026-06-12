/**
 * professor-card.js — Professor detail card component
 *
 * Used on the individual professor detail page to render:
 * - Tabs: Research, Publications, Group, Students, Admission
 * - Student inferred from papers display
 * - Source tracking display
 */
(function () {
  'use strict';

  function safeStr(value, lang) {
    lang = lang || (window.TutorHunterI18n ? window.TutorHunterI18n.getLanguage() : 'zh');
    if (value === null || value === undefined) return '';
    if (typeof value === 'object' && value.zh !== undefined) {
      return value[lang] || value.en || '';
    }
    if (Array.isArray(value)) {
      return value.map(function (v) { return safeStr(v, lang); }).join(', ');
    }
    return String(value);
  }

  function renderHero(prof) {
    var html = '<div class="hero-top">';
    html += '<div>';
    html += '<h1 class="hero-name">' + safeStr(prof.name, 'en') + '</h1>';
    html += '<div class="hero-name-zh">' + safeStr(prof.name, 'zh') + '</div>';
    html += '<div class="hero-title">' + (prof.title || '') + '</div>';
    html += '</div>';

    // Quality badge
    var quality = prof.quality_overall || 'low';
    html += '<div><span class="quality-badge quality-' + quality + '">' + quality + '</span></div>';
    html += '</div>';

    // Meta info
    html += '<div class="hero-meta">';
    if (prof.display_university) {
      html += '<div class="hero-meta-item">🏫 ' + prof.display_university + ' · ' + (prof.display_department || '') + '</div>';
    }
    if (prof.contact) {
      if (prof.has_email) {
        html += '<div class="hero-meta-item">📧 <a href="mailto:' + prof.contact.email + '">' + prof.contact.email + '</a></div>';
      }
      if (prof.has_phone) {
        html += '<div class="hero-meta-item">📞 ' + prof.contact.phone + '</div>';
      }
    }
    if (prof.contact && prof.contact.homepage_url) {
      html += '<div class="hero-meta-item">🌐 <a href="' + prof.contact.homepage_url + '" target="_blank" data-zh="个人主页" data-en="Homepage"></a></div>';
    }
    if (prof.contact && prof.has_scholar) {
      html += '<div class="hero-meta-item">📚 <a href="' + prof.contact.scholar_url + '" target="_blank">Google Scholar</a></div>';
    }
    if (prof.contact && prof.has_dblp) {
      html += '<div class="hero-meta-item">📋 <a href="' + prof.contact.dblp_url + '" target="_blank">DBLP</a></div>';
    }
    html += '</div>';

    // Tags
    if (prof.tags && prof.tags.length > 0) {
      html += '<div style="margin-top:1rem;">';
      var tagColors = ['tag-blue', 'tag-green', 'tag-purple', 'tag-orange', 'tag-red'];
      prof.tags.forEach(function (tag, i) {
        html += '<span class="tag ' + tagColors[i % tagColors.length] + '" style="font-size:0.82rem;margin-right:0.35rem;">' + tag + '</span>';
      });
      html += '</div>';
    }

    // Recruiting status
    if (prof.is_recruiting === true) {
      html += '<div style="margin-top:0.75rem;color:var(--success);font-weight:600;">🟢 <span data-zh="正在招生" data-en="Actively Recruiting"></span></div>';
    }

    document.getElementById('professor-hero').innerHTML = html;
  }

  function renderTabs(prof) {
    // Research tab
    var researchHtml = '';
    if (prof.research && prof.research.summary) {
      researchHtml += '<div class="section-card"><h3 class="section-title" data-zh="研究方向总结" data-en="Research Summary"></h3>';
      researchHtml += '<p>' + safeStr(prof.research.summary) + '</p></div>';
    }
    if (prof.homepage_dirs && prof.homepage_dirs.length > 0) {
      researchHtml += '<div class="section-card"><h3 class="section-title" data-zh="研究方向（主页标注）" data-en="Research Directions (Homepage)"></h3>';
      researchHtml += '<ul>';
      prof.homepage_dirs.forEach(function (d) {
        researchHtml += '<li>' + d + '</li>';
      });
      researchHtml += '</ul></div>';
    }
    if (prof.inferred_dirs && prof.inferred_dirs.length > 0) {
      researchHtml += '<div class="section-card"><h3 class="section-title" data-zh="研究方向（论文推断）" data-en="Research Directions (Inferred from Papers)"></h3>';
      researchHtml += '<ul><li>' + prof.inferred_dirs.join('</li><li>') + '</li></ul>';
      researchHtml += '<p style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.5rem;" data-zh="基于近两年论文自动总结" data-en="Auto-summarized from recent 2-year publications"></p>';
      researchHtml += '</div>';
    }
    if (!researchHtml) {
      researchHtml = '<div class="empty-state"><p data-zh="暂无研究方向信息" data-en="No research direction info available"></p></div>';
    }
    document.getElementById('tab-research').innerHTML = researchHtml;

    // Publications tab
    var pubHtml = '';
    var pubs = prof.recent_pubs || [];
    if (pubs.length > 0) {
      pubHtml += '<div class="section-card">';
      pubHtml += '<h3 class="section-title">' + pubs.length + ' <span data-zh="篇近期论文" data-en="Recent Publications"></span></h3>';
      if (prof.publications && prof.publications.source) {
        pubHtml += '<p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:1rem;" data-zh="来源：" data-en="Source: ">' + (prof.publications.source || '') + '</p>';
      }
      pubHtml += '<ul class="pub-list">';
      pubs.forEach(function (pub) {
        pubHtml += '<li class="pub-item">';
        pubHtml += '<div class="pub-title">' + (pub.title || '') + '</div>';
        if (pub.authors && pub.authors.length > 0) {
          pubHtml += '<div class="pub-authors">';
          pub.authors.forEach(function (author) {
            var cls = author.likely_student ? 'pub-author student' : (author.role === 'corresponding' ? 'pub-author professor' : '');
            var label = '';
            if (author.role === 'first_author') label = ' (1ˢᵗ)';
            if (author.role === 'corresponding') label = ' (✉)';
            pubHtml += '<span class="' + cls + '">' + (author.name || '') + label + '</span>; ';
          });
          pubHtml += '</div>';
        }
        pubHtml += '<div class="pub-meta">';
        if (pub.venue) pubHtml += '<span class="pub-venue">' + pub.venue + '</span>';
        if (pub.year) pubHtml += '<span class="pub-year">' + pub.year + '</span>';
        if (pub.citations) pubHtml += '<span class="pub-citations">' + pub.citations + ' citations</span>';
        if (pub.url) pubHtml += '<a href="' + pub.url + '" target="_blank" style="font-size:0.85rem;">[link]</a>';
        pubHtml += '</div>';
        pubHtml += '</li>';
      });
      pubHtml += '</ul></div>';
    } else {
      pubHtml = '<div class="empty-state"><p data-zh="暂无论文数据，需从 Google Scholar 获取" data-en="No publication data. Fetch from Google Scholar."></p></div>';
    }
    document.getElementById('tab-publications').innerHTML = pubHtml;

    // Students tab
    var studentsHtml = '';
    var inferredStudents = prof.inferred_students || [];
    if (inferredStudents.length > 0) {
      studentsHtml += '<div class="section-card">';
      studentsHtml += '<h3 class="section-title" data-zh="论文推断学生" data-en="Students Inferred from Papers"></h3>';
      studentsHtml += '<p style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:1rem;" data-zh="以下姓名从论文一作列表中复现推断" data-en="Inferred from recurring first-author names in publications"></p>';
      studentsHtml += '<ul class="destination-list">';
      inferredStudents.forEach(function (stu) {
        studentsHtml += '<li class="dest-item">';
        studentsHtml += '<div class="dest-info">';
        studentsHtml += '<div class="dest-name">' + (stu.name || '') + '</div>';
        studentsHtml += '<div style="font-size:0.85rem;color:var(--text-secondary);">' + (stu.papers_count || 0) + ' papers: ' + (stu.first_author_in || []).join(', ') + '</div>';
        studentsHtml += '</div></li>';
      });
      studentsHtml += '</ul></div>';
    }
    // Destinations
    var destinations = prof.destinations || [];
    if (destinations.length > 0) {
      studentsHtml += '<div class="section-card">';
      studentsHtml += '<h3 class="section-title" data-zh="学生去向" data-en="Student Destinations"></h3>';
      studentsHtml += '<ul class="destination-list">';
      destinations.forEach(function (dest) {
        studentsHtml += '<li class="dest-item">';
        if (dest.year) studentsHtml += '<span class="dest-year">' + dest.year + '</span>';
        studentsHtml += '<div class="dest-info">';
        studentsHtml += '<div class="dest-name">' + (dest.name || '') + ' (' + (dest.degree || '') + ')</div>';
        studentsHtml += '<div class="dest-role">→ ' + (dest.destination || '') + ' · ' + (dest.role || '') + '</div>';
        if (dest.location) studentsHtml += '<div style="font-size:0.8rem;color:var(--text-secondary);">' + dest.location + '</div>';
        studentsHtml += '</div></li>';
      });
      studentsHtml += '</ul></div>';
    }
    if (!studentsHtml) {
      studentsHtml = '<div class="empty-state"><p data-zh="暂无学生信息" data-en="No student information available"></p></div>';
    }
    document.getElementById('tab-students').innerHTML = studentsHtml;

    // Group tab
    var groupHtml = '';
    if (prof.display_group) {
      groupHtml += '<div class="section-card">';
      groupHtml += '<h3 class="section-title" data-zh="课题组" data-en="Research Group"></h3>';
      groupHtml += '<div class="group-badge">' + prof.display_group + '</div>';
      if (prof.group && prof.group.url) {
        groupHtml += ' <a href="' + prof.group.url + '" target="_blank" data-zh="[访问课题组主页]" data-en="[Visit Group Page]"></a>';
      }
      if (prof.group && prof.group.source) {
        groupHtml += '<p style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.5rem;" data-zh="来源：" data-en="Source: ">' + prof.group.source + '</p>';
      }
      groupHtml += '</div>';
    }
    // Peer professors
    var peers = prof.group && prof.group.peer_professor_ids ? prof.group.peer_professor_ids : [];
    if (peers.length > 0) {
      groupHtml += '<div class="section-card">';
      groupHtml += '<h3 class="section-title" data-zh="同组教师" data-en="Group Members"></h3>';
      groupHtml += '<ul>';
      peers.forEach(function (peerId) {
        groupHtml += '<li><a href="' + peerId + '.html">' + peerId + '</a></li>';
      });
      groupHtml += '</ul></div>';
    }
    if (!groupHtml) {
      groupHtml = '<div class="empty-state"><p data-zh="暂无课题组信息" data-en="No group information available"></p></div>';
    }
    document.getElementById('tab-group').innerHTML = groupHtml;

    // Admission tab
    var admissionHtml = '';
    if (prof.admission) {
      var adm = prof.admission;
      admissionHtml += '<div class="section-card">';
      admissionHtml += '<h3 class="section-title" data-zh="招生信息" data-en="Admission"></h3>';
      if (adm.is_recruiting === true) {
        admissionHtml += '<p style="color:var(--success);font-weight:600;">🟢 <span data-zh="正在招生" data-en="Actively Recruiting"></span></p>';
        if (adm.openings) admissionHtml += '<p><strong data-zh="名额：" data-en="Openings: "></strong>' + adm.openings + '</p>';
      } else if (adm.is_recruiting === false) {
        admissionHtml += '<p style="color:var(--danger);">🔴 <span data-zh="暂不招生" data-en="Not Currently Recruiting"></span></p>';
      } else {
        admissionHtml += '<p style="color:var(--text-secondary);">⚪ <span data-zh="招生状态未知" data-en="Recruiting Status Unknown"></span></p>';
      }
      if (adm.requirements) {
        admissionHtml += '<p style="margin-top:1rem;"><strong data-zh="要求：" data-en="Requirements: "></strong></p>';
        admissionHtml += '<p>' + safeStr(adm.requirements) + '</p>';
      }
      if (adm.preferred_background && adm.preferred_background.length > 0) {
        admissionHtml += '<p style="margin-top:0.5rem;"><strong data-zh="偏好背景：" data-en="Preferred Background: "></strong>' + adm.preferred_background.join(', ') + '</p>';
      }
      if (adm.application_deadline) {
        admissionHtml += '<p><strong data-zh="截止日期：" data-en="Deadline: "></strong>' + adm.application_deadline + '</p>';
      }
      if (adm.funding_notes) {
        admissionHtml += '<p><strong data-zh="资助：" data-en="Funding: "></strong>' + adm.funding_notes + '</p>';
      }
      if (adm.source) {
        admissionHtml += '<p style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.5rem;" data-zh="来源：" data-en="Source: ">' + adm.source + '</p>';
      }
      admissionHtml += '</div>';
    } else {
      admissionHtml = '<div class="empty-state"><p data-zh="暂无招生信息" data-en="No admission information available"></p></div>';
    }
    document.getElementById('tab-admission').innerHTML = admissionHtml;

    // Sources (底部来源追溯)
    var sourcesHtml = '';
    if (prof.sources) {
      var src = prof.sources;
      sourcesHtml += '<div class="section-card">';
      sourcesHtml += '<h3 class="section-title" data-zh="信息来源" data-en="Data Sources"></h3>';
      sourcesHtml += '<ul style="list-style:none;font-size:0.9rem;">';
      if (src.listing_page) {
        sourcesHtml += '<li>📋 <strong data-zh="清单页：" data-en="Listing: "></strong><a href="' + src.listing_page + '" target="_blank">' + src.listing_page + '</a></li>';
      }
      if (src.homepage) {
        sourcesHtml += '<li>🏠 <strong data-zh="个人主页：" data-en="Homepage: "></strong><a href="' + src.homepage + '" target="_blank">' + src.homepage + '</a></li>';
      }
      if (src.sub_pages_fetched && src.sub_pages_fetched.length > 0) {
        sourcesHtml += '<li>📄 <strong data-zh="已抓取子页：" data-en="Sub-pages fetched: "></strong>' + src.sub_pages_fetched.join(', ') + '</li>';
      }
      if (src.scholar) {
        sourcesHtml += '<li>📚 <strong>Google Scholar: </strong><a href="' + src.scholar + '" target="_blank">' + src.scholar + '</a></li>';
      }
      if (src.dblp) {
        sourcesHtml += '<li>📋 <strong>DBLP: </strong><a href="' + src.dblp + '" target="_blank">' + src.dblp + '</a></li>';
      }
      if (src.fetched_at) {
        sourcesHtml += '<li>🕐 <strong data-zh="获取时间：" data-en="Fetched: "></strong>' + src.fetched_at + '</li>';
      }
      sourcesHtml += '</ul></div>';
    }

    // Quality notes
    if (prof.quality_notes || (prof.missing_fields && prof.missing_fields.length > 0)) {
      sourcesHtml += '<div class="section-card">';
      sourcesHtml += '<h3 class="section-title" data-zh="数据质量备注" data-en="Data Quality Notes"></h3>';
      if (prof.quality_notes) {
        sourcesHtml += '<p>' + prof.quality_notes + '</p>';
      }
      if (prof.missing_fields && prof.missing_fields.length > 0) {
        sourcesHtml += '<p style="margin-top:0.5rem;"><strong data-zh="缺失字段：" data-en="Missing fields: "></strong>' + prof.missing_fields.join(', ') + '</p>';
      }
      sourcesHtml += '</div>';
    }
    document.getElementById('tab-sources').innerHTML = sourcesHtml;
  }

  function renderDetailPage(prof) {
    renderHero(prof);
    renderTabs(prof);

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var tabId = btn.getAttribute('data-tab');

        document.querySelectorAll('.tab-btn').forEach(function (b) { b.classList.remove('active'); });
        document.querySelectorAll('.tab-content').forEach(function (c) { c.classList.remove('active'); });

        btn.classList.add('active');
        document.getElementById('tab-' + tabId).classList.add('active');
      });
    });

    // Language change re-render
    window.addEventListener('languagechange', function () {
      renderTabs(prof);
    });
  }

  window.TutorHunterCard = {
    renderDetailPage: renderDetailPage
  };
})();
