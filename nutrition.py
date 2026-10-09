# -*- coding: utf-8 -*-
"""Расчёт суточной нормы КБЖУ. NRC / WSAVA-ориентиры, адаптированные под кошек и собак."""
from __future__ import annotations

import math
from datetime import date


def age_months(pet) -> int:
    if pet.get("ageMonths") is not None:
        return int(pet["ageMonths"])
    birth = pet.get("birthDate")
    if not birth:
        return 24
    y, m, d = [int(x) for x in str(birth)[:10].split("-")]
    b, n = date(y, m, d), date.today()
    return (n.year - b.year) * 12 + (n.month - b.month)


def rer(weight_kg: float) -> float:
    return 70.0 * (max(weight_kg, 0.3) ** 0.75)


def der_factor(pet) -> float:
    months = age_months(pet)
    weight = float(pet.get("weightKg") or 4)
    target = pet.get("targetWeightKg")
    losing = target is not None and float(target) < weight * 0.95
    diags = pet.get("diagnoses") or []
    activity = pet.get("activity") or "medium"
    if pet.get("species") == "cat":
        if months < 12:
            der = 2.5
        elif losing:
            der = 0.8
        elif "overweight" in diags:
            der = 1.0
        elif pet.get("sterilized"):
            der = 1.2
        else:
            der = 1.4
        if not losing:
            if activity == "high":
                der += 0.1
            elif activity == "very_high":
                der += 0.2
        return der
    if months < 4:
        der = 3.0
    elif months < 12:
        der = 2.0
    elif losing:
        der = 1.0
    elif "overweight" in diags:
        der = 1.2
    elif pet.get("sterilized"):
        der = 1.4
    else:
        der = 1.6
    if not losing:
        if activity == "high":
            der += 0.15
        elif activity == "very_high":
            der += 0.3
    if months >= 12 and weight > 40:
        der *= 0.95
    return der


def kcal_need(pet) -> int:
    return int(round(rer(float(pet.get("weightKg") or 4)) * der_factor(pet)))


def treat_kcal(pet) -> int:
    try:
        return max(0, int(round(float(pet.get("treatKcal") or 0))))
    except (TypeError, ValueError):
        return 0


def kcal_day(pet) -> int:
    """Калории, которые должен покрыть корм: суточная норма минус лакомства."""
    need = kcal_need(pet)
    left = need - treat_kcal(pet)
    return int(round(max(need * 0.75, left)))


def protein_day(pet) -> int:
    kcal = kcal_need(pet)
    months = age_months(pet)
    w = float(pet.get("weightKg") or 4)
    juvenile = months < 12
    if pet.get("species") == "cat":
        share = 0.35 if juvenile else 0.30
        return int(round(max(5.2 * w, share * kcal / 3.5)))
    return int(round((3.5 if juvenile else 2.5) * w))


def fat_day(pet) -> int:
    w = float(pet.get("weightKg") or 4)
    if pet.get("species") == "cat":
        return int(round((0.7 if pet.get("sterilized") else 0.9) * w))
    return int(round((0.9 if pet.get("sterilized") else 1.15) * w))


def carb_day(pet) -> int:
    used = protein_day(pet) * 3.5 + fat_day(pet) * 8.5
    return int(round(max(0, kcal_need(pet) - used) / 3.5))


def summary(pet) -> dict:
    need = kcal_need(pet)
    treats = treat_kcal(pet)
    food = kcal_day(pet)
    return {
        "kcal": need,
        "foodKcal": food,
        "treatKcal": treats,
        "protein": protein_day(pet),
        "fat": fat_day(pet),
        "carb": carb_day(pet),
    }


def portion_grams(pet, food) -> int:
    kcal100 = food.get("kcalPer100g") or 370
    grams = kcal_day(pet) / kcal100 * 100
    return int(round(grams / 5.0) * 5)


TIER_PRICE_KG = {
    "budget": 320,
    "mid": 520,
    "premium": 820,
}
TIER_PRICE_WET = {
    "budget": 480,
    "mid": 720,
    "premium": 1100,
}


def monthly_cost(pet, food) -> dict:
    """Ориентир стоимости рациона в месяц — у аналогов почти нигде нет под РФ."""
    grams = portion_grams(pet, food)
    wet = food.get("form") == "wet"
    table = TIER_PRICE_WET if wet else TIER_PRICE_KG
    price_kg = food.get("pricePerKg") or table.get(food.get("tier") or "mid", 520)
    day = grams / 1000.0 * price_kg
    month = day * 30
    if wet:
        pack_kg = 0.4 if pet.get("species") == "dog" else 0.085
    else:
        pack_kg = 2.0 if pet.get("species") == "dog" else 1.5
    packs = max(1, int(round((grams * 30 / 1000) / pack_kg + 0.49)))
    return {
        "gramsDay": grams,
        "pricePerKg": int(price_kg),
        "rubDay": int(round(day)),
        "rubMonth": int(round(month / 10.0) * 10),
        "packsMonth": packs,
        "packKg": pack_kg,
        "form": "wet" if wet else "dry",
    }


TRANSITION_DAYS = [
    (1, "три части старого и одна часть нового"),
    (2, "три части старого и одна часть нового"),
    (3, "поровну старого и нового"),
    (4, "поровну старого и нового"),
    (5, "одна часть старого и три части нового"),
    (6, "одна часть старого и три части нового"),
    (7, "только новый корм"),
]

PACK_CHECKS = [
    "Первые 3–5 ингредиентов — конкретное мясо или мясная мука, а не «субпродукты животного происхождения».",
    "Белок и жир на 100 г близки к вашей норме из вкладки «Рацион». Лакомства уже вычтены из калорий на корм.",
    "Если есть аллергия — этого белка нет в составе. «Без курицы» на пачке важнее слова «птица». Рис — не глютен.",
    "При стерилизации или лишнем весе жир обычно не выше 12–13%, есть клетчатка.",
    "При болезни сердца смотрите натрий на анализе. При камнях в моче важнее вода и влажный корм, чем сухой белок.",
    "Лечебный корм берите только если диагноз подтвердил врач — «на всякий случай» нельзя.",
    "Сверьте партию на пачке с типовым составом: рецептуры иногда меняют.",
]
