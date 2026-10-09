# -*- coding: utf-8 -*-
"""Дополнительные российские корма: знакомые марки, сухие линейки и большой влажный ассортимент."""


def _wet_text(species, meat, protein, fat, kcal, moisture, extra=""):
    taurin = ", таурин" if species == "cat" else ""
    return (
        f"Состав: мясо и субпродукты ({meat}), бульон, растительное масло, "
        f"минеральные вещества, витамины{taurin}. {extra}"
        f"Анализ: белок {protein}%, жир {fat}%, клетчатка 0,5%, зола 2,0%, влага {moisture}%. "
        f"Энергия {kcal} ккал/100 г. Влажный корм, производство: Россия."
    )


def extra_foods(F, ALL_CATS, ALL_DOGS, DOG_MINI_SMALL, DOG_MEDIUM, DOG_LARGE, DOG_GIANT,
                CAT_HIGH_ENERGY, CAT_LARGE, CAT_LONGHAIR, CAT_WEIGHT):
    out = []

    def dry(*args, **kwargs):
        out.append(F(*args, **kwargs))

    def wet(fid, name, brand, species, tags, meat, protein, fat, kcal, moisture, tier,
            extra="", phosphorus=None, indoor=False):
        breeds = ALL_CATS if species == "cat" else ALL_DOGS
        phos = phosphorus if phosphorus is not None else (0.18 if species == "cat" else 0.22)
        if any(t == "medical:ckd" for t in tags):
            phos = 0.12
        out.append(F(
            fid, name, brand, species, tags,
            _wet_text(species, meat, protein, fat, kcal, moisture, extra),
            protein, fat, kcal, breeds,
            fiber=0.5, ash=2.0, moisture=moisture, phosphorus=phos,
            size="any", indoor=indoor, tier=tier, form="wet",
            notes="Влажный корм: паучи и консервы. Сверяйте состав на банке.",
        ))

    # ---------- Сухие: марки, которые люди узнают с полки ----------
    dry("rcat-vas01", "Васька Adult Курица", "Васька", "cat", ["healthy"],
        "Состав: мясокостная мука, пшеница, кукуруза, жир животный, дрожжи, таурин, минералы. "
        "Анализ: белок 28%, жир 10%, клетчатка 4%, зола 9%, влага 10%. Энергия 330 ккал/100 г. Производство: Россия.",
        28, 10, 330, ALL_CATS, fiber=4.0, ash=9.0, phosphorus=1.1, tier="budget")
    dry("rcat-vas-in", "Васька Indoor", "Васька", "cat", ["healthy", "indoor"],
        "Состав: мясокостная мука, пшеница, клетчатка, жир животный, таурин. Для домашних кошек. "
        "Анализ: белок 28%, жир 9%, клетчатка 5,5%, зола 8,5%, влага 10%. Энергия 318 ккал/100 г. Россия.",
        28, 9, 318, CAT_LONGHAIR + CAT_WEIGHT, fiber=5.5, ash=8.5, phosphorus=1.0, indoor=True, tier="budget")
    dry("rcat-trap01", "Трапеза Adult Cat Мясная", "Трапеза", "cat", ["healthy"],
        "Состав: мука мясная, пшеница, ячмень, жир животный, таурин, премикс. "
        "Анализ: белок 30%, жир 12%, клетчатка 3,8%, зола 8%, влага 10%. Энергия 345 ккал/100 г. Россия.",
        30, 12, 345, ALL_CATS, fiber=3.8, ash=8.0, phosphorus=1.0, tier="budget")
    dry("rcat-ebp01", "Ем без проблем Adult Cat", "Ем без проблем", "cat", ["healthy"],
        "Состав: мука из курицы, рис, кукуруза, жир куриный, таурин. Простая повседневная формула. "
        "Анализ: белок 30%, жир 12%, клетчатка 4%, зола 8%, влага 10%. Энергия 342 ккал/100 г. Россия.",
        30, 12, 342, ALL_CATS, fiber=4.0, ash=8.0, phosphorus=0.98, tier="budget")
    dry("rcat-meow01", "Мяу Adult Курица", "Мяу", "cat", ["healthy"],
        "Состав: мясокостная мука, злаки, жир, таурин, минералы. "
        "Анализ: белок 27%, жир 10%, клетчатка 4%, зола 9%, влага 10%. Энергия 325 ккал/100 г. Россия.",
        27, 10, 325, ALL_CATS, fiber=4.0, ash=9.0, phosphorus=1.1, tier="budget")
    dry("rcat-clan01", "Clan Classic Adult Cat Курица", "Clan", "cat", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, жом свёклы, масло лосося, таурин. "
        "Анализ: белок 32%, жир 14%, клетчатка 3,2%, зола 7%, влага 9%. Энергия 368 ккал/100 г. Россия.",
        32, 14, 368, ALL_CATS, fiber=3.2, phosphorus=0.9, tier="mid")
    dry("rcat-clan-st", "Clan Classic Sterilised Cat", "Clan", "cat", ["sterilised"],
        "Состав: дегидрированная курица, рис, клетчатка, L-карнитин, клюква, таурин. "
        "Анализ: белок 34%, жир 11%, клетчатка 5%, зола 6,8%, влага 9%. Энергия 338 ккал/100 г. Россия.",
        34, 11, 338, ALL_CATS, fiber=5.0, phosphorus=0.8, indoor=True, tier="mid")
    dry("rcat-mny01", "Мнямс Adult Cat Курица и индейка", "Мнямс", "cat", ["healthy"],
        "Состав: дегидрированная курица, индейка, рис, жир птицы, масло лосося, таурин. "
        "Анализ: белок 33%, жир 15%, клетчатка 3%, зола 6,8%, влага 9%. Энергия 378 ккал/100 г. Россия.",
        33, 15, 378, ALL_CATS, phosphorus=0.88, tier="mid")
    dry("rcat-dl01", "Деревенские лакомства Adult Курица", "Деревенские лакомства", "cat", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, жом свёклы, таурин. "
        "Анализ: белок 32%, жир 14%, клетчатка 3,2%, зола 7%, влага 9%. Энергия 365 ккал/100 г. Россия.",
        32, 14, 365, ALL_CATS, fiber=3.2, phosphorus=0.9, tier="mid")
    dry("rcat-bio01", "BioMenu Adult Cat Курица", "BioMenu", "cat", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, цикорий, таурин. "
        "Анализ: белок 32%, жир 14%, клетчатка 3%, зола 6,8%, влага 9%. Энергия 370 ккал/100 г. Россия.",
        32, 14, 370, ALL_CATS, phosphorus=0.88, tier="mid")
    dry("rcat-sn01", "Solid Natura Adult Cat Индейка", "Solid Natura", "cat", ["healthy"],
        "Состав: дегидрированная индейка, рис, жир индейки, масло лосося, таурин. "
        "Анализ: белок 34%, жир 16%, клетчатка 3%, зола 6,5%, влага 9%. Энергия 388 ккал/100 г. Россия.",
        34, 16, 388, CAT_HIGH_ENERGY + CAT_LARGE, phosphorus=0.84, high_energy=True, tier="premium")
    dry("rcat-em01", "Мираторг Extra Meat Adult Cat", "Мираторг", "cat", ["healthy"],
        "Состав: свежая курица, дегидрированная курица, рис, жир куриный, таурин. Высокая доля мяса. "
        "Анализ: белок 36%, жир 16%, клетчатка 2,8%, зола 6,5%, влага 9%. Энергия 398 ккал/100 г. Россия (Мираторг).",
        36, 16, 398, ALL_CATS, fiber=2.8, phosphorus=0.88, high_energy=True, tier="premium")
    dry("rcat-pe01", "Prime Ever Adult Cat Курица", "Prime Ever", "cat", ["healthy"],
        "Состав: дегидрированная курица, рис, горох, жир куриный, цикорий, таурин. "
        "Анализ: белок 34%, жир 15%, клетчатка 3%, зола 6,5%, влага 9%. Энергия 382 ккал/100 г. Россия.",
        34, 15, 382, ALL_CATS, phosphorus=0.84, tier="premium")
    dry("rcat-nf01", "Натуральная формула Adult Cat", "Натуральная формула", "cat", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, жом свёклы, таурин. "
        "Анализ: белок 32%, жир 14%, клетчатка 3,2%, зола 7%, влага 9%. Энергия 360 ккал/100 г. Россия.",
        32, 14, 360, ALL_CATS, fiber=3.2, phosphorus=0.9, tier="mid")
    dry("rcat-hh01", "Хороший хозяин Adult Cat", "Хороший хозяин", "cat", ["healthy"],
        "Состав: мука мясная, злаки, жир, таурин, минералы. "
        "Анализ: белок 28%, жир 11%, клетчатка 4%, зола 8,5%, влага 10%. Энергия 335 ккал/100 г. Россия.",
        28, 11, 335, ALL_CATS, fiber=4.0, ash=8.5, phosphorus=1.05, tier="budget")
    dry("rcat-rk-fs", "Родные корма Adult Рыба", "Родные корма", "cat", ["healthy"],
        "Состав: мука рыбная, рис, пшеница, жир рыбы, таурин. Без курицы. "
        "Анализ: белок 30%, жир 12%, клетчатка 4%, зола 8,5%, влага 10%. Энергия 348 ккал/100 г. Россия.",
        30, 12, 348, ALL_CATS, fiber=4.0, ash=8.5, phosphorus=1.0, tier="budget")

    dry("rdog-vas01", "Гав Adult Курица", "Гав", "dog", ["healthy"],
        "Состав: мясокостная мука, пшеница, кукуруза, жир животный, минералы. "
        "Анализ: белок 21%, жир 10%, клетчатка 4,5%, зола 8,5%, влага 10%. Энергия 325 ккал/100 г. Россия.",
        21, 10, 325, ALL_DOGS, size="any", fiber=4.5, ash=8.5, phosphorus=1.05, tier="budget")
    dry("rdog-trap01", "Трапеза Adult Dog Мясная", "Трапеза", "dog", ["healthy"],
        "Состав: мука мясная, пшеница, ячмень, жир животный, премикс. "
        "Анализ: белок 22%, жир 12%, клетчатка 4%, зола 8%, влага 10%. Энергия 338 ккал/100 г. Россия.",
        22, 12, 338, ALL_DOGS, size="any", fiber=4.0, ash=8.0, phosphorus=1.0, tier="budget")
    dry("rdog-ebp01", "Ем без проблем Adult Dog", "Ем без проблем", "dog", ["healthy"],
        "Состав: мука из курицы, рис, кукуруза, жир куриный. "
        "Анализ: белок 23%, жир 12%, клетчатка 4%, зола 8%, влага 10%. Энергия 340 ккал/100 г. Россия.",
        23, 12, 340, ALL_DOGS, size="any", fiber=4.0, ash=8.0, phosphorus=0.98, tier="budget")
    dry("rdog-dilly01", "Дилли Adult Dog", "Дилли", "dog", ["healthy"],
        "Состав: мясокостная мука, злаки, жир, минералы. "
        "Анализ: белок 21%, жир 10%, клетчатка 4,5%, зола 8,5%, влага 10%. Энергия 322 ккал/100 г. Россия.",
        21, 10, 322, ALL_DOGS, size="any", fiber=4.5, ash=8.5, phosphorus=1.05, tier="budget")
    dry("rdog-hh01", "Хороший хозяин Adult Dog", "Хороший хозяин", "dog", ["healthy"],
        "Состав: мука мясная, злаки, жир, минералы. "
        "Анализ: белок 22%, жир 11%, клетчатка 4%, зола 8,5%, влага 10%. Энергия 330 ккал/100 г. Россия.",
        22, 11, 330, ALL_DOGS, size="any", fiber=4.0, ash=8.5, phosphorus=1.0, tier="budget")
    dry("rdog-clan01", "Clan Classic Adult Dog Курица", "Clan", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, жом свёклы, масло лосося. "
        "Анализ: белок 25%, жир 14%, клетчатка 3,2%, зола 7%, влага 9%. Энергия 362 ккал/100 г. Россия.",
        25, 14, 362, ALL_DOGS, size="any", fiber=3.2, phosphorus=0.9, tier="mid")
    dry("rdog-mny01", "Мнямс Adult Dog Курица", "Мнямс", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, масло лосося. "
        "Анализ: белок 26%, жир 15%, клетчатка 3%, зола 6,8%, влага 9%. Энергия 372 ккал/100 г. Россия.",
        26, 15, 372, ALL_DOGS, size="any", phosphorus=0.88, tier="mid")
    dry("rdog-dl01", "Деревенские лакомства Adult Dog", "Деревенские лакомства", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, жом свёклы. "
        "Анализ: белок 25%, жир 14%, клетчатка 3,2%, зола 7%, влага 9%. Энергия 358 ккал/100 г. Россия.",
        25, 14, 358, ALL_DOGS, size="any", fiber=3.2, phosphorus=0.9, tier="mid")
    dry("rdog-bio01", "BioMenu Adult Dog Курица", "BioMenu", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, цикорий. "
        "Анализ: белок 25%, жир 14%, клетчатка 3,2%, зола 6,8%, влага 9%. Энергия 365 ккал/100 г. Россия.",
        25, 14, 365, ALL_DOGS, size="any", fiber=3.2, phosphorus=0.88, tier="mid")
    dry("rdog-tit01", "Титбит Adult Dog Курица", "Титбит", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, жом свёклы. "
        "Анализ: белок 24%, жир 13%, клетчатка 3,5%, зола 7,2%, влага 9%. Энергия 350 ккал/100 г. Россия.",
        24, 13, 350, ALL_DOGS, size="any", fiber=3.5, phosphorus=0.9, tier="mid")
    dry("rdog-sn01", "Solid Natura Adult Dog Говядина", "Solid Natura", "dog", ["healthy"],
        "Состав: дегидрированная говядина, рис, жир говяжий, масло лосося. Без курицы. "
        "Анализ: белок 27%, жир 15%, клетчатка 3%, зола 6,5%, влага 9%. Энергия 375 ккал/100 г. Россия.",
        27, 15, 375, ALL_DOGS, size="any", phosphorus=0.86, tier="premium")
    dry("rdog-em-mi", "Мираторг Extra Meat Mini", "Мираторг", "dog", ["healthy"],
        "Состав: свежая курица, дегидрированная курица, рис, жир куриный. Мелкая гранула, много мяса. "
        "Анализ: белок 30%, жир 17%, клетчатка 2,6%, зола 6,4%, влага 9%. Энергия 405 ккал/100 г. Россия.",
        30, 17, 405, DOG_MINI_SMALL, size="mini", fiber=2.6, phosphorus=0.86, high_energy=True, tier="premium")
    dry("rdog-em-mx", "Мираторг Extra Meat Maxi", "Мираторг", "dog", ["healthy"],
        "Состав: свежая курица, дегидрированная курица, рис, глюкозамин, жир куриный. Крупная гранула. "
        "Анализ: белок 25%, жир 14%, клетчатка 3,4%, зола 6,6%, влага 9%. Энергия 355 ккал/100 г. Россия.",
        25, 14, 355, DOG_LARGE + DOG_GIANT, size="large", fiber=3.4, phosphorus=0.84,
        joint_support=True, tier="premium")
    dry("rdog-pe01", "Prime Ever Adult Dog Курица", "Prime Ever", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, горох, жир куриный, цикорий. "
        "Анализ: белок 26%, жир 15%, клетчатка 3%, зола 6,5%, влага 9%. Энергия 372 ккал/100 г. Россия.",
        26, 15, 372, ALL_DOGS, size="any", phosphorus=0.84, tier="premium")
    dry("rdog-rk01", "Родные корма Adult Dog Курица", "Родные корма", "dog", ["healthy"],
        "Состав: мука из курицы, пшеница, кукуруза, жир куриный, минералы. "
        "Анализ: белок 22%, жир 12%, клетчатка 4%, зола 8,2%, влага 10%. Энергия 338 ккал/100 г. Россия.",
        22, 12, 338, ALL_DOGS, size="any", fiber=4.0, ash=8.2, phosphorus=1.0, tier="budget")
    dry("rdog-nf01", "Натуральная формула Adult Dog", "Натуральная формула", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, жир куриный, жом свёклы. "
        "Анализ: белок 24%, жир 13%, клетчатка 3,5%, зола 7%, влага 9%. Энергия 352 ккал/100 г. Россия.",
        24, 13, 352, ALL_DOGS, size="any", fiber=3.5, phosphorus=0.9, tier="mid")
    dry("rdog-clan-md", "Clan Classic Medium Adult", "Clan", "dog", ["healthy"],
        "Состав: дегидрированная курица, рис, ячмень, жир куриный, масло лосося. "
        "Анализ: белок 25%, жир 14%, клетчатка 3,2%, зола 6,8%, влага 9%. Энергия 360 ккал/100 г. Россия.",
        25, 14, 360, DOG_MEDIUM, size="medium", fiber=3.2, phosphorus=0.88, tier="mid")

    # ---------- Влажные: кошки и собаки, знакомые марки ----------
    # id, name, brand, species, tags, meat, protein, fat, kcal, moisture, tier, extra
    wet_rows = [
        # Васька
        ("wcat-vas-ch", "Васька Курица в соусе", "Васька", "cat", ["healthy"], "курица не менее 16%", 8.0, 3.5, 72, 82, "budget"),
        ("wcat-vas-bf", "Васька Говядина в соусе", "Васька", "cat", ["healthy"], "говядина не менее 16%", 8.0, 4.0, 76, 82, "budget"),
        ("wcat-vas-fs", "Васька Рыба в соусе", "Васька", "cat", ["healthy"], "рыба не менее 16%", 8.5, 3.2, 70, 82, "budget"),
        ("wcat-vas-lv", "Васька Печень в соусе", "Васька", "cat", ["healthy"], "печень и курица не менее 18%", 8.5, 4.2, 78, 81, "budget"),
        # Наша Марка
        ("wcat-nm-ch", "Наша Марка Курица в желе", "Наша Марка", "cat", ["healthy"], "курица не менее 20%", 8.5, 4.0, 78, 81, "budget"),
        ("wcat-nm-tk", "Наша Марка Индейка в желе", "Наша Марка", "cat", ["healthy"], "индейка не менее 20%", 8.5, 4.0, 78, 81, "budget"),
        ("wcat-nm-fs", "Наша Марка Рыба в желе", "Наша Марка", "cat", ["healthy"], "рыба не менее 20%", 9.0, 3.5, 75, 81, "budget"),
        ("wcat-nm-st", "Наша Марка Sterilised Курица", "Наша Марка", "cat", ["sterilised"], "курица не менее 22%", 9.5, 3.0, 70, 82, "budget"),
        # Родные корма
        ("wcat-rk-ch", "Родные корма Курица кусочки", "Родные корма", "cat", ["healthy"], "курица не менее 22%", 9.0, 4.5, 82, 80, "budget"),
        ("wcat-rk-bf", "Родные корма Говядина кусочки", "Родные корма", "cat", ["healthy"], "говядина не менее 22%", 9.0, 5.0, 86, 80, "budget"),
        ("wcat-rk-lv", "Родные корма Печень кусочки", "Родные корма", "cat", ["healthy"], "печень не менее 20%", 9.5, 5.0, 88, 80, "budget"),
        ("wcat-rk-fs", "Родные корма Рыба кусочки", "Родные корма", "cat", ["healthy"], "рыба не менее 22%", 9.5, 4.0, 80, 80, "budget"),
        # Сириус
        ("wcat-sir-ch", "Сириус Курица в соусе", "Сириус", "cat", ["healthy"], "курица не менее 20%", 8.5, 4.2, 80, 81, "budget"),
        ("wcat-sir-bf", "Сириус Говядина в соусе", "Сириус", "cat", ["healthy"], "говядина не менее 20%", 8.5, 4.5, 82, 81, "budget"),
        ("wcat-sir-tk", "Сириус Индейка в соусе", "Сириус", "cat", ["healthy"], "индейка не менее 20%", 8.5, 4.0, 78, 81, "budget"),
        # ProBalance
        ("wcat-pb-ch", "ProBalance Курица пауч", "ProBalance", "cat", ["healthy"], "курица не менее 24%", 9.5, 4.8, 88, 80, "budget"),
        ("wcat-pb-fs", "ProBalance Рыба пауч", "ProBalance", "cat", ["healthy"], "рыба не менее 24%", 10.0, 4.2, 84, 80, "budget"),
        ("wcat-pb-st", "ProBalance Sterilised пауч", "ProBalance", "cat", ["sterilised"], "курица не менее 24%", 10.0, 3.2, 74, 81, "budget"),
        # Четвероногий Гурман
        ("wcat-4g-ch", "Четвероногий Гурман Курица", "Четвероногий Гурман", "cat", ["healthy"], "курица не менее 40%", 11.0, 6.5, 108, 78, "mid"),
        ("wcat-4g-tk", "Четвероногий Гурман Индейка", "Четвероногий Гурман", "cat", ["healthy"], "индейка не менее 40%", 11.0, 6.0, 104, 78, "mid"),
        ("wcat-4g-bf", "Четвероногий Гурман Говядина", "Четвероногий Гурман", "cat", ["healthy"], "говядина не менее 40%", 11.0, 7.0, 112, 78, "mid"),
        ("wcat-4g-lv", "Четвероногий Гурман Печень", "Четвероногий Гурман", "cat", ["healthy"], "печень не менее 35%", 11.5, 6.8, 110, 78, "mid"),
        ("wcat-4g-fs", "Четвероногий Гурман Рыба", "Четвероногий Гурман", "cat", ["healthy"], "рыба не менее 40%", 11.5, 5.5, 100, 78, "mid"),
        ("wcat-4g-dk", "Четвероногий Гурман Утка", "Четвероногий Гурман", "cat", ["healthy"], "утка не менее 38%", 11.0, 7.2, 114, 77, "mid"),
        ("wcat-4g-st", "Четвероногий Гурман Sterilised", "Четвероногий Гурман", "cat", ["sterilised"], "курица не менее 42%", 12.0, 4.0, 88, 79, "mid"),
        # Мнямс
        ("wcat-mny-ch", "Мнямс Курица пауч", "Мнямс", "cat", ["healthy"], "курица не менее 35%", 10.5, 6.0, 102, 78, "mid"),
        ("wcat-mny-tk", "Мнямс Индейка пауч", "Мнямс", "cat", ["healthy"], "индейка не менее 35%", 10.5, 5.8, 100, 78, "mid"),
        ("wcat-mny-fs", "Мнямс Лосось пауч", "Мнямс", "cat", ["healthy"], "лосось не менее 32%", 11.0, 6.5, 108, 78, "mid"),
        ("wcat-mny-bf", "Мнямс Говядина пауч", "Мнямс", "cat", ["healthy"], "говядина не менее 35%", 10.5, 6.5, 106, 78, "mid"),
        ("wcat-mny-st", "Мнямс Sterilised пауч", "Мнямс", "cat", ["sterilised"], "индейка не менее 36%", 11.0, 4.0, 86, 80, "mid"),
        # Деревенские лакомства
        ("wcat-dl-ch", "Деревенские лакомства Курица", "Деревенские лакомства", "cat", ["healthy"], "курица не менее 30%", 10.0, 5.5, 96, 79, "mid"),
        ("wcat-dl-bf", "Деревенские лакомства Говядина", "Деревенские лакомства", "cat", ["healthy"], "говядина не менее 30%", 10.0, 6.0, 100, 79, "mid"),
        ("wcat-dl-tk", "Деревенские лакомства Индейка", "Деревенские лакомства", "cat", ["healthy"], "индейка не менее 30%", 10.0, 5.2, 94, 79, "mid"),
        ("wcat-dl-lv", "Деревенские лакомства Печень", "Деревенские лакомства", "cat", ["healthy"], "печень не менее 28%", 10.5, 6.0, 102, 79, "mid"),
        # Winner
        ("wcat-w-ch", "Winner Курица пауч", "Winner", "cat", ["healthy"], "курица не менее 28%", 10.0, 5.5, 95, 79, "budget"),
        ("wcat-w-bf", "Winner Говядина пауч", "Winner", "cat", ["healthy"], "говядина не менее 28%", 10.0, 6.0, 98, 79, "budget"),
        ("wcat-w-tk", "Winner Индейка пауч", "Winner", "cat", ["healthy"], "индейка не менее 28%", 10.0, 5.2, 92, 79, "budget"),
        ("wcat-w-fs", "Winner Рыба пауч", "Winner", "cat", ["healthy"], "рыба не менее 28%", 10.5, 4.8, 90, 79, "budget"),
        ("wcat-w-st", "Winner Sterilised пауч", "Winner", "cat", ["sterilised"], "курица не менее 30%", 10.5, 3.5, 78, 81, "budget"),
        # Organix
        ("wcat-org-ch", "Organix Курица консервы", "Organix", "cat", ["healthy"], "курица не менее 45%", 11.5, 6.5, 110, 77, "mid"),
        ("wcat-org-tk", "Organix Индейка консервы", "Organix", "cat", ["healthy"], "индейка не менее 45%", 11.5, 6.0, 106, 77, "mid"),
        ("wcat-org-fs", "Organix Рыба консервы", "Organix", "cat", ["healthy"], "рыба не менее 45%", 12.0, 5.5, 102, 77, "mid"),
        ("wcat-org-dk", "Organix Утка консервы", "Organix", "cat", ["healthy"], "утка не менее 42%", 11.5, 7.0, 114, 77, "mid"),
        # Best Dinner
        ("wcat-bd-ch", "Best Dinner Курица пауч", "Best Dinner", "cat", ["healthy"], "курица не менее 32%", 10.5, 6.0, 100, 78, "mid"),
        ("wcat-bd-dk", "Best Dinner Утка пауч", "Best Dinner", "cat", ["healthy"], "утка не менее 32%", 10.5, 6.8, 108, 78, "mid"),
        ("wcat-bd-fs", "Best Dinner Рыба пауч", "Best Dinner", "cat", ["healthy"], "рыба не менее 32%", 11.0, 5.5, 98, 78, "mid"),
        # Clan
        ("wcat-cl-ch", "Clan Conserv Курица", "Clan", "cat", ["healthy"], "курица не менее 38%", 11.0, 6.2, 105, 78, "mid"),
        ("wcat-cl-tk", "Clan Conserv Индейка", "Clan", "cat", ["healthy"], "индейка не менее 38%", 11.0, 5.8, 102, 78, "mid"),
        ("wcat-cl-bf", "Clan Conserv Говядина", "Clan", "cat", ["healthy"], "говядина не менее 38%", 11.0, 6.8, 110, 78, "mid"),
        ("wcat-cl-st", "Clan Conserv Sterilised", "Clan", "cat", ["sterilised"], "курица не менее 40%", 11.5, 4.0, 86, 79, "mid"),
        # BioMenu
        ("wcat-bio-ch", "BioMenu Курица пауч", "BioMenu", "cat", ["healthy"], "курица не менее 30%", 10.0, 5.5, 96, 79, "mid"),
        ("wcat-bio-fs", "BioMenu Рыба пауч", "BioMenu", "cat", ["healthy"], "рыба не менее 30%", 10.5, 5.0, 92, 79, "mid"),
        ("wcat-bio-tk", "BioMenu Индейка пауч", "BioMenu", "cat", ["healthy"], "индейка не менее 30%", 10.0, 5.2, 94, 79, "mid"),
        # Ем без проблем
        ("wcat-ebp-ch", "Ем без проблем Курица", "Ем без проблем", "cat", ["healthy"], "курица не менее 18%", 8.5, 4.0, 78, 81, "budget"),
        ("wcat-ebp-bf", "Ем без проблем Говядина", "Ем без проблем", "cat", ["healthy"], "говядина не менее 18%", 8.5, 4.5, 82, 81, "budget"),
        ("wcat-ebp-fs", "Ем без проблем Рыба", "Ем без проблем", "cat", ["healthy"], "рыба не менее 18%", 9.0, 3.8, 76, 81, "budget"),
        # Ночной охотник
        ("wcat-nh-ch", "Ночной охотник Курица", "Night Hunter", "cat", ["healthy"], "курица не менее 40%", 12.0, 7.0, 118, 76, "premium"),
        ("wcat-nh-tk", "Ночной охотник Индейка", "Night Hunter", "cat", ["healthy"], "индейка не менее 40%", 12.0, 6.5, 114, 76, "premium"),
        ("wcat-nh-fs", "Ночной охотник Рыба", "Night Hunter", "cat", ["healthy"], "рыба не менее 40%", 12.5, 6.0, 110, 76, "premium"),
        # Solid Natura
        ("wcat-sn-ch", "Solid Natura Курица банка", "Solid Natura", "cat", ["healthy"], "курица не менее 50%", 12.0, 7.0, 120, 76, "premium"),
        ("wcat-sn-tk", "Solid Natura Индейка банка", "Solid Natura", "cat", ["healthy"], "индейка не менее 50%", 12.0, 6.5, 116, 76, "premium"),
        ("wcat-sn-bf", "Solid Natura Говядина банка", "Solid Natura", "cat", ["healthy"], "говядина не менее 50%", 12.0, 7.5, 124, 76, "premium"),
        # Мираторг Extra Meat
        ("wcat-em-ch", "Мираторг Extra Meat Курица", "Мираторг", "cat", ["healthy"], "курица не менее 55%", 12.5, 7.2, 125, 75, "premium"),
        ("wcat-em-bf", "Мираторг Extra Meat Говядина", "Мираторг", "cat", ["healthy"], "говядина не менее 55%", 12.5, 7.8, 130, 75, "premium"),
        ("wcat-em-tk", "Мираторг Extra Meat Индейка", "Мираторг", "cat", ["healthy"], "индейка не менее 55%", 12.5, 7.0, 122, 75, "premium"),
        # Blitz
        ("wcat-bl-ch", "Blitz Курица пауч", "Blitz", "cat", ["healthy"], "курица не менее 28%", 10.0, 5.5, 95, 79, "mid"),
        ("wcat-bl-tk", "Blitz Индейка пауч", "Blitz", "cat", ["healthy"], "индейка не менее 28%", 10.0, 5.2, 92, 79, "mid"),
        ("wcat-bl-st", "Blitz Sterilised пауч", "Blitz", "cat", ["sterilised"], "курица не менее 30%", 10.5, 3.5, 78, 81, "mid"),
        # AlphaPet
        ("wcat-ap-ch", "AlphaPet Курица пауч", "AlphaPet", "cat", ["healthy"], "курица не менее 42%", 11.5, 6.5, 112, 77, "premium"),
        ("wcat-ap-tk", "AlphaPet Индейка пауч", "AlphaPet", "cat", ["healthy"], "индейка не менее 42%", 11.5, 6.2, 108, 77, "premium"),
        ("wcat-ap-fs", "AlphaPet Рыба пауч", "AlphaPet", "cat", ["healthy"], "рыба не менее 42%", 12.0, 5.8, 106, 77, "premium"),
        ("wcat-ap-st", "AlphaPet Sterilised пауч", "AlphaPet", "cat", ["sterilised"], "курица не менее 44%", 12.0, 4.2, 90, 79, "premium"),
        ("wcat-ap-kt", "AlphaPet Kitten пауч", "AlphaPet", "cat", ["healthy", "kitten"], "курица не менее 45%", 12.5, 7.5, 128, 76, "premium"),
        ("wcat-ajo-kt", "AJO Kitten пауч", "AJO", "cat", ["healthy", "kitten"], "курица не менее 42%", 12.0, 7.2, 124, 76, "premium"),
        ("wcat-cr-kt", "Craftia Kitten пауч", "Craftia", "cat", ["healthy", "kitten"], "курица не менее 40%", 12.0, 7.0, 122, 76, "premium"),
        # AJO
        ("wcat-ajo-ch", "AJO Курица пауч", "AJO", "cat", ["healthy"], "курица не менее 40%", 11.5, 6.4, 110, 77, "premium"),
        ("wcat-ajo-tk", "AJO Индейка пауч", "AJO", "cat", ["healthy"], "индейка не менее 40%", 11.5, 6.0, 106, 77, "premium"),
        ("wcat-ajo-fs", "AJO Рыба пауч", "AJO", "cat", ["healthy"], "рыба не менее 40%", 12.0, 5.6, 104, 77, "premium"),
        # Grandin
        ("wcat-gr-ch", "Grandin Курица пауч", "Grandin", "cat", ["healthy"], "курица не менее 26%", 9.5, 5.0, 90, 80, "mid"),
        ("wcat-gr-bf", "Grandin Говядина пауч", "Grandin", "cat", ["healthy"], "говядина не менее 26%", 9.5, 5.5, 94, 80, "mid"),
        # ZooRing
        ("wcat-zr-ch", "ZooRing Курица пауч", "ZooRing", "cat", ["healthy"], "курица не менее 25%", 9.5, 4.8, 88, 80, "mid"),
        ("wcat-zr-fs", "ZooRing Рыба пауч", "ZooRing", "cat", ["healthy"], "рыба не менее 25%", 10.0, 4.5, 86, 80, "mid"),
        # Стаут
        ("wcat-st-ch", "Стаут Курица пауч", "Стаут", "cat", ["healthy"], "курица не менее 26%", 9.5, 5.0, 90, 80, "mid"),
        ("wcat-st-tk", "Стаут Индейка пауч", "Стаут", "cat", ["healthy"], "индейка не менее 26%", 9.5, 4.8, 88, 80, "mid"),
        # Mr.Buffalo
        ("wcat-bf-ch", "Mr.Buffalo Курица пауч", "Mr.Buffalo", "cat", ["healthy"], "курица не менее 32%", 10.5, 6.0, 100, 78, "mid"),
        ("wcat-bf-tk", "Mr.Buffalo Индейка пауч", "Mr.Buffalo", "cat", ["healthy"], "индейка не менее 32%", 10.5, 5.6, 96, 78, "mid"),
        ("wcat-bf-st", "Mr.Buffalo Sterilised пауч", "Mr.Buffalo", "cat", ["sterilised"], "курица не менее 34%", 11.0, 3.8, 82, 80, "mid"),
        # Karmy
        ("wcat-km-ch", "Karmy Курица пауч", "Karmy", "cat", ["healthy"], "курица не менее 30%", 10.5, 5.8, 98, 79, "mid"),
        ("wcat-km-dk", "Karmy Утка пауч", "Karmy", "cat", ["healthy"], "утка не менее 30%", 10.5, 6.4, 104, 79, "mid"),
        # FLORIDA
        ("wcat-fl-ch", "FLORIDA Курица пауч", "FLORIDA", "cat", ["healthy"], "курица не менее 30%", 10.5, 5.8, 98, 79, "mid"),
        ("wcat-fl-fs", "FLORIDA Рыба пауч", "FLORIDA", "cat", ["healthy"], "рыба не менее 30%", 11.0, 5.2, 94, 79, "mid"),
        ("wcat-fl-st", "FLORIDA Sterilised пауч", "FLORIDA", "cat", ["sterilised"], "курица не менее 32%", 11.0, 3.6, 80, 80, "mid"),
        # Трапеза / Мяу / Титбит
        ("wcat-tr-ch", "Трапеза Курица в соусе", "Трапеза", "cat", ["healthy"], "курица не менее 18%", 8.5, 4.0, 78, 81, "budget"),
        ("wcat-tr-bf", "Трапеза Говядина в соусе", "Трапеза", "cat", ["healthy"], "говядина не менее 18%", 8.5, 4.4, 80, 81, "budget"),
        ("wcat-meow-ch", "Мяу Курица в желе", "Мяу", "cat", ["healthy"], "курица не менее 15%", 8.0, 3.5, 70, 83, "budget"),
        ("wcat-meow-fs", "Мяу Рыба в желе", "Мяу", "cat", ["healthy"], "рыба не менее 15%", 8.5, 3.2, 68, 83, "budget"),
        ("wcat-tit-ch", "Титбит Курица пауч", "Титбит", "cat", ["healthy"], "курица не менее 24%", 9.5, 5.0, 90, 80, "mid"),
        ("wcat-pe-ch", "Prime Ever Курица пауч", "Prime Ever", "cat", ["healthy"], "курица не менее 40%", 11.5, 6.4, 110, 77, "premium"),
        ("wcat-pe-fs", "Prime Ever Рыба пауч", "Prime Ever", "cat", ["healthy"], "рыба не менее 40%", 12.0, 5.8, 106, 77, "premium"),
        ("wcat-cr-ch", "Craftia Курица пауч", "Craftia", "cat", ["healthy"], "курица не менее 38%", 11.5, 6.2, 108, 77, "premium"),
        ("wcat-aw-ch", "Award Курица пауч", "Award", "cat", ["healthy"], "курица не менее 36%", 11.0, 6.0, 104, 78, "premium"),
        ("wcat-bw-tk", "Bowl Wow Индейка и тыква пауч", "Bowl Wow", "cat", ["healthy"], "индейка не менее 40%", 11.5, 6.0, 106, 77, "premium"),
        ("wcat-zl-tk", "Zilli Индейка пауч", "Zilli", "cat", ["healthy"], "индейка не менее 38%", 11.0, 6.2, 105, 78, "premium"),
        ("wcat-bk-lb", "Berkley Ягнёнок пауч", "Berkley", "cat", ["healthy", "medical:allergy"], "ягнёнок не менее 38%", 11.0, 6.0, 104, 78, "premium"),
        ("wcat-ld-dk", "Landor Утка пауч", "Landor", "cat", ["healthy"], "утка не менее 40%", 11.5, 7.0, 114, 77, "premium"),
        ("wcat-hh-ch", "Хороший хозяин Курица", "Хороший хозяин", "cat", ["healthy"], "курица не менее 16%", 8.0, 3.8, 74, 82, "budget"),
        ("wcat-nf-ch", "Натуральная формула Курица", "Натуральная формула", "cat", ["healthy"], "курица не менее 26%", 9.5, 5.0, 90, 80, "mid"),
        # лечебные влажные кошки
        ("wcat-cg-ren", "Craftia Galena Cat Renal пауч", "Craftia Galena", "cat", ["medical:ckd"],
         "умеренное мясо птицы, сниженный фосфор", 7.5, 6.5, 92, 80, "premium"),
        ("wcat-cg-uri", "Craftia Galena Cat Urinary пауч", "Craftia Galena", "cat", ["medical:urolithiasis"],
         "курица, контроль минералов", 9.0, 4.5, 84, 81, "premium"),
        ("wcat-cg-gi", "Craftia Galena Cat GI пауч", "Craftia Galena", "cat", ["medical:gi"],
         "легкоусвояемая курица и рис", 8.5, 4.0, 80, 81, "premium"),
        ("wcat-ps-ren", "Petstory Vet Cat Renal пауч", "Petstory", "cat", ["medical:ckd"],
         "умеренный белок птицы, сниженный фосфор", 7.2, 6.0, 88, 81, "mid"),

        # ----- Собаки влажные -----
        ("wdog-4g-ch", "Четвероногий Гурман Курица", "Четвероногий Гурман", "dog", ["healthy"], "курица не менее 40%", 10.0, 6.0, 105, 78, "mid"),
        ("wdog-4g-bf", "Четвероногий Гурман Говядина", "Четвероногий Гурман", "dog", ["healthy"], "говядина не менее 40%", 10.0, 6.8, 112, 78, "mid"),
        ("wdog-4g-tk", "Четвероногий Гурман Индейка", "Четвероногий Гурман", "dog", ["healthy"], "индейка не менее 40%", 10.0, 5.8, 102, 78, "mid"),
        ("wdog-4g-lv", "Четвероногий Гурман Печень", "Четвероногий Гурман", "dog", ["healthy"], "печень не менее 35%", 10.5, 6.5, 108, 78, "mid"),
        ("wdog-4g-fs", "Четвероногий Гурман Рыба", "Четвероногий Гурман", "dog", ["healthy"], "рыба не менее 38%", 10.5, 5.2, 98, 78, "mid"),
        ("wdog-4g-st", "Четвероногий Гурман Light", "Четвероногий Гурман", "dog", ["sterilised", "medical:overweight"], "курица не менее 42%", 10.5, 3.5, 82, 80, "mid"),
        ("wdog-mny-ch", "Мнямс Курица пауч", "Мнямс", "dog", ["healthy"], "курица не менее 32%", 9.5, 5.8, 100, 79, "mid"),
        ("wdog-mny-bf", "Мнямс Говядина пауч", "Мнямс", "dog", ["healthy"], "говядина не менее 32%", 9.5, 6.2, 104, 79, "mid"),
        ("wdog-mny-tk", "Мнямс Индейка пауч", "Мнямс", "dog", ["healthy"], "индейка не менее 32%", 9.5, 5.5, 98, 79, "mid"),
        ("wdog-dl-ch", "Деревенские лакомства Курица", "Деревенские лакомства", "dog", ["healthy"], "курица не менее 28%", 9.0, 5.5, 96, 80, "mid"),
        ("wdog-dl-bf", "Деревенские лакомства Говядина", "Деревенские лакомства", "dog", ["healthy"], "говядина не менее 28%", 9.0, 6.0, 100, 80, "mid"),
        ("wdog-w-ch", "Winner Курица пауч", "Winner", "dog", ["healthy"], "курица не менее 26%", 9.0, 5.2, 94, 80, "budget"),
        ("wdog-w-bf", "Winner Говядина пауч", "Winner", "dog", ["healthy"], "говядина не менее 26%", 9.0, 5.8, 98, 80, "budget"),
        ("wdog-w-tk", "Winner Индейка пауч", "Winner", "dog", ["healthy"], "индейка не менее 26%", 9.0, 5.0, 92, 80, "budget"),
        ("wdog-nm-ch", "Наша Марка Курица в желе", "Наша Марка", "dog", ["healthy"], "курица не менее 18%", 8.0, 4.5, 82, 81, "budget"),
        ("wdog-nm-bf", "Наша Марка Говядина в желе", "Наша Марка", "dog", ["healthy"], "говядина не менее 18%", 8.0, 5.0, 86, 81, "budget"),
        ("wdog-nm-lt", "Наша Марка Light пауч", "Наша Марка", "dog", ["sterilised", "medical:overweight"], "курица не менее 20%", 8.5, 3.0, 72, 82, "budget"),
        ("wdog-sir-ch", "Сириус Курица в соусе", "Сириус", "dog", ["healthy"], "курица не менее 20%", 8.5, 4.8, 86, 81, "budget"),
        ("wdog-sir-bf", "Сириус Говядина в соусе", "Сириус", "dog", ["healthy"], "говядина не менее 20%", 8.5, 5.2, 90, 81, "budget"),
        ("wdog-pb-ch", "ProBalance Курица пауч", "ProBalance", "dog", ["healthy"], "курица не менее 22%", 9.0, 5.0, 90, 80, "budget"),
        ("wdog-pb-bf", "ProBalance Говядина пауч", "ProBalance", "dog", ["healthy"], "говядина не менее 22%", 9.0, 5.5, 94, 80, "budget"),
        ("wdog-org-ch", "Organix Курица консервы", "Organix", "dog", ["healthy"], "курица не менее 45%", 10.5, 6.5, 110, 77, "mid"),
        ("wdog-org-bf", "Organix Говядина консервы", "Organix", "dog", ["healthy"], "говядина не менее 45%", 10.5, 7.0, 114, 77, "mid"),
        ("wdog-org-fs", "Organix Рыба консервы", "Organix", "dog", ["healthy"], "рыба не менее 45%", 11.0, 5.8, 106, 77, "mid"),
        ("wdog-clan-ch", "Clan Conserv Курица", "Clan", "dog", ["healthy"], "курица не менее 36%", 10.0, 6.0, 104, 78, "mid"),
        ("wdog-clan-bf", "Clan Conserv Говядина", "Clan", "dog", ["healthy"], "говядина не менее 36%", 10.0, 6.5, 108, 78, "mid"),
        ("wdog-bio-ch", "BioMenu Курица пауч", "BioMenu", "dog", ["healthy"], "курица не менее 28%", 9.5, 5.5, 96, 79, "mid"),
        ("wdog-ebp-ch", "Ем без проблем Курица", "Ем без проблем", "dog", ["healthy"], "курица не менее 18%", 8.0, 4.5, 82, 81, "budget"),
        ("wdog-ebp-bf", "Ем без проблем Говядина", "Ем без проблем", "dog", ["healthy"], "говядина не менее 18%", 8.0, 5.0, 86, 81, "budget"),
        ("wdog-gav-ch", "Гав Курица в соусе", "Гав", "dog", ["healthy"], "курица не менее 15%", 7.5, 4.0, 74, 82, "budget"),
        ("wdog-gav-bf", "Гав Говядина в соусе", "Гав", "dog", ["healthy"], "говядина не менее 15%", 7.5, 4.5, 78, 82, "budget"),
        ("wdog-trap-ch", "Трапеза Курица", "Трапеза", "dog", ["healthy"], "курица не менее 18%", 8.0, 4.6, 84, 81, "budget"),
        ("wdog-dilly-ch", "Дилли Курица", "Дилли", "dog", ["healthy"], "курица не менее 16%", 7.8, 4.2, 78, 82, "budget"),
        ("wdog-tit-ch", "Титбит Курица пауч", "Титбит", "dog", ["healthy"], "курица не менее 24%", 9.0, 5.2, 92, 80, "mid"),
        ("wdog-tit-bf", "Титбит Говядина пауч", "Титбит", "dog", ["healthy"], "говядина не менее 24%", 9.0, 5.8, 96, 80, "mid"),
        ("wdog-sn-ch", "Solid Natura Курица банка", "Solid Natura", "dog", ["healthy"], "курица не менее 50%", 11.0, 7.0, 118, 76, "premium"),
        ("wdog-sn-bf", "Solid Natura Говядина банка", "Solid Natura", "dog", ["healthy"], "говядина не менее 50%", 11.0, 7.5, 122, 76, "premium"),
        ("wdog-em-ch", "Мираторг Extra Meat Курица", "Мираторг", "dog", ["healthy"], "курица не менее 55%", 11.5, 7.2, 124, 75, "premium"),
        ("wdog-em-bf", "Мираторг Extra Meat Говядина", "Мираторг", "dog", ["healthy"], "говядина не менее 55%", 11.5, 7.8, 128, 75, "premium"),
        ("wdog-bl-ch", "Blitz Курица пауч", "Blitz", "dog", ["healthy"], "курица не менее 26%", 9.0, 5.4, 94, 80, "mid"),
        ("wdog-ap-ch", "AlphaPet Курица пауч", "AlphaPet", "dog", ["healthy"], "курица не менее 40%", 10.5, 6.4, 110, 77, "premium"),
        ("wdog-ap-py", "AlphaPet Puppy пауч", "AlphaPet", "dog", ["healthy", "puppy"], "курица не менее 42%", 11.5, 7.2, 122, 76, "premium"),
        ("wdog-ajo-py", "AJO Puppy пауч", "AJO", "dog", ["healthy", "puppy"], "курица не менее 40%", 11.0, 7.0, 118, 76, "premium"),
        ("wdog-ap-fs", "AlphaPet Рыба пауч", "AlphaPet", "dog", ["healthy"], "рыба не менее 40%", 11.0, 5.8, 106, 77, "premium"),
        ("wdog-ajo-ch", "AJO Курица пауч", "AJO", "dog", ["healthy"], "курица не менее 38%", 10.5, 6.2, 108, 77, "premium"),
        ("wdog-km-ch", "Karmy Курица пауч", "Karmy", "dog", ["healthy"], "курица не менее 28%", 9.5, 5.6, 96, 79, "mid"),
        ("wdog-km-lb", "Karmy Ягнёнок пауч", "Karmy", "dog", ["healthy", "medical:allergy"], "ягнёнок не менее 28%", 9.5, 5.8, 98, 79, "mid"),
        ("wdog-fl-ch", "FLORIDA Курица пауч", "FLORIDA", "dog", ["healthy"], "курица не менее 28%", 9.5, 5.5, 96, 79, "mid"),
        ("wdog-bf-ch", "Mr.Buffalo Курица пауч", "Mr.Buffalo", "dog", ["healthy"], "курица не менее 30%", 9.5, 5.8, 98, 79, "mid"),
        ("wdog-st-ch", "Стаут Курица пауч", "Стаут", "dog", ["healthy"], "курица не менее 24%", 9.0, 5.2, 92, 80, "mid"),
        ("wdog-gr-ch", "Grandin Курица пауч", "Grandin", "dog", ["healthy"], "курица не менее 24%", 9.0, 5.0, 90, 80, "mid"),
        ("wdog-zr-ch", "ZooRing Курица пауч", "ZooRing", "dog", ["healthy"], "курица не менее 24%", 9.0, 5.0, 90, 80, "mid"),
        ("wdog-pe-ch", "Prime Ever Курица пауч", "Prime Ever", "dog", ["healthy"], "курица не менее 38%", 10.5, 6.2, 108, 77, "premium"),
        ("wdog-cr-ch", "Craftia Курица пауч", "Craftia", "dog", ["healthy"], "курица не менее 36%", 10.5, 6.0, 106, 78, "premium"),
        ("wdog-aw-ch", "Award Курица пауч", "Award", "dog", ["healthy"], "курица не менее 34%", 10.0, 6.0, 104, 78, "premium"),
        ("wdog-bd-ch", "Best Dinner Курица пауч", "Best Dinner", "dog", ["healthy"], "курица не менее 30%", 9.5, 5.8, 98, 79, "mid"),
        ("wdog-rk-ch", "Родные корма Курица", "Родные корма", "dog", ["healthy"], "курица не менее 20%", 8.5, 4.8, 86, 81, "budget"),
        ("wdog-rk-bf", "Родные корма Говядина", "Родные корма", "dog", ["healthy"], "говядина не менее 20%", 8.5, 5.2, 90, 81, "budget"),
        ("wdog-hh-ch", "Хороший хозяин Курица", "Хороший хозяин", "dog", ["healthy"], "курица не менее 16%", 7.8, 4.4, 80, 82, "budget"),
        ("wdog-nf-ch", "Натуральная формула Курица", "Натуральная формула", "dog", ["healthy"], "курица не менее 24%", 9.0, 5.2, 92, 80, "mid"),
        ("wdog-ld-dk", "Landor Утка пауч", "Landor", "dog", ["healthy"], "утка не менее 38%", 10.5, 6.8, 112, 77, "premium"),
        ("wdog-zl-tk", "Zilli Индейка пауч", "Zilli", "dog", ["healthy"], "индейка не менее 36%", 10.0, 6.0, 104, 78, "premium"),
        ("wdog-bk-lb", "Berkley Ягнёнок пауч", "Berkley", "dog", ["healthy", "medical:allergy"], "ягнёнок не менее 36%", 10.0, 6.0, 104, 78, "premium"),
        ("wdog-bw-fs", "Bowl Wow Рыба и тыква пауч", "Bowl Wow", "dog", ["healthy"], "рыба не менее 38%", 10.5, 6.0, 106, 77, "premium"),
        ("wdog-cg-ren", "Craftia Galena Dog Renal пауч", "Craftia Galena", "dog", ["medical:ckd"],
         "умеренный белок, сниженный фосфор", 6.5, 6.0, 90, 80, "premium"),
        ("wdog-cg-gi", "Craftia Galena Dog GI пауч", "Craftia Galena", "dog", ["medical:gi"],
         "легкоусвояемая курица", 8.0, 4.2, 82, 81, "premium"),
        ("wdog-ps-ren", "Petstory Vet Dog Renal пауч", "Petstory", "dog", ["medical:ckd"],
         "умеренный белок птицы", 6.2, 5.8, 86, 81, "mid"),
    ]

    for row in wet_rows:
        extra = ""
        if "ckd" in str(row[4]):
            extra = "Сниженный фосфор. Только по назначению врача. "
        elif "urolithiasis" in str(row[4]):
            extra = "Контроль минералов и pH мочи. По назначению врача. "
        elif "gi" in str(row[4]):
            extra = "Легкоусвояемая формула при расстройстве ЖКТ. "
        wet(*row, extra=extra)

    return out
