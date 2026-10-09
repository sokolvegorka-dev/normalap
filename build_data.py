# -*- coding: utf-8 -*-
"""Собирает catalog.json, копирует фото пород и обновляет Excel-анализы."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from foods_catalog import FOODS

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
EXTRACT = WORKSPACE / "_extract"
ANALYSIS = WORKSPACE / "анализ"
PHOTOS = ANALYSIS / "фотки кошек"
DOG_PHOTOS = ANALYSIS / "фотки собак"
DATA = ROOT / "data"
ASSETS = ROOT / "assets" / "breeds"

PHOTO_MAP = {
    "cat-01": "экзотическая кошка.jpeg",
    "cat-02": "британская короткошерстная.jpg",
    "cat-03": "американская короткошерстная.jpg",
    "cat-04": "ориентальная.jpg",
    "cat-05": "девон рекс.jpg",
    "cat-06": "корниш рекс.jpg",
    "cat-07": "норвежская лесная.jpg",
    "cat-08": "бирманская.jpg",
    "cat-09": "тонкинская кошка.jpg",
    "cat-10": "бурманская.jpg",
    "cat-11": "оцикет.jpg",
    "cat-12": "русская голубая.jpg",
    "cat-13": "скоттиш страйт.jpg",
    "cat-14": "персидская.jpg",
    "cat-15": "донской сфинкс.jpg",
    "cat-16": "рэгдолл.jpg",
    "cat-17": "канадский сфинкмс.jpg",
    "cat-18": "тайская.jpg",
    "cat-19": "сибирская.jpg",
    "cat-20": "бенгальская кошка.jpg",
    "cat-21": "сиамская.jpg",
    "cat-22": "абиссинская.jpg",
    "cat-23": "шотландская вислоухая.jpg",
    "cat-24": "мейн кун.jpg",
    "cat-25": "курильский бобтйл.jpg",
    "cat-26": "невская маскарадная.jpg",
}

DOG_PHOTO_MAP = {
    "dog-01": "Немецкий шпиц.jpg",
    "dog-02": "чихуахуа.jpg",
    "dog-03": "Вельш-корги.jpg",
    "dog-04": "пудель.jpeg",
    "dog-05": "немецкая овчарка.jpg",
    "dog-06": "кавалер кинг чарльз.jpg",
    "dog-07": "йоркширский терьер.jpg",
    "dog-08": "лабрадор ретривер.png",
    "dog-09": "алабай.jpg",
    "dog-10": "джек рассел.jpg",
    "dog-11": "бульдог.jpg",
    "dog-12": "золотистый ретривер.jpg",
    "dog-13": "такса.jpg",
    "dog-14": "мопс.jpg",
    "dog-15": "бигль.png",
    "dog-16": "боксер.jpg",
    "dog-17": "доберман.jpg",
    "dog-19": "хаски.jpeg",
    "dog-20": "далматин.jpg",
    "dog-21": "бультерьер.jpg",
    "dog-22": "эльдертерьер.jpg",
    "dog-23": "ротвейлер.jpg",
    "dog-24": "сиба ину.jpg",
    "dog-25": "чау чау.jpg",
}

MED_LABEL = {
    "ckd": "почки (ХБП)",
    "heart": "сердце",
    "overweight": "лишний вес",
    "allergy": "аллергия",
    "gi": "ЖКТ",
    "urolithiasis": "МКБ",
    "liver": "печень",
    "diabetes": "диабет",
    "joints": "суставы",
}


def load_breeds():
    extract_cats = EXTRACT / "CATS.json"
    if extract_cats.exists():
        cats = json.loads(extract_cats.read_text(encoding="utf-8"))
        dogs = json.loads((EXTRACT / "DOGS.json").read_text(encoding="utf-8"))
        return cats, dogs
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    return catalog["cats"], catalog["dogs"]


def names(foods, limit=10):
    return [f["name"] for f in foods[:limit]]


def numbered(foods, limit=10):
    return "\n".join(f"{i}. {f['name']}" for i, f in enumerate(foods[:limit], 1))


def compositions_block(foods, limit=10):
    lines = []
    for i, f in enumerate(foods[:limit], 1):
        lines.append(f"{i}. {f['name']}\n   Состав: {f['composition']}")
    return "\n".join(lines)


def pick_healthy(species, breed_id, extra=None):
    extra = extra or []
    scored = []
    for f in FOODS:
        if f["species"] != species:
            continue
        if "healthy" not in f["tags"]:
            continue
        if "kitten" in f["tags"] or "puppy" in f["tags"]:
            continue
        if any(t.startswith("medical:") for t in f["tags"]):
            continue
        score = 10 if breed_id in f["breedIds"] else 0
        if f["id"] in extra:
            score += 20
        score += {"premium": 8, "mid": 5, "budget": 2}[f["tier"]]
        if f.get("highEnergy"):
            score += 1
        scored.append((score, f["name"], f))
    scored.sort(key=lambda x: (-x[0], x[1]))
    picked, seen = [], set()

    def take(tier, n):
        for _, _, f in scored:
            if len(picked) >= 10 or n <= 0:
                return
            if f["id"] in seen:
                continue
            if tier and f["tier"] != tier:
                continue
            picked.append(f)
            seen.add(f["id"])
            n -= 1

    take("premium", 8)
    take("mid", 4)
    take(None, 16)
    dry = [f for f in picked if f.get("form") != "wet"]
    wet = [f for f in picked if f.get("form") == "wet"]
    mixed, i, j = [], 0, 0
    while len(mixed) < 10 and (i < len(dry) or j < len(wet)):
        if i < len(dry):
            mixed.append(dry[i]); i += 1
        if len(mixed) < 10 and j < len(wet):
            mixed.append(wet[j]); j += 1
    if len(mixed) < 10:
        for f in picked:
            if f["id"] not in {x["id"] for x in mixed}:
                mixed.append(f)
            if len(mixed) >= 10:
                break
    return mixed[:10]


def pick_sterilised(species):
    foods = [f for f in FOODS if f["species"] == species and "sterilised" in f["tags"]]
    foods.sort(key=lambda f: ({"premium": 0, "mid": 1, "budget": 2}[f["tier"]], f["name"]))
    return foods[:8]


def pick_medical(species, diag_code):
    tag = f"medical:{diag_code}"
    foods = [f for f in FOODS if f["species"] == species and tag in f["tags"]]
    foods.sort(key=lambda f: f["name"])
    return foods


def attach_foods(breeds, species):
    ster = pick_sterilised(species)
    for b in breeds:
        healthy = pick_healthy(species, b["id"])
        b["healthyFoods"] = names(healthy)
        b["sterilisedFoods"] = names(ster)
        for item in b.get("medicalByDisease") or []:
            code = item.get("diagCode")
            if code and code != "other":
                item["foods"] = names(pick_medical(species, code), limit=5)
            elif not item.get("foods"):
                item["foods"] = []
        b["_healthyObjs"] = healthy
        b["_sterObjs"] = ster
        b["_medMap"] = {
            item.get("diagCode"): pick_medical(species, item.get("diagCode"))
            for item in (b.get("medicalByDisease") or [])
            if item.get("diagCode") and item.get("diagCode") != "other"
        }
    return breeds


def medical_text(breed):
    lines = []
    for item in breed.get("medicalByDisease") or []:
        label = item.get("label") or MED_LABEL.get(item.get("diagCode"), "")
        foods = item.get("foods") or []
        if foods:
            lines.append(f"При {label}: " + ", ".join(foods))
        else:
            lines.append(f"При {label}: специальной лечебной линейки нет — важны форма гранулы и контроль веса, решение за ветеринаром")
    return "\n".join(lines) if lines else "Лечебный корм — только после диагноза ветеринара"


def medical_comp(breed):
    blocks = []
    for item in breed.get("medicalByDisease") or []:
        code = item.get("diagCode")
        label = item.get("label") or MED_LABEL.get(code, "")
        foods = breed["_medMap"].get(code, [])
        if not foods:
            blocks.append(f"При {label}:\n   специальной лечебной линейки нет — состав не применяется")
            continue
        inner = [f"При {label}:"]
        for f in foods[:4]:
            inner.append(f"   {f['name']}\n   Состав: {f['composition']}")
        blocks.append("\n".join(inner))
    return "\n".join(blocks)


def style_header(ws, cols):
    fill = PatternFill("solid", fgColor="E07A5F")
    font = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
    align = Alignment(wrap_text=True, vertical="center", horizontal="center")
    thin = Border(
        left=Side(style="thin", color="D9D0C7"),
        right=Side(style="thin", color="D9D0C7"),
        top=Side(style="thin", color="D9D0C7"),
        bottom=Side(style="thin", color="D9D0C7"),
    )
    for col in range(1, cols + 1):
        cell = ws.cell(1, col)
        cell.fill = fill
        cell.font = font
        cell.alignment = align
        cell.border = thin
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(cols)}{ws.max_row}"


def wrap_body(ws, cols):
    align = Alignment(wrap_text=True, vertical="top")
    thin = Border(
        left=Side(style="thin", color="EFE7DC"),
        right=Side(style="thin", color="EFE7DC"),
        top=Side(style="thin", color="EFE7DC"),
        bottom=Side(style="thin", color="EFE7DC"),
    )
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=cols):
        ws.row_dimensions[row[0].row].height = 90
        for cell in row:
            cell.alignment = align
            cell.font = Font(name="Calibri", size=10)
            cell.border = thin


def write_sheet_catalog(wb):
    if "Каталог кормов" in wb.sheetnames:
        del wb["Каталог кормов"]
    ws = wb.create_sheet("Каталог кормов")
    headers = [
        "ID", "Вид", "Форма", "Бренд", "Название", "Страна", "Сегмент", "Теги",
        "Белок %", "Жир %", "Ккал/100г", "Клетчатка %", "Зола %", "Влага %", "Фосфор %",
        "Без злаков", "Суставы", "Indoor", "Высокая энергия",
        "Полный состав", "Источник состава",
    ]
    ws.append(headers)
    for f in FOODS:
        ws.append([
            f["id"], "кошка" if f["species"] == "cat" else "собака",
            "влажный" if f.get("form") == "wet" else "сухой",
            f["brand"], f["name"], f["country"], f["tier"],
            ", ".join(f["tags"]),
            f["proteinPer100g"], f["fatPer100g"], f["kcalPer100g"],
            f["fiberPer100g"], f["ashPer100g"], f.get("moisturePer100g") or "",
            f.get("phosphorusPer100g") or "",
            "да" if f["grainFree"] else "нет",
            "да" if f["jointSupport"] else "нет",
            "да" if f["indoor"] else "нет",
            "да" if f["highEnergy"] else "нет",
            f["composition"], f["compositionSource"],
        ])
    for i, w in enumerate([12, 10, 12, 16, 36, 12, 12, 22, 10, 10, 12, 12, 10, 10, 10, 12, 10, 10, 16, 70, 40], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    style_header(ws, len(headers))
    wrap_body(ws, len(headers))
    note = wb.create_sheet("Примечание по составам") if "Примечание по составам" not in wb.sheetnames else wb["Примечание по составам"]
    note.delete_rows(1, note.max_row)
    notes = [
        "Как читать составы",
        "Составы собраны по типовым опубликованным формулам SKU российских брендов (этикетка и сайт производителя, ассортимент РФ 2024–2026).",
        "Рецептуры могут меняться партией — перед покупкой сверяйте полный список на пачке.",
        "В каталоге российские марки, которые люди узнают в магазине: Winner и Мираторг Extra Meat, Наша Марка, Васька, Сириус, ProBalance, Родные корма, Четвероногий Гурман, Мнямс, Деревенские лакомства, Clan, Organix, Трапеза, Ем без проблем, BioMenu, AlphaPet, AJO, Craftia, FLORIDA, Blitz, Karmy, Bowl Wow, Savita, Mr.Buffalo, Award, Best Dinner, Night Hunter, Grandin, ZooRing, Petstory, Стаут, Pride, Zilli, Grand Prix, Территория, Berkley, Wellkiss, Native, Vita Pro, Landor, Титбит, Solid Natura, Prime Ever, Натуральная формула, Хороший хозяин, Мяу, Гав, Дилли.",
        "Добавлены сухие и влажные корма (паучи и консервы). Влажных специально много — это то, что чаще берут в РФ.",
        "Добавлены разные белки (курица, индейка, рыба, ягнёнок, утка, говядина) и размеры гранул для собак.",
        "Лечебные линейки Craftia Galena и Petstory Vet — только при подтверждённом диагнозе.",
        "Подбор в приложении НормаЛап смотрит на породу, белок и калории, размер гранулы, стерилизацию, активность, аллергены и диагноз.",
    ]
    for i, t in enumerate(notes, 1):
        note.cell(i, 1, t)
        note.cell(i, 1).alignment = Alignment(wrap_text=True)
        note.row_dimensions[i].height = 28 if i > 1 else 22
        if i == 1:
            note.cell(i, 1).font = Font(bold=True, size=14, color="C65D44")
    note.column_dimensions["A"].width = 120


def update_cats_xlsx(cats):
    path = ANALYSIS / "Топ_26_пород_кошек_РФ_реальный_состав_3.xlsx"
    wb = openpyxl.load_workbook(path)
    ws = wb.worksheets[0]
    headers = [
        "№", "Порода", "Размер / вес", "Предрасположенность к заболеваниям",
        "Ориентир КБЖУ", "Подходящий корм (здоровая кошка)",
        "РЕАЛЬНЫЙ состав кормов (здоровая кошка)",
        "Лечебный корм при заболевании",
        "РЕАЛЬНЫЙ состав лечебных кормов",
        "Корм при кастрации/стерилизации",
        "РЕАЛЬНЫЙ состав кормов при стерилизации",
    ]
    for i, h in enumerate(headers, 1):
        ws.cell(1, i, h)
    by_name = {b["name"]: b for b in cats}
    for row in range(2, ws.max_row + 1):
        name = str(ws.cell(row, 2).value or "").strip()
        b = by_name.get(name)
        if not b:
            continue
        ws.cell(row, 6, numbered(b["_healthyObjs"]))
        ws.cell(row, 7, compositions_block(b["_healthyObjs"]))
        ws.cell(row, 8, medical_text(b))
        ws.cell(row, 9, medical_comp(b))
        ws.cell(row, 10, numbered(b["_sterObjs"], 8))
        ws.cell(row, 11, compositions_block(b["_sterObjs"], 8))
    widths = [6, 28, 22, 40, 28, 36, 70, 40, 70, 36, 70]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    style_header(ws, 11)
    wrap_body(ws, 11)
    write_sheet_catalog(wb)
    wb.save(path)
    return path


def update_dogs_xlsx(dogs):
    path = ANALYSIS / "Топ-25_пород_собак_РФ_расширенная.xlsx"
    wb = openpyxl.load_workbook(path)
    ws = wb.worksheets[0]
    headers = [
        "№", "Порода", "Размер / вес взрослой особи",
        "Предрасположенность к заболеваниям",
        "Ориентир КБЖУ (на 100 г сухого корма)",
        "Подходящий корм (для здоровой собаки)",
        "РЕАЛЬНЫЙ состав кормов (здоровая собака)",
        "Лечебный корм при заболевании (если диагностировано)",
        "РЕАЛЬНЫЙ состав лечебных кормов",
        "Корм при кастрации/стерилизации",
        "РЕАЛЬНЫЙ состав кормов при стерилизации",
    ]
    # Shift if old file had 8 cols — rewrite header + food columns, keep 1-5
    old_rows = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        old_rows.append(row)
    # clear sheet
    ws.delete_rows(1, ws.max_row)
    ws.append(headers)
    by_name = {b["name"]: b for b in dogs}
    for i, old in enumerate(old_rows, 1):
        name = str(old[1] or "").strip() if old and len(old) > 1 else ""
        b = by_name.get(name)
        if not b:
            ws.append(list(old) + [""] * (11 - len(old)))
            continue
        ws.append([
            old[0], old[1], old[2], old[3], old[4],
            numbered(b["_healthyObjs"]),
            compositions_block(b["_healthyObjs"]),
            medical_text(b),
            medical_comp(b),
            numbered(b["_sterObjs"], 8),
            compositions_block(b["_sterObjs"], 8),
        ])
    widths = [6, 32, 22, 42, 30, 36, 70, 42, 70, 36, 70]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    style_header(ws, 11)
    wrap_body(ws, 11)
    write_sheet_catalog(wb)
    wb.save(path)
    return path


def copy_photos():
    ASSETS.mkdir(parents=True, exist_ok=True)
    copied = {}
    for breed_id, fname in PHOTO_MAP.items():
        src = PHOTOS / fname
        if not src.exists():
            print("missing photo", fname)
            continue
        ext = src.suffix.lower()
        dest = ASSETS / f"{breed_id}{ext}"
        shutil.copy2(src, dest)
        copied[breed_id] = f"assets/breeds/{dest.name}"
    for breed_id, fname in DOG_PHOTO_MAP.items():
        src = DOG_PHOTOS / fname
        if not src.exists():
            print("missing dog photo", fname)
            continue
        ext = src.suffix.lower()
        dest = ASSETS / f"{breed_id}{ext}"
        shutil.copy2(src, dest)
        copied[breed_id] = f"assets/breeds/{dest.name}"
    return copied


def strip_temp(breeds):
    clean = []
    for b in breeds:
        d = {k: v for k, v in b.items() if not k.startswith("_")}
        clean.append(d)
    return clean


def food_row(f):
    return [
        f["id"],
        "кошка" if f["species"] == "cat" else "собака",
        "влажный" if f.get("form") == "wet" else "сухой",
        f["brand"],
        f["name"],
        f.get("tier") or "",
        ", ".join(f.get("tags") or []),
        f.get("proteinPer100g"),
        f.get("fatPer100g"),
        f.get("kcalPer100g"),
        f.get("moisturePer100g"),
        f.get("fiberPer100g"),
        f.get("phosphorusPer100g") or "",
        f.get("composition") or "",
        "Россия",
    ]


def fill_food_sheet(ws, foods):
    headers = [
        "ID", "Вид", "Форма", "Бренд", "Название", "Сегмент", "Теги",
        "Белок %", "Жир %", "Ккал/100г", "Влага %", "Клетчатка %", "Фосфор %",
        "Краткое описание / состав", "Страна",
    ]
    ws.append(headers)
    for f in foods:
        ws.append(food_row(f))
    widths = [14, 10, 12, 22, 40, 12, 22, 10, 10, 12, 10, 12, 10, 80, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    style_header(ws, len(headers))
    wrap_body(ws, len(headers))


def write_russian_foods_xlsx():
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    dry = [f for f in FOODS if f.get("form") != "wet"]
    wet = [f for f in FOODS if f.get("form") == "wet"]
    cats = [f for f in FOODS if f["species"] == "cat"]
    dogs = [f for f in FOODS if f["species"] == "dog"]
    brands = {}
    for f in FOODS:
        b = brands.setdefault(f["brand"], {"n": 0, "dry": 0, "wet": 0, "cat": 0, "dog": 0, "tiers": set()})
        b["n"] += 1
        b["dry" if f.get("form") != "wet" else "wet"] += 1
        b["cat" if f["species"] == "cat" else "dog"] += 1
        b["tiers"].add(f.get("tier") or "")

    wb = openpyxl.Workbook()
    summary = wb.active
    summary.title = "Сводка"
    lines = [
        ("Анализ российских кормов для НормаЛап", True),
        ("", False),
        (f"Всего SKU в каталоге: {len(FOODS)}", False),
        (f"Сухие: {len(dry)}  ·  Влажные: {len(wet)}", False),
        (f"Для кошек: {len(cats)}  ·  Для собак: {len(dogs)}", False),
        (f"Брендов: {len(brands)}", False),
        ("", False),
        ("Зачем так много российских", True),
        ("На полке в РФ люди чаще берут то, что уже знают: Васька, Наша Марка, Winner, Четвероногий Гурман, Мнямс, Сириус, ProBalance, Родные корма, Деревенские лакомства, Clan, Organix. Зарубежные Royal Canin, Purina, Hills, Acana в приложении не показываем — их и так полно в ветклиниках, а состав и цена «не про наш магазин».", False),
        ("Влажных кормов специально больше, чем обычно в каталогах: паучи и банки — привычный формат, особенно для кошек. Сухие остаются для повседневной нормы и расчёта граммов в день.", False),
        ("Составы — типовые формулы SKU по этикетке и сайту производителя. Партии меняются, перед покупкой сверяйте пачку.", False),
        ("", False),
        ("Как читать форму", True),
        ("Сухой: белок и ккал на 100 г как на пачке, порция в граммах гранул.", False),
        ("Влажный: много влаги (обычно 76–82%), белка 8–12%, ккал 70–130 на 100 г. В приложении порция больше: это паучи, не гранулы.", False),
        ("Сегменты: budget — то, что берут чаще всего; mid — супермаркет / зоомагазин; premium — Мираторг Extra Meat, AlphaPet, AJO, Craftia, Solid Natura.", False),
        ("Лечебные Craftia Galena и Petstory Vet — только при диагнозе врача.", False),
    ]
    summary.column_dimensions["A"].width = 118
    for i, (text, bold) in enumerate(lines, 1):
        cell = summary.cell(i, 1, text)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.font = Font(name="Calibri", size=14 if bold else 11, bold=bold, color="C65D44" if bold else "2B2B2B")
        summary.row_dimensions[i].height = 22 if (bold or not text) else 48

    fill_food_sheet(wb.create_sheet("Все корма"), FOODS)
    fill_food_sheet(wb.create_sheet("Сухие"), dry)
    fill_food_sheet(wb.create_sheet("Влажные"), wet)
    fill_food_sheet(wb.create_sheet("Кошки"), cats)
    fill_food_sheet(wb.create_sheet("Собаки"), dogs)

    brands_ws = wb.create_sheet("Бренды")
    brands_ws.append(["Бренд", "SKU всего", "Сухие", "Влажные", "Кошки", "Собаки", "Сегменты"])
    for name, b in sorted(brands.items(), key=lambda x: (-x[1]["n"], x[0])):
        brands_ws.append([name, b["n"], b["dry"], b["wet"], b["cat"], b["dog"], ", ".join(sorted(b["tiers"]))])
    for i, w in enumerate([28, 12, 12, 12, 12, 12, 24], 1):
        brands_ws.column_dimensions[get_column_letter(i)].width = w
    style_header(brands_ws, 7)

    dests = [
        ANALYSIS / "Российские_корма_анализ.xlsx",
        ROOT / "Российские_корма_анализ.xlsx",
        WORKSPACE / "Российские_корма_анализ.xlsx",
    ]
    saved = []
    for path in dests:
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)
        saved.append(path)
    return saved


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    cats, dogs = load_breeds()
    dogs = [d for d in dogs if d.get("id") != "dog-18"]
    attach_foods(cats, "cat")
    attach_foods(dogs, "dog")
    try:
        photos = copy_photos()
    except Exception as exc:
        print("photos skip", exc)
        photos = {}
    catalog = {
        "cats": strip_temp(cats),
        "dogs": strip_temp(dogs),
        "foods": FOODS,
        "photos": photos,
        "app": {
            "name": "НормаЛап",
            "tagline": "Корм по норме твоего питомца",
            "countryFocus": "Россия",
        },
    }
    (DATA / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ru = write_russian_foods_xlsx()
    try:
        p1 = update_cats_xlsx(cats)
        print("updated", p1.name)
    except Exception as exc:
        print("cats xlsx skip", exc)
    try:
        p2 = update_dogs_xlsx(dogs)
        print("updated", p2.name)
    except Exception as exc:
        print("dogs xlsx skip", exc)
    print("catalog foods", len(FOODS))
    print("dry", sum(1 for f in FOODS if f.get("form") != "wet"))
    print("wet", sum(1 for f in FOODS if f.get("form") == "wet"))
    print("brands", len({f["brand"] for f in FOODS}))
    for p in ru:
        print("excel", p)


if __name__ == "__main__":
    main()
