import csv, re
from openpyxl import load_workbook
from openpyxl.styles import Font
RATE = {"RUB": 1, "USD": 82.9803, "EUR": 92.3322, "CNY": 12.4009, "INR": 0.884982, "PLN": 20.9145}  # ЦБ РФ на 13.11.2026
PERGB_AS_IS = {"iproyal", "oxylabs", "hydraproxy", "simplynode", "proxy4u"}
FORCE_GB = {"rayobyte", "relayox", "evomi", "decodo", "proxyempire", "proxyrack", "helodata", "kookeey",
            "voidmob", "proxidize", "dataimpulse", "resiprox", "infatica", "anyip", "proxy-store"}
rows = list(csv.DictReader(open("prices_all.csv", encoding="utf-8-sig"), delimiter=";"))

def gb_of(t):
    m = re.search(r"(\d[\d.,]*)\s*\+?\s*(tb|тб|gb|gib|гб|mb|мб)", t.lower())
    if not m: return None
    v = float(m.group(1).replace(",", ""))
    return v * {"t": 1000, "т": 1000, "g": 1, "г": 1, "m": 0.001, "м": 0.001}[m.group(2)[0]]

def days_of(p):
    p = p.lower()
    if re.search(r"trial|от 2 дней", p): return None
    m = re.search(r"(\d+)\s*(hour|час)", p)
    if m: return int(m.group(1)) / 24
    if "per day" in p: return 1
    m = re.search(r"(\d+)\s*(day|дн|ден)", p)
    if m: return int(m.group(1))
    m = re.search(r"(\d+)\s*(week|недел)", p)
    if m: return int(m.group(1)) * 7
    m = re.search(r"(\d+)\s*(month|месяц)", p)
    if m: return int(m.group(1)) * 30
    m = re.search(r"(\d+)\s*(year|год|лет)", p)
    if m: return int(m.group(1)) * 365
    if re.search(r"month|месяц", p): return 30
    return None

for r in rows:
    price = float(r["price"]); rub = price * RATE[r["currency"]]
    r["price_rub"] = round(rub, 2)
    prov = r["provider"].lower().replace(" ", "")
    acc, per, tar, tr = r["access"].lower(), r["period"].lower(), r["tariff"].lower(), r["traffic"].lower()
    r["unit"] = r["rub_per_gb"] = r["rub_per_day"] = r["rub_per_30d"] = ""
    r["kind"] = ("общий" if re.search(r"shared|общ", acc) and "not shared" not in acc else
                 "приватный" if re.search(r"приват|private|dedicated|выделен|в одни руки", acc) else
                 "общий" if re.search(r"общ|shared|публич|public|pool|пул|multi", acc) else "не указан")
    if "credit" in tar or "trial" in per or "trial" in tar or "wifi" in tar or "test" in tar or "port fee" in tar or "prepaid traffic" in tar:
        r["unit"] = "не сравнимо (кредиты/пробный/WiFi)"; continue
    is_gb = not re.match(r"приват|private|dedicated", acc) and (re.search(r"pool|per gb|пул|гб|\bgb\b", acc) or re.search(r"gb|гб|pay.as|package|expir|истек|без срока|commitment|subscription", per)
             or any(prov.startswith(x) for x in FORCE_GB | PERGB_AS_IS))
    if any(prov.startswith(x) for x in FORCE_GB | PERGB_AS_IS) and gb_of(tr) and "unlim" not in tr: is_gb = True
    if re.search(r"\d+\s*ports", tar):
        d = days_of(per); r["unit"] = "пакет портов"
        if d: r["rub_per_day"] = round(rub / d, 2); r["rub_per_30d"] = round(rub / d * 30, 2)
        continue
    if is_gb and "unlim" not in tr and "безлим" not in tr:
        r["unit"] = "за ГБ"
        m = re.search(r"[$¥€]\s*([\d.]+)\s*/\s*gb", tar)
        gb = gb_of(tr)
        if m: per_gb = float(m.group(1)) * RATE[r["currency"]]
        elif re.search(r"per gb|за гб|оплата за|цена за|from ", tr) or gb is None or per.startswith("per gb") \
                or per in ("pay as you go",) or any(prov.startswith(x) for x in PERGB_AS_IS): per_gb = rub
        else: per_gb = rub / gb
        if per_gb < 20: per_gb = rub  # меньше 20 ₽/ГБ не бывает: цена уже указана за гигабайт
        r["rub_per_gb"] = round(per_gb, 2); continue
    d = days_of(per)
    r["unit"] = "за время" if d else "срок не разобран"
    if d: r["rub_per_day"] = round(rub / d, 2); r["rub_per_30d"] = round(rub / d * 30, 2); r["_days"] = d

