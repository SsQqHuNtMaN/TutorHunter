# CLAUDE.md — TutorHunter 项目指南

## 项目简介

TutorHunter（导师猎人）批量查询和整理目标院校导师信息，辅助研究生申请（套磁）。输入学院教师清单 URL → 自动发现所有教师 → 深度提取 → 结构化输出。

## 核心原则

> **当需求有不清楚的地方时，先停下来询问用户确认，不要自行假设。**

## 项目架构

```
data/professors/     ← 单一数据源：所有导师 JSON
scripts/             ← Python 构建脚本：JSON → HTML + Excel
web/                 ← 前端源码：原生 JS，零依赖
docs/                ← GitHub Pages 部署目录（构建产物）
.claude/skills/      ← Claude Code Skill 定义
```

## 实际工作流（经验证）

```
用户输入学院清单 URL
         │
Phase A ─┼─ 批量发现（curl + Python regex）
         │  ① curl 获取第1页 → 解析 totalpage=N
         │  ② 遍历 PAGENUM=1..N → 提取 {name, department, profile_url}
         │  ③ USTC selector: span.tc_name + a[href] + i.yx_name
         │  输出：完整教师清单
         │
Phase B ─┼─ 信息提取（分层策略）
         │  ┌─ B1: curl 批量主页抓取 → 职称关键词、电话
         │  ├─ B2: WebSearch 深度搜索（⭐ 主力）→ 邮箱/方向/荣誉/课题组
         │  ├─ B3: DBLP API (curl) → CS领域论文（需要唯一名称）
         │  ├─ B4: OpenReview API (curl) → ML会议论文
         │  └─ B5: Python 标签生成 → 从论文标题自动归纳研究方向
         │
Phase C ─┼─ 后处理 + 自动部署
         │  ① 写 JSON → 更新 index.json
         │  ② python scripts/build_site.py
         │  ③ git add -A && git commit && git push（自动）
         │  ④ GitHub Pages 自动部署
         │
输出：JSON + HTML + Excel + GitHub Pages
```

## 论文获取渠道（实测状态）

| 渠道 | 访问方式 | 效果 | 适用场景 |
|------|----------|------|----------|
| **WebSearch** | Claude 内置 | ⭐最佳 | 所有领域，知名度越高越准 |
| **DBLP API** | `curl https://dblp.org/pid/{pid}.xml` | ✅ 很好 | CS/EE领域，需唯一名称 |
| **OpenReview API** | `curl https://api2.openreview.net/notes/search?term=...` | ✅ 可用 | ML会议 (NeurIPS/ICML/ICLR) |
| **arXiv API** | `curl http://export.arxiv.org/api/query?search_query=au:{name}` | ✅ 可用 | 预印本 |
| **Google Scholar** | ❌ WebFetch 阻止 | 不可用 | — |
| **Semantic Scholar** | ❌ API 空返回 | 不可用 | — |
| **Google Scholar MCP** | 需 `pip install google-scholar-mcp-server` | ⚠️ 需权限 | 可直接搜索Scholar |
| **scholarly (Python)** | 需 `pip install scholarly` | ⚠️ 需权限 | Python Scholar 抓取 |

### DBLP 使用要点
- 作者搜索 API: `https://dblp.org/search/author/api?q={name}&format=json`
- 论文 XML: `https://dblp.org/pid/{pid}.xml`
- curl 必须用 `capture_output=True` + `.decode('utf-8', errors='replace')` 避免编码问题
- 常见中文名重名严重（Li Chen 有几十个），需要用单位筛选
- 非CS领域（控制、振动）不被DBLP收录

### 多渠道论文搜集（collect_papers.py）

```bash
python scripts/collect_papers.py  # 5线程并发，DBLP+OpenReview+arXiv
```

**去重策略**：按标题归一化（小写+去标点+前60字符）去重。

