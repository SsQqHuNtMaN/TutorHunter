# University Page Structure Patterns

This document records the HTML structure patterns for different university faculty systems.

## USTC (中国科学技术大学) — `faculty.ustc.edu.cn`

### Listing Page
- **URL Pattern**: `https://faculty.ustc.edu.cn/xyjslb.jsp?urltype=tsites.CollegeTeacherList&wbtreeid={dept_id}&st=0&id={dept_id}&lang=zh_CN`
- **English version**: `https://faculty-en.ustc.edu.cn/` (same pattern)
- **Pagination**: `PAGENUM={1..N}` URL parameter; `totalpage=N` in pagination HTML
- **Teacher extraction**:
  - Container: `div.tc_list > ul > li`
  - Name: `span.tc_name`
  - Department: `i.yx_name`
  - Profile link: `a[href]` (href like `http://faculty.ustc.edu.cn/{username}/zh_CN/index.htm`)
  - Avatar: `img[src]` inside `div.tc_img`

### Professor Homepage Template: `jszwmb08`
- **URL Pattern**: `http://faculty.ustc.edu.cn/{username}/zh_CN/index.htm`
- **English version**: `http://faculty.ustc.edu.cn/{username}/en/index.htm`
- **Login page**: `https://manage.faculty.ustc.edu.cn/system/caslogin.jsp`

**Structure:**
- Name: `div.t_name` (text content)
- Photo: `div.t_photo img`
- Info sidebar (left column `div.t_content`):
  - Title: `<li>` items within `div#contentscroll2 ul` (e.g., "教授", "博士生导师")
  - Email: `<span _tsites_encrypt_field="..." id="_tsites_encryp_tsteacher_tsemail">` (ENCRYPTED)
  - Phone: `<li>` containing "办公电话："
  - Degree: `<li>` containing "学位："
  - Disciplines: `<li>` containing "学科："
- Main content (right column):
  - Tab navigation: `ul.TabbedPanelsTabGroup > li.TabbedPanelsTab`
  - Tab panels: `div.TabbedPanelsContentGroup > div.TabbedPanelsContent`
  - Tabs typically include: 个人简介, 研究方向, 社会兼职, 教育经历, 工作经历, 团队成员, 其他联系方式
- Navigation menu (top):
  - `ul#topnav > li > a[href]`
  - Links to sub-pages: 首页, 科学研究, 教学信息, 获奖信息, 招生信息

**Sub-page URL patterns:**
- 科学研究 (Research/Publications): `/{username}/zh_CN/zdylm/{id}/list/index.htm`
- 招生信息 (Admission): `/{username}/zh_CN/zdylm/{id}/list/index.htm`
- 教学信息 (Teaching): `/{username}/zh_CN/zdylm/{id}/list/index.htm`
- 获奖信息 (Awards): `/{username}/zh_CN/zdylm/{id}/list/index.htm`

### Email Decryption (USTC)
The email is stored encrypted in a `<span>` with attribute `_tsites_encrypt_field`. The decryption script is at `/system/resource/tsites/tsitesencrypt.js`. The email is Base64-encoded and XOR'd. If you can't decode it:
1. Try fetching the English version of the page (sometimes has unencrypted email)
2. Check Google Scholar profile for verified email
3. Check recent paper author affiliations

---

## Template for Adding New Universities

When you encounter a new university's faculty system, document:

```markdown
### University Name — Domain

#### Listing Page
- URL Pattern:
- Pagination mechanism:
- Teacher extraction selectors:
  - Name:
  - Department:
  - Profile link:
  - Other:

#### Professor Homepage Template
- URL Pattern:
- Name:
- Title:
- Email:
- Research directions:
- Publications:
- Group/Lab:
- Navigation to sub-pages:

#### Notes
- Any encryption or dynamic loading:
- Language toggle:
- Special considerations:
```
