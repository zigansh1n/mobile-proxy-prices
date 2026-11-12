#!/usr/bin/env python3
"""Builds index.html (English, USD), ru/index.html (Russian, RUB) and README.md from data/tops/*.csv.
Run from the repository root: python3 scripts/build_site.py"""
import csv, html, json, os, re

URL = "https://zigansh1n.github.io/mobile-proxy-prices/"
REPO = "https://github.com/zigansh1n/mobile-proxy-prices"
E = html.escape
N_PROV, N_ROWS = 80, 4226

COUNTRY = {"Россия": "Russia", "США": "USA", "Великобритания": "United Kingdom", "Германия": "Germany",
           "Беларусь": "Belarus", "Казахстан": "Kazakhstan", "Болгария": "Bulgaria", "Грузия": "Georgia",
           "Португалия": "Portugal", "Румыния": "Romania", "Польша": "Poland", "Франция": "France",
           "Испания": "Spain", "Италия": "Italy", "Нидерланды": "Netherlands", "Таиланд": "Thailand",
           "Индия": "India", "Турция": "Turkey", "Узбекистан": "Uzbekistan", "Киргизия": "Kyrgyzstan",
           "Кыргызстан": "Kyrgyzstan", "Армения": "Armenia", "Латвия": "Latvia", "Литва": "Lithuania",
           "Эстония": "Estonia", "Молдова": "Moldova", "Израиль": "Israel", "Канада": "Canada",
           "Австралия": "Australia", "Вьетнам": "Vietnam", "Индонезия": "Indonesia", "Бразилия": "Brazil", "Украина": "Ukraine", "Словения": "Slovenia",
           "все": "all countries", "all": "all countries", "не указана": "not stated",
           "Россия (Санкт-Петербург)": "Russia (St. Petersburg)", "Россия (Москва)": "Russia (Moscow)"}
KIND = {"приватный": "dedicated", "общий": "shared", "не указан": "n/a"}
PERIOD = [(r"месяц(ев|а)?", "month"), (r"дн(ей|я)?\.?|день|дня", "days"), (r"недел[яиь]", "week"), (r"час(ов|а)?", "h")]

