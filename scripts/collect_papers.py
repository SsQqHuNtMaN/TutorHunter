#!/usr/bin/env python3
"""
collect_papers.py — 多渠道论文搜集
DBLP + OpenReview + arXiv + WebSearch 后备
支持去重、标签生成、增量更新
"""
import json, os, re, subprocess, time, urllib.request, urllib.error
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'professors')
MAX_WORKERS = 5

# Research tag patterns
TAG_PATTERNS = {
    'Computer Vision': ['vision', 'image', 'video', 'visual', 'object detection', 'segmentation'],
    'Deep Learning': ['deep learn', 'neural network', 'transformer', 'attention', 'CNN'],
    'Multimodal': ['multimodal', 'cross-modal', 'vision-language', 'text-to-image'],
    'Embodied AI': ['embodied', 'robot', 'manipulation', 'reinforcement learn'],
    'LLM/MLLM': ['LLM', 'large language', 'GPT', 'language model', 'VLM'],
    'Image Restoration': ['restoration', 'denoising', 'deblurring', 'super-resolution', 'deraining'],
    'Speech/Audio': ['speech', 'audio', 'voice', 'acoustic', 'ASR', 'TTS'],
    'Wireless/Comm': ['wireless', 'communication', '5G', '6G', 'MIMO', 'channel', 'beamforming', 'ISAC'],
    'Networking': ['network', 'routing', 'protocol', 'SDN', 'NFV', 'internet'],
    'Security': ['security', 'attack', 'defense', 'privacy', 'encryption', 'anomaly'],
    'Signal Processing': ['signal process', 'filter', 'Fourier', 'wavelet', 'compressive'],
    'Radar/Microwave': ['radar', 'microwave', 'SAR', 'antenna', 'electromagnetic'],
    'Control Systems': ['control', 'ADRC', 'PID', 'vibration', 'stabilization'],
    'Machine Learning': ['machine learn', 'classification', 'clustering', 'SVM', 'XGBoost'],
    'Generative AI': ['generative', 'GAN', 'diffusion', 'VAE', 'image synthesis'],
    'Natural Language': ['NLP', 'natural language', 'text', 'sentiment'],
    'Edge Computing': ['edge comput', 'mobile edge', 'MEC'],
    'Event Camera': ['event camera', 'event-based', 'neuromorphic', 'spike'],
    '3D Vision': ['3D', 'point cloud', 'depth', 'NeRF', 'reconstruction'],
    'Quantum': ['quantum', 'qubit', 'entanglement'],
    'Biomedical': ['medical', 'biomedical', 'clinical', 'diagnosis', 'MRI', 'CT'],
    'Optimization': ['optimization', 'convex', 'gradient', 'stochastic'],
    'Circuit/IC': ['circuit', 'IC ', 'VLSI', 'CMOS', 'chip', 'FPGA'],
    'Power/Energy': ['power', 'energy', 'battery', 'solar', 'grid'],
    'Robotics': ['robot', 'autonomous', 'drone', 'UAV', 'SLAM'],
}

def curl(url, timeout=15):
    """Fetch URL via curl with UTF-8 handling"""
    try:
        r = subprocess.run(['curl', '-s', '-L', '--max-time', str(timeout), url],
                          capture_output=True, timeout=timeout+5)
        return r.stdout.decode('utf-8', errors='replace')
    except:
        return ''

def name_match_score(candidate_name, target_name):
    """Score how well a DBLP author name matches the target. Returns 0-100."""
    c = candidate_name.lower().replace('  ', ' ')
    t = target_name.lower()
    # Direct match
    if c == t: return 100
    # Split into parts
    c_parts = set(c.split())
    t_parts = set(t.split())
    common = c_parts & t_parts
    if not common: return 0
    # Score based on common parts
    score = len(common) / max(len(t_parts), 1) * 80
    # Bonus for matching first and last name
    t_first, t_last = t.split()[0] if t.split() else '', t.split()[-1] if t.split() else ''
    if t_last and t_last in c: score += 15
    if t_first and t_first in c: score += 5
    return min(score, 100)

