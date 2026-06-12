# CLAUDE.md — TutorHunter 项目指南

## 项目简介

TutorHunter（导师猎人）批量查询和整理目标院校导师信息，辅助研究生申请（套磁）。输入学院教师清单 URL → 自动发现全部教师 → 多渠道深度提取 → 结构化输出。

**当前状态**：USTC 信息科学技术学院 164 位教师已入库，https://ssqqhuntman.github.io/TutorHunter

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
         │  ├─ B2: WebSearch "{英文名} {机构名} publications 2024"（⭐ 主力）
         │  ├─ B3: DBLP API (curl) → name_match_score() 匹配合格者
         │  ├─ B4: OpenReview API → "{英文名} USTC" 格式
         │  ├─ B5: arXiv API → "au:{name} AND all:USTC" 格式
         │  └─ B6: Python 标签生成 → TAG_PATTERNS 从论文标题归纳方向
         │
Phase C ─┼─ 后处理 + 自动部署
         │  ① 去重（标题归一化）+ 写 JSON → 更新 index.json
         │  ② python scripts/build_site.py
         │  ③ git add -A && git commit && git push（自动）
         │  ④ GitHub Pages 自动部署
         │
输出：JSON + HTML + Excel + GitHub Pages
```

## 论文获取渠道（实测状态）

### 效果排名

| 渠道 | 访问方式 | 命中率(164人) | 精度 | 最佳实践 |
|------|----------|-------------|------|----------|
| **WebSearch** | `"{英文名} {机构名} publications 2024"` | ~15% | ⭐高 | 所有教授，首选渠道 |
| **DBLP API** | `curl dblp.org/pid/{pid}.xml` + name_match_score | ~5% | ⚠️中 | 仅唯一英文名可用 |
| **OpenReview API** | `curl api2.openreview.net/notes/search?term={name}+USTC` | ~2% | ✅中 | ML会议论文 |
| **arXiv API** | `curl export.arxiv.org/api/query?search_query=au:{name}+AND+all:USTC` | ~1% | ⚠️低 | 预印本补充 |
| **Google Scholar** | ❌ WebFetch 阻止 | — | — | — |
| **Semantic Scholar** | ❌ API 空返回 | — | — | — |

### 搜索格式规范

**正确格式**（加入机构名减少重名）：
```
WebSearch:  "Xiaojun Chang USTC publications 2024 2025"
DBLP:       搜索 "Xiaojun Chang" → name_match_score() 评分 ≥50 才使用
OpenReview: "Xiaojun Chang USTC"
arXiv:      au: Xiaojun_Chang AND all: USTC
```

**错误格式**（不要用）：
```
❌ 仅中文名搜索 → 信息量不足
❌ 仅英文名不加机构 → 重名泛滥（Li Chen 几十个同名）
❌ DBLP 盲取第一个结果 → 90% 假阳性
```

### DBLP name_match_score() 机制

```python
def name_match_score(candidate_name, target_name):
    """评分 0-100，阈值 50"""
    # 100: 完全匹配 (e.g., "Zhengjun Zha" = "Zhengjun Zha")
    # 80+: 姓和名都在 (e.g., "Xiaojun Chang" ≈ "X. Chang")
    # 50-80: 部分匹配 (需人工判断)
    # <50: 不匹配，丢弃
