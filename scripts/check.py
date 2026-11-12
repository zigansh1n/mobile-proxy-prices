#!/usr/bin/env python3
"""Приёмка CSV с ценами: check.py file.csv MIN_DOMAINS
Строка засчитывается, только если цена — число, заполнены обязательные поля
и это число реально есть в тексте страницы url (скрипт сам её скачивает)."""
import csv, re, subprocess, sys
from urllib.parse import urlparse

COLS = ["source", "provider", "url", "country", "countries_total", "carrier", "network",
        "access", "protocols", "tariff", "period", "price", "currency", "traffic",
        "rotation", "speed", "threads", "evidence", "note"]
REQUIRED = ["provider", "url", "country", "countries_total", "carrier", "network", "access",
            "protocols", "period", "price", "currency", "traffic", "rotation", "speed",
            "threads", "evidence"]
MAX_COUNTRIES = 1000  # потолка нет: нужны все страны продавца
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
_pages = {}


def page_text(url):
    if url not in _pages:
        try:
            raw = subprocess.run(["curl", "-sL", "--max-time", "25", "-A", UA, url],
                                 capture_output=True, timeout=40).stdout.decode("utf-8", "ignore")
        except Exception:
            raw = ""
        raw = re.sub(r"[\s  ]", "", raw)
        # запятая бывает и разделителем тысяч (1,500), и десятичной (1,67) — ищем в обоих прочтениях
        _pages[url] = raw.replace(",", "") + "\n" + raw.replace(",", ".")
    return _pages[url]


def digits(price):
    p = re.sub(r"[\s ,]", "", price)
    return p if re.fullmatch(r"\d+(\.\d+)?", p) else None


def main(path, min_domains):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter=";"))
    if rows[0] != COLS:
        sys.exit(f"FAIL: заголовок должен быть {';'.join(COLS)}")
    ok_domains, problems, seen, declared = set(), [], {}, {}
    for n, r in enumerate(rows[1:], 2):
        if len(r) != len(COLS):
            problems.append(f"строка {n}: полей {len(r)}, надо {len(COLS)}"); continue
        d = dict(zip(COLS, r))
        empty = [c for c in REQUIRED if not d[c].strip()]
        if empty:
            problems.append(f"строка {n} ({d['provider']}): пусто {empty}"); continue
        p = digits(d["price"])
        if not p:
            problems.append(f"строка {n} ({d['provider']}): цена не число: {d['price']!r}"); continue
        text = page_text(d["url"])
        if p not in text and p.rstrip("0").rstrip(".") not in text:
            problems.append(f"строка {n} ({d['provider']}): цены {p} нет на странице {d['url']}"); continue
        if not d["countries_total"].strip().isdigit():
            problems.append(f"строка {n} ({d['provider']}): countries_total не число"); continue
        ok_domains.add(urlparse(d["url"]).netloc.removeprefix("www."))
        seen.setdefault(d["provider"], set()).add(d["country"].strip().lower())
        declared[d["provider"]] = max(declared.get(d["provider"], 0), int(d["countries_total"]))
    for prov, total in declared.items():
        need = min(total, MAX_COUNTRIES)
        if seen[prov] & {"all", "все"}:  # единая цена для всех стран
            continue
        if len(seen[prov]) < need:
            problems.append(f"{prov}: стран с ценой {len(seen[prov])}, надо {need} (продаёт в {total})")
    for x in problems:
        print(x)
    print(f"Подтверждённых доменов: {len(ok_domains)} из нужных {min_domains}; проблемных строк: {len(problems)}")
    print("PASS" if len(ok_domains) >= min_domains and not problems else "FAIL")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
