import csv, re, sys
from urllib.parse import urlparse
from openpyxl import Workbook
from openpyxl.styles import Font
csv.field_size_limit(10**7)
SRC = ["add_c", "add_d", "add_a", "add_b", "web_ru", "web_en", "telegram", "twitter", "youtube"]
ADD = set(); FULL = set()

def read(f):
    try:
        with open(f, encoding="utf-8") as h:
            return list(csv.DictReader(h, delimiter=";"))
    except FileNotFoundError:
        return []

def dom(u):
    d = urlparse(u).netloc.removeprefix("www.").removeprefix("api.").removeprefix("docs.").removeprefix("app.")
    return {"proxy-seller.io": "proxy-seller.com", "proxyempire.com": "proxyempire.io"}.get(d, d)

# --- цены: склейка с объединением источников ---
prices, order = {}, []
for s in SRC:
    for r in read(s + ".csv"):
        r = {k: (v or "").strip() for k, v in r.items() if k}
        if s in ("add_c", "add_d"): FULL.add(dom(r["url"]).split(".")[-2])
        elif dom(r["url"]).split(".")[-2] in FULL and not s.startswith("add_"): continue
        if s.startswith("add_"): ADD.add(dom(r["url"])); r["source"] = "добор"
        elif dom(r["url"]) in ADD and r["country"].lower() in ("all", "все"): continue
        key = (dom(r["url"]), r["country"].lower(), r["tariff"].lower(), r["period"].lower(),
               r["price"], r["currency"].lower(), r["access"].lower())
        if key in prices:
            p = prices[key]
            s2 = "добор" if s.startswith("add_") else s
            if s2 not in p["sources"].split(", "): p["sources"] += ", " + s2
            if r["note"] and r["note"] not in p["note"]: p["note"] += " | " + r["note"]
            continue
        r["currency"] = re.sub(r"\s*\(.*\)", "", r["currency"]).upper()
        r["sources"] = "добор" if s.startswith("add_") else s; r["domain"] = key[0]
        blob = (r["tariff"] + " " + r["note"] + " " + r["evidence"]).lower()
        r["price_kind"] = "от" if re.search(r"\(from\)|цена .от.|\bfrom\b|starts? at|\bот\b", blob) else "точная"
        if r["countries_total"] == "0": r["countries_total"] = "не указано"
        try: r["price"] = float(r["price"])
        except ValueError: pass
        prices[key] = r; order.append(key)
PC = ["domain", "provider", "sources", "country", "countries_total", "carrier", "network", "access",
      "protocols", "tariff", "period", "price", "currency", "price_kind", "traffic", "rotation",
      "speed", "threads", "url", "evidence", "note"]
rows = sorted((prices[k] for k in order), key=lambda r: (r["domain"], r["country"], str(r["period"])))

def stack(files):
    out, cols = [], ["source"]
    for s, f in files:
        for r in read(f):
            r = {k: (v or "").strip() for k, v in r.items() if k}
            r["source"] = s
            for c in r:
                if c not in cols: cols.append(c)
            out.append(r)
    return cols, out

sheets = [
 ("Отчёт добора", stack([("A", "add_a_report.csv"), ("B", "add_b_report.csv"), ("В", "add_c_report.csv"), ("Г", "add_d_report.csv")])),
 ("Неподтверждённые", stack([(s, s + "_unverified.csv") for s in SRC])),
 ("Рекомендации", stack([("youtube", "youtube_recommendations.csv"), ("twitter", "twitter_recommendations.csv"), ("telegram", "telegram_recommendations.csv")])),
 ("Комментарии", stack([("youtube", "youtube_comments.csv"), ("twitter", "twitter_replies.csv")])),
 ("Упоминания Twitter", stack([("twitter", "twitter_mentions.csv")])),
 ("Видео YouTube", stack([("youtube", "youtube_videos.csv")])),
]
wb = Workbook(); ws = wb.active; ws.title = "Цены"
def fill(ws, cols, data):
    ws.append(cols)
    for c in ws[1]: c.font = Font(bold=True)
    for r in data: ws.append([r.get(c, "") for c in cols])
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
fill(ws, PC, rows)
# сводка по продавцам
sv = {}
for r in rows:
    d = sv.setdefault(r["domain"], {"domain": r["domain"], "provider": r["provider"], "src": set(), "countries": set(), "n": 0, "kinds": set(), "total": r["countries_total"]})
    d["src"].update(r["sources"].split(", ")); d["countries"].add(r["country"]); d["n"] += 1; d["kinds"].add(r["price_kind"])
ws2 = wb.create_sheet("Продавцы")
fill(ws2, ["domain", "provider", "источники", "стран с ценой", "стран всего", "строк", "тип цены"],
     [{"domain": d["domain"], "provider": d["provider"], "источники": ", ".join(sorted(d["src"])),
       "стран с ценой": len(d["countries"]), "стран всего": d["total"], "строк": d["n"],
       "тип цены": "/".join(sorted(d["kinds"]))} for d in sorted(sv.values(), key=lambda x: x["domain"])])
for name, (cols, data) in sheets:
    fill(wb.create_sheet(name), cols, data)
    print(name, len(data))
wb.save("mobile_proxies.xlsx")
with open("prices_all.csv", "w", encoding="utf-8-sig", newline="") as h:
    w = csv.DictWriter(h, PC, delimiter=";", extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("Цены", len(rows), "продавцов", len(sv), "с ценой 'от':", sum(1 for d in sv.values() if d["kinds"] == {"от"}))
from collections import Counter
print(Counter(r["currency"] for r in rows).most_common(8))
