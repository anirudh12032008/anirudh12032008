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
