# Extraction Rules & Priority

## Channel Priority by Field

### 1. Name & Title
1. **Homepage** (highest authority) — page title, hero section
2. **Listing page** — name as listed in department directory

### 2. Contact (email, phone)
1. **Homepage** — sidebar or "联系方式" section
2. **Paper author metadata** — corresponding author email in recent papers
3. **Scholar profile** — sometimes includes verified email
4. **Department directory** — if available as a separate page

Note: USTC encrypts email via `_tsites_encrypt_field`. If JS-decoded value isn't available:
- Try to find the email on Google Scholar profile
- Try to find it on paper author pages
- Mark as null with `email_note: "主页 JS 加密"`

### 3. Research Directions
**PRIMARY**: Inferred from recent 2 years of paper titles/topics
**SECONDARY**: Homepage "研究方向" section (may be outdated)
**TERTIARY**: Scholar profile keywords

When inferring from papers:
- Look at paper titles and venues for topic patterns
- Group similar topics
- Produce both Chinese and English direction labels
- Mark `inferred_from_papers_note` with the date range used

### 4. Publications
**PRIMARY**: Google Scholar (most comprehensive, includes citations)
**SECONDARY**: DBLP (CS only, very structured)
**TERTIARY**: Homepage publications list (often incomplete)
**QUATERNARY**: Semantic Scholar / arXiv

For each paper, ALWAYS record authors IN ORDER. This is critical for student inference.

### 5. Students (Inferred from Papers)
1. Collect ALL first authors from ALL recent papers
2. Remove the professor's own name from the list
3. Group by recurring names (same person appearing as first author on multiple papers)
4. Each recurring first author = one inferred student
5. Record: name, paper count, which papers they first-authored

### 6. Students (Destinations)
1. Check if the professor's homepage has an "Alumni" or "学生" section
2. Search: `"{name} {university} 学生 毕业去向"`
3. Search: `"{name} alumni placement"`
4. **DO NOT spend more than 2 searches on this.** Mark as `[]` if not found.

### 7. Group/Lab
1. Check homepage "团队成员" tab/section
2. Look for lab/group name patterns: "XXX实验室", "XXX课题组", "XXX Lab", "XXX Group"
3. If not on homepage: search `"{name} {university} 课题组"`
4. If found: check if other professors in the same department share the same group name → cross-link

### 8. Admission
1. Check for "招生信息" sub-page or tab
2. Look for recruitment-related content on homepage
3. Check lab/group page for recruitment info
4. If nothing found: mark `is_recruiting: null`, add to `missing_fields`

## Handling Common Issues

### JS-Encrypted Email (USTC pattern)
The USTC `_tsites_encrypt_field` stores encrypted email. The `_tsitesencrypt.js` script decrypts it client-side. If you can't decode it:
- Option A: Find the email on Google Scholar (scholar often displays verified email)
- Option B: Look at recent paper metadata for corresponding author email
- Option C: Mark email as null and note "encrypted"

### Incomplete Publication Lists
Many Chinese professor homepages have outdated or incomplete publication lists.
**Always prefer Scholar/DBLP over homepage lists.**

### Determining "Recent 3 Years"
Current year minus 3. E.g., in 2026: papers from 2024, 2025, 2026.

### Chinese Name Disambiguation
When searching Scholar: always include the university name to disambiguate common Chinese names.
If still ambiguous: check the research topics match what's on the homepage.