```

**精度 vs 覆盖率权衡**：
- 阈值=0（盲取第一个）：91篇/10人，但大部分是别人论文
- 阈值=50（当前）：1篇/1人，精度高但漏检严重
- **结论：DBLP 仅对唯一英文名有效（如 Zhengjun Zha, Houqiang Li）**

### 各渠道搜索格式速查

| 渠道 | 格式 | 示例 |
|------|------|------|
| WebSearch | `"{English Name} {Institution} publications {year}"` | `"Xiaojun Chang USTC publications 2024 2025"` |
| DBLP | 先搜作者 → name_match_score ≥50 → 取论文XML | 仅查正军、李厚强等唯一名称 |
| OpenReview | `"{English Name} USTC"` | `"Xiaojun Chang USTC"` |
| arXiv | `au:{Name_Parts} AND all:USTC` | `au:Xiaojun_Chang AND all:USTC` |

## 中文姓名歧义问题（核心挑战）

### 问题本质
- 中国有 14 亿人，但常用姓氏仅 ~100 个，常用名字仅 ~500 个
- "Li Chen" 在 DBLP 有 **数十个**同名作者
- "Yang Cao" (曹洋) 在 USTC 就有 **2 个**同名教师
- "Weidong Chen" (陈卫东) 与 **天津大学**同名教授混淆

### 缓解策略
1. **加机构名**：`{name} {institution}` 格式（本 session 验证有效）
2. **加领域词**：`{name} {institution} {research_keyword}`
3. **DBLP name_match_score()**：自动过滤不匹配的作者
4. **WebSearch 语义理解**：Claude 能根据上下文判断是不是对的教授
5. **多渠道交叉验证**：Scholar + DBLP + 主页三者一致的才标记 high

## USTC 主页系统特征

- 4+ 种 CMS 模板：jszwmb02, jszwmb08, jszw40, 自定义模板
- 邮箱全站 JS 加密（`_tsites_encrypt_field`），需从 WebSearch 交叉获取
- 不同模板的 HTML 结构完全不同，正则提取不可靠
- **结论：WebSearch > 正则HTML解析**
- 论文子页面 URL 模式：`/{username}/zh_CN/lwcg/{id}/list/index.htm`

## 信息获取渠道优先级

| 信息 | 首选 | 备选 | 备注 |
|------|------|------|------|
| 姓名/职称/学院 | curl 清单页 + 主页 | WebSearch | 清单页正则稳定 |
| 邮箱 | WebSearch ⭐ | 主页 JS 解密 | USTC全站加密，WebSearch 80%命中 |
| 研究方向 | **论文标题自动标签** | 主页标注（可能过时） | TAG_PATTERNS 25个方向 |
| 近三年论文 | WebSearch "{name} {inst} publications" | DBLP(唯一名) + OpenReview + arXiv | API ~6%覆盖，WebSearch ~15% |
| 学生信息 | 论文一作反推 | — | 复现姓名 = 推断学生 |
| 课题组 | WebSearch | 主页"团队成员" | |
| 招生要求 | 主页子页面 | WebSearch | |

## 当前论文覆盖统计（164人）

| 质量等级 | 人数 | 代表教授 |
|----------|------|----------|
| 🟢 high（Scholar确认+论文详情） | 4 | 常晓军(20000+引用)、查正军(692篇DBLP)、陈力(优青)、李厚强(IEEE Fellow) |
| 🟡 medium（WebSearch有方向/计数） | 12 | 艾杨(60篇)、凌震华(36篇2024)、曹洋(H=13)、王永、陈双武等 |
| 🔴 low / 待补充 | 148 | 大部分通过curl批量获取基础信息，论文待WebSearch补充 |

## 关键设计决策

1. **所有信息保留来源 URL**（`_sources` 字段），可溯源核查
2. **研究方向不依赖主页标注**，从论文标题自动生成标签（25 个 TAG_PATTERNS）
3. **论文按年份排序**，前端分年显示带年份分隔线
4. **每篇论文标注来源**（dblp / openreview / arxiv / web_search）
5. **全量分批执行**，支持 `--limit N` 和 `--resume`
6. **前端零依赖原生 JS**，兼容 GitHub Pages 静态部署
7. **每次 hunt 后自动 commit + push**，GitHub Actions 自动部署
8. **搜索格式统一为 `{英文名} {机构名}`**，减少中文姓名歧义

## 数据 Schema 关键字段

```json
{
  "id": "ustc-sist-{username}",
  "name": {"zh": "中文名", "en": "English Name"},
  "_quality": {"overall": "high|medium|low", "missing_fields": [...], "notes": "..."},
  "_sources": {"homepage": "...", "scholar": "...", "dblp": "...", "web_search_done": true, "fetched_at": "..."},
  "publications": {
    "source": "dblp+openreview+web_search",
    "source_note": "DBLP:3 OR:2 arXiv:1 WebSearch:5",
    "recent": [{title, authors[{name, role, likely_student}], venue, year, type, source}]
  },
  "auto_tags_from_papers": ["Computer Vision", "Deep Learning"],
  "group": {"peer_professor_ids": ["ustc-sist-xxx"]}
}
```

## 常用命令

```bash
# --- Claude Code 中使用 ---
/tutor-hunter:hunt <学院清单URL> --limit N    # 批量提取

# --- 论文搜集 ---
python scripts/collect_papers.py               # DBLP+OpenReview+arXiv 并发搜集
# 然后在 Claude Code 中用 WebSearch 补充:
#   "{英文名} {机构名} publications 2024 2025"

# --- 构建部署 ---
python scripts/build_site.py                   # 重建整个站点
git add -A && git commit -m "hunt: ..." && git push  # 自动部署

# --- 数据维护 ---
python scripts/_enrich_tags.py                 # 从论文标题生成研究方向标签
```

## 已知限制

1. **中文姓名歧义**：DBLP/OpenReview/arXiv 对常见中文名唯一匹配率仅 ~6%
2. **Google Scholar 封锁**：WebFetch 和 Python urllib 均无法访问，只能通过 WebSearch 间接获取
3. **USTC 模板多样**：不同教师使用不同CMS模板，正则解析不可靠
4. **非CS领域覆盖差**：DBLP 不收录控制工程、振动控制等领域；arXiv 侧重 CS/物理/数学
5. **学生去向**：中国教师主页极少公开，仅可通过论文一作推断学生身份
6. **API 精度-覆盖率矛盾**：name_match_score 阈值越低假阳性越多，越高漏检越多
