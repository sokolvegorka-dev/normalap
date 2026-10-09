# -*- coding: utf-8 -*-
"""
Алгоритм подбора корма НормаЛап.

Жёсткие фильтры:
  вид животного, несовместимый лечебный тег, заявленный аллерген в составе,
  повседневный корм при строгом диагнозе (почки, печень, сердце и др.).

Мягкий скор 0–100:
  порода, размер гранулы по реальному весу, белок и калорийность,
  стерилизация, активность, indoor/шерсть, суставы крупных пород,
  возраст (котёнок / щенок), фосфор и натрий при диагнозе.
"""
from __future__ import annotations

import re

from nutrition import age_months

ALLERGENS = [
    {"code": "chicken", "label": "Курица",
     "keywords": ["курин", "куриц", "цыпл", "цыпля", "chicken"]},
    {"code": "beef", "label": "Говядина", "keywords": ["говя", "beef"]},
    {"code": "fish", "label": "Рыба",
     "keywords": ["рыб", "лосос", "тунец", "тунц", "треск", "форел", "сельд", "минтай", "камбал", "сельдь"]},
    {"code": "lamb", "label": "Баранина", "keywords": ["баран", "ягнён", "ягнен", "ягнят", "lamb"]},
    {"code": "turkey", "label": "Индейка", "keywords": ["индей", "turkey"]},
    {"code": "duck", "label": "Утка", "keywords": ["утк", "утин", "duck"]},
    {"code": "dairy", "label": "Молочное", "keywords": ["молок", "молоч", "сыр", "dairy", "йогурт"]},
    {"code": "egg", "label": "Яйцо", "keywords": ["яйц", "яичн", "egg"]},
    {"code": "grain", "label": "Злаки / глютен",
     "keywords": ["пшениц", "кукуруз", "ячмен", "овёс", "овес", "ржи", "рожь", "глютен", "злак"]},
    {"code": "soy", "label": "Соя", "keywords": ["соя", "соев", "soy"]},
]

HYPO_HINTS = ["гипоаллерген", "hypoallergenic", "sensitive", "гидролизат", "монобелок"]
WITHOUT_CLAUSE = re.compile(r"без\s+[^.]*", re.IGNORECASE)

DOG_SIZE = {
    "dog-01": "mini", "dog-02": "mini", "dog-07": "mini",
    "dog-04": "small", "dog-06": "small", "dog-10": "small",
    "dog-13": "small", "dog-14": "small", "dog-24": "small",
    "dog-03": "medium", "dog-11": "medium", "dog-15": "medium",
    "dog-21": "medium", "dog-22": "medium",
    "dog-05": "large", "dog-08": "large", "dog-12": "large",
    "dog-16": "large", "dog-17": "large",
    "dog-19": "large", "dog-20": "large", "dog-25": "large",
    "dog-09": "giant", "dog-23": "giant",
}

SIZE_COMPAT = {
    "mini": {"mini", "small", "any"},
    "small": {"mini", "small", "any"},
    "medium": {"small", "medium", "any"},
    "large": {"medium", "large", "any"},
    "giant": {"large", "any"},
}

OBESITY_BREEDS = {
    "cat-01", "cat-02", "cat-03", "cat-13", "cat-14", "cat-16", "cat-23",
    "dog-03", "dog-08", "dog-11", "dog-12", "dog-14", "dog-15",
}
JOINT_BREEDS = {
    "cat-02", "cat-07", "cat-16", "cat-23", "cat-24",
    "dog-03", "dog-05", "dog-08", "dog-09", "dog-12", "dog-16", "dog-23",
}
HIGH_METABOLISM = {
    "cat-04", "cat-05", "cat-06", "cat-15", "cat-17", "cat-20", "cat-21", "cat-22",
    "dog-01", "dog-02", "dog-07", "dog-10", "dog-19",
}
HAIRBALL_BREEDS = {
    "cat-07", "cat-08", "cat-14", "cat-16", "cat-19", "cat-24", "cat-26",
}

