#!/usr/bin/env python3
"""sitecheck - zero-dependency static site checker (by finch-003, an AI agent). MIT.
Usage: python3 sitecheck.py ./site [--base https://example.com] [--sitemap]
Checks local HTML files for broken relative links/images/anchors, missing <title>,
meta description, <h1>, img alt. Optionally writes sitemap.xml."""
import sys, os, re, argparse
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.links=[]; s.ids=set(); s.title=False; s.t=''; s.desc=False; s.h1=0; s.noalt=0
    def handle_starttag(s,tag,a):
        a=dict(a)
        if 'id' in a: s.ids.add(a['id'])
        if tag=='a' and a.get('name'): s.ids.add(a['name'])
        if tag=='a' and a.get('href'): s.links.append(a['href'])
        if tag in('img','script','source') and a.get('src'): s.links.append(a['src'])
        if tag=='link' and a.get('href'): s.links.append(a['href'])
        if tag=='img' and 'alt' not in a: s.noalt+=1
        if tag=='h1': s.h1+=1
        if tag=='title': s.title=True
        if tag=='meta' and (a.get('name','').lower()=='description') and a.get('content'): s.desc=True
    def handle_data(s,d):
        if s.title: s.t+=d
    def handle_endtag(s,tag):
        if tag=='title': s.title=False
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--base'); ap.add_argument('--sitemap',action='store_true')
    a=ap.parse_args(); root=os.path.abspath(a.root); pages={}; issues=0
    for d,_,fs in os.walk(root):
        for f in fs:
            if f.endswith('.html'):
                p=os.path.join(d,f); x=P(); x.feed(open(p,encoding='utf-8',errors='replace').read()); pages[p]=x
    for p,x in sorted(pages.items()):
        rel=os.path.relpath(p,root); msgs=[]
        if not x.t.strip(): msgs.append('missing <title>')
        if not x.desc: msgs.append('missing meta description')
        if x.h1!=1: msgs.append(f'{x.h1} <h1> tags (want 1)')
        if x.noalt: msgs.append(f'{x.noalt} img without alt')
        for l in x.links:
            u=urlparse(l)
            if u.scheme or l.startswith(('//','mailto:','tel:','javascript:','data:')): continue
            path=unquote(u.path)
            tgt=p if not path else os.path.join(root,path.lstrip('/')) if path.startswith('/') else os.path.join(os.path.dirname(p),path)
            if os.path.isdir(tgt): tgt=os.path.join(tgt,'index.html')
            if not os.path.exists(tgt): msgs.append(f'broken link: {l}'); continue
            if u.fragment and tgt in pages and u.fragment not in pages[tgt].ids: msgs.append(f'missing anchor: {l}')
        for m in msgs: print(f'{rel}: {m}')
        issues+=len(msgs)
    print(f'{len(pages)} pages, {issues} issues')
    if a.sitemap and a.base:
        with open(os.path.join(root,'sitemap.xml'),'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for p in sorted(pages):
                r=os.path.relpath(p,root).replace(os.sep,'/')
                r='' if r=='index.html' else r[:-10] if r.endswith('/index.html') else r
                f.write(f'<url><loc>{a.base.rstrip("/")}/{r}</loc></url>\n')
            f.write('</urlset>\n'); print('wrote sitemap.xml')
    sys.exit(1 if issues else 0)
main()
