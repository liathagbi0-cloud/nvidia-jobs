import time, json, urllib.request, urllib.parse, html, datetime, os
from concurrent.futures import ThreadPoolExecutor

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

first = page(0, {})
groups = [(v["id"], v["descriptor"]) for f in first["facets"] if f["facetParameter"] == "jobFamilyGroup" for v in f["values"]]

def fetch_group(g):
    gid, name = g
    facets = {"jobFamilyGroup": [gid]}
    t = page(0, facets)["total"]
    out = []
    for off in range(0, t, 20):
        for j in page(off, facets)["jobPostings"]:
            j["cat"] = name
            out.append(j)
    return out

with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(fetch_group, groups))
seen = {}
for r in res:
    for j in r: seen[j["externalPath"]] = j
jobs = list(seen.values())
assert len(jobs) >= 0.9 * first["total"], "incomplete job list, not publishing"

POSTED_RANK = {"Posted Today": 0, "Posted Yesterday": 1}
def rank(j):
    p = j.get("postedOn", "")
    if p in POSTED_RANK: return POSTED_RANK[p]
    digits = "".join(c for c in p if c.isdigit())
    return 2 + (int(digits) if digits else 99)

data = []
for j in sorted(jobs, key=rank):
    jr = j["externalPath"].rsplit("_", 1)[-1]
    seg = j["externalPath"].split("/")[2] if j["externalPath"].count("/") >= 2 else ""
    country = seg.split("-")[0]
    msg = f"היי, אשמח לקישור הפניה למשרה:\n{j['title']}\n{j.get('locationsText','')}\nמספר משרה: {jr}\n{BASE + j['externalPath']}"
    data.append({
        "t": j["title"], "l": j.get("locationsText", ""), "p": j.get("postedOn", ""),
        "c": country, "k": j["cat"], "u": BASE + j["externalPath"],
        "w": "https://wa.me/" + WHATSAPP + "?text=" + urllib.parse.quote(msg), "r": rank(j),
    })

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

