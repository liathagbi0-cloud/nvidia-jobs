import time, json, urllib.request, html, datetime

WHATSAPP = "972507568256"
BASE = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite"
API = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"

def page(offset, facets):
    req = urllib.request.Request(API, json.dumps({"appliedFacets": facets, "limit": 20, "offset": offset, "searchText": ""}).encode(),
                                {"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            if attempt == 5: raise
            time.sleep(2 ** attempt)

from concurrent.futures import ThreadPoolExecutor
first = page(0, {})
groups = [v["id"] for f in first["facets"] if f["facetParameter"] == "jobFamilyGroup" for v in f["values"]]

def fetch_group(g):
    facets = {"jobFamilyGroup": [g]}
    t = page(0, facets)["total"]
    out = []
    for off in range(0, t, 20):
        out += page(off, facets)["jobPostings"]
    return out

with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(fetch_group, groups))
seen = {}
for r in res:
    for j in r: seen[j["externalPath"]] = j
jobs = list(seen.values())
total = len(jobs)
assert total >= 0.9 * first['total'], 'incomplete job list, not publishing'

import urllib.parse, os
def row(j):
    jr = j["externalPath"].rsplit("_", 1)[-1]
    url = BASE + j["externalPath"]
    msg = (f"היי, אשמח לקישור הפניה למשרה:\n{j['title']}\n{j.get('locationsText','')}\nמספר משרה: {jr}")
    wa = "https://wa.me/" + WHATSAPP + "?text=" + urllib.parse.quote(msg)
    return (f'<tr><td>{html.escape(j["title"])}<br><small><a href="{html.escape(url)}" target="_blank" rel="noopener">פרטי המשרה</a></small></td>'
            f'<td>{html.escape(j.get("locationsText",""))}</td><td>{html.escape(j.get("postedOn",""))}</td>'
            f'<td><a class="btn" href="{wa}" target="_blank" rel="noopener">בקשי ממני קישור</a></td></tr>')
rows = "\n".join(row(j) for j in jobs)

os.makedirs("site", exist_ok=True)
open("site/index.html", "w", encoding="utf-8").write(f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>משרות פתוחות ב-NVIDIA</title>
<style>body{{font-family:system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem}}
input{{width:100%;box-sizing:border-box;padding:.7rem;font-size:1rem;margin:1rem 0}}table{{width:100%;border-collapse:collapse}}
td,th{{padding:.5rem;border-bottom:1px solid #ddd;text-align:start}}.btn{{background:#25d366;color:#fff;padding:.4rem .7rem;border-radius:6px;text-decoration:none;white-space:nowrap;font-size:.9rem}}
small a{{color:#555}}</style></head><body>
<h1>משרות פתוחות ב-NVIDIA ({len(jobs)})</h1>
<p>מצאת משרה? לחצו "בקשי ממני קישור" ואשלח לכם קישור הגשה אישי. כדי שההפניה תירשם, הגישו קורות חיים דרך הקישור שאשלח ולא דרך "פרטי המשרה". עודכן: {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC</p>
<input id="q" placeholder="חיפוש לפי שם משרה או מיקום (למשל Israel, Firmware)…">
<table><thead><tr><th>משרה</th><th>מיקום</th><th>פורסם</th><th></th></tr></thead><tbody id="t">{rows}</tbody></table>
<script>q.oninput=()=>{{const v=q.value.toLowerCase();for(const r of t.rows)r.hidden=!r.textContent.toLowerCase().includes(v)}}</script>
</body></html>""")
print(f"Done: {len(jobs)} jobs")