PC = list(rows[0].keys()); PC = [c for c in PC if not c.startswith("_")]
i = PC.index("price_kind"); order = PC[:i] + ["price_rub", "kind", "unit", "rub_per_day", "rub_per_30d", "rub_per_gb"] + [c for c in PC[i:] if c not in ("price_rub", "kind", "unit", "rub_per_day", "rub_per_30d", "rub_per_gb")]

def best(sel, key, by):
    b = {}
    for r in sel:
        k = by(r)
        if k not in b or r[key] < b[k][key]: b[k] = r
    out, grp = [], {}
    for r in sorted(b.values(), key=lambda r: r[key]):
        k = (r["domain"], round(r[key], 2), r.get("kind"))
        if k in grp: grp[k]["_c"].append(r["country"])
        else: r = dict(r); r["_c"] = [r["country"]]; grp[k] = r; out.append(r)
    for r in out:
        if len(r["_c"]) > 1: r["country"] = f'{len(r["_c"])} стран: ' + ", ".join(r["_c"][:40])
    return out

t = [r for r in rows if r["unit"] == "за время"]
top_month = best([r for r in t if r["_days"] >= 28], "price_rub_m", lambda r: (r["domain"], r["country"])) if False else None
for r in t: r["_m"] = r["price_rub"] / r["_days"] * 30
mm = [r for r in t if 28 <= r["_days"] <= 31]
month = best([r for r in mm if r["kind"] == "приватный"], "_m", lambda r: (r["domain"], r["country"].lower()))
month_sh = best([r for r in mm if r["kind"] != "приватный"], "_m", lambda r: (r["domain"], r["country"].lower()))
day = best([r for r in t if r["_days"] <= 1], "rub_per_day", lambda r: (r["domain"], r["country"].lower()))
gbs = best([r for r in rows if r["unit"] == "за ГБ"], "rub_per_gb", lambda r: r["domain"])
TC = ["место", "provider", "domain", "country", "carrier", "network", "access", "kind", "tariff", "period", "price", "currency",
      "price_rub", "rub_per_day", "rub_per_30d", "rub_per_gb", "price_kind", "traffic", "rotation", "sources", "url"]
wb = load_workbook("mobile_proxies.xlsx")
for n in ["Цены", "Топ месяц", "Топ месяц приватные", "Топ месяц общие", "Топ день", "Топ за ГБ"]:
    if n in wb.sheetnames: del wb[n]
def fill(ws, cols, data):
    ws.append(cols)
    for c in ws[1]: c.font = Font(bold=True)
    for k, r in enumerate(data, 1): ws.append([k if c == "место" else r.get(c, "") for c in cols])
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
fill(wb.create_sheet("Топ месяц приватные", 0), TC, month)
fill(wb.create_sheet("Топ месяц общие", 1), TC, month_sh)
fill(wb.create_sheet("Топ день", 2), TC, day)
fill(wb.create_sheet("Топ за ГБ", 3), TC, gbs)
for r in rows: r["price"] = float(r["price"])
fill(wb.create_sheet("Цены", 4), order, rows)
wb.save("mobile_proxies.xlsx")
from collections import Counter
print(Counter(r["unit"] for r in rows))
def show(name, data, key, n=12):
    print("==", name, len(data))
    for r in data[:n]: print(f'{r[key]:>9.0f} ₽ | {r["provider"][:18]} | {r["country"][:14]} | {r["access"][:26]} | {r["tariff"][:30]} | {r["period"][:10]} | {r["price"]} {r["currency"]} | {r["price_kind"]} | {r["traffic"][:14]}')
show("месяц приватные", month, "_m", 26); show("месяц общие", month_sh, "_m", 6); show("день", day, "rub_per_day", 15); show("ГБ", gbs, "rub_per_gb", 15)
print("срок не разобран:", Counter(r["period"] for r in rows if r["unit"] == "срок не разобран"))
