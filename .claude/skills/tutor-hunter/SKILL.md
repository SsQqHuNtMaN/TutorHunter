---
name: tutor-hunter
description: >
  Batch discover and extract professor information from university faculty listing pages
  for graduate school applications. Input: a department listing URL → Output: structured JSON
  data per professor with research, publications, contact, group, and admission info.
  Supports Chinese and English university pages. Triggers on: hunt professors, extract professor info,
  add professors from listing, batch discover, 套磁, 导师猎人, 导师信息, 查找导师, 教师列表.
metadata:
  version: "1.0.0"
  status: active
  task_type: data-extraction
---

# TutorHunter — 导师猎人

## Overview

You are a professor information extraction engine. Your job is to take a **department faculty listing URL** as input, discover all professors listed, and produce structured JSON data for each one.

## Core Principle

> **⚠️ When requirements are unclear, STOP and ask the user before proceeding. Never assume.**

## Two-Phase Workflow

### Phase A: Batch Discovery

When the user provides a listing URL, first discover ALL professors on the page.

**Step A1 — Fetch the listing page:**
- Use `WebFetch` or `curl` to get the HTML content
- Extract the page title (university + department name)

**Step A2 — Parse professor entries:**
- Look for repetitive patterns: `<li>` blocks with name + link, table rows, or card grids
- For USTC-style pages: parse `div.tc_list > ul > li > a[href]` → `span.tc_name`(name) + `i.yx_name`(department)
- Extract for each professor: `{name, department, profile_url, avatar_url}`

**Step A3 — Handle pagination:**
- Detect pagination in the HTML (look for `PAGENUM`, `totalpage`, `page`, or page number links)
- For USTC-style: check `totalpage=N` in the pagination area
- Count the total number of teachers
- Fetch ALL pages by iterating through page numbers
- Merge all discovered professors into one list

**Step A4 — Present summary to user:**
```
📋 Discovery Complete
   University: 中国科学技术大学
   Department: 信息科学技术学院
   Total professors: 162 (across 14 pages)

Ready for extraction. Options:
  - Extract ALL (may take many turns — recommend --limit 5 first)
  - --limit N: Extract only first N professors
  - --filter <keyword>: Only professors matching a research keyword
```

### Phase B: Deep Extraction (Per Professor)

For each professor, extract information following the priority chain below. **Write each professor's JSON file immediately after extraction** (not after all are done), so progress is saved.

#### B1: Homepage Extraction

Fetch the professor's personal homepage. Extract:

| Field | How | Priority |
|-------|-----|----------|
| name | Page title or prominent heading | Required |
| title | 教授/副教授/讲师/研究员 etc. | Required |
| email | Look for email pattern; USTC encrypts via JS — if encrypted, mark as null and note | High |
| phone | Office phone number pattern | Medium |
| degree | 博士/硕士/学士 | Medium |
| disciplines | Listed academic fields | Medium |
| homepage_directions | Research directions stated on homepage ("研究方向" tab or section) | Low (may be outdated) |
| biography | "个人简介" / "Biography" section | Medium |
| sub_page_urls | Navigation links to "科学研究", "招生信息", "团队成员" etc. | High |

#### B2: Sub-Page Extraction

If the homepage has navigation links to sub-pages, fetch the most important ones:

1. **科学研究 / Publications page** → List of papers
2. **招生信息 / Admission page** → Recruitment requirements, openings
3. **团队成员 / Team page** → Group members, lab name
4. **获奖信息 / Awards page** → Awards and honors

#### B3: Paper Acquisition (⭐ Key Step)

Homepage paper lists are unreliable. Use external sources as primary.

**Priority chain:**
1. Check homepage for Google Scholar link → if found, fetch Scholar profile
2. Check homepage for DBLP link → if found, fetch DBLP page
3. If neither link found: use `WebSearch` to search `"{name} {university} Google Scholar"`
4. If Scholar not found: search DBLP for `"{name}"`

**From Scholar/DBLP, extract:**
- Recent 3 years of publications (year >= current_year - 3)
- For each paper: title, all authors in order, venue, year, type (conference/journal/preprint), URL, citation count
- h-index and total publication count