DIAG_PRIORITY = ["ckd", "liver", "diabetes", "heart", "urolithiasis", "allergy", "gi", "joints", "overweight"]
STRICT_DIETS = {"ckd", "liver", "heart", "diabetes", "gi"}

DIAG_PLAIN = {
    "ckd": "почек",
    "liver": "печени",
    "diabetes": "диабета",
    "heart": "сердца",
    "urolithiasis": "мочекаменной болезни",
    "allergy": "аллергии",
    "gi": "желудка и кишечника",
    "joints": "суставов",
    "overweight": "лишнего веса",
}

KIBBLE_PLAIN = {
    "mini": "мелкие гранулы — удобно маленькой собаке",
    "small": "гранулы под небольшую собаку",
    "medium": "гранулы среднего размера",
    "large": "крупные гранулы — под большую собаку",
    "giant": "крупные гранулы — под очень крупную собаку",
}

QUALITY_BRANDS = {
    "AlphaPet", "AJO", "Craftia", "Craftia Galena", "Bowl Wow", "Savita", "Award",
    "Мираторг", "FLORIDA", "Blitz", "Karmy", "Mr.Buffalo", "Best Dinner", "Night Hunter",
}


def pet_weight_kg(pet) -> float:
    try:
        return float(pet.get("weightKg") or 0)
    except (TypeError, ValueError):
        return 0.0


def size_from_weight(kg: float):
    if kg <= 0:
        return None
    if kg < 5:
        return "mini"
    if kg < 10:
        return "small"
    if kg < 22:
        return "medium"
    if kg < 40:
        return "large"
    return "giant"


def kibble_size_for(pet, breed_id):
    """Гранула по весу; у щенка крупной породы — по взрослому размеру."""
    by_weight = size_from_weight(pet_weight_kg(pet))
    by_breed = DOG_SIZE.get(breed_id)
    if age_months(pet) < 12 and by_breed in ("large", "giant"):
        return by_breed
    if by_weight:
        return by_weight
    return by_breed


def typical_adult_range(breed):
    text = (breed or {}).get("weightText") or ""
    nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+[.,]?\d*", text)]
    if len(nums) < 2:
        return None
    lo, hi = sorted((nums[-2], nums[-1]))
    if hi / max(lo, 0.3) > 5:
        return None
    return lo, hi


def looks_heavy(pet, breed) -> bool:
    if age_months(pet) < 12:
        return False
    if "overweight" in (pet.get("diagnoses") or []):
        return True
    rng = typical_adult_range(breed)
    kg = pet_weight_kg(pet)
    if not rng or kg <= 0:
        return False
    _lo, hi = rng
    return kg > hi * 1.12


def prone_to_weight(pet, breed_id) -> bool:
    if age_months(pet) < 12 or not breed_id or breed_id not in OBESITY_BREEDS:
        return False
    return not looks_heavy(pet, None)


def default_targets(pet, breed):
    species = pet.get("species")
    months = age_months(pet)
    size = kibble_size_for(pet, (breed or {}).get("id"))
    if months < 12:
        if species == "cat":
            return 38.0, 410.0
        if size in ("mini", "small"):
            return 30.0, 405.0
        if size == "giant":
            return 27.0, 380.0
        return 28.0, 390.0
    if breed and breed.get("targetProtein100") and breed.get("targetKcal100"):
        return float(breed["targetProtein100"]), float(breed["targetKcal100"])
    if species == "cat":
        return 34.0, 380.0
    if size in ("mini", "small"):
        return 28.0, 390.0
    if size == "giant":
        return 24.0, 345.0
    if size == "large":
        return 25.0, 350.0
    return 26.0, 365.0


def asfed_like_dry(food, key):
    """Влажный корм сравниваем с сухим через сухое вещество."""
    value = food.get(key)
    if value is None:
        return None
    if food.get("form") != "wet":
        return float(value)
    moisture = float(food.get("moisturePer100g") or 80)
    dm = max(15.0, 100.0 - moisture)
    return float(value) / dm * 91.0