def search_dblp(name_en):
    """Search DBLP for an author, return (pid_url, papers). Uses name matching to avoid wrong authors."""
    papers = []
    pid_url = None
    try:
        # Step 1: Author search
        q = urllib.request.quote(name_en)
        html = curl(f'https://dblp.org/search/author/api?q={q}&format=json')
        if not html: return None, []

        data = json.loads(html)
        hits = data.get('result', {}).get('hits', {}).get('hit', [])
        if not hits: return None, []

        # Try to find best matching author (not just first)
        best_hit = None
        best_score = 0
        for h in hits[:10]:
            info = h.get('info', {})
            author_name = info.get('author', '')
            url_str = info.get('url', '')
            if not url_str or 'pid' not in url_str: continue
            score = name_match_score(author_name, name_en)
            if score > best_score:
                best_score = score
                best_hit = info

        # Require minimum match score to avoid wrong authors
        if not best_hit or best_score < 50:
            return None, []

        info = best_hit
        pid_url = info.get('url', '')
        if not pid_url: return None, []

        # Step 2: Fetch papers
        xml = curl(pid_url + '.xml')
        if not xml: return pid_url, []

        pubs = re.findall(r'<(?:article|inproceedings|informal)[^>]*?>(.*?)</(?:article|inproceedings|informal)>', xml, re.DOTALL)
        for pub_xml in pubs:
            ym = re.search(r'<year>(.*?)</year>', pub_xml)
            if not ym or not ym.group(1).isdigit(): continue
            year = int(ym.group(1))
            if year < 2024: continue

            tm = re.search(r'<title>(.*?)</title>', pub_xml)
            vm = re.search(r'<journal>(.*?)</journal>|<booktitle>(.*?)</booktitle>', pub_xml)
            am = re.findall(r'<author[^>]*>(.*?)</author>', pub_xml)

            venue = vm.group(1) or vm.group(2) if vm else 'Unknown'
            authors = [a.strip() for a in am if a.strip()]

            papers.append({
                'title': tm.group(1) if tm else '?',
                'authors': authors,
                'venue': venue,
                'year': year,
                'type': 'journal' if vm and vm.group(1) else 'conference',
                'source': 'dblp'
            })

        return pid_url, papers[:30]
    except:
        return pid_url, papers

def search_openreview(name_en):
    """Search OpenReview for papers — use name+USTC to reduce noise"""
    papers = []
    try:
        # Add institution context to reduce false matches
        q = urllib.request.quote(f'{name_en} USTC')
        html = curl(f'https://api2.openreview.net/notes/search?term={q}&limit=15')
        if not html: return []

        data = json.loads(html)
        for note in data.get('notes', []):
            c = note.get('content', {})
            title = c.get('title', '')
            venue = c.get('venue', '')
            cdate = note.get('cdate', 0)
            year = int(str(cdate)[:4]) if cdate else None

            if not year or year < 2024 or not title: continue

            authors_raw = c.get('authors', [])
            authors = [str(a) for a in authors_raw] if isinstance(authors_raw, list) else [authors_raw]

            papers.append({
                'title': str(title),
                'authors': authors,
                'venue': str(venue) if venue else 'OpenReview',
                'year': year,
                'type': 'conference',
                'source': 'openreview'
            })
        return papers[:15]
    except:
        return papers

def search_arxiv(name_en):
    """Search arXiv for papers — use name+USTC format"""
    papers = []
    try:
        # Include both name variants in search
        name_parts = name_en.replace(' ', '_')
        q = urllib.request.quote(f'au:{name_parts}+AND+all:USTC')
        xml = curl(f'http://export.arxiv.org/api/query?search_query={q}&start=0&max_results=10&sortBy=lastUpdatedDate&sortOrder=descending')
        if not xml: return []

        entries = re.findall(r'<entry>(.*?)</entry>', xml, re.DOTALL)
        for entry in entries:
            tm = re.search(r'<title>(.*?)</title>', entry)
            ym = re.search(r'<published>(\d{4})', entry)
            am = re.findall(r'<author>.*?<name>(.*?)</name>.*?</author>', entry, re.DOTALL)
            cm = re.search(r'<arxiv:comment[^>]*>(.*?)</arxiv:comment>', entry)

            if not ym: continue
            year = int(ym.group(1))
            if year < 2024: continue

            authors = [a.strip() for a in am if a.strip()]
            venue = cm.group(1)[:80] if cm else 'arXiv preprint'

            papers.append({
                'title': re.sub(r'\s+', ' ', (tm.group(1) if tm else '?')).strip(),
                'authors': authors,
                'venue': venue,
                'year': year,
                'type': 'preprint',
                'source': 'arxiv'
            })
        return papers[:10]
    except:
        return papers

def deduplicate(papers):
    """Deduplicate papers by normalized title"""
    seen = set()
    unique = []
    for p in papers:
        # Normalize title for dedup
        key = re.sub(r'[^a-z0-9]', '', p['title'].lower())[:60]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique

def generate_tags(papers):
    """Generate research tags from paper titles"""
    all_titles = ' '.join(p['title'].lower() for p in papers)
    scores = Counter()
    for tag, kws in TAG_PATTERNS.items():
        for kw in kws:
            if kw.lower() in all_titles:
                scores[tag] += all_titles.count(kw.lower())
    return [t for t, s in scores.most_common(6) if s >= 2]