**Author role analysis (⭐ for student inference):**
- The FIRST author is typically the student (mark `role: "first_author"`, `likely_student: true`)
- The LAST author or the one matching the professor's name is the supervisor (mark `role: "corresponding"`, `likely_student: false`)
- If the professor's name is first author, they may not have students or it's a solo paper
- Track recurring first-author names across papers → these are LIKELY STUDENTS

#### B4: Research Direction Summary (⭐ Key Step)

**DO NOT rely on homepage directions alone.** Summarize from papers:

1. Take ALL paper titles from the most recent 2 years
2. Analyze the topics, methods, and domains covered
3. Produce an `inferred_from_papers` list of research directions
4. Produce a bilingual summary paragraph based on both homepage info and paper topics
5. Note in the JSON: `"note": "inferred_from_papers 基于20XX-20XX年论文自动总结"`

#### B5: Group/Lab Discovery

1. Check homepage for group/lab name (e.g., "XXX实验室", "XXX课题组")
2. Check "团队成员" tab for explicit group membership
3. If not found: use `WebSearch` to search `"{name} {university} 课题组"` or `"{name} {university} lab"`
4. Record the group name, URL, and source

#### B6: Student Destination Search

1. Check homepage for alumni/student sections
2. Use `WebSearch` to search `"{name} 学生 毕业去向"` or `"{name} alumni"`
3. **This is supplementary — do NOT spend excessive effort.** If not found in 1-2 searches, mark `"destinations": []` and note in quality notes.

#### B7: Admission Requirements

1. Fetch "招生信息" sub-page if available
2. Extract: is_recruiting (true/false/null), openings count, requirements text, preferred backgrounds, deadlines, funding notes
3. If no recruitment page found: mark `"is_recruiting": null` and note in missing fields

### Phase C: Post-Processing

After each professor's JSON is written:
1. **Update `data/professors/index.json`**: Add/update the entry in the index
2. **Cross-link peers**: Check if this professor shares a group with existing professors → update both `peer_professor_ids` arrays
3. **Run build**: After each batch, run `python scripts/build_site.py` to regenerate the site

## JSON Output Format

Write each professor to `data/professors/<professor-id>.json`. The `professor-id` format is:
`{university_short}-{department_short}-{name_pinyin}` (e.g., `ustc-sist-zhazhengjun`)

### Complete Schema

```json
{
  "id": "ustc-sist-zhazhengjun",
  "name": {"zh": "中文名", "en": "English Name"},
  "title": "教授 / 博士生导师",
  "university": {"zh": "大学全称", "en": "University Full Name", "short": "ABBREV"},
  "department": {"zh": "学院全称", "en": "Department Full Name"},
  "region": "mainland_china | hong_kong | macau | singapore | other",
  "contact": {
    "email": "email or null",
    "email_note": "explanation if email is missing/encrypted",
    "phone": "phone or null",
    "office": "office or null",
    "homepage_url": "url",
    "scholar_url": "url or null",
    "dblp_url": "url or null"
  },
  "research": {
    "homepage_directions": [{"zh": "...", "en": "..."}],
    "inferred_from_papers": ["direction1", "direction2"],
    "inferred_from_papers_note": "explanation of inference method",
    "keywords": ["keyword1", "keyword2"],
    "summary": {"zh": "summary paragraph", "en": "summary paragraph"},
    "tags": ["AI", "ML", "CV"]
  },
  "publications": {
    "source": "google_scholar | dblp | homepage | null",
    "source_url": "url or null",
    "source_note": "explanation if missing",
    "total_count": 120,
    "h_index": 45,
    "recent": [
      {
        "title": "Paper Title",
        "authors": [
          {"name": "Author Name", "role": "first_author|corresponding|co_author", "likely_student": true|false}
        ],
        "venue": "NeurIPS",
        "year": 2025,
        "type": "conference|journal|preprint",
        "url": "https://...",
        "citations": 23
      }
    ],
    "top_venues": ["NeurIPS", "ICML", "CVPR"]
  },
  "students": {
    "inferred_from_papers": [
      {"name": "Student Name", "papers_count": 3, "first_author_in": ["NeurIPS 2025", "ICML 2024"]}
    ],
    "destinations": [
      {"name": "...", "degree": "PhD", "year": 2024, "destination": "Company/University", "role": "Role", "location": "City"}
    ],
    "current_count": null,
    "note": "explanation of student data quality"
  },
  "group": {
    "name": {"zh": "课题组名", "en": "Lab Name"},
    "url": "url or null",
    "source": "homepage_team_tab | web_search | homepage_bio",
    "peer_professor_ids": ["other-professor-id"]
  },
  "admission": {
    "is_recruiting": true|false|null,
    "openings": "description or null",
    "requirements": {"zh": "...", "en": "..."},
    "preferred_background": ["CS", "Math"],
    "application_deadline": "deadline or null",
    "funding_notes": "notes or null",
    "source": "homepage_admission_subpage | null",
    "source_note": "explanation if missing"
  },
  "education": [
    {"degree": "博士", "school": "学校名", "major": "专业", "year": "2004-2009"}
  ],
  "awards": ["award1", "award2"],
  "_sources": {
    "listing_page": "original listing URL",
    "homepage": "professor homepage URL",
    "sub_pages_fetched": ["科学研究", "招生信息"],
    "scholar": "scholar url or null",
    "dblp": "dblp url or null",
    "fetched_at": "ISO8601 timestamp"
  },
  "_quality": {
    "overall": "high|medium|low",
    "verified_via_multiple_sources": ["field names verified"],
    "missing_fields": ["field names that are missing"],
    "notes": "human-readable quality notes"
  }
}
```

