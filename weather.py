# -*- coding: utf-8 -*-
"""Погода по выбранному городу и короткие советы для питомца."""
from __future__ import annotations

import json
import ssl
import urllib.request
from functools import lru_cache

# Область / город / координаты. Только крупные пункты, без сёл.
# id региона, название, id города, город, широта, долгота
_ROWS = [
    ("adygea", "Адыгея", "maykop", "Майкоп", 44.61, 40.11),
    ("altay", "Алтай", "gornoaltaysk", "Горно-Алтайск", 51.96, 85.96),
    ("altay-krai", "Алтайский край", "barnaul", "Барнаул", 53.35, 83.78),
    ("altay-krai", "Алтайский край", "biysk", "Бийск", 52.54, 85.20),
    ("amur", "Амурская область", "blagoveshchensk", "Благовещенск", 50.29, 127.53),
    ("arkhangelsk", "Архангельская область", "arkhangelsk", "Архангельск", 64.54, 40.54),
    ("arkhangelsk", "Архангельская область", "severodvinsk", "Северодвинск", 64.56, 39.83),
    ("astrakhan", "Астраханская область", "astrakhan", "Астрахань", 46.35, 48.04),
    ("bashkortostan", "Башкортостан", "ufa", "Уфа", 54.73, 55.97),
    ("bashkortostan", "Башкортостан", "sterlitamak", "Стерлитамак", 53.63, 55.95),
    ("belgorod", "Белгородская область", "belgorod", "Белгород", 50.60, 36.59),
    ("belgorod", "Белгородская область", "staryoskol", "Старый Оскол", 51.30, 37.84),
    ("bryansk", "Брянская область", "bryansk", "Брянск", 53.25, 34.37),
    ("buryatia", "Бурятия", "ulanude", "Улан-Удэ", 51.83, 107.61),
    ("vladimir", "Владимирская область", "vladimir", "Владимир", 56.13, 40.41),
    ("vladimir", "Владимирская область", "kovrov", "Ковров", 56.36, 41.32),
    ("volgograd", "Волгоградская область", "volgograd", "Волгоград", 48.72, 44.50),
    ("volgograd", "Волгоградская область", "volzhsky", "Волжский", 48.79, 44.78),
    ("vologda", "Вологодская область", "vologda", "Вологда", 59.22, 39.89),
    ("vologda", "Вологодская область", "cherepovets", "Череповец", 59.13, 37.90),
    ("voronezh", "Воронежская область", "voronezh", "Воронеж", 51.66, 39.20),
    ("dagestan", "Дагестан", "makhachkala", "Махачкала", 42.98, 47.50),
    ("dagestan", "Дагестан", "derbent", "Дербент", 42.07, 48.29),
    ("donetsk", "Донецкая Народная Республика", "donetsk", "Донецк", 48.02, 37.80),
    ("jewish", "Еврейская АО", "birobidzhan", "Биробиджан", 48.79, 132.92),
    ("zabaykalye", "Забайкальский край", "chita", "Чита", 52.03, 113.50),
    ("zaporizhzhia", "Запорожская область", "melitopol", "Мелитополь", 46.85, 35.37),
    ("ivanovo", "Ивановская область", "ivanovo", "Иваново", 57.00, 40.97),
    ("ingushetia", "Ингушетия", "magas", "Магас", 43.17, 44.81),
    ("irkutsk", "Иркутская область", "irkutsk", "Иркутск", 52.29, 104.28),
    ("irkutsk", "Иркутская область", "bratsk", "Братск", 56.13, 101.61),
    ("irkutsk", "Иркутская область", "angarsk", "Ангарск", 52.54, 103.89),
    ("kabardino", "Кабардино-Балкария", "nalchik", "Нальчик", 43.50, 43.62),
    ("kaliningrad", "Калининградская область", "kaliningrad", "Калининград", 54.71, 20.51),
    ("kalmykia", "Калмыкия", "elista", "Элиста", 46.31, 44.26),
    ("kaluga", "Калужская область", "kaluga", "Калуга", 54.53, 36.28),
    ("kaluga", "Калужская область", "obninsk", "Обнинск", 55.10, 36.61),
    ("kamchatka", "Камчатский край", "petropavlovsk", "Петропавловск-Камчатский", 53.04, 158.65),
    ("karachay", "Карачаево-Черкесия", "cherkessk", "Черкесск", 44.22, 42.06),
    ("karelia", "Карелия", "petrozavodsk", "Петрозаводск", 61.78, 34.35),
    ("kemerovo", "Кемеровская область", "kemerovo", "Кемерово", 55.33, 86.08),
    ("kemerovo", "Кемеровская область", "novokuznetsk", "Новокузнецк", 53.76, 87.11),
    ("kirov", "Кировская область", "kirov", "Киров", 58.60, 49.66),
    ("komi", "Коми", "syktyvkar", "Сыктывкар", 61.67, 50.84),
    ("komi", "Коми", "ukhta", "Ухта", 63.57, 53.68),
    ("kostroma", "Костромская область", "kostroma", "Кострома", 57.77, 40.93),
    ("krasnodar", "Краснодарский край", "krasnodar", "Краснодар", 45.04, 38.98),
    ("krasnodar", "Краснодарский край", "sochi", "Сочи", 43.60, 39.73),
    ("krasnodar", "Краснодарский край", "novorossiysk", "Новороссийск", 44.72, 37.77),
    ("krasnodar", "Краснодарский край", "armavir", "Армавир", 45.00, 41.12),
    ("krasnodar", "Краснодарский край", "anapa", "Анапа", 44.89, 37.32),
    ("krasnoyarsk", "Красноярский край", "krasnoyarsk", "Красноярск", 56.02, 92.87),
    ("krasnoyarsk", "Красноярский край", "norilsk", "Норильск", 69.35, 88.20),
    ("crimea", "Крым", "simferopol", "Симферополь", 44.95, 34.10),
    ("crimea", "Крым", "yalta", "Ялта", 44.50, 34.17),
    ("crimea", "Крым", "kerch", "Керчь", 45.36, 36.47),
    ("kurgan", "Курганская область", "kurgan", "Курган", 55.45, 65.33),
    ("kursk", "Курская область", "kursk", "Курск", 51.73, 36.19),
    ("leningrad", "Ленинградская область", "gatchina", "Гатчина", 59.58, 30.13),
    ("leningrad", "Ленинградская область", "vyborg", "Выборг", 60.71, 28.75),
    ("lipetsk", "Липецкая область", "lipetsk", "Липецк", 52.60, 39.57),
    ("lipetsk", "Липецкая область", "yelets", "Елец", 52.62, 38.50),
    ("lugansk", "Луганская Народная Республика", "lugansk", "Луганск", 48.57, 39.32),
    ("magadan", "Магаданская область", "magadan", "Магадан", 59.56, 150.80),
    ("mariel", "Марий Эл", "yoshkarola", "Йошкар-Ола", 56.64, 47.89),
    ("mordovia", "Мордовия", "saransk", "Саранск", 54.18, 45.17),
    ("moscow-city", "Москва", "moscow", "Москва", 55.76, 37.62),
    ("moscow-obl", "Московская область", "balashikha", "Балашиха", 55.81, 37.96),
    ("moscow-obl", "Московская область", "podolsk", "Подольск", 55.43, 37.54),
    ("moscow-obl", "Московская область", "khimki", "Химки", 55.89, 37.43),
    ("moscow-obl", "Московская область", "korolev", "Королёв", 55.92, 37.83),
    ("moscow-obl", "Московская область", "mytishchi", "Мытищи", 55.91, 37.73),
    ("moscow-obl", "Московская область", "lyubertsy", "Люберцы", 55.68, 37.89),
    ("moscow-obl", "Московская область", "krasnogorsk", "Красногорск", 55.82, 37.33),
    ("moscow-obl", "Московская область", "odintsovo", "Одинцово", 55.68, 37.28),
    ("moscow-obl", "Московская область", "serpukhov", "Серпухов", 54.92, 37.41),
    ("moscow-obl", "Московская область", "elektrostal", "Электросталь", 55.79, 38.45),
    ("moscow-obl", "Московская область", "kolomna", "Коломна", 55.08, 38.78),
    ("moscow-obl", "Московская область", "domodedovo", "Домодедово", 55.44, 37.75),
    ("murmansk", "Мурманская область", "murmansk", "Мурманск", 68.97, 33.09),
    ("murmansk", "Мурманская область", "apatity", "Апатиты", 67.57, 33.39),
    ("nenets", "Ненецкий АО", "naryanmar", "Нарьян-Мар", 67.64, 53.01),
    ("nizhegorod", "Нижегородская область", "nnovgorod", "Нижний Новгород", 56.33, 44.00),
    ("nizhegorod", "Нижегородская область", "dzerzhinsk", "Дзержинск", 56.24, 43.46),
    ("novgorod", "Новгородская область", "veliky-novgorod", "Великий Новгород", 58.52, 31.27),
    ("novosibirsk", "Новосибирская область", "novosibirsk", "Новосибирск", 55.03, 82.92),
    ("novosibirsk", "Новосибирская область", "berdsk", "Бердск", 54.76, 83.10),
    ("omsk", "Омская область", "omsk", "Омск", 54.99, 73.37),
    ("orenburg", "Оренбургская область", "orenburg", "Оренбург", 51.77, 55.10),
    ("orenburg", "Оренбургская область", "orsk", "Орск", 51.23, 58.47),
    ("orel", "Орловская область", "orel", "Орёл", 52.97, 36.06),
    ("penza", "Пензенская область", "penza", "Пенза", 53.20, 45.00),
    ("perm", "Пермский край", "perm", "Пермь", 58.01, 56.25),
    ("perm", "Пермский край", "berezniki", "Березники", 59.41, 56.82),
    ("primorye", "Приморский край", "vladivostok", "Владивосток", 43.12, 131.89),
    ("primorye", "Приморский край", "nakhodka", "Находка", 42.81, 132.87),
    ("primorye", "Приморский край", "ussuriysk", "Уссурийск", 43.80, 131.95),
    ("pskov", "Псковская область", "pskov", "Псков", 57.81, 28.33),
    ("rostov", "Ростовская область", "rostov", "Ростов-на-Дону", 47.23, 39.72),
    ("rostov", "Ростовская область", "taganrog", "Таганрог", 47.22, 38.90),
    ("rostov", "Ростовская область", "shakhty", "Шахты", 47.71, 40.21),
    ("rostov", "Ростовская область", "volgodonsk", "Волгодонск", 47.51, 42.16),
    ("ryazan", "Рязанская область", "ryazan", "Рязань", 54.63, 39.74),
    ("samara", "Самарская область", "samara", "Самара", 53.20, 50.15),
    ("samara", "Самарская область", "togliatti", "Тольятти", 53.53, 49.35),
    ("samara", "Самарская область", "syzran", "Сызрань", 53.16, 48.47),
    ("spb", "Санкт-Петербург", "spb", "Санкт-Петербург", 59.93, 30.32),
    ("saratov", "Саратовская область", "saratov", "Саратов", 51.53, 46.03),
    ("saratov", "Саратовская область", "engels", "Энгельс", 51.50, 46.12),
    ("sakha", "Саха (Якутия)", "yakutsk", "Якутск", 62.03, 129.73),
    ("sakhalin", "Сахалинская область", "yuzhnosakhalinsk", "Южно-Сахалинск", 46.96, 142.73),
    ("sverdlovsk", "Свердловская область", "ekaterinburg", "Екатеринбург", 56.84, 60.61),
    ("sverdlovsk", "Свердловская область", "nizhny-tagil", "Нижний Тагил", 57.92, 59.97),
    ("sverdlovsk", "Свердловская область", "kamensk", "Каменск-Уральский", 56.42, 61.93),
    ("sevastopol", "Севастополь", "sevastopol", "Севастополь", 44.62, 33.53),
    ("north-ossetia", "Северная Осетия", "vladikavkaz", "Владикавказ", 43.02, 44.68),
    ("smolensk", "Смоленская область", "smolensk", "Смоленск", 54.78, 32.05),
    ("stavropol", "Ставропольский край", "stavropol", "Ставрополь", 45.04, 41.97),
    ("stavropol", "Ставропольский край", "pyatigorsk", "Пятигорск", 44.05, 43.06),
    ("stavropol", "Ставропольский край", "kislovodsk", "Кисловодск", 43.91, 42.72),
    ("tambov", "Тамбовская область", "tambov", "Тамбов", 52.72, 41.45),
    ("tatarstan", "Татарстан", "kazan", "Казань", 55.79, 49.12),
    ("tatarstan", "Татарстан", "nabchelny", "Набережные Челны", 55.74, 52.40),
    ("tatarstan", "Татарстан", "nizhnekamsk", "Нижнекамск", 55.64, 51.82),
    ("tatarstan", "Татарстан", "almetyevsk", "Альметьевск", 54.90, 52.32),
    ("tver", "Тверская область", "tver", "Тверь", 56.86, 35.90),
    ("tomsk", "Томская область", "tomsk", "Томск", 56.48, 84.95),
    ("tomsk", "Томская область", "seversk", "Северск", 56.60, 84.85),
    ("tula", "Тульская область", "tula", "Тула", 54.20, 37.62),
    ("tula", "Тульская область", "novomoskovsk", "Новомосковск", 54.01, 38.28),
    ("tyva", "Тыва", "kyzyl", "Кызыл", 51.71, 94.45),
    ("tyumen", "Тюменская область", "tyumen", "Тюмень", 57.15, 65.53),
    ("tyumen", "Тюменская область", "tobolsk", "Тобольск", 58.20, 68.25),
    ("udmurtia", "Удмуртия", "izhevsk", "Ижевск", 56.85, 53.20),
    ("udmurtia", "Удмуртия", "sarapul", "Сарапул", 56.48, 53.80),
    ("ulyanovsk", "Ульяновская область", "ulyanovsk", "Ульяновск", 54.31, 48.39),
    ("ulyanovsk", "Ульяновская область", "dimitrovgrad", "Димитровград", 54.22, 49.57),
    ("khabarovsk", "Хабаровский край", "khabarovsk", "Хабаровск", 48.48, 135.07),
    ("khabarovsk", "Хабаровский край", "komsomolsk", "Комсомольск-на-Амуре", 50.55, 137.01),
    ("khakassia", "Хакасия", "abakan", "Абакан", 53.72, 91.44),
    ("khmao", "Ханты-Мансийский АО", "surgut", "Сургут", 61.25, 73.40),
    ("khmao", "Ханты-Мансийский АО", "nizhnevartovsk", "Нижневартовск", 60.93, 76.55),
    ("khmao", "Ханты-Мансийский АО", "khanty", "Ханты-Мансийск", 61.00, 69.02),
    ("kherson", "Херсонская область", "genichesk", "Геническ", 46.18, 34.80),
    ("chelyabinsk", "Челябинская область", "chelyabinsk", "Челябинск", 55.16, 61.40),
    ("chelyabinsk", "Челябинская область", "magnitogorsk", "Магнитогорск", 53.42, 59.05),
    ("chelyabinsk", "Челябинская область", "zlatoust", "Златоуст", 55.17, 59.67),
    ("chechnya", "Чечня", "grozny", "Грозный", 43.32, 45.69),
    ("chuvashia", "Чувашия", "cheboksary", "Чебоксары", 56.13, 47.25),
    ("chuvashia", "Чувашия", "novocheboksarsk", "Новочебоксарск", 56.11, 47.48),
    ("chukotka", "Чукотский АО", "anadyr", "Анадырь", 64.73, 177.51),
    ("yanao", "Ямало-Ненецкий АО", "novyurengoy", "Новый Уренгой", 66.08, 76.68),
    ("yanao", "Ямало-Ненецкий АО", "noyabrsk", "Ноябрьск", 63.20, 75.45),
    ("yaroslavl", "Ярославская область", "yaroslavl", "Ярославль", 57.63, 39.87),
    ("yaroslavl", "Ярославская область", "rybinsk", "Рыбинск", 58.04, 38.84),
]


