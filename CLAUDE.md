# CLAUDE.md — TutorHunter 项目指南

## 项目简介

TutorHunter（导师猎人）是一个用于批量查询和整理目标院校导师信息的工具，辅助研究生申请（套磁）。

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

## 数据流

```
学院清单 URL → [阶段A: 批量发现] → 教师姓名+主页链接列表
                                    ↓
                [阶段B: 深度提取] → 逐个访问主页 + Scholar/DBLP → JSON
                                    ↓
                [build_site.py]   → docs/ (HTML + Excel)
                                    ↓
                [git push]        → GitHub Pages 自动部署
```

## 信息获取渠道优先级（已确认）

| 信息 | 首选 | 备选 |
|------|------|------|
| 姓名/职称/学院 | 清单页 + 个人主页 | — |
| 研究方向 | **从近两年论文总结** | 主页标注（可能过时） |
| 近三年论文 | **Google Scholar** | DBLP → Semantic Scholar → arXiv |
| 邮箱/电话 | 个人主页 | 论文通讯作者邮箱 |
| 学生信息 | 论文一作反推 | Web 搜索 |
| 学生去向 | Web 搜索（不强求） | — |
| 课题组 | 个人主页"团队成员" | Web 搜索 |
| 招生要求 | 个人主页"招生信息" | — |

## 关键设计决策

1. **所有信息保留来源 URL**（`_sources` 字段），可溯源核查
2. **研究方向不依赖主页标注**，而是从近两年论文由 LLM 归纳
3. **学生信息从论文一作/通讯作者反推**，复现姓名推断为学生
4. **全量分批执行**，支持 `--limit N` 和 `--resume`
5. **前端零依赖原生 JS**，兼容 GitHub Pages 静态部署

## 常用命令

```bash
# 构建站点
python scripts/build_site.py

# 仅生成 Excel
python scripts/generate_excel.py

# 仅生成 HTML
python scripts/generate_html.py
```
