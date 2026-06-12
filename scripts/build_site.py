#!/usr/bin/env python3
"""
build_site.py — 主编排脚本
1. 读取 data/professors/*.json
2. 生成 Excel (comparison.xlsx)
3. 生成 HTML (index.html + professors/*.html)
4. 复制静态资源 (css/, js/, data/) 到 docs/
"""

import json
import os
import shutil
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "professors")
WEB_DIR = os.path.join(PROJECT_ROOT, "web")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "docs")

# Add scripts to path for importing
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
from generate_excel import generate_excel, load_professors
from generate_html import generate_html


def copy_static_assets():
    """Copy CSS, JS, and data files to docs/"""
    # Copy CSS
    src_css = os.path.join(WEB_DIR, "css")
    dst_css = os.path.join(OUTPUT_DIR, "css")
    if os.path.exists(dst_css):
        shutil.rmtree(dst_css)
    if os.path.exists(src_css):
        shutil.copytree(src_css, dst_css)

    # Copy JS
    src_js = os.path.join(WEB_DIR, "js")
    dst_js = os.path.join(OUTPUT_DIR, "js")
    if os.path.exists(dst_js):
        shutil.rmtree(dst_js)
    if os.path.exists(src_js):
        shutil.copytree(src_js, dst_js)

    # Copy data JSON files (for client-side loading)
    dst_data = os.path.join(OUTPUT_DIR, "data", "professors")
    if os.path.exists(dst_data):
        shutil.rmtree(dst_data)
    os.makedirs(dst_data, exist_ok=True)
    if os.path.exists(DATA_DIR):
        for fname in os.listdir(DATA_DIR):
            if fname.endswith(".json"):
                shutil.copy2(
                    os.path.join(DATA_DIR, fname),
                    os.path.join(dst_data, fname)
                )

    print("Static assets copied to docs/")


def generate_build_info():
    """Write a build info file"""
    info = {
        "built_at": datetime.now().isoformat(),
        "professor_count": 0
    }

    index_path = os.path.join(DATA_DIR, "index.json")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        info["professor_count"] = len(index)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "build-info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 50)
    print("TutorHunter — Site Builder")
    print("=" * 50)

    # Load data
    professors = load_professors()
    print(f"\n[1/4] Loaded {len(professors)} professors from data/")

    # Generate Excel
    if professors:
        print("[2/4] Generating Excel...")
        generate_excel(professors, os.path.join(OUTPUT_DIR, "comparison.xlsx"))
    else:
        print("[2/4] Skipping Excel (no data)")

    # Generate HTML
    print("[3/4] Generating HTML pages...")
    generate_html(professors)

    # Copy static assets
    print("[4/4] Copying static assets...")
    copy_static_assets()

    # Build info
    generate_build_info()

    print("\n" + "=" * 50)
    print(f"Build complete! Output in {OUTPUT_DIR}/")
    print("=" * 50)


if __name__ == "__main__":
    main()