def regions():
    out = []
    by_id = {}
    for rid, rname, cid, cname, lat, lon in _ROWS:
        block = by_id.get(rid)
        if not block:
            block = {"id": rid, "name": rname, "cities": []}
            by_id[rid] = block
            out.append(block)
        if any(c["id"] == cid for c in block["cities"]):
            continue
        block["cities"].append({"id": cid, "name": cname, "lat": lat, "lon": lon})
    out.sort(key=lambda r: r["name"])
    for block in out:
        block["cities"].sort(key=lambda c: c["name"])
    return out


@lru_cache(maxsize=1)
def all_cities():
    items = []
    for region in regions():
        for city in region["cities"]:
            items.append({**city, "regionId": region["id"], "regionName": region["name"]})
    return items


def find_city(city_id):
    return next((c for c in all_cities() if c["id"] == city_id), None)


def find_region(region_id):
    return next((r for r in regions() if r["id"] == region_id), None)


def icon_name(code):
    code = int(code or 0)
    if code == 0:
        return "WB_SUNNY"
    if code in (1, 2, 3):
        return "WB_CLOUDY"
    if code in (45, 48):
        return "FOGGY"
    if code in (71, 73, 75, 77, 85, 86):
        return "AC_UNIT"
    if code in (95, 96, 99):
        return "THUNDERSTORM"
    return "WATER_DROP"