**执行流程**：
1. DBLP: 搜索作者 → 取第一个匹配 → 获取论文XML → 筛选 year>=2024
2. OpenReview: 搜索作者名 → 获取notes → 筛选 year>=2024
3. arXiv: 搜索作者名 → 解析XML → 筛选 year>=2024
4. 合并去重 → 生成研究方向标签 → 写入JSON

**注意**：DBLP 名称歧义严重（Li Chen 几十个），只取第一个匹配；OpenReview 仅覆盖 ML 会议；arXiv 仅预印本。

### USTC 主页系统特征
- 4+ 种 CMS 模板：jszwmb02, jszwmb08, jszw40, 自定义模板
- 邮箱全站 JS 加密（`_tsites_encrypt_field`），需从 WebSearch 交叉获取
- 不同模板的 HTML 结构完全不同，正则提取不可靠
- **结论：WebSearch > 正则HTML解析**

## 信息获取渠道优先级

| 信息 | 首选 | 备选 | 备注 |
|------|------|------|------|
| 姓名/职称/学院 | curl 清单页 + 主页 | WebSearch | 清单页正则稳定 |
| 邮箱 | WebSearch ⭐ | 主页 JS 解密 | USTC全站加密 |
| 研究方向 | **论文标题自动标签** | 主页标注（可能过时） | Python 关键词匹配 |
| 近三年论文 | DBLP (CS) + OpenReview (ML) | WebSearch | 唯一名称可用DBLP |
| 学生信息 | 论文一作反推 | — | 复现姓名 = 推断学生 |
| 课题组 | WebSearch | 主页"团队成员" | |
| 招生要求 | 主页子页面 | WebSearch | |

## 关键设计决策

1. **所有信息保留来源 URL**（`_sources` 字段），可溯源核查
2. **研究方向不依赖主页标注**，从论文标题自动生成标签（TAG_PATTERNS）
3. **论文按年份排序**，前端分年显示带年份分隔线
4. **每篇论文标注来源**（DBLP / OpenReview / WebSearch）
5. **全量分批执行**，支持 `--limit N` 和 `--resume`
6. **前端零依赖原生 JS**，兼容 GitHub Pages 静态部署
7. **每次 hunt 后自动 commit + push**，GitHub Actions 自动部署

## 数据 Schema 关键字段

```json
{
  "id": "ustc-sist-{username}",
  "_quality": {"overall": "high|medium|low", "missing_fields": [...], "notes": "..."},
  "_sources": {"homepage": "...", "scholar": "...", "dblp": "...", "fetched_at": "..."},
  "publications": {
    "source": "dblp | openreview | web_search",
    "source_note": "...",
    "recent": [{title, authors[{name, role, likely_student}], venue, year, type, source}]
  },
  "auto_tags_from_papers": ["tag1", "tag2"]
}
```

## 常用命令

```bash
# 在 Claude Code 中使用
/tutor-hunter:hunt <学院清单URL> --limit N    # 批量提取
/tutor-hunter:compare                          # 生成对比视图
/tutor-hunter:export                           # 导出 Excel

# 本地命令行
python scripts/build_site.py                   # 重建整个站点
python scripts/_fetch_papers.py                # DBLP+OpenReview 论文抓取
python scripts/_enrich_tags.py                 # 从论文标题生成研究方向标签
python scripts/_batch_hunt.py                  # 批量curl提取主页信息

# 部署
git add -A && git commit -m "hunt: ..." && git push  # 自动触发 Pages 部署
```

## 已知限制

1. **DBLP 名称歧义**：常见中文名（Li Chen, Yang Cao）无法唯一匹配
2. **Google Scholar 封锁**：WebFetch 和 Python urllib 均无法访问
3. **USTC 模板多样**：不同教师使用不同CMS模板，正则解析不可靠
4. **非CS领域覆盖差**：DBLP不收录控制工程、振动控制等领域
5. **学生去向**：中国教师主页极少公开，仅可通过论文一作推断学生身份
