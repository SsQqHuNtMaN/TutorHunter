#!/usr/bin/env python3
"""Fetch papers from OpenReview + DBLP + arXiv for all professors"""
import json, os, re, urllib.request, urllib.error, sys
from datetime import datetime

data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'professors')

# Load professor index
with open(os.path.join(data_dir, 'index.json'), 'r', encoding='utf-8') as f:
    index = json.load(f)

def fetch_dblp_papers(english_name, max_papers=20):
    """Search DBLP for an author and return recent papers"""
    papers = []
    try:
        # Step 1: search for author
        url = f"https://dblp.org/search/author/api?q={urllib.request.quote(english_name)}&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'TutorHunter/1.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        hits = data.get('result', {}).get('hits', {}).get('hit', [])
        if not hits:
            return papers, None

        # Take first match that has a URL
        pid_url = None
        for h in hits:
            info = h.get('info', {})
            url_str = info.get('url', '')
            if url_str and 'pid' in url_str:
                pid_url = url_str
                break

        if not pid_url:
            return papers, None

        # Step 2: fetch publications XML
        xml_url = pid_url + '.xml'
        req2 = urllib.request.Request(xml_url, headers={'User-Agent': 'TutorHunter/1.0'})
        xml = urllib.request.urlopen(req2, timeout=15).read().decode('utf-8')

        # Extract publications
        pub_pattern = r'<(?:article|inproceedings|informal)[^>]*?>(.*?)</(?:article|inproceedings|informal)>'
        pubs = re.findall(pub_pattern, xml, re.DOTALL)

        for pub_xml in pubs:
            title_m = re.search(r'<title>(.*?)</title>', pub_xml)
            year_m = re.search(r'<year>(.*?)</year>', pub_xml)
            venue_m = re.search(r'<journal>(.*?)</journal>|<booktitle>(.*?)</booktitle>', pub_xml)
            authors_m = re.findall(r'<author[^>]*>(.*?)</author>', pub_xml)

            if not year_m or not year_m.group(1).isdigit():
                continue
            year = int(year_m.group(1))
            if year < 2024:
                continue

            title = title_m.group(1) if title_m else 'Unknown'
            venue = venue_m.group(1) or venue_m.group(2) if venue_m else 'Unknown'
            authors = [a.strip() for a in authors_m if a.strip()]

            papers.append({
                'title': title,
                'authors': authors,
                'venue': venue,
                'year': year,
                'type': 'conference' if 'booktitle' in (venue_m.group(0) if venue_m else '') else 'journal',
                'citations': None
            })

        return papers[:max_papers], pid_url
    except Exception as e:
        print(f'  DBLP error: {e}', file=sys.stderr)
        return papers, None


def fetch_openreview_papers(english_name, max_papers=15):
    """Search OpenReview for an author"""
    papers = []
    try:
        url = f"https://api2.openreview.net/notes/search?term={urllib.request.quote(english_name)}&limit={max_papers}"
        req = urllib.request.Request(url, headers={'User-Agent': 'TutorHunter/1.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        notes = data.get('notes', [])

        for n in notes:
            c = n.get('content', {})
            title = c.get('title', '')
            venue = c.get('venue', '')
            cdate = n.get('cdate', 0)
            year = int(str(cdate)[:4]) if cdate else None

            authors_raw = c.get('authors', [])
            if isinstance(authors_raw, list):
                authors = [str(a) for a in authors_raw]
            elif isinstance(authors_raw, str):
                authors = [a.strip() for a in authors_raw.split(',')]
            else:
                authors = []

            if year and year >= 2024 and title:
                papers.append({
                    'title': str(title),
                    'authors': authors,
                    'venue': str(venue) if venue else 'OpenReview',
                    'year': year,
                    'type': 'conference',
                    'citations': None
                })

        return papers[:max_papers]
    except Exception as e:
        print(f'  OpenReview error: {e}', file=sys.stderr)
        return papers


# Process each professor
total_new = 0
for entry in index:
    prof_id = entry['id']
    en_name = entry['name'].get('en', '')
    zh_name = entry['name'].get('zh', '')

    print(f'\n=== {zh_name} ({en_name}) ===')

    # Fetch from sources
    dblp_papers, dblp_url = fetch_dblp_papers(en_name, 15)
    or_papers = fetch_openreview_papers(en_name, 10)

    all_papers = {}
    for p in dblp_papers + or_papers:
        key = p['title'][:80]
        if key not in all_papers:
            all_papers[key] = p

    unique_papers = sorted(all_papers.values(), key=lambda x: x['year'], reverse=True)
    print(f'  DBLP: {len(dblp_papers)}, OpenReview: {len(or_papers)}, Unique: {len(unique_papers)}')

    if not unique_papers:
        print('  No papers found')
        continue

    # Print sample
    for p in unique_papers[:5]:
        authors_short = ', '.join(p['authors'][:3])
        if len(p['authors']) > 3:
            authors_short += f' +{len(p["authors"])-3}'
        print(f'  [{p["year"]}] {p["title"][:70]} | {p["venue"][:30]} | {authors_short}')

    # Write to JSON
    json_path = os.path.join(data_dir, f'{prof_id}.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            prof = json.load(f)

        # Convert to schema format
        papers_schema = []
        for p in unique_papers:
            authors_schema = []
            for i, a_name in enumerate(p['authors']):
                role = 'first_author' if i == 0 else ('corresponding' if i == len(p['authors'])-1 else 'co_author')
                authors_schema.append({
                    'name': a_name,
                    'role': role,
                    'likely_student': (i == 0 and a_name != en_name)
                })
            papers_schema.append({
                'title': p['title'],
                'authors': authors_schema,
                'venue': p['venue'],
                'year': p['year'],
                'type': p['type'],
                'url': '',
                'citations': p.get('citations')
            })

        existing_titles = {p['title'] for p in prof['publications'].get('recent', [])}
        new_papers = [p for p in papers_schema if p['title'] not in existing_titles]
        prof['publications']['recent'] = (prof['publications'].get('recent', []) + new_papers)[:25]

        if dblp_url:
            prof['contact']['dblp_url'] = dblp_url
        prof['publications']['source'] = 'dblp+openreview'
        all_venues = set(prof['publications'].get('top_venues', []))
        for p in unique_papers:
            all_venues.add(p['venue'])
        prof['publications']['top_venues'] = sorted(all_venues)[:15]
        prof['publications']['source_note'] = f'DBLP API + OpenReview API; {len(dblp_papers)} from DBLP, {len(or_papers)} from OpenReview'
        if 'publications' in prof['_quality'].get('missing_fields', []):
            prof['_quality']['missing_fields'].remove('publications')
        prof['_quality']['overall'] = 'high' if len(prof['publications']['recent']) >= 8 else 'medium'
        prof['_sources']['dblp_fetched'] = True
        prof['_sources']['openreview_fetched'] = True
        prof['_sources']['fetched_at'] = datetime.now().isoformat()

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(prof, f, ensure_ascii=False, indent=2)

        total_new += len(new_papers)

print(f'\n{"="*50}')
print(f'Total new papers added: {total_new}')
print('Done!')