L = {
 "en": dict(
  lang="en", cur="$", col30="usd_per_30d", colday="usd_per_day", colgb="usd_per_gb", base="", canonical=URL,
  switch="RU", switch_url="ru/", switch_lang="ru",
  title=f"Mobile Proxy Prices Compared: {N_PROV} Providers (4G / LTE / 5G), November 2026",
  desc=f"How much do mobile proxies cost? Prices of {N_PROV} mobile proxy providers: {N_ROWS:,} plans by country and carrier, "
       "in USD, with the cheapest dedicated, shared, daily and per-GB plans. Shared from {S}, dedicated from {P} per month.",
  brand="Mobile proxies", brand2="prices", n_tops="Cheapest", n_all="All prices", n_faq="FAQ",
  h1=f"Mobile proxy prices of {N_PROV} providers, compared",
  sub=f"{N_ROWS:,} plans by country and carrier. Prices taken from the providers' own websites, in US dollars. November 2026",
  btn="See the cheapest", frm="from ", f1="shared, per month", f2="dedicated, per month", f3="per day",
  tops_h="Cheapest mobile proxies",
  tops_lead="Prices are converted to US dollars at the Bank of Russia rate of 13 November 2026 (1 USD = 82.98 RUB). "
            "Each list shows the best plan per provider and country. “from” means the provider only publishes a starting "
            "price, so the exact price for a country may be higher.",
  all_h=f"All {N_ROWS:,} plans", all_lead="Type a country or a provider to see the cheapest matching plans.",
  ph="Country or provider: USA, Germany, Russia, LTE Space…", ph_a="Country or provider", unit_a="Price unit",
  o30="per 30 days", oday="per day", ogb="per GB", kind_a="Access type", k_any="any type", k_priv="dedicated", k_sh="shared",
  status0="The table loads on your first query (2.5 MB). Without JavaScript, use the", status0_link="CSV file on GitHub",
  faq_h="FAQ", how_h="How the data was collected",
  s1="Found the providers", s1t="Across five sources: English and Russian web search, Telegram, Twitter/X and YouTube.",
  s2="Took prices from their websites", s2t="From the pricing page or the pricing calculator data. Prices quoted in reviews are not used.",
  s3="Verified every price with a script", s3t="It downloads the provider's page and looks for the number. No match, no row.",
  s4="Checked completeness", s4t="For every provider: are all countries, rental periods and plan types collected.",
  lim1="For 26 providers some prices are behind a login or bot protection; the reasons are listed in the",
  lim_link="completeness report", lim2="Only price is compared, not IP quality. This is not an advertisement.",
  foot1="Snapshot of 13 November 2026. Check the price on the provider's website before you buy.",
  foot2="Data and scripts on GitHub", foot3="Download Excel",
  heads=("#", "Provider", "Country", "Plan", "On the website"), full="Full list, {n} rows", tfrom="from", from_title="The website shows a starting price",
  tops=[("private", "Dedicated, per month", "$ per 30 days", "One modem or port for a single customer, 28–31 day rental."),
        ("shared", "Shared, per month", "$ per 30 days", "The channel is shared by several customers, so it costs 4–5 times less."),
        ("day", "Per day", "$ per day", "One-day rental."),
        ("gb", "Per GB", "$ per GB", "Pay-per-traffic pools. The lowest price usually applies to large plans only.")],
  rheads=("SHARED, MONTH", "DEDICATED, MONTH", "PER DAY", "PER GB"),
  rfoot=f"TOTAL: {N_PROV} providers<br>{N_ROWS:,} plans<br>2026-11-13",
  js=dict(enter="Type a country or a provider.", loading="Loading the table…", shown="Showing {a} of {b} options, cheapest first.",
          none="Nothing found. Try the country name in English or another price unit.", fail="Could not load the table.", **{"from": "from"}),
  faq=[("How much do mobile proxies cost?",
        "A shared mobile proxy starts at about $5.4 per month, a dedicated one (a modem for a single customer) at $16 per month, "
        "daily rental at about $1. Pay-per-GB pools start at $0.75 per GB."),
       ("What is the difference between dedicated and shared mobile proxies?",
        "A dedicated proxy is a separate modem with a SIM card for one customer. A shared one is used by several people at once, which is why it costs 4–5 times less."),
       ("Which is cheaper: unlimited rental or pay-per-GB?",
        "For accounts and browser work an unlimited time-based rental is usually cheaper; for scraping with little traffic a pay-per-GB pool is."),
       ("Which countries are covered?",
        "USA, United Kingdom, Germany, France, Poland, Russia, Kazakhstan, India and more than a hundred other countries."),
       ("Where do the prices come from, and can they be trusted?",
        "Only from the providers' own websites. Every price was verified by a script that downloads the provider's page and looks for the number. "
        "This is a snapshot of 13 November 2026, so check the provider's website before buying.")]),
 "ru": dict(
  lang="ru", cur="₽", col30="rub_per_30d", colday="rub_per_day", colgb="rub_per_gb", base="../", canonical=URL + "ru/",
  switch="EN", switch_url="../", switch_lang="en",
  title=f"Мобильные прокси: сравнение цен {N_PROV} продавцов (4G / LTE / 5G), ноябрь 2026",
  desc=f"Сколько стоят мобильные прокси: цены {N_PROV} продавцов, 4 226 тарифов по странам и операторам, пересчёт в рубли, "
       "топы самых дешёвых. Общие от {S}, приватные от {P} в месяц.",
  brand="Мобильные прокси", brand2="цены", n_tops="Топы", n_all="Все цены", n_faq="Вопросы",
  h1=f"Сравнение цен {N_PROV} продавцов мобильных прокси",
  sub="4 226 тарифов по странам и операторам. Цены с сайтов продавцов, в рублях. Ноябрь 2026",
  btn="Смотреть самые дешёвые", frm="от ", f1="общий, месяц", f2="приватный, месяц", f3="в день",
  tops_h="Самые дешёвые мобильные прокси",
  tops_lead="Цены пересчитаны в рубли по курсу ЦБ на 13.11.2026: 1 USD = 82,98 ₽. В каждом списке — одна лучшая строка на "
            "продавца и страну. Пометка «от» значит, что точная цена по стране может быть выше.",
  all_h="Все 4 226 тарифов", all_lead="Введите страну или продавца — покажем самые дешёвые подходящие тарифы.",
  ph="Страна или продавец: Россия, USA, LTE Space…", ph_a="Страна или продавец", unit_a="Единица цены",
  o30="за 30 дней", oday="за день", ogb="за гигабайт", kind_a="Тип доступа", k_any="любой тип", k_priv="приватный", k_sh="общий",
  status0="Таблица загрузится при первом запросе (2,5 МБ). Без скриптов —", status0_link="файл на GitHub",
  faq_h="Частые вопросы", how_h="Как собирали",
  s1="Нашли продавцов", s1t="По пяти источникам: русскоязычный и англоязычный веб, Telegram, Twitter и YouTube.",
  s2="Взяли цены с их сайтов", s2t="Со страницы тарифов или из данных калькулятора. Цены из обзоров не берутся.",
  s3="Проверили скриптом", s3t="Он скачивает страницу продавца и ищет на ней число. Нет числа — строка бракуется.",
  s4="Сверили полноту", s4t="По каждому продавцу: все ли страны, сроки и типы тарифов собраны.",
  lim1="У 26 продавцов часть цен закрыта личным кабинетом или защитой от роботов — причины в",
  lim_link="отчёте о полноте", lim2="Сравнивается только цена, а не качество адресов. Это не реклама.",
  foot1="Срез на 13 ноября 2026. Перед покупкой сверяйте цену на сайте продавца.",
  foot2="Данные и скрипты на GitHub", foot3="Скачать Excel",
  heads=("№", "Продавец", "Страна", "Тариф", "На сайте"), full="Полный список, {n} строк", tfrom="от", from_title="На сайте указано «от»",
  tops=[("private", "Приватные на месяц", "₽ за 30 дней", "Один модем или порт в одни руки, аренда на 28–31 день."),
        ("shared", "Общие на месяц", "₽ за 30 дней", "Канал делят несколько клиентов, поэтому он в 4–5 раз дешевле."),
        ("day", "На день", "₽ за день", "Аренда на сутки."),
        ("gb", "За гигабайт", "₽ за ГБ", "Пулы с оплатой за трафик. Минимальная цена обычно только на больших пакетах.")],
  rheads=("ОБЩИЕ, МЕСЯЦ", "ПРИВАТНЫЕ, МЕСЯЦ", "НА ДЕНЬ", "ЗА ГИГАБАЙТ"),
  rfoot=f"ИТОГО: {N_PROV} продавцов<br>4 226 тарифов<br>13.11.2026",
  js=dict(enter="Введите страну или продавца.", loading="Загружаю таблицу…", shown="Показано {a} из {b} вариантов, по возрастанию цены.",
          none="Ничего не нашлось. Попробуйте название страны по-английски или другую единицу.", fail="Не удалось загрузить таблицу.", **{"from": "от"}),
  faq=[("Сколько стоят мобильные прокси в России?",
        "Общий канал — от 449–500 ₽ в месяц, приватный (один модем в одни руки) — от 1 790–2 500 ₽ в месяц, на день — от 90–150 ₽."),
       ("Чем приватные мобильные прокси отличаются от общих?",
        "Приватный канал — отдельный модем с SIM-картой для одного клиента. Общий делят несколько человек, поэтому он в 4–5 раз дешевле."),
       ("Что дешевле: аренда на срок или оплата за гигабайты?",
        "Для аккаунтов и работы в браузере обычно выгоднее безлимитная аренда на срок, для парсинга с небольшим трафиком — пул с оплатой за гигабайты."),
       ("Какие страны есть в сравнении?",
        "Россия, Казахстан, Беларусь, США, Великобритания, Германия, Франция, Польша, Индия и ещё более ста стран."),
       ("Откуда взяты цены и можно ли им верить?",
        "Только с сайтов продавцов. Каждую цену проверил скрипт: он скачивает страницу продавца и ищет на ней это число. "
        "Это срез на 13 ноября 2026 года — перед покупкой сверяйтесь с сайтом.")]),
}
FILES = {"private": "tops/month_private.csv", "shared": "tops/month_shared.csv", "day": "tops/day.csv", "gb": "tops/per_gb.csv"}
COLKEY = {"private": "col30", "shared": "col30", "day": "colday", "gb": "colgb"}


