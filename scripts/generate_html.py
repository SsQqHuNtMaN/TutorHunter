#!/usr/bin/env python3
"""
generate_html.py — 从 data/professors/*.json 生成静态 HTML 页面
使用 Jinja2 模板渲染，输出到 docs/
"""

import json
import os
import sys
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "professors")
WEB_DIR = os.path.join(PROJECT_ROOT, "web")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "docs")


def load_professors():
    """Load all professor JSON files"""
    professors = []
    index_path = os.path.join(DATA_DIR, "index.json")
    if not os.path.exists(index_path):
        print(f"Warning: {index_path} not found")
        return professors

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    for entry in index:
        prof_path = os.path.join(DATA_DIR, f"{entry['id']}.json")
        if os.path.exists(prof_path):
            with open(prof_path, "r", encoding="utf-8") as f:
                professors.append(json.load(f))
    return professors


def safe_str(value, lang="zh"):
    """Safely extract string from possibly-bilingual field"""
    if value is None:
        return ""
    if isinstance(value, dict):
        result = value.get(lang) or value.get("en") or ""
        return result if result else ""
    if isinstance(value, list):
        if len(value) > 0 and isinstance(value[0], dict):
            return ", ".join(safe_str(v, lang) for v in value)
        return ", ".join(str(v) for v in value if v is not None)
    return str(value) if value else ""


def prepare_professor_for_template(prof):
    """Prepare a professor dict for Jinja2 template rendering"""
    r = prof.get("research", {})
    c = prof.get("contact", {})
    g = prof.get("group", {})
    a = prof.get("admission", {})
    p = prof.get("publications", {})
    s = prof.get("students", {})
    q = prof.get("_quality", {})

    # Sort publications by year descending
    recent_pubs = sorted(
        p.get("recent", []),
        key=lambda x: x.get("year", 0),
        reverse=True
    )

    # Get directions as display strings
    homepage_dirs = [safe_str(d) for d in r.get("homepage_directions", [])]

    return {
        **prof,
        "display_name": safe_str(prof.get("name", {})),
        "display_name_en": safe_str(prof.get("name", {}), "en"),
        "display_university": safe_str(prof.get("university", {})),
        "display_department": safe_str(prof.get("department", {})),
        "display_group": safe_str(g.get("name", {})),
        "display_admission": safe_str(a.get("requirements", {})),
        "homepage_dirs": homepage_dirs,
        "inferred_dirs": r.get("inferred_from_papers", []),
        "keywords": r.get("keywords", []),
        "tags": r.get("tags", []),
        "recent_pubs": recent_pubs,
        "inferred_students": s.get("inferred_from_papers", []),
        "destinations": s.get("destinations", []),
        "quality_overall": q.get("overall", "unknown"),
        "quality_notes": q.get("notes", ""),
        "missing_fields": q.get("missing_fields", []),
        "sources": prof.get("_sources", {}),
        "has_email": bool(c.get("email")),
        "has_phone": bool(c.get("phone")),
        "has_scholar": bool(c.get("scholar_url")),
        "has_dblp": bool(c.get("dblp_url")),
        "is_recruiting": a.get("is_recruiting"),
    }


def generate_professor_pages(env, professors):
    """Generate individual professor detail pages"""
    template = env.get_template("professor-template.html")
    output_dir = os.path.join(OUTPUT_DIR, "professors")
    os.makedirs(output_dir, exist_ok=True)

    for prof in professors:
        data = prepare_professor_for_template(prof)
        html = template.render(
            professor=data,
            generated_at=datetime.now().isoformat()
        )
        output_path = os.path.join(output_dir, f"{prof['id']}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    print(f"Generated {len(professors)} professor detail pages")


def generate_index_page(env, professors):
    """Generate the main index page with comparison table"""
    template = env.get_template("index.html")
    data = [prepare_professor_for_template(p) for p in professors]

    # Collect unique filter values
    universities = sorted(set(
        safe_str(p.get("university", {})) for p in professors
    ))
    regions = sorted(set(
        p.get("region", "") for p in professors
    ))
    all_tags = sorted(set(
        tag for p in professors
        for tag in (p.get("research", {}).get("tags", []))
    ))

    html = template.render(
        professors=data,
        universities=universities,
        regions=regions,
        all_tags=all_tags,
        total_count=len(professors),
        generated_at=datetime.now().isoformat()
    )
    output_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated index page with {len(professors)} professors")


def generate_html(professors):
    """Main function: generate all HTML pages"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(WEB_DIR),
        autoescape=select_autoescape(["html", "htm"])
    )

    generate_professor_pages(env, professors)
    generate_index_page(env, professors)


def main():
    professors = load_professors()
    if not professors:
        print("No professor data found. Generating empty site structure.")
        professors = []

    generate_html(professors)
    print(f"Done. Generated HTML for {len(professors)} professors.")


if __name__ == "__main__":
    main()