def process_professor(prof):
    """Process one professor: search all channels, dedup, update JSON"""
    prof_id = prof['id']
    en_name = prof['name'].get('en', '')
    zh_name = prof['name'].get('zh', prof_id)

    if not en_name:
        return (prof_id, zh_name, 0, [])

    # Search all channels
    dblp_url, dblp_papers = search_dblp(en_name)
    or_papers = search_openreview(en_name)
    arxiv_papers = search_arxiv(en_name)

    # Combine and deduplicate
    all_papers = dblp_papers + or_papers + arxiv_papers
    unique = deduplicate(all_papers)

    # Generate tags
    tags = generate_tags(unique)

    # Write updated JSON
    json_path = os.path.join(DATA_DIR, f'{prof_id}.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert to schema format
        schema_papers = []
        for p in unique:
            authors_schema = []
            for i, a in enumerate(p['authors']):
                role = 'first_author' if i == 0 else ('corresponding' if i == len(p['authors'])-1 else 'co_author')
                authors_schema.append({
                    'name': a, 'role': role,
                    'likely_student': (i == 0 and a != en_name)
                })
            schema_papers.append({
                'title': p['title'], 'authors': authors_schema,
                'venue': p['venue'], 'year': p['year'],
                'type': p['type'], 'source': p['source'],
                'url': '', 'citations': None
            })

        # Merge with existing, sort by year
        existing_titles = {p['title'] for p in data['publications'].get('recent', [])}
        new_only = [p for p in schema_papers if p['title'] not in existing_titles]
        data['publications']['recent'] = (data['publications'].get('recent', []) + new_only)[:25]
        data['publications']['recent'] = sorted(
            data['publications']['recent'],
            key=lambda x: x.get('year', 0), reverse=True
        )

        # Update source info
        sources = []
        if dblp_papers: sources.append('dblp')
        if or_papers: sources.append('openreview')
        if arxiv_papers: sources.append('arxiv')
        data['publications']['source'] = '+'.join(sources) if sources else data['publications'].get('source')
        data['publications']['source_note'] = f'DBLP:{len(dblp_papers)} OR:{len(or_papers)} arXiv:{len(arxiv_papers)}'

        if dblp_url and not data['contact'].get('dblp_url'):
            data['contact']['dblp_url'] = dblp_url

        # Update tags
        existing_tags = set(data.get('research', {}).get('tags', []))
        for t in tags:
            existing_tags.add(t)
        data['research']['tags'] = sorted(existing_tags)
        data['auto_tags_from_papers'] = tags

        # Update quality
        if len(unique) >= 5:
            data['_quality']['overall'] = 'high'
        elif len(unique) >= 2:
            data['_quality']['overall'] = 'medium'
        if 'publications' in data['_quality'].get('missing_fields', []):
            data['_quality']['missing_fields'].remove('publications')
        data['_sources']['papers_fetched'] = True
        data['_sources']['fetched_at'] = datetime.now().isoformat()

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return (prof_id, zh_name, len(unique), tags)

def main():
    print("=" * 60)
    print("TutorHunter — Multi-Channel Paper Collection")
    print(f"DBLP + OpenReview + arXiv API | {MAX_WORKERS} concurrent workers")
    print("=" * 60)

    # Load all professors
    index_path = os.path.join(DATA_DIR, 'index.json')
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    print(f"\nLoaded {len(index)} professors from index")

    # Process in parallel
    results = []
    total_papers = 0
    with_profiles = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_professor, p): p for p in index}
        for i, future in enumerate(as_completed(futures)):
            prof_id, zh_name, paper_count, tags = future.result()
            results.append((prof_id, zh_name, paper_count, tags))
            total_papers += paper_count
            if paper_count > 0:
                with_profiles += 1
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{len(index)} professors, {total_papers} papers found")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  Professors with papers: {with_profiles}/{len(index)}")
    print(f"  Total papers collected: {total_papers}")
    print(f"\nTop professors by paper count:")

    results.sort(key=lambda x: x[2], reverse=True)
    for prof_id, zh_name, count, tags in results[:15]:
        if count > 0:
            print(f"  {zh_name}: {count} papers | tags: {tags[:4]}")

    # Rebuild index
    print(f"\nRebuilding index.json...")
    new_index = []
    for f in sorted(os.listdir(DATA_DIR)):
        if not f.startswith('ustc-sist-') or not f.endswith('.json'):
            continue
        with open(os.path.join(DATA_DIR, f), 'r', encoding='utf-8') as fp:
            p = json.load(fp)
        new_index.append({
            "id": p["id"], "name": p["name"], "title": p.get("title", ""),
            "university": p["university"], "department": p["department"],
            "region": p.get("region", "mainland_china"),
            "research_tags": p.get("research", {}).get("tags", []),
            "is_recruiting": p.get("admission", {}).get("is_recruiting"),
            "last_updated": p.get("_sources", {}).get("fetched_at", "")
        })
    with open(os.path.join(DATA_DIR, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(new_index, f, ensure_ascii=False, indent=2)

    print(f"Index updated: {len(new_index)} professors")
    print("Done!")

if __name__ == '__main__':
    main()