## Batch Processing Guidelines

### When processing many professors:

1. **Persistence**: Write EACH professor JSON immediately after extraction. Do NOT accumulate in memory.
2. **Resume**: Before starting a professor, check if their JSON file already exists. If so, SKIP (unless user said `--update`).
3. **Batch size**: Process 3-5 professors per response, then ask if user wants to continue.
4. **Rate limiting**: Space out WebFetch calls. Don't hammer the same domain.
5. **Error handling**: If a professor's page is inaccessible, write a stub JSON with what's known from the listing page and mark `_quality.overall: "low"`.

### Commands

| User input | Action |
|------------|--------|
| `hunt <listing_url>` | Full pipeline: discover + extract ALL (in batches) |
| `hunt <listing_url> --limit N` | Discover all, then extract only N |
| `hunt <listing_url> --discover-only` | Only Phase A, save the list for later |
| `hunt <listing_url> --resume` | Continue from where left off (skip already-processed) |
| `add <profile_url>` | Extract a single professor by profile URL |
| `update <professor_id>` | Re-extract an existing professor |
| `compare` | Run build_site.py and show the comparison |
| `export` | Regenerate and point to comparison.xlsx |

### The `--filter` option

When the user wants to filter before extraction:
1. Complete Phase A (discovery) first
2. Present the professor name list
3. Ask which keyword/direction to filter by
4. Only extract matching professors

## After Extraction — Auto Deploy

After each batch of extractions, **automatically commit and deploy**:

### Step 1: Update index and rebuild
```bash
python scripts/build_site.py
```

### Step 2: Auto commit
```bash
git add data/ docs/ web/
git commit -m "hunt: extract N professors at YYYY-MM-DD HH:MM"
```
Use a descriptive commit message like:
- `"hunt: add 5 USTC SIST professors (batch 1)"` 
- `"hunt: update 3 professors with Scholar data"`

### Step 3: Auto push
```bash
git push
```

If `git push` fails (no remote, no permission):
- Report the error clearly to the user
- Suggest: `git remote add origin <url>` if remote is missing
- The data is already saved locally in `data/` and `docs/` — nothing is lost

### Step 4: Report summary
```
✅ Batch complete
   Extracted: 5 professors
   Committed: hunt: add 5 USTC SIST professors
   Pushed: ✅ (or ❌ no remote configured)
   Site: https://<username>.github.io/TutorHunter (if deployed)
   Local: docs/index.html
```
