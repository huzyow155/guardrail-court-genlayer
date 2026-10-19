import os
import re

md_files = []
for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root:
        continue
    for f in files:
        if f.endswith('.md'):
            md_files.append(os.path.join(root, f))

broken_links = []
link_pat = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

for path in md_files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for match in link_pat.finditer(content):
        label, url = match.groups()
        if url.startswith('http://') or url.startswith('https://') or url.startswith('mailto:') or url.startswith('#') or url.startswith('file://'):
            continue
        clean_url = url.split('#')[0]
        if not clean_url:
            continue
        target_path = os.path.normpath(os.path.join(os.path.dirname(path), clean_url))
        if not os.path.exists(target_path):
            broken_links.append((path, url, target_path))

print(f"Checked {len(md_files)} markdown files.")
if broken_links:
    print(f"FOUND {len(broken_links)} BROKEN LINKS:")
    for p, u, t in broken_links:
        print(f"  In {p}: link '{u}' -> {t} NOT FOUND")
else:
    print("ALL RELATIVE LINKS RESOLVED CLEANLY (0 broken links).")
