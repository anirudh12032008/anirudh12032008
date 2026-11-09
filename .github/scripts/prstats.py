# Rewrites the block between the PRSTATS markers in README.md with live PR stats.
import json, os, re, urllib.request
from collections import Counter

USER = os.environ["USER_LOGIN"]

def search(q):
    items, page = [], 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/search/issues?q={q}&per_page=100&page={page}&sort=updated",
            headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"})
        data = json.load(urllib.request.urlopen(req))
        items += data["items"]
        if len(items) >= data["total_count"] or not data["items"]:
            return items
        page += 1

def upstream(items):
    return [i for i in items if not i["repository_url"].split("/repos/")[1].startswith(USER + "/")]

merged = upstream(search(f"author:{USER}+type:pr+is:merged"))
opened = upstream(search(f"author:{USER}+type:pr+is:open"))
repos = Counter(i["repository_url"].split("/repos/")[1] for i in merged)
merged.sort(key=lambda i: i["pull_request"]["merged_at"], reverse=True)

lines = [f"**{len(merged)}** PRs merged into **{len(repos)}** repos · **{len(opened)}** open right now",
         "", "latest ones:"]
for i in merged[:5]:
    repo = i["repository_url"].split("/repos/")[1]
    lines.append(f"- [{repo}#{i['number']}]({i['html_url']}) {i['title']} ({i['pull_request']['merged_at'][:10]})")
lines += ["", "<sub>updates by itself every few hours</sub>"]

readme = open("README.md").read()
new = re.sub(r"(<!-- PRSTATS:START -->).*?(<!-- PRSTATS:END -->)",
             lambda m: m[1] + "\n" + "\n".join(lines) + "\n" + m[2], readme, flags=re.S)
open("README.md", "w").write(new)

# --- SVG cards (they follow the viewer's light/dark theme) ---
def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                                               "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(req))

STYLE = """<style>
text{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:#24292f}
.mut{fill:#57606a}.bg{fill:#ffffff;stroke:#d0d7de}
@media (prefers-color-scheme:dark){text{fill:#e6edf3}.mut{fill:#8d96a0}.bg{fill:#0d1117;stroke:#30363d}}
</style>"""
COLORS = ["#2da44e", "#0969da", "#bf3989", "#d4a72c", "#8250df", "#cf222e", "#1b7c83", "#6e7781"]

os.makedirs("assets", exist_ok=True)
stats = [(len(merged), "PRs merged"), (len(repos), "repos"), (len(opened), "open right now")]
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="190" viewBox="0 0 600 190">{STYLE}',
       '<rect class="bg" x=".5" y=".5" width="599" height="189" rx="10"/>']
for k, (n, label) in enumerate(stats):
    x = 100 + k * 200
    svg.append(f'<text x="{x}" y="70" text-anchor="middle" font-size="40" font-weight="700">{n}</text>'
               f'<text class="mut" x="{x}" y="96" text-anchor="middle" font-size="14">{label}</text>')
top = repos.most_common(6)
total = sum(c for _, c in top)
x = 30
for k, (r, c) in enumerate(top):
    w = 540 * c / total
    svg.append(f'<rect x="{x:.1f}" y="120" width="{max(w - 2, 1):.1f}" height="10" rx="2" fill="{COLORS[k]}"/>')
    x += w
for k, (r, c) in enumerate(top):
    cx, cy = 30 + (k % 3) * 180, 152 + (k // 3) * 20
    svg.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLORS[k]}"/>'
               f'<text x="{cx + 15}" y="{cy}" font-size="12">{r.split("/")[1]} <tspan class="mut">{c}</tspan></text>')
open("assets/pr-stats.svg", "w").write("\n".join(svg + ["</svg>"]))

langs = Counter()
page = 1
while True:
    batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
    for r in batch:
        if not r["fork"]:
            langs.update(get(r["languages_url"]))
    if len(batch) < 100:
        break
    page += 1
for skip in ("HTML", "CSS", "Jupyter Notebook", "TeX", "Makefile", "Shell"):
    langs.pop(skip, None)
top = langs.most_common(8)
total = sum(b for _, b in top)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="120" viewBox="0 0 600 120">{STYLE}',
       '<rect class="bg" x=".5" y=".5" width="599" height="119" rx="10"/>',
       '<text x="30" y="32" font-size="14" font-weight="600">what I write the most</text>']
x = 30
for k, (l, b) in enumerate(top):
    w = 540 * b / total
    svg.append(f'<rect x="{x:.1f}" y="46" width="{max(w - 2, 1):.1f}" height="10" rx="2" fill="{COLORS[k]}"/>')
    x += w
for k, (l, b) in enumerate(top):
    cx, cy = 30 + (k % 4) * 135, 80 + (k // 4) * 20
    svg.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLORS[k]}"/>'
               f'<text x="{cx + 15}" y="{cy}" font-size="12">{l} <tspan class="mut">{100 * b / total:.0f}%</tspan></text>')
open("assets/languages.svg", "w").write("\n".join(svg + ["</svg>"]))