def rd(f):
    return list(csv.DictReader(open("data/" + f, encoding="utf-8")))


RAW = {k: [r for r in rd(f) if "своя sim" not in r["access"].lower()] for k, f in FILES.items()}


def money(v, t):
    v = float(v)
    if t["cur"] == "$":
        return "$" + (f"{v:.2f}" if v < 100 else f"{v:,.0f}")
    return f"{v:,.0f}".replace(",", " ") + " ₽"


def tr_country(c, t):
    if " стран: " in c:
        n, rest = c.split(" стран: ", 1)
        names = list(dict.fromkeys(tr_country(x, t) if t["lang"] == "en" else x.replace("Russia", "Россия") for x in rest.split(", ")))
        if len(names) <= 3:
            return ", ".join(names)
        return (f"{n} countries: " if t["lang"] == "en" else f"{n} стран: ") + ", ".join(names[:3]) + "…"
    return COUNTRY.get(c, c) if t["lang"] == "en" else c


PLAN = [("Выделенное устройство", "Dedicated device"), ("Много городов", "many cities"), ("без ожидания", "no wait"),
        ("[Мм]обильные прокси", "Mobile proxies"), ("[Мм]обильны[ей]", "Mobile"), ("[Пп]риватны[ейх]", "dedicated"),
        ("[Ии]ндивидуальные", "dedicated"), ("[Оо]бщи[йе]|шаред", "shared"), ("[Пп]убличный", "public"), ("мультипорт", "multiport"),
        ("мультирегион", "multi-region"), ("канал", "channel"), ("Россия", "Russia"), ("США", "USA"), ("дней", "days"), ("Спб", "St. Petersburg"),
        ("Москва", "Moscow"), ("Болгария", "Bulgaria"), ("Беларусь", "Belarus"), ("Казахстан", "Kazakhstan")]