def label(code):
    code = int(code or 0)
    if code == 0:
        return "ясно"
    if code == 1:
        return "почти ясно"
    if code in (2, 3):
        return "облачно"
    if code in (45, 48):
        return "туман"
    if code in (51, 53, 55, 56, 57):
        return "морось"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "дождь"
    if code in (71, 73, 75, 77, 85, 86):
        return "снег"
    if code in (95, 96, 99):
        return "гроза"
    return "пасмурно"


def tile_sub(snap):
    if not snap:
        return "город"
    temp = snap.get("temp")
    if temp is None:
        return "обновить"
    word = snap.get("word") or label(snap.get("code"))
    return f"{int(round(temp))}° · {word}"


def alert(snap):
    if not snap:
        return False
    temp = snap.get("temp")
    code = int(snap.get("code") or 0)
    if temp is not None and (temp >= 28 or temp <= -18):
        return True
    return code in (95, 96, 99)


POPULAR_IDS = (
    "moscow", "spb", "kazan", "novosibirsk", "ekaterinburg",
    "krasnodar", "sochi", "rostov", "ufa", "nnovgorod",
)


def popular_cities():
    by_id = {c["id"]: c for c in all_cities()}
    return [by_id[i] for i in POPULAR_IDS if i in by_id]


def fetch(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat:.3f}&longitude={lon:.3f}"
        "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,precipitation"
        "&wind_speed_unit=ms&timezone=auto"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Normalap/1.0"})
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    cur = raw.get("current") or {}
    code = cur.get("weather_code")
    temp = cur.get("temperature_2m")
    return {
        "temp": temp,
        "feels": cur.get("apparent_temperature"),
        "code": code,
        "wind": cur.get("wind_speed_10m"),
        "precip": cur.get("precipitation"),
        "word": label(code),
    }
