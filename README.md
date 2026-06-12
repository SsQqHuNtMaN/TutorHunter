# TutorHunter 导师猎人

批量查询和整理目标院校导师信息，辅助研究生申请（套磁）。

## 功能

- 🔍 **批量发现**：输入学院教师清单 URL，自动发现所有教师
- 📄 **深度提取**：逐个访问教师主页 + Google Scholar + DBLP，提取详细信息
- 📊 **多格式输出**：JSON 数据库 + Excel 对比表 + HTML 可视化页面
- 🌐 **GitHub Pages 部署**：一键 push，自动构建和部署

## 使用方法

### 在 Claude Code 中使用

```
/tutor-hunter:hunt <学院清单URL>
/tutor-hunter:hunt <学院清单URL> --limit 5    # 仅提取前5位
/tutor-hunter:hunt <学院清单URL> --resume      # 从上次中断处继续
/tutor-hunter:compare                          # 生成对比视图
/tutor-hunter:export                           # 导出 Excel
```

### 本地构建站点

```bash
pip install -r scripts/requirements.txt
python scripts/build_site.py
```

## 提取的信息

- 基本信息：姓名、职称、院校、学院
- 研究方向（从近两年论文总结）
- 近三年论文（来自 Google Scholar）
- 联系方式：邮箱、电话、主页链接
- 学生信息（从论文一作反推）
- 课题组归属
- 招生要求

## 项目结构

```
TutorHunter/
├── .claude/skills/tutor-hunter/  # Claude Code Skill
├── data/professors/              # 导师 JSON 数据
├── scripts/                      # Python 构建脚本
├── web/                          # 前端源码
├── docs/                         # GitHub Pages 部署目录
└── CLAUDE.md                     # 项目指南
```