def tr_plan(p, t):
    if t["lang"] == "en":
        for a, b in PLAN:
            p = re.sub(a, b, p)
    return p


def tr_period(p, t):
    if t["lang"] == "en":
        for a, b in PERIOD:
            p = re.sub(a, b, p)
    return p[:18]


def table(key, t):
    _, title, unit, note = next(x for x in t["tops"] if x[0] == key)
    col, rows, h = t[COLKEY[key]], RAW[key], t["heads"]
    out = [f'<section class="top" id="top-{key}" data-top="{key}"><h3>{title}</h3><p class="note">{note} '
           f'<a href="{REPO}/blob/main/data/{FILES[key]}">{t["full"].format(n=len(rows))}</a></p>',
           f'<div class="ledger"><div class="row head"><span>{h[0]}</span><span>{h[1]}</span><span>{h[2]}</span>'
           f'<span>{h[3]}</span><span class="r">{unit}</span><span>{h[4]}</span></div>']
    for i, r in enumerate(rows[:12], 1):
        frm = f' <i class="from" title="{t["from_title"]}">{t["tfrom"]}</i>' if r["price_kind"] == "от" else ""
        out.append(
            f'<div class="row"><span class="n">{i:02d}</span>'
            f'<span class="p"><a href="{E(r["url"])}" rel="nofollow noopener" target="_blank">{E(r["provider"])}</a></span>'
            f'<span class="c">{E(tr_country(r["country"], t))}</span><span class="t">{E(tr_plan(r["tariff"], t)[:44])}</span>'
            f'<span class="r"><b>{money(r[col], t)}</b>{frm}</span>'
            f'<span class="s">{float(r["price"]):g} {E(r["currency"])} · {E(tr_period(r["period"], t))}</span></div>')
    out.append("</div></section>")
    return "\n".join(out)