def _hay(food) -> str:
    return f"{food.get('name', '')} {food.get('composition', '')}".lower()


def allergy_text(food) -> str:
    """Убираем фразы «без курицы», чтобы они не считались наличием аллергена."""
    return WITHOUT_CLAUSE.sub(" ", _hay(food))


def contains_allergen(food, code: str) -> bool:
    item = next((a for a in ALLERGENS if a["code"] == code), None)
    if not item:
        return False
    text = allergy_text(food)
    return any(kw in text for kw in item["keywords"])


def looks_hypo(food) -> bool:
    text = _hay(food)
    return any(h in text for h in HYPO_HINTS) or "medical:allergy" in (food.get("tags") or [])


def is_growth(food) -> bool:
    tags = food.get("tags") or []
    name = (food.get("name") or "").lower()
    return (
        "kitten" in tags or "puppy" in tags
        or "kitten" in name or "puppy" in name
        or "котён" in name or "котен" in name or "щенок" in name or "щенк" in name
    )


def closeness(value, target, window) -> float:
    if value is None or target is None:
        return 0.0
    diff = abs(float(value) - float(target))
    if diff <= window:
        return 1.0 - diff / (window * 2)
    return max(0.0, 1.0 - diff / (window * 4))


def _is_medical(food) -> bool:
    return any(str(t).startswith("medical:") for t in (food.get("tags") or []))


def _med_codes(food):
    return [t.split(":", 1)[1] for t in (food.get("tags") or []) if str(t).startswith("medical:")]


def primary_diag(diags):
    for code in DIAG_PRIORITY:
        if code in diags:
            return code
    return diags[0] if diags else None


def everyday_ok_for(primary, food, protein, species) -> bool:
    """Повседневный корм не ставим рядом с диетой по строгому диагнозу."""
    if primary not in STRICT_DIETS:
        return True
    form = food.get("form")
    phos = food.get("phosphorusPer100g")
    sodium = food.get("sodiumPer100g")
    kcal = food.get("kcalPer100g")
    if primary == "ckd":
        if phos is None:
            return False
        limit = 0.22 if form == "wet" else 0.55
        if phos > limit:
            return False
        if protein is not None and protein > (28 if species == "cat" else 22):
            return False
        return True
    if primary == "liver":
        if protein is not None and protein > (30 if species == "cat" else 24):
            return False
        return True
    if primary == "heart":
        if sodium is None:
            return False
        return sodium <= 0.35
    if primary == "diabetes":
        if food.get("highEnergy"):
            return False
        if form != "wet" and kcal and kcal >= 390:
            return False
        return True
    if primary == "gi":
        return False
    return True


