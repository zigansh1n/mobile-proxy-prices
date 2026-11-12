#!/usr/bin/env python3
"""Собирает index.html из data/tops/*.csv. Запуск из корня репозитория: python3 scripts/build_site.py"""
import csv, html, json, re

URL = "https://zigansh1n.github.io/mobile-proxy-prices/"
REPO = "https://github.com/zigansh1n/mobile-proxy-prices"
E = html.escape


def rd(f):
    return list(csv.DictReader(open("data/" + f, encoding="utf-8")))


def money(v):
    return f"{float(v):,.0f}".replace(",", " ")


def country(c):
    if " стран: " in c:
        n, rest = c.split(" стран: ", 1)
        names = list(dict.fromkeys(x.replace("Russia", "Россия") for x in rest.split(", ")))
        return ", ".join(names) if len(names) <= 3 else f"{n} стран: {', '.join(names[:3])}…"
    return c


TOPS = [
    ("private", "Приватные на месяц", "tops/month_private.csv", "rub_per_30d", "₽ за 30 дней",
     "Один модем или порт в одни руки, аренда на 28–31 день."),
    ("shared", "Общие на месяц", "tops/month_shared.csv", "rub_per_30d", "₽ за 30 дней",
     "Канал делят несколько клиентов, поэтому он в 4–5 раз дешевле."),
    ("day", "На день", "tops/day.csv", "rub_per_day", "₽ за день", "Аренда на сутки."),
    ("gb", "За гигабайт", "tops/per_gb.csv", "rub_per_gb", "₽ за ГБ",
     "Пулы с оплатой за трафик. Минимальная цена обычно только на больших пакетах."),
]
data = {}
for key, _, f, col, _, _ in TOPS:
    rows = [r for r in rd(f) if "своя sim" not in r["access"].lower()]
    data[key] = [(r, float(r[col])) for r in rows]


def table(key, title, f, col, unit, note, n=12):
    out = [f'<section class="top" id="top-{key}" data-top="{key}"><h3>{title}</h3><p class="note">{note} '
           f'<a href="{REPO}/blob/main/data/{f}">Полный список, {len(data[key])} строк</a></p>',
           f'<div class="ledger"><div class="row head"><span>№</span><span>Продавец</span><span>Страна</span>'
           f'<span>Тариф</span><span class="r">{unit}</span><span>На сайте</span></div>']
    for i, (r, v) in enumerate(data[key][:n], 1):
        frm = ' <i class="from" title="На сайте указано «от»">от</i>' if r["price_kind"] == "от" else ""
        out.append(
            f'<div class="row"><span class="n">{i:02d}</span>'
            f'<span class="p"><a href="{E(r["url"])}" rel="nofollow noopener" target="_blank">{E(r["provider"])}</a></span>'
            f'<span class="c">{E(country(r["country"]))}</span><span class="t">{E(r["tariff"][:44])}</span>'
            f'<span class="r"><b>{money(v)}</b>{frm}</span>'
            f'<span class="s">{float(r["price"]):g} {E(r["currency"])} · {E(r["period"][:18])}</span></div>')
    out.append("</div></section>")
    return "\n".join(out)


def rc(key, n, exact=False):
    """Строки чека: одна на продавца."""
    seen, out = set(), []
    for r, v in data[key]:
        if r["domain"] in seen or (exact and r["price_kind"] == "от"):
            continue
        seen.add(r["domain"])
        out.append((re.sub(r"\.(com|ru|net|io)$", "", r["provider"]), v))
        if len(out) == n:
            break
    return out


receipt = [("ОБЩИЕ, МЕСЯЦ", rc("shared", 3)), ("ПРИВАТНЫЕ, МЕСЯЦ", rc("private", 3)),
           ("НА ДЕНЬ", rc("day", 3, exact=True)), ("ЗА ГИГАБАЙТ", rc("gb", 2, exact=True))]
best = {k: data[k][0][1] for k in data}
best_day = rc("day", 1, exact=True)[0][1]
lines, k = [], 0
for head, items in receipt:
    lines.append(f'<p class="rh" style="--i:{k}">{head}</p>'); k += 1
    for j, (name, v) in enumerate(items):
        mark = ' class="hit"' if head.startswith("ОБЩИЕ") and j == 0 else ""
        lines.append(f'<p class="rl" style="--i:{k}"><span>{E(name)}</span><i></i><b{mark}>{money(v)} ₽</b></p>'); k += 1
lines.append(f'<p class="rf" style="--i:{k}">ИТОГО: 80 продавца<br>4 226 тарифов<br>13.11.2026</p>')

FAQ = [
    ("Сколько стоят мобильные прокси в России?",
     "Общий канал — от 449–500 ₽ в месяц, приватный (один модем в одни руки) — от 1 790–2 500 ₽ в месяц, на день — от 90–150 ₽."),
    ("Чем приватные мобильные прокси отличаются от общих?",
     "Приватный канал — отдельный модем с SIM-картой для одного клиента. Общий делят несколько человек, поэтому он в 4–5 раз дешевле."),
    ("Что дешевле: аренда на срок или оплата за гигабайты?",
     "Для аккаунтов и работы в браузере обычно выгоднее безлимитная аренда на срок, для парсинга с небольшим трафиком — пул с оплатой за гигабайты."),
    ("Какие страны есть в сравнении?",
     "Россия, Украина, Казахстан, Беларусь, США, Великобритания, Германия, Франция, Польша, Индия и ещё более ста стран."),
    ("Откуда взяты цены и можно ли им верить?",
     "Только с сайтов продавцов. Каждую цену проверил скрипт: он скачивает страницу продавца и ищет на ней это число. Это срез на 13 ноября 2026 года — перед покупкой сверяйтесь с сайтом."),
]
ld = [{"@context": "https://schema.org", "@type": "Dataset", "name": "Цены на мобильные прокси: 80 продавца, ноябрь 2026",
       "description": "Сравнение цен 80 продавцов мобильных прокси 4G/LTE/5G: 4 226 тарифов по странам и операторам, пересчёт в рубли.",
       "url": URL, "inLanguage": "ru", "license": "https://creativecommons.org/licenses/by/4.0/", "dateModified": "2026-11-13",
       "keywords": ["мобильные прокси", "цены на мобильные прокси", "mobile proxy prices", "4G proxy", "LTE proxy"],
       "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv",
                         "contentUrl": "https://raw.githubusercontent.com/zigansh1n/mobile-proxy-prices/main/data/prices.csv"}]},
      {"@context": "https://schema.org", "@type": "FAQPage",
       "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}]

tpl = open("scripts/site_template.html", encoding="utf-8").read()
page = (tpl.replace("{{RECEIPT}}", "\n".join(lines))
        .replace("{{TOPS}}", "\n".join(table(*t) for t in TOPS))
        .replace("{{TABS}}", "".join(f'<button data-tab="{k}"{" class=on" if i == 0 else ""}>{t}</button>' for i, (k, t, *_) in enumerate(TOPS)))
        .replace("{{FAQ}}", "\n".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in FAQ))
        .replace("{{LD}}", json.dumps(ld, ensure_ascii=False))
        .replace("{{F_SHARED}}", money(best["shared"])).replace("{{F_PRIVATE}}", money(best["private"]))
        .replace("{{F_DAY}}", money(best_day)).replace("{{URL}}", URL).replace("{{REPO}}", REPO))
open("index.html", "w", encoding="utf-8").write(page)
print("index.html", len(page), "байт; чек:", [(h, [(n, round(v)) for n, v in it]) for h, it in receipt])