def rc(key, n, t, exact=False):
    """Receipt lines: one per provider."""
    seen, out = set(), []
    for r in RAW[key]:
        if r["domain"] in seen or (exact and r["price_kind"] == "от"):
            continue
        seen.add(r["domain"])
        out.append((re.sub(r"\.(com|ru|net|io)$", "", r["provider"]), r[t[COLKEY[key]]]))
        if len(out) == n:
            break
    return out


def page(t):
    rec = list(zip(t["rheads"], [rc("shared", 3, t), rc("private", 3, t), rc("day", 3, t, True), rc("gb", 2, t, True)]))
    lines, k = [], 0
    for hi, (head, items) in enumerate(rec):
        lines.append(f'<p class="rh" style="--i:{k}">{head}</p>'); k += 1
        for j, (name, v) in enumerate(items):
            mark = ' class="hit"' if hi == 0 and j == 0 else ""
            lines.append(f'<p class="rl" style="--i:{k}"><span>{E(name)}</span><i></i><b{mark}>{money(v, t)}</b></p>'); k += 1
    lines.append(f'<p class="rf" style="--i:{k}">{t["rfoot"]}</p>')
    fs, fp, fd = (t["frm"] + money(x, t) for x in (rec[0][1][0][1], rec[1][1][0][1], rec[2][1][0][1]))
    desc = t["desc"].replace("{S}", money(rec[0][1][0][1], t)).replace("{P}", money(rec[1][1][0][1], t))
    ld = [{"@context": "https://schema.org", "@type": "Dataset", "name": t["title"], "description": desc, "url": t["canonical"],
           "inLanguage": t["lang"], "license": "https://creativecommons.org/licenses/by/4.0/", "dateModified": "2026-11-13",
           "keywords": ["mobile proxy prices", "mobile proxies", "4G proxy", "LTE proxy", "5G proxy", "cheap mobile proxies",
                        "мобильные прокси", "цены на мобильные прокси"],
           "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv",
                             "contentUrl": "https://raw.githubusercontent.com/zigansh1n/mobile-proxy-prices/main/data/prices.csv"}]},
          {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]}]
    h = t["heads"]
    cfg = {"cur": t["cur"], "u30": t["col30"], "uday": t["colday"], "cm": COUNTRY if t["lang"] == "en" else {},
           "k": KIND if t["lang"] == "en" else {},
           "t": dict(t["js"], head=f'<div class="row head"><span>{h[0]}</span><span>{h[1]}</span><span>{h[2]}</span><span>{h[3]}</span>'
                                   f'<span class="r">{t["cur"]}</span><span>{h[4]}</span></div>')}
    s = open("scripts/site_template.html", encoding="utf-8").read()
    s = (s.replace("{{RECEIPT}}", "\n".join(lines)).replace("{{TOPS}}", "\n".join(table(k, t) for k in FILES))
         .replace("{{TABS}}", "".join(f'<button data-tab="{k}"{" class=on" if i == 0 else ""}>{ti}</button>' for i, (k, ti, *_) in enumerate(t["tops"])))
         .replace("{{FAQ}}", "\n".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in t["faq"]))
         .replace("{{LD}}", json.dumps(ld, ensure_ascii=False)).replace("{{F_SHARED}}", fs).replace("{{F_PRIVATE}}", fp)
         .replace("{{F_DAY}}", fd).replace("{{URL}}", URL).replace("{{REPO}}", REPO)
         .replace("[[cfg]]", json.dumps(cfg, ensure_ascii=False)).replace("[[desc]]", E(desc))
         .replace("[[u30]]", t["col30"]).replace("[[uday]]", t["colday"]).replace("[[ugb]]", t["colgb"]))
    for k, v in t.items():
        if isinstance(v, str):
            s = s.replace(f"[[{k}]]", v)
    left = re.findall(r"\[\[\w+\]\]", s)
    assert not left, left[:5]
    return s, rec


