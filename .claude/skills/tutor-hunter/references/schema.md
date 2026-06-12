# Data Schema Reference

## Professor ID Convention

`{university_short}-{department_short}-{name_pinyin}`

Examples:
- `ustc-sist-zhazhengjun` — 中国科学技术大学 信息科学技术学院 查正军
- `cuhk-cse-zhangwei` — 香港中文大学 CSE 张伟
- `pku-cs-liming` — 北京大学 计算机学院 李明

Rules:
- Use lowercase ASCII only
- Remove spaces and special characters from pinyin
- If pinyin unknown, use numeric suffix

## Field Completeness Tiers

| Tier | Fields | When to mark |
|------|--------|-------------|
| **High** | name, title, university, department, homepage_url | Always extractable from listing+homepage |
| **Medium** | email, research directions, publications, group | Usually extractable with effort |
| **Low** | student destinations, phone, office, admission details | May not be available |

## Region Enum

- `mainland_china` — 中国大陆
- `hong_kong` — 香港
- `macau` — 澳门
- `taiwan` — 台湾
- `singapore` — 新加坡
- `north_america` — 北美
- `europe` — 欧洲
- `other` — 其他

## Data Quality Levels

| Level | Meaning | When to use |
|-------|---------|-------------|
| `high` | Most fields verified from multiple sources | Scholar + DBLP + homepage all consistent |
| `medium` | Core fields extracted, some missing or single-source | Homepage only, or some missing fields |
| `low` | Minimal info, mostly missing | Only listing page data available |

## _sources Object

Every data point should be traceable to its origin. The `_sources` object records:
- Which URLs were fetched
- Which sub-pages were accessed
- When the data was fetched

This enables later verification and re-extraction.