TEMPLATE = r"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>משרות פתוחות ב-NVIDIA</title>
<style>
:root{--g:#76b900;--bg:#f4f6f1;--card:#fff;--tx:#1a1a1a;--mu:#667;--bd:#e3e7dc}
@media(prefers-color-scheme:dark){:root{--bg:#0f1210;--card:#1a1e1a;--tx:#eef1ea;--mu:#9aa595;--bd:#2a312a}}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Arial,sans-serif;background:var(--bg);color:var(--tx)}
header{background:linear-gradient(135deg,#000,#1d2b0a 60%,#3d6200);color:#fff;padding:2.5rem 1rem 4.5rem}
.w{max-width:980px;margin:0 auto;padding:0 1rem}
h1{margin:0 0 .5rem;font-size:clamp(1.6rem,4vw,2.4rem)}h1 b{color:var(--g)}
header p{margin:.3rem 0;opacity:.9;max-width:680px;line-height:1.6}
.note{display:inline-block;margin-top:.8rem;background:rgba(118,185,0,.18);border:1px solid rgba(118,185,0,.5);padding:.5rem .8rem;border-radius:8px;font-size:.9rem}
.panel{margin-top:-3rem;background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:1rem;box-shadow:0 8px 24px rgba(0,0,0,.08);display:grid;gap:.7rem;grid-template-columns:2fr 1fr 1fr}
.panel input,.panel select{width:100%;padding:.75rem .9rem;font-size:1rem;border:1px solid var(--bd);border-radius:10px;background:var(--bg);color:var(--tx)}
.panel input:focus,.panel select:focus{outline:2px solid var(--g)}
.meta{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;color:var(--mu);font-size:.9rem;margin:1rem .2rem}
.job{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1.1rem;margin-bottom:.7rem;display:flex;gap:1rem;align-items:center;justify-content:space-between;transition:.15s}
.job:hover{border-color:var(--g);box-shadow:0 4px 14px rgba(118,185,0,.15)}
.job h3{margin:0 0 .35rem;font-size:1.05rem;direction:ltr;text-align:start}
.tags{display:flex;flex-wrap:wrap;gap:.4rem;font-size:.82rem;color:var(--mu)}
.tag{background:var(--bg);border:1px solid var(--bd);padding:.15rem .55rem;border-radius:99px}
.tag.new{background:#76b90022;border-color:var(--g);color:#4b7500;font-weight:600}
@media(prefers-color-scheme:dark){.tag.new{color:var(--g)}}
.job a.d{color:var(--mu);font-size:.82rem}
.btn{background:#25d366;color:#fff;padding:.65rem 1rem;border-radius:10px;text-decoration:none;font-weight:600;white-space:nowrap;display:inline-flex;gap:.4rem;align-items:center}
.btn:hover{background:#1ebe5b}
#more{display:block;margin:1.2rem auto;padding:.8rem 2rem;border:0;border-radius:10px;background:var(--g);color:#000;font-weight:700;font-size:1rem;cursor:pointer}
.empty{text-align:center;color:var(--mu);padding:3rem 0}footer{text-align:center;color:var(--mu);font-size:.8rem;padding:2rem 1rem}
@media(max-width:700px){.panel{grid-template-columns:1fr}.job{flex-direction:column;align-items:stretch}.btn{justify-content:center}}
</style></head><body>
<header><div class="w"><h1>משרות פתוחות ב-<b>NVIDIA</b></h1>
<p>מצאתם משרה שמתאימה לכם? לחצו על "בקשו קישור" ואשלח לכם קישור הגשה אישי בוואטסאפ.</p>
<span class="note">חשוב: כדי שההפניה תירשם, הגישו קורות חיים דרך הקישור שאשלח, ולא דרך "פרטי המשרה".</span></div></header>
<main class="w">
<div class="panel"><input id="q" type="search" placeholder="חיפוש משרה, תפקיד או מיקום…"><select id="co"><option value="">כל המדינות</option></select><select id="ca"><option value="">כל התחומים</option></select></div>
<div class="meta"><span id="cnt"></span><span>עודכן: __STAMP__</span></div>
<div id="list"></div><div id="empty" class="empty" hidden>לא נמצאו משרות מתאימות</div>
<button id="more" hidden>הצג עוד</button></main>
<footer>המשרות נלקחות מאתר הקריירה הרשמי של NVIDIA ומתעדכנות אוטומטית כל שעה.</footer>
<script>
const D=__DATA__,PAGE=40;let F=[],shown=0;
const $=id=>document.getElementById(id);
const esc=s=>s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fill=(sel,key)=>{const m={};D.forEach(j=>m[j[key]]=(m[j[key]]||0)+1);
 Object.entries(m).filter(e=>e[0]).sort((a,b)=>b[1]-a[1]).forEach(([k,n])=>sel.add(new Option(k+" ("+n+")",k)))};
fill($("co"),"c");fill($("ca"),"k");
const he=p=>p==="Posted Today"?"פורסם היום":p==="Posted Yesterday"?"פורסם אתמול":p.replace("Posted ","").replace("Days Ago","ימים").replace("30+","30+");
function card(j){const n=j.r<=1?'<span class="tag new">חדש</span>':'';
 return `<div class="job"><div><h3>${esc(j.t)}</h3><div class="tags">${n}<span class="tag">📍 ${esc(j.l.replace(/^(\d+) Locations$/,'$1 מיקומים'))}</span><span class="tag">${esc(j.k)}</span><span class="tag">${esc(he(j.p))}</span></div>
 <a class="d" href="${esc(j.u)}" target="_blank" rel="noopener">פרטי המשרה ↗</a></div><a class="btn" href="${esc(j.w)}" target="_blank" rel="noopener">💬 בקשו קישור</a></div>`}
function more(){const s=F.slice(shown,shown+PAGE);$("list").insertAdjacentHTML("beforeend",s.map(card).join(""));shown+=s.length;$("more").hidden=shown>=F.length}
function apply(){const v=$("q").value.trim().toLowerCase(),c=$("co").value,k=$("ca").value;
 F=D.filter(j=>(!c||j.c===c)&&(!k||j.k===k)&&(!v||(j.t+" "+j.l).toLowerCase().includes(v)));
 $("list").innerHTML="";shown=0;$("cnt").textContent=F.length+" משרות";$("empty").hidden=F.length>0;more()}
$("q").oninput=apply;$("co").onchange=apply;$("ca").onchange=apply;$("more").onclick=more;apply();
</script></body></html>"""

os.makedirs("site", exist_ok=True)
open("site/index.html", "w", encoding="utf-8").write(TEMPLATE.replace("__DATA__", payload).replace("__STAMP__", stamp))
print(f"Done: {len(jobs)} jobs")