def readme(t, rec):
    def tbl(key, n=10):
        col = t[COLKEY[key]]
        out = ["| # | Provider | Country | Price | On the website | Plan | Accuracy |", "|---|---|---|---:|---|---|---|"]
        for i, r in enumerate(RAW[key][:n], 1):
            out.append(f"| {i} | [{r['provider']}](https://{r['domain']}) | {tr_country(r['country'], t).replace('|', '/')} | **{money(r[col], t)}** | "
                       f"{float(r['price']):g} {r['currency']} / {tr_period(r['period'], t).replace('|', '/')} | {tr_plan(r['tariff'], t)[:38].replace('|', '/')} | "
                       f"{'from' if r['price_kind'] == 'от' else 'exact'} |")
        return "\n".join(out)
    m = lambda i: money(rec[i][1][0][1], t)
    return f"""# Mobile Proxy Prices Compared: {N_PROV} Providers (4G / LTE / 5G), November 2026

**How much do mobile proxies cost, and where are they cheapest?** A price comparison of **{N_PROV} mobile proxy providers**: **{N_ROWS:,} plans** by country and carrier, in US dollars, with lists of the cheapest dedicated, shared, daily and pay-per-GB plans. Prices were collected from the providers' own websites on 12–13 November 2026.

🌐 **Website with search:** [zigansh1n.github.io/mobile-proxy-prices]({URL}) · 🇷🇺 [Русская версия](README.ru.md) · [сайт на русском]({URL}ru/)

Every row lists the country, carrier (T-Mobile, Verizon, Vodafone, O2, Three, MTS, Beeline and others), access type (dedicated or shared), rental period, price in the original currency, in USD and in RUB, traffic limit, IP rotation method and the URL of the page where the price is published.

Every price was verified by a script: it downloads the source page and looks for the number on it. Prices quoted in reviews, rankings or search snippets are not included.

**At a glance:**
- dedicated mobile proxies per month: from **{m(1)}** (Germany, United Kingdom, USA);
- shared mobile proxies per month: from **{m(0)}**;
- daily dedicated mobile proxies: from **{m(2)}**;
- pay-per-GB mobile proxy pools: from **{m(3)} per GB**.

| | |
|---|---|
| Providers | {N_PROV} |
| Pricing rows | {N_ROWS:,} |
| Recommendations from YouTube and Twitter/X | {len(rd('recommendations.csv'))} |
| Comments and replies rated as substantiated or not | {len(rd('comments.csv'))} |
| Collected | 12–13 November 2026 |

Download everything as one workbook: [`mobile_proxies.xlsx`](mobile_proxies.xlsx).

## Cheapest mobile proxies

Prices are converted to US dollars at the Bank of Russia rate of 13 November 2026 (1 USD = 82.98 RUB, 1 EUR = 92.33 RUB). Plans are sold in different units, so there are four lists. Each shows the best plan per provider and country; identical prices in several countries are merged into one row.

### Cheapest dedicated mobile proxies per month

One modem or port for a single customer, 28–31 day rental. Full list: [`data/tops/month_private.csv`](data/tops/month_private.csv).

{tbl('private', 15)}

### Cheapest shared mobile proxies per month

The channel is shared by several customers. Full list: [`data/tops/month_shared.csv`](data/tops/month_shared.csv).

{tbl('shared')}

### Cheapest mobile proxies per day

Full list: [`data/tops/day.csv`](data/tops/day.csv).

{tbl('day')}

### Cheapest pay-per-GB mobile proxies

Traffic-based pools. The lowest price usually applies to large plans only. Full list: [`data/tops/per_gb.csv`](data/tops/per_gb.csv).

{tbl('gb')}

## FAQ

""" + "\n\n".join(f"**{q}** {a}" for q, a in t["faq"]) + f"""

## What is in the repository

| File | Contents |
|---|---|
| [`mobile_proxies.xlsx`](mobile_proxies.xlsx) | All sheets in one workbook, with filters |
| [`data/prices.csv`](data/prices.csv) | All prices: provider, country, carrier, network, access type, protocols, plan, period, price, USD and RUB, traffic, IP rotation, speed, threads, source URL, quote from the page |
| [`data/providers.csv`](data/providers.csv) | Summary per provider: sources, number of countries, number of rows |
| [`data/tops/`](data/tops) | The four cheapest-plan lists in full |
| [`data/completeness_report.csv`](data/completeness_report.csv) | Per provider: countries, periods and plan types on the website versus collected, and the reason for any gap |
| [`data/unverified.csv`](data/unverified.csv) | Providers whose prices could not be verified, with the reason |
| [`data/recommendations.csv`](data/recommendations.csv) | Advice from YouTube transcripts and Twitter/X: quote, link, one-line summary |
| [`data/comments.csv`](data/comments.csv) | YouTube comments and replies to tweets, marked substantiated or not |
| [`data/twitter_mentions.csv`](data/twitter_mentions.csv) | Discounts, promo codes, complaints and announcements from tweets |
| [`data/youtube_videos.csv`](data/youtube_videos.csv) | List of the videos reviewed |
| [`scripts/check.py`](scripts/check.py) | Acceptance script: checks that every price is present on its source page |
| [`scripts/merge.py`](scripts/merge.py), [`scripts/rub.py`](scripts/rub.py) | Merging sources, currency conversion, cheapest-plan lists |
| [`scripts/build_site.py`](scripts/build_site.py) | Builds the website and this README from the data |

Column names are in English. Values are in the language of the source: plan names, notes and summaries of Russian-language sources are in Russian. `kind` is `приватный` (dedicated) or `общий` (shared); `price_kind` is `точная` (exact) or `от` (starting price).

## How the data was collected

1. **Finding providers** across five sources: English and Russian web search, Telegram, Twitter/X and YouTube (transcripts, descriptions and comments).
2. **Prices only from the provider's website**: the pricing page, the calculator data embedded in the page, or the open endpoint the calculator loads it from.
3. **Script acceptance.** `check.py` downloads the URL in the `url` column and looks for the number from the `price` column. A row without a match is rejected. It also checks required fields and that all countries the provider sells are covered.
4. **Completeness check.** For every provider the collected countries, rental periods and plan types were compared with the website. The result is in `completeness_report.csv`.

To check any file in the same format (19 columns separated by `;`):

```bash
python3 scripts/check.py my_prices.csv 1
```

## Limitations

- **Starting prices.** Some providers only publish a “from” price; the exact price for a country is visible after login. Such rows are marked in `price_kind`.
- **Incomplete providers.** For 26 of {N_PROV} providers some prices are behind a login, bot protection or simply not published. See `completeness_report.csv`.
- **Per-GB unit** (package price versus price of one gigabyte) was derived by rules in `rub.py` and not checked row by row.
- **Recommendations and comments** are not script-verified. Quotes were spot-checked against the originals; the “substantiated” mark was assigned by a language model. Quotes from auto-generated subtitles may contain errors.
- **Snapshot.** Prices and availability change; check the provider's website via the link in the row before buying.
- This is not an advertisement and not a quality ranking: only price is compared.

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Scripts: MIT. Quotes belong to their authors and are given with a link to the source.
"""


if __name__ == "__main__":
    en, rec_en = page(L["en"])
    open("index.html", "w", encoding="utf-8").write(en)
    os.makedirs("ru", exist_ok=True)
    ru, _ = page(L["ru"])
    open("ru/index.html", "w", encoding="utf-8").write(ru)
    open("README.md", "w", encoding="utf-8").write(readme(L["en"], rec_en))
    print("en", len(en), "ru", len(ru), [(h, [(n, v) for n, v in it]) for h, it in rec_en])