def match(pet, breed, foods):
    diags = [d for d in (pet.get("diagnoses") or []) if d != "healthy"]
    allergens = (pet.get("allergens") or []) if "allergy" in diags else []
    species = pet.get("species")
    months = age_months(pet)
    young = months < 12
    activity = pet.get("activity") or "medium"
    breed_id = (breed or {}).get("id")
    target_p, target_k = default_targets(pet, breed)
    dog_size = kibble_size_for(pet, breed_id) if species == "dog" else None
    heavy = looks_heavy(pet, breed)
    prone = prone_to_weight(pet, breed_id)
    primary = primary_diag(diags)
    results = []

    for food in foods:
        if food.get("species") != species:
            continue
        tags = food.get("tags") or []
        med_codes = _med_codes(food)
        medical_fit = any(code in diags for code in med_codes)
        exclusive_medical = bool(med_codes) and "healthy" not in tags
        growth = is_growth(food)
        if exclusive_medical and not medical_fit:
            continue
        if not young and growth:
            continue
        if allergens and any(contains_allergen(food, code) for code in allergens):
            continue

        protein = asfed_like_dry(food, "proteinPer100g")
        if not exclusive_medical and not everyday_ok_for(primary, food, protein, species):
            continue

        score = 8.0
        reasons = []
        is_wet = food.get("form") == "wet"
        food_ids = food.get("breedIds") or []

        breed_name = (breed or {}).get("name")
        if breed_id and breed_id in food_ids:
            score += 8
            if breed_name:
                reasons.append(f"подходит породе «{breed_name}»")
            else:
                reasons.append("подходит этой породе")

        food_size = food.get("size") or "any"
        if is_wet:
            score += 4
            reasons.append("влажный корм — много влаги, привычный вкус")
        elif species == "dog" and dog_size:
            if food_size == dog_size:
                score += 10 if heavy else 18
                reasons.append(KIBBLE_PLAIN.get(food_size, "размер гранул подходит"))
            elif food_size in SIZE_COMPAT.get(dog_size, {"any"}):
                score += 8
                if food_size != "any":
                    reasons.append("размер гранул подойдёт при этом весе")
            elif food_size != "any":
                score -= 16
                reasons.append("гранулы не того размера для этого веса")

        if protein is not None and target_p:
            window = 8 if is_wet else 3
            c = closeness(protein, target_p, window)
            score += 16 * c
            if c >= 0.7:
                reasons.append("белка достаточно для этой породы")
            elif c > 0:
                reasons.append("белка почти столько, сколько нужно этой породе")
        elif target_p:
            score += 4

        kcal = asfed_like_dry(food, "kcalPer100g")
        kcal_asfed = food.get("kcalPer100g")
        if kcal is not None and target_k:
            want = target_k
            if pet.get("sterilized") or heavy:
                want *= 0.90
            elif prone:
                want *= 0.97
            if activity in ("high", "very_high") and not young:
                want *= 1.06
            if breed_id in HIGH_METABOLISM and not young:
                want *= 1.04
            c = closeness(kcal, want, 40 if is_wet else 25)
            score += 12 * c
            if c >= 0.65:
                reasons.append("калорийность подходит по энергии")

        if young:
            if growth:
                score += 22
                reasons.append("это корм для котёнка или щенка")
            else:
                score -= 18
            if "sterilised" in tags:
                score -= 16
            if protein is not None and protein < (32 if species == "cat" else 26):
                score -= 8
        elif pet.get("sterilized") and not exclusive_medical:
            fat_asfed = food.get("fatPer100g") or 20
            if "sterilised" in tags:
                score += 18
                reasons.append("меньше жира — как раз после стерилизации")
            elif (is_wet and fat_asfed <= 4.2) or (not is_wet and fat_asfed <= 13):
                score += 6
                reasons.append("не слишком жирный — удобно после стерилизации")
            elif (not is_wet and fat_asfed >= 17) or (is_wet and fat_asfed >= 7.5):
                score -= 10
        elif "sterilised" in tags and not heavy:
            score -= 12

        if medical_fit:
            score += 18
            labels = [DIAG_PLAIN.get(c, c) for c in med_codes]
            reasons.append("лечебный корм для " + ", ".join(labels))
            ranks = [DIAG_PRIORITY.index(c) for c in med_codes if c in diags and c in DIAG_PRIORITY]
            if ranks:
                score += max(0, 28 - min(ranks) * 10)

        if "medical:allergy" in tags and "allergy" not in diags:
            score -= 24

        if allergens:
            if looks_hypo(food) or (food.get("grainFree") and "grain" in allergens):
                score += 16
                reasons.append("без вашего аллергена")
            else:
                reasons.append("в составе нет заявленного аллергена")

        if activity == "very_high" and food.get("highEnergy") and not young:
            score += 10
            reasons.append("больше энергии — для активного питомца")
        if activity == "low" and food.get("highEnergy") and not young:
            score -= 8
        if breed_id in HIGH_METABOLISM and not young and (protein or 0) >= (36 if species == "cat" else 28):
            score += 6
            reasons.append("больше белка — порода очень подвижная")
        if breed_id in HIGH_METABOLISM and not young and not is_wet and (kcal_asfed or 0) < 360:
            score -= 4

        if species == "cat" and (food.get("indoor") or (food.get("fiberPer100g") or 0) >= 5):
            if breed_id in HAIRBALL_BREEDS or pet.get("sterilized"):
                score += 6
                reasons.append("больше клетчатки — помогает выводить шерсть")

        needs_joints = (not young) and (breed_id in JOINT_BREEDS or (species == "dog" and pet_weight_kg(pet) >= 25))
        if needs_joints and food.get("jointSupport"):
            score += 8
            reasons.append("есть добавки для суставов — при таком весе это важно")

        if heavy and not exclusive_medical:
            light = (kcal or 400) <= 345 if not is_wet else (kcal_asfed or 200) <= 85 or "sterilised" in tags
            if light or "sterilised" in tags:
                score += 16
                reasons.append("меньше калорий — при этом весе набор лишнего проще")
            elif not is_wet and (kcal or 0) >= 390:
                score -= 8
        elif heavy and exclusive_medical and "overweight" in med_codes and primary == "overweight":
            score += 12
            reasons.append("меньше калорий — при этом весе набор лишнего проще")

        if food.get("brand") in QUALITY_BRANDS:
            score += 2
        if food.get("tier") == "premium":
            score += 3
        elif food.get("tier") == "mid":
            score += 1
        if food.get("compositionVerified") and food.get("proteinPer100g") is not None:
            score += 2

        if "ckd" in diags and food.get("phosphorusPer100g") is not None:
            limit = 0.2 if is_wet else 0.5
            if food["phosphorusPer100g"] <= limit:
                score += 10
                reasons.append("меньше фосфора — мягче для почек")

        if "heart" in diags:
            sodium = food.get("sodiumPer100g")
            if sodium is not None and sodium <= 0.35:
                score += 10
                reasons.append("меньше натрия — мягче для сердца")
            elif sodium is not None and sodium >= 0.5:
                score -= 12

        if "urolithiasis" in diags:
            if is_wet:
                score += 10
                reasons.append("влажный корм даёт воду — это важно при камнях")
            elif "urolithiasis" in med_codes:
                reasons.append("контроль минералов при мочекаменной болезни")

        if score <= 0:
            continue

        percent = int(max(0, min(100, round(score))))
        results.append({
            "food": food,
            "score": percent,
            "percent": percent,
            "isMedical": medical_fit and exclusive_medical,
            "isSterilised": "sterilised" in tags,
            "reasons": reasons[:4],
            "tier": food.get("tier") or "mid",
        })

    results.sort(key=lambda r: -r["score"])
    medical = [r for r in results if r["isMedical"]]
    everyday = [r for r in results if not r["isMedical"]]

    def mix_form(items, n):
        dry = [r for r in items if r["food"].get("form") != "wet"]
        wet = [r for r in items if r["food"].get("form") == "wet"]
        out, i, j = [], 0, 0
        while len(out) < n and (i < len(dry) or j < len(wet)):
            if i < len(dry):
                out.append(dry[i])
                i += 1
            if len(out) < n and j < len(wet):
                out.append(wet[j])
                j += 1
        return out

    if primary in STRICT_DIETS and medical:
        best = mix_form(medical, 6)
        used = {r["food"]["id"] for r in best}
        good = mix_form([r for r in everyday if r["food"]["id"] not in used], 6)
        medical_rest = mix_form([r for r in medical if r["food"]["id"] not in used], 8)
    else:
        best = mix_form(everyday, 6)
        used = {r["food"]["id"] for r in best}
        good = mix_form([r for r in everyday if r["food"]["id"] not in used], 8)
        medical_rest = mix_form(medical, 8) if diags else []

    return {
        "best": best,
        "good": good,
        "budget": [],
        "medical": medical_rest,
        "conflict": bool(set(diags) & STRICT_DIETS) and not medical,
        "all": results[:20],
        "primary": primary,
    }
