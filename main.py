# -*- coding: utf-8 -*-
"""НормаЛап — нативное приложение для подбора корма."""
from __future__ import annotations

import asyncio
import copy
import json
import os
import shutil
import sys
import uuid
import calendar
from datetime import date, datetime, timedelta
from pathlib import Path

import flet as ft
import flet_video as fv

import matcher
import nutrition
import five_letters as five
import bowl_draw as bowl
import bowl_live
import weather

PRIMARY = "#668875"
PRIMARY_DARK = "#4C6959"
BG = "#F6F3EC"
SURFACE = "#FFFFFF"
TEXT = "#2C2A26"
MUTED = "#7A746C"
BORDER = "#E8E2D6"
SUCCESS = "#2A9D8F"
DANGER = "#C44536"
CHIP = "#E6ECE5"
ACCENT = "#E07A5F"
ACCENT_SOFT = "#F8E6DF"
ACCENT_INK = "#9A4E3C"
FIVE_BG = "#FFFFFF"        # поле игры — белая карточка, как остальные в приложении
FIVE_CELL = "#F6F3EC"      # пустая клетка
FIVE_LINE = "#E1DACB"      # рамка пустой клетки
FIVE_TYPED = "#9A9283"     # рамка клетки с набранной буквой
FIVE_HIT = "#668875"       # буква на своём месте — фирменный шалфей
FIVE_PRESENT = "#E6B655"   # буква есть, но не там — тёплый мёд
FIVE_MISS = "#A9A398"      # такой буквы нет — тёплый серый
FIVE_INK = "#2C2A26"       # тёмный текст на светлых и медовых клетках
FIVE_ON = "#FFFFFF"        # светлый текст на зелёных и серых клетках
FIVE_KEY = "#E6ECE5"       # обычная клавиша

PET_VIDEOS = [
    {
        "id": "fly",
        "file": "fly.mp4",
        "thumb": "fly.jpg",
        "title": "Муха",
        "text": "Муха быстро носится по экрану: зависает и резко перелетает. За ней удобно следить и тыкаться лапой.",
    },
    {
        "id": "birds",
        "file": "birds.mp4",
        "thumb": "birds.jpg",
        "title": "Птицы",
        "text": "Птицы быстро пролетают через экран и машут крыльями. Можно следить за одной и тыкаться лапой.",
    },
]


TIER_LABEL = {
    "budget": "подешевле",
    "mid": "средний",
    "premium": "премиум",
}

ARTICLES = [
    {
        "id": "a1",
        "title": "Как читать состав корма",
        "text": "Ингредиенты в составе перечисляются по убыванию массовой доли на момент производства. Первые 3–5 позиций дают основное представление о корме: если это конкретное мясо или мясная мука («курица», «мука из индейки»), а не общие формулировки вроде «мясо и субпродукты животного происхождения», состав обычно прозрачнее. Наличие злаков не делает корм плохим — важен баланс белка, жира и клетчатки под конкретное животное, а не сам факт их присутствия.",
    },
    {
        "id": "a2",
        "title": "Зачем считать суточную норму, а не следовать таблице на пачке",
        "text": "Таблицы на упаковке усреднены и не учитывают породу, стерилизацию, реальную активность и диагнозы конкретного животного. Формула на основе базового обмена и уровня активности даёт индивидуальный ориентир, который можно скорректировать по фактической динамике веса — раз в 2–4 недели.",
    },
    {
        "id": "a3",
        "title": "Стерилизация и обмен веществ",
        "text": "После стерилизации и кастрации энергозатраты животного снижаются в среднем на 20–30% при том же уровне активности, а аппетит часто увеличивается. Это главная причина набора веса в первый год после операции. Снижение суточной нормы и переход на корм с более высоким содержанием белка при умеренном жире помогают удержать вес в норме.",
    },
    {
        "id": "a4",
        "title": "Лишний вес у кошек и собак",
        "text": "Избыточный вес — один из самых частых факторов риска у домашних животных в России: по разным оценкам, с ним сталкивается каждый четвёртый питомец. Он повышает нагрузку на суставы, сердце и увеличивает риск диабета у кошек. Снижение веса должно быть постепенным — резкое ограничение калорийности, особенно у кошек, опасно для печени.",
    },
    {
        "id": "a5",
        "title": "Что значит «лечебный корм» и когда он нужен",
        "text": "Лечебные корма разработаны для животных с подтверждённым диагнозом — например, хронической болезнью почек, мочекаменной болезнью или пищевой аллергией. Их не стоит давать «на всякий случай»: изменённый баланс минералов и белка рассчитан на конкретное состояние и без показаний может быть не полезен, а иногда и вреден.",
    },
    {
        "id": "a6",
        "title": "Переход на новый корм",
        "text": "Резкая смена рациона часто вызывает расстройство пищеварения. Стандартная схема — постепенная замена старого корма новым в течение 7–10 дней, начиная с 25% нового корма и постепенно увеличивая долю. При хронических заболеваниях смену корма стоит согласовывать с лечащим врачом.",
    },
]


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _app_zip() -> Path | None:
    """Путь к app.zip, если Python запущен из архива (сборка Android/iOS)."""
    raw = str(Path(__file__).resolve())
    low = raw.lower()
    idx = low.find(".zip")
    if idx == -1:
        return None
    end = idx + 4
    if end < len(raw) and raw[end] not in "/\\":
        return None
    zp = Path(raw[:end])
    return zp if zp.is_file() else None


_ZIP_NAMES: set[str] | None = None


def _zip_names() -> set[str]:
    global _ZIP_NAMES
    if _ZIP_NAMES is None:
        zp = _app_zip()
        if zp is None:
            _ZIP_NAMES = set()
        else:
            import zipfile
            with zipfile.ZipFile(zp) as zf:
                _ZIP_NAMES = set(zf.namelist())
    return _ZIP_NAMES


def resource(*parts) -> Path:
    if parts and parts[0] == "assets":
        env = os.environ.get("FLET_ASSETS_DIR")
        if env:
            alt = Path(env).joinpath(*parts[1:])
            if alt.exists():
                return alt
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = app_dir()
    return base.joinpath(*parts)


def bundled_exists(*parts) -> bool:
    if resource(*parts).is_file():
        return True
    rel = "/".join(parts)
    return rel in _zip_names()


def read_bundled(*parts) -> bytes:
    path = resource(*parts)
    if path.is_file():
        return path.read_bytes()
    zp = _app_zip()
    rel = "/".join(parts)
    if zp is not None and rel in _zip_names():
        import zipfile
        with zipfile.ZipFile(zp) as zf:
            return zf.read(rel)
    raise FileNotFoundError(rel)


def ensure_file(*parts) -> Path:
    """Реальный файл на диске: как есть, либо копия из app.zip во временную папку."""
    path = resource(*parts)
    if path.is_file():
        return path
    data = read_bundled(*parts)
    root = (
        os.environ.get("FLET_APP_STORAGE_CACHE")
        or os.environ.get("FLET_APP_STORAGE_TEMP")
    )
    if not root:
        import tempfile
        root = tempfile.gettempdir()
    dest = Path(root) / "bundled" / Path(*parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.is_file() or dest.stat().st_size != len(data):
        dest.write_bytes(data)
    return dest


def user_dir() -> Path:
    """Папка питомцев. На телефоне — хранилище приложения, на Windows — как раньше."""
    if os.getenv("FLET_PLATFORM") in ("android", "ios"):
        root = os.environ.get("FLET_APP_STORAGE_DATA")
        path = Path(root) if root else Path.home() / "normalap"
    elif os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        path = root / "Normalap"
    else:
        data = os.environ.get("FLET_APP_STORAGE_DATA")
        path = Path(data) if data else Path.home() / ".normalap"
    path.mkdir(parents=True, exist_ok=True)
    (path / "photos").mkdir(exist_ok=True)
    return path


def is_phone(page: ft.Page) -> bool:
    return bool(page.platform and page.platform.is_mobile())


DIAGNOSIS = {
    "healthy": "Здоров",
    "overweight": "Лишний вес",
    "ckd": "Болезнь почек",
    "diabetes": "Диабет",
    "allergy": "Аллергия",
    "heart": "Сердце",
    "joints": "Суставы",
    "gi": "ЖКТ",
    "urolithiasis": "МКБ",
    "liver": "Печень",
}
ACTIVITY = {
    "low": "Низкая",
    "medium": "Средняя",
    "high": "Высокая",
    "very_high": "Очень высокая",
}
WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WEEKDAYS_FULL_RU = [
    "понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье",
]
MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
MONTHS_GEN_RU = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]
WEIGHT_MAX_PER_DAY = 2
# тип события: ключ, название, иконка Material, цвет метки
EVENT_KINDS = [
    ("vet", "Ветеринар", "MEDICAL_SERVICES", "#E07A5F"),
    ("vaccine", "Прививка", "VACCINES", "#668875"),
    ("med", "Лекарство", "MEDICATION", "#D4A24C"),
    ("groom", "Груминг", "CONTENT_CUT", "#8E7DBE"),
    ("other", "Другое", "EVENT", "#7A746C"),
]
EVENT_KIND_BY_KEY = {k[0]: k for k in EVENT_KINDS}
# самочувствие: ключ, название, варианты (значение, подпись, тревожный ли признак)
HEALTH_METRICS = [
    ("appetite", "Аппетит", [("low", "Слабый", True), ("ok", "Нормальный", False), ("great", "Отличный", False)]),
    ("activity", "Активность", [("low", "Вялый", True), ("ok", "Обычная", False), ("high", "Бодрый", False)]),
    ("stool", "Стул", [("loose", "Жидкий", True), ("ok", "Норма", False), ("hard", "Твёрдый", True)]),
]
HEALTH_SYMPTOMS = [
    ("vomit", "Рвота"), ("cough", "Кашель"), ("itch", "Чешется"),
    ("limp", "Хромает"), ("thirst", "Много пьёт"), ("eyes", "Глаза слезятся"),
]
HEALTH_SYMPTOM_NAMES = dict(HEALTH_SYMPTOMS)
HEALTH_WARN = "#E07A5F"
HEALTH_HONEY = "#D4A24C"
ONBOARD = [
    ("85% семей в России живут с питомцем",
     "Выбрать корм всё равно сложно: на полке десятки пачек, а состав читают единицы."),
    ("Считаем норму, а не верим рекламе",
     "Учитываем вес, породу, стерилизацию, активность и диагноз — и показываем, сколько корма нужно."),
    ("Российские корма и полный состав",
     "В подборе популярные марки: AlphaPet, AJO, Craftia, Мираторг Extra Meat, Bowl Wow, FLORIDA и другие. Данные остаются на устройстве."),
]


class Normalap:
    def __init__(self, page: ft.Page):
        self.page = page
        self.catalog = json.loads(read_bundled("data", "catalog.json").decode("utf-8"))
        try:
            self.breed_info = json.loads(read_bundled("data", "breed_info.json").decode("utf-8"))
        except FileNotFoundError:
            self.breed_info = {}
        self.state = self.load_state()
        tab = int(self.state.get("lastTab") or 0)
        self.tab = tab if tab in (0, 1, 2, 3, 4) else 0
        self.form_pet = None
        self.form_edit = False
        self.onboard_i = 0
        self.open_food = None
        self.open_breed_ids = set()
        self.article_id = None
        self.subview = None
        self.pack_query = ""
        self.pack_brand = None
        self.weight_draft = ""
        self.weight_month = date.today().replace(day=1)
        self.weight_selected = date.today()
        self.weight_adding = False
        self.event_month = date.today().replace(day=1)
        self.event_selected = date.today()
        self.event_adding = False
        self.event_kind = "vet"
        self.event_title_draft = ""
        self.event_time_draft = ""
        self.health_day = date.today()
        self.feed_draft = ""
        self.feed_busy = False
        self._feed_intro = False
        self._bowl_gen = 0
        self.weather_step = "region"
        self.weather_region_id = None
        self._weather_busy = False
        self._weather_fail_at = None
        self._weather_gen = 0
        self.five_cal_open = False
        self.five_month = date.today().replace(day=1)
        self.fun_tab = None
        self.pet_video_id = None
        self.pet_video_full = False
        self._photo_meta = {}
        self.five_game = self.make_five_game()
        self.persist_five()
        self.picker = ft.FilePicker()
        self.apply_palette()
        self.body = ft.Column(expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)
        self.icon_ration = self.nav_img("nav_scale.svg")
        self.icon_ration_on = self.nav_img("nav_scale.svg", selected=True)
        self.icon_breeds = self.nav_img("nav_breeds.png", tint=False)
        self.icon_breeds_on = self.nav_img("nav_breeds_on.png", tint=False)
        self.icon_fun = self.nav_img("nav_fun.png", tint=False)
        self.icon_fun_on = self.nav_img("nav_fun.png", tint=False)
        self.nav = ft.NavigationBar(
            selected_index=self.tab,
            bgcolor=SURFACE,
            indicator_color=CHIP,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.PETS_OUTLINED, selected_icon=ft.Icons.PETS, label="Питомец"),
                ft.NavigationBarDestination(icon=self.icon_ration, selected_icon=self.icon_ration_on, label="Рацион"),
                ft.NavigationBarDestination(icon=self.icon_breeds, selected_icon=self.icon_breeds_on, label="Породы"),
                ft.NavigationBarDestination(icon=self.icon_fun, selected_icon=self.icon_fun_on, label="Развлечения"),
                ft.NavigationBarDestination(icon=ft.Icons.MORE_HORIZ, selected_icon=ft.Icons.MORE_HORIZ, label="Ещё"),
            ],
            on_change=self.on_nav,
        )
        self.header_brand = ft.Text("НормаЛап", size=13, weight=ft.FontWeight.W_800, color=PRIMARY)
        self.header_title = ft.Text("Мой питомец", size=24, weight=ft.FontWeight.W_800, color=TEXT)
        self.header_box = ft.Container(
            ft.Column([self.header_brand, self.header_title], spacing=2),
            padding=ft.Padding.only(left=20, top=12, right=20, bottom=8),
            bgcolor=BG,
        )
        self.body_box = ft.Container(
            self.body,
            expand=True,
            padding=ft.Padding.only(left=16, top=4, right=16, bottom=8),
            bgcolor=BG,
        )
        self.frame = ft.Container(
            ft.Column([self.header_box, self.body_box, self.nav], spacing=0, expand=True),
            expand=True,
            bgcolor=BG,
        )
        self.side_l = ft.Container(width=0, bgcolor=BG)
        self.side_r = ft.Container(width=0, bgcolor=BG)
        page.add(
            ft.SafeArea(
                ft.Row(
                    [self.side_l, self.frame, self.side_r],
                    spacing=0,
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                expand=True,
            )
        )
        self.sync_frame()
        self.render()
        self.page.on_keyboard_event = self.on_key
        self.page.on_resize = self.on_page_resize
        self.wire_system_back()

    def apply_palette(self):
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = BG
        if hasattr(self, "header_box"):
            self.header_box.bgcolor = BG
            self.body_box.bgcolor = BG
            self.nav.bgcolor = SURFACE
            self.nav.indicator_color = CHIP
            self.header_title.color = TEXT
            if hasattr(self, "icon_ration"):
                self.icon_ration.color = MUTED
                self.icon_ration_on.color = PRIMARY

    def sync_frame(self, width=None):
        """На планшете и широком окне колонка как у телефона по центру, на телефоне — во весь экран."""
        w = self.page.width if width is None else width
        wide = (w or 0) >= 720
        self.frame.width = 480 if wide else None
        self.frame.expand = not wide
        self.side_l.expand = wide
        self.side_r.expand = wide
        self.side_l.width = None if wide else 0
        self.side_r.width = None if wide else 0

    def on_page_resize(self, e):
        self.sync_frame(getattr(e, "width", None))
        self.page.update()

    def wire_system_back(self):
        if not is_phone(self.page) or not self.page.views:
            return
        view = self.page.views[0]
        view.can_pop = False
        view.on_confirm_pop = self.on_system_back
        self.page.update()

    async def on_system_back(self, e):
        await e.control.confirm_pop(not self.try_back())

    def try_back(self):
        """Закрыть текущий экран. True — остались в приложении."""
        if not self.state.get("onboardingDone"):
            if self.onboard_i > 0:
                self.onboard_i -= 1
                self.render()
                return True
            return False
        if self.pet_video_full:
            self.pet_video_full = False
            self.render()
            return True
        if self.tab == 3 and self.pet_video_id:
            self.close_pet_video()
            return True
        if self.tab == 3 and self.fun_tab == "letters" and self.five_cal_open:
            self.five_cal_open = False
            self.render()
            return True
        if self.tab == 3 and self.fun_tab:
            self.set_fun_tab(None)
            return True
        if self.form_pet:
            self.cancel_form()
            return True
        if self.article_id:
            self.open_article(None)
            return True
        if self.subview == "weight" and self.weight_adding:
            self.weight_adding = False
            self.render()
            return True
        if self.subview == "events" and self.event_adding:
            self.event_adding = False
            self.render()
            return True
        if self.open_breed_ids:
            self.open_breed_ids = set()
            self.render()
            return True
        if self.subview == "weather":
            self.weather_back()
            return True
        if self.subview:
            self.subview_back()
            return True
        return False

    def nav_img(self, filename, selected=False, tint=True):
        kwargs = {
            "src": f"icons/{filename}",
            "width": 26,
            "height": 26,
            "fit": ft.BoxFit.CONTAIN,
        }
        if tint:
            kwargs["color"] = PRIMARY if selected else MUTED
            kwargs["color_blend_mode"] = ft.BlendMode.SRC_IN
        return ft.Image(**kwargs)

    def face_img(self, species, happy, size=24):
        kind = "cat" if species == "cat" else "dog"
        mood = "happy" if happy else "sad"
        filename = f"face_{kind}_{mood}.png"
        return ft.Image(
            src=f"icons/{filename}",
            width=size,
            height=size,
            fit=ft.BoxFit.CONTAIN,
        )

    def load_state(self):
        path = user_dir() / "state.json"
        base = {
            "pets": [],
            "activePetId": None,
            "onboardingDone": False,
            "theme": "light",
            "selectedFoods": {},
            "weightDiary": {},
            "feedDiary": {},
            "events": {},
            "health": {},
            "transitionDone": {},
            "fiveLetters": {"calendar": {}},
            "lastTab": 0,
            "weatherCityId": None,
            "weatherCache": None,
        }
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                base.update({k: v for k, v in data.items() if v is not None})
                base.setdefault("selectedFoods", {})
                base.setdefault("weightDiary", {})
                base.setdefault("feedDiary", {})
                base.setdefault("events", {})
                base.setdefault("health", {})
                base.setdefault("transitionDone", {})
                base.setdefault("fiveLetters", {})
                if isinstance(base.get("fiveLetters"), dict):
                    base["fiveLetters"].setdefault("calendar", {})
                base.setdefault("lastTab", 0)
                base.setdefault("weatherCityId", None)
                base.setdefault("weatherCache", None)
                for pet in base.get("pets") or []:
                    if pet.get("breedId") == "dog-18":
                        pet["breedId"] = "dog-08"
                base["theme"] = "light"
                return base
            except Exception:
                pass
        return base

    def save(self):
        (user_dir() / "state.json").write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def pets(self):
        return self.state["pets"]

    def active(self):
        pid = self.state.get("activePetId")
        return next((p for p in self.pets() if p["id"] == pid), None)

    def breed_of(self, pet):
        if not pet or pet.get("breedId") in (None, "unknown", "mixed"):
            return None
        lst = self.catalog["cats"] if pet["species"] == "cat" else self.catalog["dogs"]
        return next((b for b in lst if b["id"] == pet["breedId"]), None)

    def photo_of_breed(self, breed_id):
        rel = self.catalog.get("photos", {}).get(breed_id)
        if not rel:
            return None
        parts = rel.replace("\\", "/").split("/")
        if parts[0] == "assets":
            return "/".join(parts[1:]) if bundled_exists(*parts) else None
        path = resource(*parts)
        return str(path) if path.is_file() else None

    def photo_file(self, src):
        if not src:
            return None
        p = Path(src)
        if p.is_file():
            return p
        parts = [x for x in str(src).replace("\\", "/").split("/") if x]
        if parts and parts[0] != "assets":
            parts = ["assets", *parts]
        try:
            return ensure_file(*parts)
        except FileNotFoundError:
            return None

    def photo_meta(self, src):
        """Соотношение сторон кадра — фото уже на белом фоне."""
        if src in self._photo_meta:
            return self._photo_meta[src]
        path = self.photo_file(src)
        aspect = None
        if path:
            try:
                from PIL import Image
                with Image.open(path) as im:
                    w, h = im.size
                    aspect = w / max(h, 1)
            except Exception:
                aspect = None
        self._photo_meta[src] = aspect
        return aspect

    def photo_frame(self, src, height=None, *, width=None, radius=0, fallback=None, min_h=140, max_h=220):
        """Целое фото на белом, высота под кадр."""
        aspect = self.photo_meta(src) if src else None
        if height is None:
            if aspect:
                target = (0.58 * (min_h + max_h)) / aspect
                height = int(max(min_h, min(max_h, target)))
            else:
                height = min_h
        if not src:
            return ft.Container(
                fallback or ft.Icon(ft.Icons.PETS, color=PRIMARY, size=32),
                height=height, width=width, bgcolor=SURFACE,
                alignment=ft.Alignment.CENTER, border_radius=radius,
            )
        return ft.Container(
            ft.Image(
                src=src,
                fit=ft.BoxFit.CONTAIN,
                gapless_playback=True,
                filter_quality=ft.FilterQuality.MEDIUM,
            ),
            height=height,
            width=width,
            bgcolor=SURFACE,
            alignment=ft.Alignment.CENTER,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border_radius=radius,
        )

    def on_nav(self, e):
        new_tab = int(e.control.selected_index)
        if new_tab == 3 and self.tab != 3:
            self.fun_tab = None
            self.pet_video_id = None
            self.pet_video_full = False
        if new_tab != 3:
            self.pet_video_full = False
        self.tab = new_tab
        self.state["lastTab"] = new_tab
        self.save()
        self.form_pet = None
        self.open_food = None
        self.open_breed_ids = set()
        self.article_id = None
        self.subview = None
        self.render()

    def toast(self, text):
        self.page.show_dialog(ft.SnackBar(ft.Text(text, color=BG), bgcolor=TEXT, duration=2500))

    def render(self):
        self.apply_palette()
        titles = ["Сегодня", "Рацион", "Породы", "Развлечения", "Ещё"]
        show_chrome = self.state.get("onboardingDone")
        video_full = bool(
            show_chrome
            and self.tab == 3
            and self.fun_tab == "video"
            and self.pet_video_id
            and self.pet_video_full
        )
        self.header_box.visible = show_chrome and not video_full
        self.header_brand.visible = show_chrome and not video_full
        self.header_title.visible = show_chrome and not video_full
        self.nav.visible = show_chrome and self.form_pet is None and not video_full
        self.body_box.padding = (
            0 if video_full else ft.Padding.only(left=16, top=4, right=16, bottom=8)
        )
        self.body.scroll = None if video_full else ft.ScrollMode.AUTO
        if show_chrome:
            if self.form_pet and not self.form_edit:
                self.header_title.value = "Новый питомец"
            elif self.form_pet:
                self.header_title.value = "Питомец"
            elif self.subview == "weight":
                self.header_title.value = "Вес"
            elif self.subview == "bowl":
                self.header_title.value = "Миска"
            elif self.subview == "weather":
                self.header_title.value = "Погода"
            elif self.subview == "events":
                self.header_title.value = "Календарь"
            elif self.subview == "health":
                self.header_title.value = "Самочувствие"
            elif self.subview == "transition":
                self.header_title.value = "Переход на корм"
            elif self.subview == "pack":
                self.header_title.value = "Корм с полки"
            elif self.tab == 0 and not self.pets():
                self.header_title.value = "Мой питомец"
            else:
                self.header_title.value = titles[self.tab]
        if not show_chrome:
            self.body.controls = [self.view_onboard()]
        elif self.form_pet:
            self.body.controls = [self.view_form()]
        elif self.subview == "weight":
            self.body.controls = [self.view_weight_diary()]
        elif self.subview == "bowl":
            self.body.controls = [self.view_bowl()]
        elif self.subview == "weather":
            self.body.controls = [self.view_weather()]
        elif self.subview == "events":
            self.body.controls = [self.view_events()]
        elif self.subview == "health":
            self.body.controls = [self.view_health()]
        elif self.subview == "transition":
            self.body.controls = [self.view_transition()]
        elif self.subview == "pack":
            self.body.controls = [self.view_pack_check()]
        elif self.tab == 0:
            self.body.controls = [self.view_pets()]
        elif self.tab == 1:
            self.body.controls = [self.view_ration()]
        elif self.tab == 2:
            self.body.controls = [self.view_breeds()]
        elif self.tab == 3:
            self.body.controls = [self.view_fun()]
        else:
            self.body.controls = [self.view_more()]
        self.page.update()
        if show_chrome and self.subview == "bowl" and not self.feed_busy:
            self._bowl_gen = getattr(self, "_bowl_gen", 0) + 1
            self.page.run_task(self._bowl_boot, self._bowl_gen)
        if (
            show_chrome
            and not self.form_pet
            and self.state.get("weatherCityId")
            and self.weather_stale()
            and not self._weather_busy
            and (self.tab == 0 or self.subview == "weather")
        ):
            self._weather_gen += 1
            self.page.run_task(self._weather_load, self._weather_gen, True)

    def view_onboard(self):
        title, text = ONBOARD[self.onboard_i]
        dots = ft.Row([
            ft.Container(
                width=20 if i == self.onboard_i else 7,
                height=7,
                bgcolor=PRIMARY if i == self.onboard_i else BORDER,
                border_radius=4,
            ) for i in range(3)
        ], alignment=ft.MainAxisAlignment.CENTER)
        last = self.onboard_i == len(ONBOARD) - 1
        return ft.Container(
            ft.Column([
                ft.Icon(ft.Icons.PETS, size=72, color=PRIMARY),
                ft.Text(title, size=24, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER, color=TEXT),
                ft.Text(text, size=15, color=MUTED, text_align=ft.TextAlign.CENTER),
                dots,
                ft.Container(height=8),
                self.primary_btn("Начать" if last else "Далее", self.next_onboard),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
            padding=32, alignment=ft.Alignment.CENTER, expand=True,
        )

    def next_onboard(self, e=None):
        if self.onboard_i < len(ONBOARD) - 1:
            self.onboard_i += 1
        else:
            self.state["onboardingDone"] = True
            self.save()
        self.render()

    def primary_btn(self, text, on_click, expand=True):
        return ft.Container(
            content=ft.Row(
                [ft.Text(
                    text, color="white", weight=ft.FontWeight.W_700, size=15,
                    text_align=ft.TextAlign.CENTER, font_family="Nunito",
                )],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            bgcolor=PRIMARY,
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            border_radius=18,
            alignment=ft.Alignment.CENTER,
            on_click=on_click,
            width=float("inf") if expand else None,
        )

    def outline_btn(self, text, on_click, expand=True):
        return ft.Container(
            content=ft.Row(
                [ft.Text(
                    text, color=TEXT, weight=ft.FontWeight.W_700, size=15,
                    text_align=ft.TextAlign.CENTER, font_family="Nunito",
                )],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            bgcolor=SURFACE,
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            border_radius=18,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(width=1.5, color=BORDER),
            on_click=on_click,
            width=float("inf") if expand else None,
        )

    def card(self, *controls, on_click=None, border_color=None):
        return ft.Container(
            ft.Column(list(controls), spacing=8),
            bgcolor=SURFACE, padding=14, border_radius=20,
            border=ft.Border.all(width=1.5, color=border_color or BORDER),
            on_click=on_click,
        )

    def asset_icon(self, filename, width, height):
        return ft.Image(
            src=f"icons/{filename}",
            width=width,
            height=height,
            fit=ft.BoxFit.CONTAIN,
        )

    def credits_footer(self):
        russia = ft.Row([
            self.asset_icon("flag_russia.svg", 36, 24),
            ft.Text(
                "made in Russia",
                size=13.5,
                italic=True,
                weight=ft.FontWeight.W_700,
                color=TEXT,
                font_family="Nunito",
            ),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        hse = ft.Row([
            self.asset_icon("hse.png", 48, 48),
            ft.Text(
                "НИУ ВШЭ",
                size=13,
                weight=ft.FontWeight.W_800,
                color="#102039",
                font_family="Nunito",
            ),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        return ft.Container(
            ft.Row(
                [
                    russia,
                    ft.Container(width=1, height=42, bgcolor=BORDER),
                    hse,
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=SURFACE,
            padding=ft.Padding.symmetric(vertical=16, horizontal=8),
            border_radius=20,
            border=ft.Border.all(width=1.5, color=BORDER),
        )

    def view_pets(self):
        if not self.pets():
            return ft.Column([
                ft.Container(height=40),
                ft.Icon(ft.Icons.PETS, size=64, color=PRIMARY),
                ft.Text("Пока нет питомцев", size=20, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER, color=TEXT),
                ft.Text("Добавьте кошку или собаку — рассчитаем норму и подберём российский корм.",
                        color=MUTED, text_align=ft.TextAlign.CENTER),
                self.primary_btn("Добавить питомца", lambda e: self.start_form(None)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
        pet = self.active() or self.pets()[0]
        if self.state.get("activePetId") != pet["id"]:
            self.state["activePetId"] = pet["id"]
            self.save()
        blocks = []
        if len(self.pets()) > 1:
            blocks.append(self.pet_pills(pet["id"]))
        blocks.append(self.today_hero(pet))
        blocks.append(self.today_tiles(pet))
        blocks.append(self.health_entry_card(pet))
        blocks.append(self.events_entry_card(pet))
        blocks.append(self.today_food_card(pet))
        blocks.append(self.outline_btn("+ Добавить питомца", lambda e: self.start_form(None)))
        blocks.append(ft.Container(height=16))
        return ft.Column(blocks, spacing=12)

    def pet_pills(self, active_id):
        pills = []
        for p in self.pets():
            on = p["id"] == active_id
            pills.append(ft.Container(
                ft.Text(
                    p.get("name") or "Без имени",
                    size=13, weight=ft.FontWeight.W_700,
                    color="white" if on else MUTED, font_family="Nunito",
                ),
                bgcolor=PRIMARY if on else SURFACE,
                padding=ft.Padding.symmetric(horizontal=14, vertical=9),
                border_radius=20,
                border=ft.Border.all(width=1.5, color=PRIMARY if on else BORDER),
                on_click=lambda e, x=p: self.select_pet(x),
            ))
        return ft.Row(pills, spacing=8, scroll=ft.ScrollMode.AUTO)

    def today_hero(self, pet):
        breed = self.breed_of(pet)
        breed_name = breed["name"] if breed else ("Метис" if pet.get("breedId") == "mixed" else "Порода неизвестна")
        s = nutrition.summary(pet)
        src = pet.get("photoPath") or self.photo_of_breed(pet.get("breedId"))
        try:
            weight_txt = f"{float(pet.get('weightKg') or 0):g} кг"
        except (TypeError, ValueError):
            weight_txt = f"{pet.get('weightKg')} кг"
        meta = f"{weight_txt} · {self.age_label(pet.get('ageMonths') or 0)}"
        if pet.get("sterilized"):
            meta += " · стерил."
        today = date.today()
        weekday = WEEKDAYS_FULL_RU[today.weekday()]
        date_line = f"{weekday.capitalize()}, {today.day} {MONTHS_GEN_RU[today.month - 1]}"
        kcal_note = "норма на сегодня"
        if s.get("treatKcal"):
            kcal_note = f"на корм {s['foodKcal']} · лакомства {s['treatKcal']}"
        cover = None
        if src:
            cover = self.photo_frame(src, min_h=150, max_h=210)
        body = [
            ft.Text(date_line, size=13, weight=ft.FontWeight.W_700, color=MUTED, font_family="Nunito"),
            ft.Text(
                pet.get("name") or "Без имени",
                size=22, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito",
            ),
            ft.Text(f"{breed_name} · {meta}", size=13, color=MUTED, font_family="Nunito"),
            ft.Container(
                ft.Row([
                    ft.Container(
                        ft.Column([
                            ft.Text(str(s["kcal"]), size=24, weight=ft.FontWeight.W_800, color=TEXT,
                                    text_align=ft.TextAlign.CENTER, font_family="Nunito"),
                            ft.Text("ккал", size=11, weight=ft.FontWeight.W_700, color=MUTED,
                                    text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                        width=88, height=88, border_radius=44, bgcolor=SURFACE,
                        alignment=ft.Alignment.CENTER,
                        border=ft.Border.all(width=5, color=PRIMARY),
                    ),
                    ft.Column([
                        ft.Text("Сколько нужно сегодня", size=13, weight=ft.FontWeight.W_700,
                                color=MUTED, font_family="Nunito"),
                        ft.Text(kcal_note, size=15, weight=ft.FontWeight.W_700, color=TEXT,
                                font_family="Nunito"),
                        ft.Container(
                            ft.Text("Изменить профиль →", size=13, weight=ft.FontWeight.W_700,
                                    color=PRIMARY, font_family="Nunito"),
                            on_click=lambda e, p=pet: self.start_form(p),
                            padding=ft.Padding.only(top=4),
                        ),
                    ], spacing=4, expand=True),
                ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CHIP, padding=14, border_radius=20,
            ),
        ]
        inner = []
        if cover:
            inner.append(cover)
        inner.append(ft.Container(ft.Column(body, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), padding=16))
        return ft.Container(
            ft.Column(inner, spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            bgcolor=SURFACE, border_radius=24,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(width=1.5, color=BORDER),
            shadow=ft.BoxShadow(blur_radius=18, spread_radius=0, offset=ft.Offset(0, 6), color="#2C2A2614"),
        )

    def today_tiles(self, pet):
        diary = self.state.get("weightDiary", {}).get(pet["id"], [])
        logged = bool(self.weight_entries_on(diary, date.today()))
        snap = self.weather_snap()
        city = weather.find_city(self.state.get("weatherCityId"))
        if snap and snap.get("temp") is not None:
            weather_icon = ft.Text(
                f"{int(round(snap['temp']))}°",
                size=22, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito",
            )
            weather_sub = snap.get("word") or "сейчас"
        elif city:
            weather_icon = self.weather_ft_icon("WB_CLOUDY", 26)
            weather_sub = "обновить"
        else:
            weather_icon = self.weather_ft_icon("LOCATION_ON", 26)
            weather_sub = "город"
        return ft.Row([
            self.today_tile(
                self.face_img(pet.get("species"), logged, size=28),
                "Вес",
                "записан" if logged else "добавить",
                lambda e, p=pet: self.open_weight(p),
                highlight=not logged,
            ),
            self.today_tile(
                weather_icon,
                "Погода",
                weather_sub,
                self.open_weather,
                highlight=not city or weather.alert(snap),
            ),
            self.today_tile(
                ft.Icon(
                    ft.Icons.PETS if pet.get("species") == "cat" else ft.Icons.CRUELTY_FREE,
                    size=26, color=PRIMARY,
                ),
                "Миска",
                self.feed_tile_sub(pet),
                lambda e, p=pet: self.open_bowl(p),
                highlight=self.feed_ratio(pet) < 0.9,
            ),
        ], spacing=8)

    def today_tile(self, icon, title, sub, on_click, highlight=False):
        return ft.Container(
            ft.Column([
                icon,
                ft.Text(title, size=13, weight=ft.FontWeight.W_800, color=TEXT,
                        text_align=ft.TextAlign.CENTER, font_family="Nunito"),
                ft.Text(sub, size=11, weight=ft.FontWeight.W_700, color=PRIMARY_DARK if highlight else MUTED,
                        text_align=ft.TextAlign.CENTER, font_family="Nunito",
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            expand=True, height=108, alignment=ft.Alignment.CENTER,
            bgcolor=CHIP if highlight else SURFACE,
            padding=10, border_radius=20,
            border=ft.Border.all(width=1.5, color=PRIMARY if highlight else BORDER),
            on_click=on_click,
        )

    def today_pick(self, pet):
        foods = self.catalog.get("foods") or []
        fid = (self.state.get("selectedFoods") or {}).get(pet["id"])
        if fid:
            food = next((f for f in foods if f.get("id") == fid), None)
            if food:
                return food, None, True
        breed = self.breed_of(pet)
        matched = matcher.match(pet, breed, foods)
        items = matched.get("best") or matched.get("medical") or matched.get("good") or []
        if items:
            return items[0]["food"], items[0], False
        return None, None, False

    def today_food_card(self, pet):
        food, item, chosen = self.today_pick(pet)
        if not food:
            return ft.Container(
                ft.Column([
                    ft.Text("Корм на сегодня", size=13, weight=ft.FontWeight.W_800, color=PRIMARY_DARK),
                    ft.Text("Подберём корм на вкладке «Рацион».", size=14, color=MUTED),
                ], spacing=6),
                bgcolor=SURFACE, padding=16, border_radius=20,
                border=ft.Border.all(width=1.5, color=BORDER),
                on_click=lambda e: self.goto(1),
            )
        grams = nutrition.portion_grams(pet, food)
        why = (item["reasons"][0] if item and item.get("reasons") else "Откройте рацион — там порция и состав")
        form = "влажный" if food.get("form") == "wet" else "сухой"
        label = "Вы выбрали" if chosen else "Корм на сегодня"
        return ft.Container(
            ft.Column([
                ft.Row([
                    ft.Container(
                        ft.Text(label, size=11, weight=ft.FontWeight.W_800, color=PRIMARY_DARK, font_family="Nunito"),
                        bgcolor=CHIP, padding=ft.Padding.symmetric(horizontal=10, vertical=4), border_radius=10,
                    ),
                    ft.Container(expand=True),
                    ft.Text(f"{grams} г", size=22, weight=ft.FontWeight.W_800, color=PRIMARY, font_family="Nunito"),
                ]),
                ft.Text(food["name"], size=17, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito",
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{food.get('brand')} · {form}", size=13, color=MUTED, font_family="Nunito"),
                ft.Text(why, size=13.5, color=MUTED, font_family="Nunito",
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text("Насыпать в миску →", size=14, weight=ft.FontWeight.W_700, color=PRIMARY, font_family="Nunito"),
            ], spacing=6),
            bgcolor=SURFACE, padding=16, border_radius=22,
            border=ft.Border.all(width=2, color=PRIMARY),
            on_click=lambda e, p=pet: self.open_bowl(p),
        )

    def weather_ft_icon(self, name, size=26, color=None):
        icon = getattr(ft.Icons, name, None) or getattr(ft.Icons, "CLOUD", ft.Icons.PETS)
        return ft.Icon(icon, size=size, color=color or PRIMARY)

    def weather_snap(self):
        city_id = self.state.get("weatherCityId")
        cache = self.state.get("weatherCache") or {}
        if not city_id or cache.get("cityId") != city_id:
            return None
        return cache.get("snap")

    def weather_stale(self, ttl=30 * 60):
        city_id = self.state.get("weatherCityId")
        if not city_id:
            return False
        fail = self._weather_fail_at
        if fail and (datetime.now() - fail).total_seconds() < 300:
            return False
        cache = self.state.get("weatherCache") or {}
        if cache.get("cityId") != city_id:
            return True
        raw = cache.get("at")
        if not raw:
            return True
        try:
            ts = datetime.fromisoformat(str(raw))
        except ValueError:
            return True
        return (datetime.now() - ts).total_seconds() > ttl

    def open_weather(self, e=None):
        pet = self.active()
        if pet:
            self.state["activePetId"] = pet["id"]
        self.tab = 0
        self.nav.selected_index = 0
        self.state["lastTab"] = 0
        self.save()
        self.form_pet = None
        self.subview = "weather"
        if self.state.get("weatherCityId"):
            self.weather_step = "forecast"
        else:
            self.weather_step = "region"
            self.weather_region_id = None
        self.render()

    def weather_back(self, e=None):
        if self.weather_step == "city":
            self.weather_step = "region"
            self.weather_region_id = None
            self.render()
            return
        if self.weather_step == "region" and self.state.get("weatherCityId"):
            self.weather_step = "forecast"
            self.render()
            return
        self.subview_back()

    def pick_weather_region(self, region_id, e=None):
        self.weather_region_id = region_id
        self.weather_step = "city"
        self.render()

    def pick_weather_city(self, city_id, e=None):
        self.state["weatherCityId"] = city_id
        self.state["weatherCache"] = None
        self.save()
        self.weather_step = "forecast"
        self._weather_fail_at = None
        self._weather_busy = True
        self._weather_gen += 1
        self.render()
        self.page.run_task(self._weather_load, self._weather_gen, False)

    def change_weather_city(self, e=None):
        self.weather_step = "region"
        self.weather_region_id = None
        self.render()

    def refresh_weather(self, e=None):
        if not self.state.get("weatherCityId") or self._weather_busy:
            return
        self._weather_fail_at = None
        self._weather_busy = True
        self._weather_gen += 1
        self.render()
        self.page.run_task(self._weather_load, self._weather_gen, False)

    async def _weather_load(self, gen, silent=True):
        city = weather.find_city(self.state.get("weatherCityId"))
        if not city or gen != self._weather_gen:
            return
        self._weather_busy = True
        try:
            snap = await asyncio.to_thread(weather.fetch, city["lat"], city["lon"])
            if gen != self._weather_gen:
                return
            self.state["weatherCache"] = {
                "cityId": city["id"],
                "at": datetime.now().isoformat(),
                "snap": snap,
            }
            self.save()
            self._weather_fail_at = None
        except Exception:
            if gen != self._weather_gen:
                return
            self._weather_fail_at = datetime.now()
            if not silent:
                self.toast("Погоду сейчас не достать — нажмите обновить")
        finally:
            if gen == self._weather_gen:
                self._weather_busy = False
                if self.subview == "weather" or (self.tab == 0 and not self.subview and not self.form_pet):
                    self.render()

    def weather_city_count(self, n):
        n = int(n)
        if n % 100 in (11, 12, 13, 14):
            word = "городов"
        elif n % 10 == 1:
            word = "город"
        elif n % 10 in (2, 3, 4):
            word = "города"
        else:
            word = "городов"
        return f"{n} {word}"

    def weather_place_row(self, title, sub, on_click):
        return ft.Container(
            ft.Row([
                ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=TEXT, font_family="Nunito"),
                    ft.Text(sub, size=12, color=MUTED, font_family="Nunito") if sub else ft.Container(height=0),
                ], spacing=1, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=10),
            on_click=on_click,
        )

    def view_weather(self):
        back = ft.TextButton("‹ Назад", on_click=self.weather_back)
        if self.weather_step == "city":
            region = weather.find_region(self.weather_region_id)
            if not region:
                self.weather_step = "region"
                return self.view_weather()
            rows = [
                self.weather_place_row(
                    city["name"],
                    None,
                    lambda e, cid=city["id"]: self.pick_weather_city(cid),
                )
                for city in region["cities"]
            ]
            return ft.Column([
                back,
                ft.Text(region["name"], size=22, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
                ft.Text(
                    "Выберите город — по нему покажу погоду."
                    if len(region["cities"]) > 1 else "В этой области один крупный город.",
                    size=14, color=MUTED, font_family="Nunito",
                ),
                self.card(*rows),
                ft.Container(height=24),
            ], spacing=12)

        if self.weather_step == "forecast":
            return self.view_weather_forecast(back)

        regions_col = ft.Column(spacing=0)

        def region_rows(query=""):
            q = (query or "").strip().lower().replace("ё", "е")
            rows = []
            for region in weather.regions():
                names = [c["name"] for c in region["cities"]]
                hay = (region["name"] + " " + " ".join(names)).lower().replace("ё", "е")
                if q and q not in hay:
                    continue
                preview = " · ".join(names[:3])
                if len(names) > 3:
                    preview += f" · ещё {len(names) - 3}"
                rows.append(self.weather_place_row(
                    region["name"],
                    preview,
                    lambda e, rid=region["id"]: self.pick_weather_region(rid),
                ))
            if not rows:
                rows.append(ft.Container(
                    ft.Text("Такой области не нашла. Попробуйте начало названия.",
                            size=14, color=MUTED, font_family="Nunito"),
                    padding=ft.Padding.symmetric(vertical=12),
                ))
            return rows

        regions_col.controls = region_rows()

        def on_search(e):
            regions_col.controls = region_rows(e.control.value)
            self._bowl_touch(regions_col)

        search = ft.TextField(
            hint_text="Найти область или город",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=14, bgcolor=SURFACE, color=TEXT, border_color=BORDER,
            on_change=on_search,
        )
        return ft.Column([
            back,
            ft.Text("Где вы живёте", size=22, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
            ft.Text("Сначала выберите область, потом один из её крупных городов.",
                    size=14, color=MUTED, font_family="Nunito"),
            search,
            self.card(regions_col),
            ft.Container(height=24),
        ], spacing=12)

    def view_weather_forecast(self, back):
        city = weather.find_city(self.state.get("weatherCityId"))
        snap = self.weather_snap()
        if not city:
            self.weather_step = "region"
            return self.view_weather()
        if self._weather_busy and not snap:
            status = ft.Text("Спрашиваю погоду…", size=15, color=MUTED, font_family="Nunito")
        elif snap and snap.get("temp") is not None:
            status = ft.Column([
                self.weather_ft_icon(weather.icon_name(snap.get("code")), 42),
                ft.Text(
                    f"{int(round(snap['temp']))}°",
                    size=56, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito",
                ),
                ft.Text(
                    snap.get("word") or weather.label(snap.get("code")),
                    size=18, weight=ft.FontWeight.W_700, color=TEXT, font_family="Nunito",
                ),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            status = ft.Text("Погоду пока не вижу — нажмите обновить.", size=15, color=MUTED, font_family="Nunito")
        meta_bits = []
        if snap and snap.get("feels") is not None:
            meta_bits.append(f"ощущается как {int(round(snap['feels']))}°")
        if snap and snap.get("wind") is not None:
            meta_bits.append(f"ветер {int(round(snap['wind']))} м/с")
        meta = " · ".join(meta_bits)
        return ft.Column([
            back,
            ft.Column([
                status,
                ft.Text(
                    f"{city['name']} · {city['regionName']}",
                    size=14, color=MUTED, font_family="Nunito",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(meta, size=13, color=MUTED, font_family="Nunito") if meta else ft.Container(height=0),
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            self.outline_btn("Сменить город", self.change_weather_city),
            self.outline_btn("Обновить", self.refresh_weather),
            ft.Container(height=24),
        ], spacing=14)

    def open_weight(self, pet):
        self.state["activePetId"] = pet["id"]
        self.tab = 0
        self.nav.selected_index = 0
        self.state["lastTab"] = 0
        self.save()
        self.subview = "weight"
        self.weight_draft = ""
        self.weight_month = date.today().replace(day=1)
        self.weight_selected = date.today()
        self.weight_adding = False
        self.form_pet = None
        self.render()

    def open_bowl(self, pet):
        self.state["activePetId"] = pet["id"]
        self.tab = 0
        self.nav.selected_index = 0
        self.state["lastTab"] = 0
        self.save()
        self.subview = "bowl"
        self.feed_draft = str(self.feed_portion_for(pet, self.feed_suggest_meal(pet)))
        self.feed_busy = False
        self._feed_intro = True
        self.form_pet = None
        self.render()

    def feed_entries(self, pet):
        return list((self.state.get("feedDiary") or {}).get(pet["id"]) or [])

    def feed_entries_today(self, pet):
        day = date.today().isoformat()
        return [e for e in self.feed_entries(pet) if str(e.get("date") or "") == day]

    def feed_grams_today(self, pet):
        return int(sum(int(e.get("grams") or 0) for e in self.feed_entries_today(pet)))

    def feed_norm_grams(self, pet):
        food, _, _ = self.today_pick(pet)
        if food:
            return max(5, nutrition.portion_grams(pet, food))
        return max(5, int(round(nutrition.kcal_day(pet) / 370 * 100 / 5.0) * 5))

    def feed_ratio(self, pet):
        norm = self.feed_norm_grams(pet)
        return self.feed_grams_today(pet) / max(norm, 1)

    def feed_fill_height(self, ratio):
        r = max(0.0, min(1.0, float(ratio)))
        if r <= 0:
            return 0
        return 14 + r * bowl.FILL_MAX

    def feed_fill_colors(self, pet):
        food, _, _ = self.today_pick(pet)
        return bowl.fill_colors(bool(food and food.get("form") == "wet"))

    def feed_is_wet(self, pet):
        food, _, _ = self.today_pick(pet)
        return bool(food and food.get("form") == "wet")

    def feed_portions(self, norm):
        """Дневная норма делится на три равных приёма; остаток от округления идёт на вечер."""
        norm = max(3, int(norm))
        part = max(1, int(round(norm / 3)))
        morning = part
        day = part
        evening = max(1, norm - morning - day)
        return morning, day, evening

    def feed_portion_for(self, pet, meal):
        morning, day, evening = self.feed_portions(self.feed_norm_grams(pet))
        if meal == "morning":
            return morning
        if meal == "day":
            return day
        if meal == "evening":
            return evening
        return max(5, morning)

    def feed_meals_today(self, pet):
        """Одно нажатие — один приём: первое утро, второе день, третье вечер."""
        n = len(self.feed_entries_today(pet))
        return n >= 1, n >= 2, n >= 3

    def feed_suggest_meal(self, pet):
        """Рекомендуем следующий по порядку приём, а не по часам: так подсветка совпадает с миской."""
        n = len(self.feed_entries_today(pet))
        if n < 3:
            return ("morning", "day", "evening")[n]
        return "extra"

    def feed_week_marks(self, pet):
        today = date.today()
        marks = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            key = d.isoformat()
            grams = sum(int(e.get("grams") or 0) for e in self.feed_entries(pet) if str(e.get("date") or "") == key)
            marks.append((d, grams))
        return marks

    def feed_tile_sub(self, pet):
        eaten = self.feed_grams_today(pet)
        ratio = eaten / max(self.feed_norm_grams(pet), 1)
        if eaten <= 0:
            return "насыпать"
        if ratio > 1.0:
            return "достаточно"
        if ratio >= 0.92:
            return "норма"
        return f"{eaten} г"

    def feed_caption(self, pet):
        eaten = self.feed_grams_today(pet)
        norm = self.feed_norm_grams(pet)
        ratio = eaten / max(norm, 1)
        left = max(0, norm - eaten)
        hour = datetime.now().hour
        if eaten <= 0:
            if hour < 12:
                return "Утренняя порция ещё в пакете."
            if hour < 18:
                return "Дневная миска ждёт своего часа."
            return "Вечерняя порция ещё не насыпана."
        if ratio > 1.0:
            return "Вы насыпали уже достаточно корма."
        if ratio < 0.40:
            return f"Утро. До нормы ещё {left} г."
        if ratio < 0.80:
            return f"День. До нормы ещё {left} г."
        return "Вечер — миска полная."

    def log_feed(self, grams, meal):
        pet = self.active()
        if not pet:
            return
        try:
            grams = int(round(float(str(grams).replace(",", ".").strip())))
        except (TypeError, ValueError):
            self.toast("Напишите, сколько граммов насыпать")
            return
        if grams <= 0:
            self.toast("Нужно хотя бы немного корма")
            return
        norm = self.feed_norm_grams(pet)
        if grams > norm * 3:
            self.toast("Слишком много за раз — проверьте граммы")
            return
        pours_before = len(self.feed_entries_today(pet))
        if pours_before < 3:
            # какая бы кнопка ни была нажата, засчитывается ближайший по порядку приём
            slot = ("morning", "day", "evening")[pours_before]
            if meal in ("morning", "day", "evening"):
                grams = self.feed_portion_for(pet, slot)
            meal = slot
        old_ratio = self.feed_ratio(pet)
        diary = self.state.setdefault("feedDiary", {}).setdefault(pet["id"], [])
        diary.append({
            "id": "f" + uuid.uuid4().hex[:8],
            "date": date.today().isoformat(),
            "grams": grams,
            "meal": meal,
            "at": datetime.now().strftime("%H:%M"),
        })
        self.save()
        self.feed_draft = str(self.feed_portion_for(pet, self.feed_suggest_meal(pet)))
        new_ratio = self.feed_ratio(pet)
        if pours_before >= 4:
            self.toast("В миску уже четыре горсти — больше не сыплю")
            self._feed_intro = False
            if not self.feed_busy and self.subview == "bowl":
                self.render()
            return
        if old_ratio <= 1.0 < new_ratio:
            self.toast("Вы насыпали уже достаточно корма")
        self._bowl_target = pours_before + 1
        if self.feed_busy:
            return
        self.page.run_task(self._bowl_pour)

    def undo_feed(self, e=None):
        pet = self.active()
        if not pet or self.feed_busy:
            return
        today = self.feed_entries_today(pet)
        if not today:
            self.toast("Сегодня ещё ничего не сыпали")
            return
        last = today[-1]
        diary = self.state.setdefault("feedDiary", {}).setdefault(pet["id"], [])
        self.state["feedDiary"][pet["id"]] = [e for e in diary if e.get("id") != last.get("id")]
        self.save()
        self._feed_intro = False
        self.render()
        self.toast(f"Убрала {last.get('grams')} г")

    def _bowl_touch(self, ctrl):
        if not ctrl:
            return
        try:
            ctrl.update()
        except Exception:
            pass

    def view_bowl(self):
        pet = self.active()
        if not pet:
            return ft.Column([
                ft.TextButton("‹ Назад", on_click=self.subview_back),
                ft.Text("Сначала добавьте питомца", color=MUTED),
            ])
        eaten = self.feed_grams_today(pet)
        norm = self.feed_norm_grams(pet)
        ratio = eaten / max(norm, 1)
        is_cat = pet.get("species") == "cat"
        name = pet.get("name") or "Питомец"
        food, _, _ = self.today_pick(pet)
        food_name = food["name"] if food else "корм по норме"
        self._bowl_ratio = ratio
        self._bowl_is_cat = is_cat

        anim = ft.Animation(720, ft.AnimationCurve.EASE_OUT_CUBIC)
        pours = min(4, len(self.feed_entries_today(pet)))
        seed = f"{pet['id']}:{date.today().isoformat()}:{int(self.feed_is_wet(pet))}"
        previous = getattr(self, "_bowl_scene", None)
        scene_now = bowl_live.BowlLive(wet=self.feed_is_wet(pet), seed=seed)
        if previous is not None and previous.seed == seed and previous.done == pours and not previous.busy:
            scene_now.restore(previous.export_state())
        else:
            scene_now.settle(pours)
        self._bowl_scene = scene_now
        self._bowl_target = pours
        self._bowl_dots = [
            ft.Container(
                width=70, height=6, border_radius=3,
                bgcolor=PRIMARY if i < pours else CHIP,
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            )
            for i in range(3)
        ]
        meal_marks = ft.Row(
            [
                ft.Column(
                    [
                        self._bowl_dots[i],
                        ft.Text(
                            bowl_live.MEALS[i], size=11,
                            weight=ft.FontWeight.W_800 if i < pours else ft.FontWeight.W_600,
                            color=TEXT if i < pours else MUTED, font_family="Nunito",
                        ),
                    ],
                    spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
                for i in range(3)
            ],
            alignment=ft.MainAxisAlignment.CENTER, spacing=8,
        )
        scene = ft.Container(
            scene_now.canvas,
            width=bowl_live.VIEW_W,
            height=bowl_live.VIEW_H,
            border_radius=18,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor="#FBF4EA",
        )

        morning_g, day_g, evening_g = self.feed_portions(norm)
        leftover = max(0, norm - eaten)
        status_color = ACCENT if ratio > 1.0 else (PRIMARY if ratio >= 0.92 else MUTED)
        bar_w = int(228 * min(1.0, ratio))
        self._bowl_bar = ft.Container(
            width=0 if self._feed_intro else bar_w, height=8,
            bgcolor=ACCENT if ratio > 1.0 else PRIMARY,
            border_radius=8, animate_size=anim,
        )
        self._bowl_bar_target = bar_w
        self._bowl_stat = ft.Text(
            f"{eaten} из {norm} г",
            size=28, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito",
            text_align=ft.TextAlign.CENTER,
        )
        self._bowl_note = ft.Text(
            self.feed_caption(pet), size=14, color=status_color, font_family="Nunito",
            text_align=ft.TextAlign.CENTER,
        )
        happy = eaten > 0 and 0.78 <= ratio <= 1.0
        mood = ft.Row([
            self.face_img(pet.get("species"), happy, size=22),
            ft.Text(
                "сыт и доволен" if happy else ("уже достаточно" if ratio > 1.0 else "ждёт горсть"),
                size=13, weight=ft.FontWeight.W_700, color=MUTED, font_family="Nunito",
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)

        today_e = self.feed_entries_today(pet)
        last_line = None
        if today_e:
            last = today_e[-1]
            last_line = ft.Text(
                f"Последняя горсть в {last.get('at') or '—'}",
                size=12, color=MUTED, font_family="Nunito", text_align=ft.TextAlign.CENTER,
            )

        morning, day, evening = self.feed_meals_today(pet)

        suggest_now = self.feed_suggest_meal(pet)

        def meal_slot(title, done, meal, grams):
            now = meal == suggest_now and not done
            return ft.Container(
                ft.GestureDetector(
                    on_tap=lambda e, g=grams, m=meal: self.log_feed(g, m),
                    content=ft.Container(
                        ft.Column([
                            ft.Row([
                                ft.Container(
                                    width=10, height=10, border_radius=5,
                                    bgcolor=PRIMARY if done else SURFACE,
                                    border=ft.Border.all(width=1.5, color=PRIMARY if (done or now) else BORDER),
                                ),
                                ft.Text(title, size=13, weight=ft.FontWeight.W_800,
                                        color=TEXT if (done or now) else MUTED, font_family="Nunito"),
                            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                            ft.Text(f"{grams} г", size=12, weight=ft.FontWeight.W_700,
                                    color=PRIMARY_DARK if (done or now) else MUTED, font_family="Nunito"),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=CHIP if done else ("#D7E4D6" if now else BG),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=10), border_radius=14,
                        border=ft.Border.all(width=1.5, color=PRIMARY if (done or now) else BORDER),
                        alignment=ft.Alignment.CENTER,
                    ),
                ),
                expand=True,
            )

        week_names = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
        week_dots = []
        for d, grams in self.feed_week_marks(pet):
            filled = grams > 0
            is_today = d == date.today()
            week_dots.append(ft.Column([
                ft.Container(
                    width=12, height=12, border_radius=6,
                    bgcolor=PRIMARY if filled else SURFACE,
                    border=ft.Border.all(width=1.6, color=PRIMARY if (filled or is_today) else BORDER),
                ),
                ft.Text(week_names[d.weekday()], size=10, color=TEXT if is_today else MUTED,
                        font_family="Nunito", weight=ft.FontWeight.W_700 if is_today else ft.FontWeight.W_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2))

        chips = []
        labels = {"morning": "утро", "day": "день", "evening": "вечер", "extra": "ещё"}
        for entry in reversed(today_e):
            chips.append(ft.Container(
                ft.Text(
                    f"{entry.get('at') or '—'} · {labels.get(entry.get('meal'), 'ещё')} · {entry.get('grams')} г",
                    size=12, weight=ft.FontWeight.W_700, color=TEXT, font_family="Nunito",
                ),
                bgcolor=CHIP, padding=ft.Padding.symmetric(horizontal=10, vertical=6), border_radius=12,
            ))
        if not chips:
            chips.append(ft.Text("Сегодня ещё не сыпали", size=13, color=MUTED, font_family="Nunito"))

        grams_field = ft.TextField(
            label="Свои граммы",
            value=self.feed_draft,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=14, bgcolor=SURFACE, color=TEXT, border_color=BORDER,
            on_change=lambda e: setattr(self, "feed_draft", e.control.value),
        )
        suggest = self.feed_suggest_meal(pet)

        meal_words = {"morning": "утреннюю", "day": "дневную", "evening": "вечернюю"}
        if suggest in meal_words:
            suggest_g = {"morning": morning_g, "day": day_g, "evening": evening_g}[suggest]
            rec_lines = [
                ft.Text(
                    f"Норма на сегодня {norm} г — делим на три приёма",
                    size=12, weight=ft.FontWeight.W_700, color=MUTED, font_family="Nunito",
                ),
                ft.Text(
                    f"Дальше: {meal_words[suggest]} порцию — {suggest_g} г",
                    size=15, weight=ft.FontWeight.W_800, color=PRIMARY_DARK, font_family="Nunito",
                ),
                ft.Text(
                    f"Утро {morning_g} г · День {day_g} г · Вечер {evening_g} г",
                    size=12, color=MUTED, font_family="Nunito",
                ),
            ]
        elif ratio >= 1.0:
            rec_lines = [
                ft.Text(
                    f"Норма на сегодня {norm} г уже в миске",
                    size=15, weight=ft.FontWeight.W_800, color=PRIMARY_DARK, font_family="Nunito",
                ),
            ]
        else:
            rec_lines = [
                ft.Text(
                    f"Приёмы на сегодня прошли — до нормы ещё {leftover} г",
                    size=15, weight=ft.FontWeight.W_800, color=PRIMARY_DARK, font_family="Nunito",
                ),
            ]
        rec_block = ft.Container(
            ft.Column(rec_lines, spacing=3),
            bgcolor="#EAF1E8", padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=16, border=ft.Border.all(width=1.5, color=PRIMARY),
        )

        note_block = self._bowl_note
        if ratio > 1.0 and not self._feed_intro:
            note_block = ft.Container(
                ft.Text(
                    "Вы насыпали уже достаточно корма",
                    size=14, weight=ft.FontWeight.W_800, color=ACCENT,
                    font_family="Nunito", text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT_SOFT,
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                border_radius=14,
                border=ft.Border.all(width=1.5, color=ACCENT),
                margin=ft.Margin.only(left=8, right=8, top=4),
            )
        card_bits = [
            ft.Row([scene], alignment=ft.MainAxisAlignment.CENTER),
            meal_marks,
            self._bowl_stat,
            ft.Container(
                ft.Container(self._bowl_bar, height=8, border_radius=8),
                width=228, height=8, bgcolor=CHIP, border_radius=8,
            ),
            note_block,
            mood,
            ft.Text(food_name, size=13, color=MUTED, text_align=ft.TextAlign.CENTER,
                    font_family="Nunito", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
        ]
        if last_line:
            card_bits.append(last_line)

        return ft.Column([
            ft.TextButton("‹ К питомцу", on_click=self.subview_back),
            ft.Text(
                f"Миска · {name}",
                size=13, weight=ft.FontWeight.W_700, color=MUTED, font_family="Nunito",
            ),
            rec_block,
            ft.Container(
                ft.Column(card_bits, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=SURFACE, padding=ft.Padding.only(top=8, bottom=16, left=8, right=8),
                border_radius=28, border=ft.Border.all(width=1.5, color=BORDER),
                shadow=ft.BoxShadow(blur_radius=18, offset=ft.Offset(0, 8), color="#2C2A2614"),
            ),
            ft.Row([
                meal_slot("Утро", morning, "morning", morning_g),
                meal_slot("День", day, "day", day_g),
                meal_slot("Вечер", evening, "evening", evening_g),
            ], spacing=8),
            ft.Row(week_dots, spacing=0, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            grams_field,
            self.primary_btn("Насыпать в миску", lambda e: self.log_feed(self.feed_draft, "extra")),
            ft.Row([
                ft.Container(self.outline_btn("Отменить последнюю", self.undo_feed), expand=True),
            ]),
            ft.Text("Сегодня", size=13, weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
            ft.Row(chips, wrap=True, spacing=6, run_spacing=6),
            ft.Container(height=12),
        ], spacing=10)

    def _sync_bowl_numbers(self):
        pet = self.active()
        if not pet:
            return
        eaten = self.feed_grams_today(pet)
        norm = self.feed_norm_grams(pet)
        ratio = eaten / max(norm, 1)
        bar = getattr(self, "_bowl_bar", None)
        if bar:
            bar.width = int(228 * min(1.0, ratio))
            bar.bgcolor = ACCENT if ratio > 1.0 else PRIMARY
            self._bowl_touch(bar)
        stat = getattr(self, "_bowl_stat", None)
        if stat:
            stat.value = f"{eaten} из {norm} г"
            self._bowl_touch(stat)

    async def _bowl_boot(self, gen):
        await asyncio.sleep(0.05)
        if gen != getattr(self, "_bowl_gen", 0) or self.subview != "bowl":
            return
        bar = getattr(self, "_bowl_bar", None)
        if bar:
            bar.width = getattr(self, "_bowl_bar_target", bar.width)
            self._bowl_touch(bar)

    async def _bowl_pour(self):
        self._bowl_gen += 1
        gen = self._bowl_gen
        self.feed_busy = True
        self._feed_intro = False
        scene = getattr(self, "_bowl_scene", None)
        try:
            self._sync_bowl_numbers()
            while scene and self.subview == "bowl" and gen == self._bowl_gen:
                target = min(4, int(getattr(self, "_bowl_target", scene.done)))
                if scene.done >= target:
                    break
                if not scene.begin():
                    break
                note = getattr(self, "_bowl_note", None)
                if note is not None:
                    note.value = scene.label()
                    note.color = TEXT
                    self._bowl_touch(note)
                loops = 0
                while scene.busy and self.subview == "bowl" and gen == self._bowl_gen and loops < 800:
                    scene.tick()
                    scene.tick()
                    scene.apply()
                    self._bowl_touch(scene.canvas)
                    await asyncio.sleep(0.032)
                    loops += 1
                if self.subview != "bowl" or gen != self._bowl_gen:
                    break
                if scene.busy:
                    scene.force_rest()
                    scene.apply()
                    self._bowl_touch(scene.canvas)
                scene.commit()
                dot_i = scene.done - 1
                dots = getattr(self, "_bowl_dots", None)
                if dots and 0 <= dot_i < len(dots):
                    dots[dot_i].bgcolor = PRIMARY
                    self._bowl_touch(dots[dot_i])
        except Exception:
            pass
        self.feed_busy = False
        if self.subview == "bowl" and gen == self._bowl_gen:
            self._feed_intro = False
            self.render()

    def mini_chip(self, text, color=None):
        return ft.Container(
            ft.Text(text, size=12, weight=ft.FontWeight.W_700, color=color or MUTED),
            bgcolor=BG, padding=ft.Padding.symmetric(horizontal=6, vertical=4), border_radius=20,
        )

    def age_label(self, months):
        months = int(months or 0)
        if months < 12:
            return f"{months} мес."
        y = months // 12
        if y % 10 == 1 and y % 100 != 11:
            return f"{y} год"
        if 2 <= y % 10 <= 4 and not (12 <= y % 100 <= 14):
            return f"{y} года"
        return f"{y} лет"

    def select_pet(self, pet):
        self.state["activePetId"] = pet["id"]
        self.save()
        self.render()

    def empty_pet(self, species="cat"):
        return {
            "id": "p" + uuid.uuid4().hex[:10],
            "species": species,
            "name": "",
            "breedId": "unknown",
            "sex": "female",
            "ageMonths": 24,
            "weightKg": 4 if species == "cat" else 15,
            "targetWeightKg": None,
            "heightCm": None,
            "sterilized": False,
            "activity": "medium",
            "diagnoses": ["healthy"],
            "allergens": [],
            "treatKcal": 0,
            "photoPath": None,
        }

    def start_form(self, pet):
        self.form_edit = pet is not None
        self.form_pet = json.loads(json.dumps(pet or self.empty_pet()))
        self.render()

    def view_form(self):
        p = self.form_pet
        breeds = self.catalog["cats"] if p["species"] == "cat" else self.catalog["dogs"]
        src = p.get("photoPath") or self.photo_of_breed(p.get("breedId"))
        photo = self.photo_frame(
            src, 72, width=72, radius=20,
            fallback=ft.Icon(ft.Icons.PETS, color=PRIMARY, size=32),
        )
        name = ft.TextField(label="Кличка", value=p.get("name") or "", border_radius=14, bgcolor=SURFACE, color=TEXT, border_color=BORDER,
                           on_change=lambda e: self.set_field("name", e.control.value))
        age = ft.TextField(label="Возраст, мес.", value=str(p.get("ageMonths") or ""), keyboard_type=ft.KeyboardType.NUMBER, border_radius=14,
                           bgcolor=SURFACE, color=TEXT, border_color=BORDER,
                           on_change=lambda e: self.set_num("ageMonths", e.control.value, True))
        weight = ft.TextField(label="Вес, кг", value=str(p.get("weightKg") or ""), keyboard_type=ft.KeyboardType.NUMBER, border_radius=14,
                              bgcolor=SURFACE, color=TEXT, border_color=BORDER,
                              on_change=lambda e: self.set_num("weightKg", e.control.value, False))
        target = ft.TextField(label="Целевой вес, кг (если худеем)", value=str(p.get("targetWeightKg") or ""),
                              keyboard_type=ft.KeyboardType.NUMBER, border_radius=14, bgcolor=SURFACE, color=TEXT, border_color=BORDER,
                              on_change=lambda e: self.set_num("targetWeightKg", e.control.value, False, nullable=True))
        treats = ft.TextField(
            label="Лакомства, ккал в день",
            value=str(p.get("treatKcal") or 0),
            keyboard_type=ft.KeyboardType.NUMBER, border_radius=14,
            bgcolor=SURFACE, color=TEXT, border_color=BORDER,
            on_change=lambda e: self.set_num("treatKcal", e.control.value, True),
        )
        breed_opts = [ft.DropdownOption("unknown", "Неизвестна"), ft.DropdownOption("mixed", "Метис")] + [
            ft.DropdownOption(b["id"], b["name"]) for b in breeds
        ]
        breed_dd = ft.Dropdown(label="Порода", value=p.get("breedId") or "unknown", options=breed_opts, bgcolor=SURFACE, color=TEXT, border_color=BORDER,
                              on_select=lambda e: self.set_field("breedId", e.control.value))
        act_dd = ft.Dropdown(
            label="Активность", value=p.get("activity") or "medium",
            options=[ft.DropdownOption(k, v) for k, v in ACTIVITY.items()],
            bgcolor=SURFACE, color=TEXT, border_color=BORDER,
            on_select=lambda e: self.set_field("activity", e.control.value),
        )
        diag_row = ft.Row([self.diag_chip(code, label) for code, label in DIAGNOSIS.items()], wrap=True, spacing=8)
        controls = [
            ft.Row([photo, ft.TextButton("Фото", on_click=self.pick_photo)], spacing=12),
            name,
            self.seg("Вид", [("cat", "Кошка"), ("dog", "Собака")], p["species"], self.set_species),
            breed_dd,
            self.seg("Пол", [("female", "Самка"), ("male", "Самец")], p.get("sex") or "female", lambda v: self.set_field("sex", v)),
            age, weight, target, treats,
            ft.Text("Калории лакомств вычитаются из нормы на корм, не больше четверти дня.", size=11, color=MUTED),
            self.seg("Стерилизация", [("0", "Нет"), ("1", "Да")], "1" if p.get("sterilized") else "0",
                     lambda v: self.set_field("sterilized", v == "1")),
            act_dd,
            ft.Text("Диагнозы", size=13, weight=ft.FontWeight.W_700, color=MUTED),
            diag_row,
            ft.Text("«Здоров» снимает остальные диагнозы. Лечебный корм показываем только при диагнозе.", size=11, color=MUTED),
        ]
        if "allergy" in (p.get("diagnoses") or []):
            controls += [
                ft.Text("Аллергия на", size=13, weight=ft.FontWeight.W_700, color=MUTED),
                ft.Row([self.allergen_chip(a) for a in matcher.ALLERGENS], wrap=True, spacing=8),
            ]
        controls += [
            ft.Row([
                ft.Container(self.outline_btn("Отмена", lambda e: self.cancel_form()), expand=True),
                ft.Container(self.primary_btn("Сохранить", self.save_form), expand=True),
            ], spacing=10),
        ]
        if self.form_edit:
            controls.append(ft.TextButton("Удалить питомца", on_click=self.delete_pet, style=ft.ButtonStyle(color=DANGER)))
        return ft.Column(controls, spacing=12)

    def diag_chip(self, code, label):
        on = code in (self.form_pet.get("diagnoses") or [])
        return ft.Container(
            ft.Text(label, size=13, weight=ft.FontWeight.W_700, color="white" if on else TEXT),
            bgcolor=PRIMARY if on else SURFACE, padding=ft.Padding.symmetric(horizontal=14, vertical=9),
            border=ft.Border.all(width=1, color=PRIMARY if on else BORDER), border_radius=20,
            on_click=lambda e, c=code: self.toggle_diag(c),
        )

    def allergen_chip(self, a):
        on = a["code"] in (self.form_pet.get("allergens") or [])
        return ft.Container(
            ft.Text(a["label"], size=13, weight=ft.FontWeight.W_700, color="white" if on else TEXT),
            bgcolor=PRIMARY if on else SURFACE, padding=ft.Padding.symmetric(horizontal=14, vertical=9),
            border=ft.Border.all(width=1, color=PRIMARY if on else BORDER), border_radius=20,
            on_click=lambda e, c=a["code"]: self.toggle_allergen(c),
        )

    def seg(self, label, pairs, value, setter):
        btns = []
        for key, text in pairs:
            on = key == value
            btns.append(ft.Container(
                ft.Text(text, weight=ft.FontWeight.W_700, color="white" if on else MUTED, text_align=ft.TextAlign.CENTER),
                bgcolor=PRIMARY if on else SURFACE, padding=10, border_radius=11, expand=True, alignment=ft.Alignment.CENTER,
                on_click=lambda e, k=key: setter(k) or self.render(),
            ))
        return ft.Column([
            ft.Text(label, size=13, weight=ft.FontWeight.W_700, color=MUTED),
            ft.Container(ft.Row(btns, spacing=4), bgcolor=SURFACE, padding=4, border=ft.Border.all(width=1, color=BORDER), border_radius=14),
        ], spacing=6)

    def set_field(self, key, value):
        self.form_pet[key] = value

    def set_num(self, key, value, integer, nullable=False):
        raw = str(value).replace(",", ".").strip()
        if raw == "":
            self.form_pet[key] = None if nullable else (0 if integer else self.form_pet.get(key))
            return
        try:
            self.form_pet[key] = int(float(raw)) if integer else float(raw)
        except ValueError:
            pass

    def set_species(self, species):
        self.form_pet["species"] = species
        self.form_pet["breedId"] = "unknown"
        self.form_pet["weightKg"] = 4 if species == "cat" else 15
        self.render()

    def toggle_diag(self, code):
        p = self.form_pet
        if code == "healthy":
            p["diagnoses"] = ["healthy"]
            p["allergens"] = []
        else:
            cur = [d for d in (p.get("diagnoses") or []) if d != "healthy"]
            if code in cur:
                cur.remove(code)
            else:
                cur.append(code)
            p["diagnoses"] = cur or ["healthy"]
            if "allergy" not in p["diagnoses"]:
                p["allergens"] = []
        self.render()

    def toggle_allergen(self, code):
        cur = list(self.form_pet.get("allergens") or [])
        if code in cur:
            cur.remove(code)
        else:
            cur.append(code)
        self.form_pet["allergens"] = cur
        self.render()

    async def pick_photo(self, e=None):
        if not self.form_pet:
            return
        files = await self.picker.pick_files(
            dialog_title="Фото питомца",
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=["jpg", "jpeg", "png", "webp"],
            with_data=True,
        )
        if not files:
            return
        picked = files[0]
        suffix = Path(picked.name or "").suffix.lower()
        if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
            suffix = ".jpg"
        dest = user_dir() / "photos" / f"{self.form_pet['id']}{suffix}"
        if picked.bytes:
            dest.write_bytes(picked.bytes)
        elif picked.path and Path(picked.path).is_file():
            shutil.copy2(picked.path, dest)
        else:
            self.toast("Не получилось прочитать фото")
            return
        photos = dest.parent
        for old in photos.glob(f"{self.form_pet['id']}.*"):
            if old != dest:
                old.unlink(missing_ok=True)
        self.form_pet["photoPath"] = str(dest)
        self.render()

    def cancel_form(self, e=None):
        self.form_pet = None
        self.render()

    def save_form(self, e=None):
        p = self.form_pet
        p["name"] = (p.get("name") or "").strip() or "Без имени"
        p["weightKg"] = float(p.get("weightKg") or (4 if p["species"] == "cat" else 15))
        p["ageMonths"] = int(p.get("ageMonths") or 0)
        found = False
        for i, old in enumerate(self.pets()):
            if old["id"] == p["id"]:
                self.pets()[i] = p
                found = True
                break
        if not found:
            self.pets().append(p)
        self.state["activePetId"] = p["id"]
        self.form_pet = None
        self.tab = 1
        self.nav.selected_index = 1
        self.state["lastTab"] = 1
        self.save()
        self.render()
        self.toast("Питомец сохранён — вот рацион")

    def delete_pet(self, e=None):
        pid = self.form_pet["id"]
        self.state["pets"] = [p for p in self.pets() if p["id"] != pid]
        if self.state.get("activePetId") == pid:
            self.state["activePetId"] = self.pets()[0]["id"] if self.pets() else None
        self.form_pet = None
        self.save()
        self.render()

    def view_ration(self):
        pet = self.active()
        if not pet:
            return ft.Column([
                ft.Icon(ft.Icons.SCALE, size=64, color=PRIMARY),
                ft.Text("Сначала добавьте питомца", size=20, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER, color=TEXT),
                self.primary_btn("Перейти к питомцу", lambda e: self.goto(0)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
        s = nutrition.summary(pet)
        breed = self.breed_of(pet)
        matched = matcher.match(pet, breed, self.catalog["foods"])
        switcher = []
        if len(self.pets()) > 1:
            switcher = [ft.Row([
                ft.Container(
                    ft.Text(p["name"], weight=ft.FontWeight.W_700, color="white" if p["id"] == pet["id"] else MUTED),
                    bgcolor=PRIMARY if p["id"] == pet["id"] else SURFACE,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=8), border_radius=20,
                    border=ft.Border.all(width=1, color=PRIMARY if p["id"] == pet["id"] else BORDER),
                    on_click=lambda e, x=p: self.select_pet(x),
                ) for p in self.pets()
            ], scroll=ft.ScrollMode.AUTO)]
        kcal_caption = "ккал в день"
        if s.get("treatKcal"):
            kcal_caption = f"из них {s['foodKcal']} на корм"
        kbju = self.card(
            ft.Row([
                ft.Container(
                    ft.Column([
                        ft.Text(str(s["kcal"]), size=26, weight=ft.FontWeight.W_800, color=TEXT),
                        ft.Text(kcal_caption, size=11, color=MUTED, weight=ft.FontWeight.W_700,
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    width=110, height=110, border_radius=55, bgcolor=BG, alignment=ft.Alignment.CENTER,
                    border=ft.Border.all(width=6, color=PRIMARY),
                ),
                ft.Column([
                    self.legend(PRIMARY, "Белок", f"{s['protein']} г"),
                    self.legend("#E9C46A", "Жир", f"{s['fat']} г"),
                    self.legend(SUCCESS, "Углеводы", f"{s['carb']} г"),
                ], expand=True, spacing=8),
            ], spacing=16)
        )
        blocks = list(switcher) + [kbju]
        diags = [d for d in (pet.get("diagnoses") or []) if d != "healthy"]
        if s.get("treatKcal"):
            blocks.append(ft.Text(
                f"Лакомства {s['treatKcal']} ккал уже вычтены: на корм остаётся {s['foodKcal']} ккал.",
                size=13, color=MUTED,
            ))
        if "urolithiasis" in diags:
            blocks.append(ft.Container(
                ft.Text("При камнях в моче важнее вода, чем сухой корм: миска всегда полная, лучше влажный рацион. Тип камней подтверждает врач.",
                        size=13, weight=ft.FontWeight.W_700, color=ACCENT_INK),
                bgcolor=ACCENT_SOFT, padding=12, border_radius=14,
            ))
        if "heart" in diags:
            blocks.append(ft.Container(
                ft.Text("При болезни сердца смотрите натрий на анализе пачки. Обычный корм с высоким натрием сюда не ставим.",
                        size=13, weight=ft.FontWeight.W_700, color=ACCENT_INK),
                bgcolor=ACCENT_SOFT, padding=12, border_radius=14,
            ))
        if matched["conflict"]:
            blocks.append(ft.Container(
                ft.Text("Для этих диагнозов мало готовых ветеринарных линеек — согласуйте рацион с врачом.",
                        size=13, weight=ft.FontWeight.W_700, color=ACCENT_INK),
                bgcolor=ACCENT_SOFT, padding=12, border_radius=14,
            ))
        strict = matched.get("primary") in matcher.STRICT_DIETS
        if strict:
            if matched["best"]:
                blocks.append(self.food_group("Лучший выбор", matched["best"], pet, True, featured=True))
            if matched["medical"]:
                blocks.append(self.food_group("Ещё лечебный", matched["medical"], pet, True))
            if matched["good"]:
                blocks.append(self.food_group("Если врач разрешит обычный", matched["good"], pet, False))
        else:
            if matched["medical"]:
                blocks.append(self.food_group("Лечебный", matched["medical"], pet, True))
            if matched["best"]:
                blocks.append(self.food_group("Лучший выбор", matched["best"], pet, False, featured=True))
            if matched["good"]:
                blocks.append(self.food_group("Хороший вариант", matched["good"], pet, False))
        blocks.append(self.outline_btn("Проверить корм с полки", lambda e: self.open_pack()))
        blocks.append(ft.Text(
            "Рекомендации информационные и не заменяют ветеринара. Лечебные корма — только при подтверждённом диагнозе. Сверяйте состав на пачке.",
            size=13, color=MUTED, text_align=ft.TextAlign.CENTER,
        ))
        return ft.Column(blocks, spacing=14)

    def open_subview(self, view):
        self.subview = view
        self.article_id = None
        self.form_pet = None
        self.render()

    def open_pack(self, e=None):
        self.pack_brand = None
        self.pack_query = ""
        self.open_subview("pack")

    def legend(self, color, label, value):
        return ft.Row([
            ft.Container(width=10, height=10, bgcolor=color, border_radius=5),
            ft.Text(label, size=13, weight=ft.FontWeight.W_700, color=MUTED, expand=True),
            ft.Text(value, size=13, weight=ft.FontWeight.W_800, color=TEXT),
        ])

    def food_group(self, title, items, pet, medical, featured=False):
        if not items:
            return ft.Container()
        if featured:
            cards = [self.food_hero(items[0], pet, medical)]
            cards += [self.food_row(item, pet, medical) for item in items[1:]]
            return ft.Column(
                [ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=TEXT), *cards],
                spacing=8,
            )
        cards = [self.food_row(item, pet, medical) for item in items]
        return ft.Column(
            [ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=TEXT), *cards],
            spacing=6,
        )

    def food_hero(self, item, pet, medical):
        food = item["food"]
        grams = nutrition.portion_grams(pet, food)
        why = item["reasons"][0] if item["reasons"] else "подходит вашему питомцу"
        cost = nutrition.monthly_cost(pet, food)
        open_comp = lambda e, f=food, it=item: self.show_food(f, it, pet)
        tier = TIER_LABEL.get(food.get("tier") or "", food.get("tier") or "")
        form = "влажный" if food.get("form") == "wet" else "сухой"
        ribbon = "По диагнозу" if medical else "На сегодня"
        ribbon_bg = ACCENT_SOFT if medical else CHIP
        ribbon_fg = ACCENT_INK if medical else PRIMARY_DARK
        edge = ACCENT if medical else PRIMARY
        return ft.Container(
            ft.Column([
                ft.Row([
                    ft.Container(
                        ft.Text(ribbon, size=11, weight=ft.FontWeight.W_800, color=ribbon_fg, font_family="Nunito"),
                        bgcolor=ribbon_bg, padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        border_radius=10,
                    ),
                    ft.Container(expand=True),
                    ft.Text(f"{grams} г", size=24, weight=ft.FontWeight.W_800, color=PRIMARY, font_family="Nunito"),
                ]),
                ft.Text(food["name"], weight=ft.FontWeight.W_800, size=18, color=TEXT, font_family="Nunito"),
                ft.Text(
                    f"{food['brand']} · {form} · около {cost['rubMonth']} ₽/мес",
                    size=13, color=MUTED, font_family="Nunito",
                ),
                ft.Text(why, size=14, color=TEXT, font_family="Nunito"),
                ft.Row([
                    self.mini_chip(form),
                    self.mini_chip(tier) if tier else ft.Container(),
                    self.mini_chip("без злаков") if food.get("grainFree") else ft.Container(),
                    ft.Container(expand=True),
                    ft.Text("Подробнее →", color=PRIMARY, weight=ft.FontWeight.W_700, size=14),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=8),
            bgcolor=SURFACE, padding=18, border_radius=22,
            border=ft.Border.all(width=2, color=edge),
            shadow=ft.BoxShadow(blur_radius=16, spread_radius=0, offset=ft.Offset(0, 6), color="#2C2A2612"),
            on_click=open_comp,
        )

    def food_row(self, item, pet, medical):
        food = item["food"]
        grams = nutrition.portion_grams(pet, food)
        open_comp = lambda e, f=food, it=item: self.show_food(f, it, pet)
        form = "влажный" if food.get("form") == "wet" else "сухой"
        return ft.Container(
            ft.Row([
                ft.Column([
                    ft.Text(
                        food["name"], weight=ft.FontWeight.W_700, size=14, color=TEXT,
                        font_family="Nunito", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"{food['brand']} · {form} · {grams} г",
                        size=12, color=MUTED, font_family="Nunito",
                    ),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED, size=20),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE,
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            border_radius=16,
            border=ft.Border.all(width=1.5, color=ACCENT if medical else BORDER),
            on_click=open_comp,
        )

    def show_food(self, food, item, pet=None):
        pet = pet or self.active()
        grams = nutrition.portion_grams(pet, food) if pet else 0
        parts = []
        if food.get("proteinPer100g") is not None:
            parts.append(f"белка {food['proteinPer100g']} г")
        if food.get("fatPer100g") is not None:
            parts.append(f"жира {food['fatPer100g']} г")
        if food.get("fiberPer100g") is not None:
            parts.append(f"клетчатки {food['fiberPer100g']} г")
        if food.get("kcalPer100g") is not None:
            parts.append(f"{food['kcalPer100g']} ккал")
        analysis = "В 100 г корма: " + ", ".join(parts) if parts else ""
        if food.get("phosphorusPer100g") is not None:
            analysis += f". Фосфора {food['phosphorusPer100g']} г"
        if food.get("sodiumPer100g") is not None:
            analysis += f". Натрия {food['sodiumPer100g']} г"
        if analysis and not analysis.endswith("."):
            analysis += "."
        reasons = [ft.Text("• " + r, size=14, color=TEXT) for r in item.get("reasons") or []]
        cost = nutrition.monthly_cost(pet, food) if pet else None
        form = "влажный" if food.get("form") == "wet" else "сухой"
        portion = f"Давать примерно {grams} г в день"
        if food.get("form") == "wet" and grams:
            pouches = max(1, round(grams / 85))
            portion += f" — около {pouches} пауча по 85 г" if pouches != 1 else " — примерно один пауч 85 г"
        controls = [
            ft.Text(f"{food['brand']} · российский {form} корм", size=14, color=MUTED),
            ft.Text(portion, size=15, weight=ft.FontWeight.W_700, color=TEXT),
        ]
        if cost:
            controls.append(ft.Text(
                f"На месяц выйдет примерно {cost['rubMonth']} ₽ (если пачка около {cost['pricePerKg']} ₽/кг)",
                size=13.5, color=MUTED,
            ))
        controls += [
            ft.Text("Почему этот корм", size=12, weight=ft.FontWeight.W_700, color=MUTED),
            *reasons,
            ft.Text("Что внутри", size=12, weight=ft.FontWeight.W_700, color=MUTED),
            ft.Text(analysis, size=14, color=TEXT),
            ft.Text("Состав", size=12, weight=ft.FontWeight.W_700, color=MUTED),
            ft.Text(food.get("composition") or "", size=14.5, color=TEXT),
            self.primary_btn("Как перейти на этот корм", lambda e, f=food: self.start_transition(f)),
        ]
        self.show_dialog_sheet(food["name"], controls)

    def start_transition(self, food):
        try:
            self.page.pop_dialog()
        except Exception:
            pass
        pet = self.active()
        if pet:
            self.state.setdefault("selectedFoods", {})[pet["id"]] = food["id"]
            self.save()
        self.tab = 1
        self.nav.selected_index = 1
        self.open_subview("transition")

    def show_dialog_sheet(self, title, controls):
        try:
            self.page.pop_dialog()
        except Exception:
            pass
        body = ft.Column(controls, spacing=10, scroll=ft.ScrollMode.AUTO, tight=True)
        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Text(title, size=18, weight=ft.FontWeight.W_700, font_family="Nunito", color=TEXT),
            content=ft.Container(body, width=340, height=460),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: self._close_dialog()),
            ],
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=20),
            scrollable=True,
        )
        self.page.show_dialog(dlg)

    def _close_dialog(self, e=None):
        try:
            self.page.pop_dialog()
        except Exception:
            pass

    def goto(self, idx):
        self.tab = idx
        self.nav.selected_index = idx
        self.state["lastTab"] = idx
        self.save()
        self.form_pet = None
        self.render()

    def view_breeds(self):
        cats = [self.breed_tile(b, True) for b in self.catalog["cats"]]
        dogs = [self.breed_tile(b, False) for b in self.catalog["dogs"]]
        return ft.Column([
            ft.Text("Нажмите карточку — сначала коротко, что нужно этой породе.", size=13, color=MUTED),
            ft.Text("Кошки — топ пород РФ", size=16, weight=ft.FontWeight.W_700, color=TEXT),
            *cats,
            ft.Text("Собаки — топ пород РФ", size=16, weight=ft.FontWeight.W_700, color=TEXT),
            *dogs,
        ], spacing=8)

    def toggle_breed(self, breed):
        bid = breed["id"]
        if bid in self.open_breed_ids:
            self.open_breed_ids.discard(bid)
        else:
            self.open_breed_ids.add(bid)
        self.render()

    def breed_lead(self, breed):
        raw = (breed.get("kcalRefText") or "").split("—")[0].strip().lstrip("~").strip()
        if raw:
            return f"Для этой породы: {raw}"
        return breed.get("weightText") or ""

    def breed_tile(self, breed, is_cat):
        src = self.photo_of_breed(breed["id"])
        opened = breed["id"] in self.open_breed_ids
        photo = self.photo_frame(
            src,
            fallback=ft.Icon(
                ft.Icons.PETS if is_cat else ft.Icons.CRUELTY_FREE, color=PRIMARY, size=36,
            ),
            min_h=120 if not opened else 152,
            max_h=196 if not opened else 236,
        )
        lead = self.breed_lead(breed)
        header_bits = [
            ft.Row([
                ft.Text(breed["name"], weight=ft.FontWeight.W_800, size=17, color=TEXT, expand=True,
                        font_family="Nunito"),
                ft.Icon(ft.Icons.EXPAND_LESS if opened else ft.Icons.EXPAND_MORE, color=MUTED),
            ]),
        ]
        if not opened:
            if lead:
                header_bits.append(ft.Text(
                    lead, size=13, color=MUTED, font_family="Nunito",
                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                ))
            elif breed.get("weightText"):
                header_bits.append(ft.Text(breed["weightText"], size=13, color=MUTED, font_family="Nunito"))
        inner = [
            ft.Container(
                ft.Column([
                    photo,
                    ft.Container(
                        ft.Column(header_bits, spacing=8),
                        padding=ft.Padding.only(left=14, right=14, top=12, bottom=14 if opened else 14),
                    ),
                ], spacing=0),
                on_click=lambda e, b=breed: self.toggle_breed(b),
            ),
        ]
        if opened:
            inner.append(ft.Container(
                self.breed_details(breed),
                padding=ft.Padding.only(left=14, right=14, bottom=16),
            ))
        return ft.Container(
            ft.Column(inner, spacing=0),
            bgcolor=SURFACE, border_radius=22,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(width=1.5, color=PRIMARY if opened else BORDER),
            shadow=ft.BoxShadow(blur_radius=12, spread_radius=0, offset=ft.Offset(0, 4), color="#2C2A2610") if opened else None,
        )

    def breed_details(self, breed):
        info = self.breed_info.get(breed["id"]) or {}
        chips = []
        if breed.get("weightText"):
            chips.append(self.mini_chip(breed["weightText"], TEXT))
        if info.get("lifespan"):
            chips.append(self.mini_chip("живёт " + info["lifespan"], TEXT))
        blocks = []
        lead = self.breed_lead(breed)
        if lead:
            blocks.append(ft.Text(lead, size=14.5, weight=ft.FontWeight.W_700, color=TEXT, font_family="Nunito"))
        if chips:
            blocks.append(ft.Row(chips, wrap=True, spacing=8, run_spacing=8))
        if info.get("distinctive"):
            blocks += [
                ft.Text("Как узнать породу", size=12, weight=ft.FontWeight.W_700, color=MUTED),
                ft.Text(info["distinctive"], size=14.5, color=TEXT),
            ]
        if info.get("growth"):
            blocks += [
                ft.Text("Рост и созревание", size=12, weight=ft.FontWeight.W_700, color=MUTED),
                ft.Text(info["growth"], size=14.5, color=TEXT),
            ]
        if info.get("lifespan"):
            blocks += [
                ft.Text("Сколько живёт", size=12, weight=ft.FontWeight.W_700, color=MUTED),
                ft.Text("Обычно " + info["lifespan"] + ".", size=14.5, color=TEXT),
            ]
        if info.get("funFact"):
            blocks += [
                ft.Text("Интересный факт", size=12, weight=ft.FontWeight.W_700, color=PRIMARY),
                ft.Text(info["funFact"], size=14.5, color=TEXT),
            ]
        return ft.Column(blocks, spacing=8)

    def view_five(self):
        g = self.five_game
        rows = []
        for r in range(five.ROWS):
            cells = []
            for c in range(five.COLS):
                letter, kind = g.letter_at(r, c)
                if kind == "hit":
                    bg, fg, border = FIVE_HIT, FIVE_ON, FIVE_HIT
                elif kind == "present":
                    bg, fg, border = FIVE_PRESENT, FIVE_INK, FIVE_PRESENT
                elif kind == "miss":
                    bg, fg, border = FIVE_MISS, FIVE_ON, FIVE_MISS
                elif kind == "typed":
                    bg, fg, border = FIVE_CELL, FIVE_INK, FIVE_TYPED
                else:
                    bg, fg, border = FIVE_CELL, FIVE_INK, FIVE_LINE
                cells.append(ft.Container(
                    ft.Text((letter or "").upper(), size=22, weight=ft.FontWeight.W_800,
                            color=fg, text_align=ft.TextAlign.CENTER, font_family="Nunito"),
                    width=52, height=52, bgcolor=bg, border_radius=10,
                    alignment=ft.Alignment.CENTER,
                    border=ft.Border.all(width=2, color=border),
                ))
            rows.append(ft.Row(cells, alignment=ft.MainAxisAlignment.CENTER, spacing=7))

        def key_btn(label, on_click, color_key=None, wide=False):
            kind = g.keys.get(color_key) if color_key else None
            if kind == "hit":
                bg, fg = FIVE_HIT, FIVE_ON
            elif kind == "present":
                bg, fg = FIVE_PRESENT, FIVE_INK
            elif kind == "miss":
                bg, fg = FIVE_MISS, FIVE_ON
            else:
                bg, fg = FIVE_KEY, FIVE_INK
            return ft.Container(
                ft.Text(label, size=13 if wide else 15, weight=ft.FontWeight.W_800,
                        color=fg, text_align=ft.TextAlign.CENTER),
                height=46, bgcolor=bg, border_radius=10,
                alignment=ft.Alignment.CENTER,
                on_click=on_click,
                expand=2 if wide else 1,
            )

        kb_rows = []
        for i, line in enumerate(five.KEYBOARD):
            keys = []
            if i == 2:
                keys.append(key_btn("Ввод", lambda e: self.five_submit(), wide=True))
            for ch in line:
                keys.append(key_btn(ch, lambda e, letter=ch: self.five_type(letter), color_key=ch))
            if i == 2:
                keys.append(key_btn("⌫", lambda e: self.five_back(), wide=True))
            kb_rows.append(ft.Row(keys, alignment=ft.MainAxisAlignment.CENTER, spacing=5, expand=False))

        stats = self.state.get("fiveLetters") or {}
        wins, games = stats.get("wins", 0), stats.get("games", 0)
        streak = self.five_day_streak()
        actions = []
        daily_done = g.mode == "daily" and g.status in ("win", "lose")
        extra_done = g.mode != "daily" and g.status in ("win", "lose")
        if daily_done or extra_done:
            actions.append(self.primary_btn("Ещё слово", lambda e: self.five_new("random")))
        if g.mode != "daily":
            actions.append(self.outline_btn("К слову дня", lambda e: self.five_new("daily")))

        arrow = ft.Icons.EXPAND_LESS if self.five_cal_open else ft.Icons.EXPAND_MORE
        title = ft.Row([
            ft.Container(width=40),
            ft.Text("5 букв", size=26, weight=ft.FontWeight.W_800, color=TEXT,
                    text_align=ft.TextAlign.CENTER, expand=True),
            ft.Container(
                ft.Icon(arrow, color=TEXT, size=26),
                width=40, height=40, border_radius=20,
                alignment=ft.Alignment.CENTER,
                on_click=self.toggle_five_cal,
            ),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Column([
            title,
            ft.Text("Существительное из пяти букв · 6 попыток", size=13, color=MUTED,
                    text_align=ft.TextAlign.CENTER),
            *([self.view_five_calendar()] if self.five_cal_open else []),
            ft.Container(
                ft.Column([
                    ft.Text(g.message or " ", size=14, weight=ft.FontWeight.W_700,
                            color=TEXT, text_align=ft.TextAlign.CENTER),
                    *rows,
                    ft.Container(height=8),
                    *kb_rows,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=7),
                bgcolor=FIVE_BG, padding=16, border_radius=24,
                border=ft.Border.all(width=1.5, color=BORDER),
                shadow=ft.BoxShadow(blur_radius=18, offset=ft.Offset(0, 8), color="#2C2A2614"),
            ),
            ft.Text(
                f"Угадано {wins} из {games} · серия {streak} {self.ru_days(streak)}" if streak
                else f"Угадано {wins} из {games}",
                size=13, color=MUTED, text_align=ft.TextAlign.CENTER,
            ),
            *actions,
            ft.Text("Зелёная — буква на своём месте. Медовая — есть, но в другом месте. Серая — такой буквы нет.",
                    size=13, color=MUTED),
            ft.Container(height=20),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def view_fun(self):
        if not self.fun_tab:
            return self.view_fun_folder()
        if self.fun_tab == "video" and self.pet_video():
            return self.view_pet_videos()
        return ft.Column([
            self.fun_back(),
            self.view_pet_videos() if self.fun_tab == "video" else self.view_five(),
        ], spacing=4)

    def fun_back(self):
        return ft.Container(
            ft.Row([
                ft.Icon(ft.Icons.CHEVRON_LEFT, size=18, color=TEXT),
                ft.Text("Назад", size=14, weight=ft.FontWeight.W_700, color=TEXT),
            ], spacing=0, tight=True),
            on_click=lambda e: self.set_fun_tab(None),
            padding=ft.Padding.only(top=2, bottom=2),
        )

    def fun_card(self, body, wash, angle, top, on_click):
        inner = max(260, (self.page.width or 420) - 32)
        width = 174 if inner >= 174 * 2 + 12 else max(136, int((inner - 12) / 2))
        return ft.Container(
            body,
            width=width,
            height=200,
            bgcolor=wash,
            padding=ft.Padding.only(left=16, top=14, right=12, bottom=14),
            border=ft.Border.all(2.5, TEXT),
            border_radius=4,
            margin=ft.Margin.only(top=top),
            rotate=angle,
            shadow=ft.BoxShadow(blur_radius=14, spread_radius=0, offset=ft.Offset(0, 5), color="#2C2A2620"),
            on_click=on_click,
        )

    def fun_tape(self, color):
        return ft.Container(
            width=44, height=11, bgcolor=color, border_radius=2,
            rotate=-0.08, opacity=0.95,
            margin=ft.Margin.only(left=2, top=4, bottom=8),
        )

    def fun_letter_tile(self, letter, bg, fg, size=24):
        return ft.Container(
            ft.Text(letter, size=13, weight=ft.FontWeight.W_800, color=fg),
            width=size, height=size, bgcolor=bg, border_radius=4,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, TEXT),
        )

    def fun_letters_card(self):
        tiles = [
            ("Л", FIVE_HIT, FIVE_ON),
            ("А", FIVE_PRESENT, FIVE_INK),
            ("П", FIVE_MISS, FIVE_ON),
            ("К", FIVE_HIT, FIVE_ON),
            ("А", FIVE_PRESENT, FIVE_INK),
        ]
        small = (self.page.width or 420) < 390
        tile = 22 if small else 24
        return self.fun_card(
            ft.Column([
                self.fun_tape(PRIMARY),
                ft.Text("5", size=42, weight=ft.FontWeight.W_800, color=TEXT),
                ft.Text("букв", size=22, weight=ft.FontWeight.W_700, color=TEXT),
                ft.Container(height=12),
                ft.Row(
                    [self.fun_letter_tile(a, b, c, tile) for a, b, c in tiles],
                    spacing=2 if small else 3,
                ),
            ], spacing=0),
            "#F4F7F2",
            -0.045,
            16,
            lambda e: self.set_fun_tab("letters"),
        )

    def fun_film_holes(self):
        return ft.Column(
            [ft.Container(width=7, height=7, bgcolor=BG, border_radius=2) for _ in range(3)],
            spacing=5,
        )

    def fun_video_card(self):
        screen = ft.Container(
            ft.Row([
                self.fun_film_holes(),
                ft.Container(
                    ft.Icon(ft.Icons.PLAY_ARROW, color="white", size=30),
                    width=42, height=42, bgcolor=ACCENT, border_radius=21,
                    alignment=ft.Alignment.CENTER,
                ),
                self.fun_film_holes(),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            height=64, bgcolor="#1A1A1A", border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8),
        )
        return self.fun_card(
            ft.Column([
                self.fun_tape(ACCENT),
                ft.Text("Видео", size=30, weight=ft.FontWeight.W_800, color=TEXT),
                ft.Container(height=14),
                screen,
            ], spacing=0),
            "#FBF4F0",
            0.04,
            0,
            lambda e: self.set_fun_tab("video"),
        )

    def view_fun_folder(self):
        return ft.Column([
            ft.Container(height=28),
            ft.Row([
                self.fun_letters_card(),
                ft.Container(expand=True),
                self.fun_video_card(),
            ]),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def set_fun_tab(self, key):
        self.fun_tab = key
        self.pet_video_full = False
        if key != "video":
            self.pet_video_id = None
        self.render()

    def pet_video(self):
        for video in PET_VIDEOS:
            if video["id"] == self.pet_video_id:
                return video
        return None

    def pet_file(self, video, name):
        return resource("assets", "videos", video[name])

    def pet_thumb(self, video, height=None):
        return ft.Container(
            ft.Image(
                src=f"videos/{video['thumb']}",
                fit=ft.BoxFit.COVER,
                filter_quality=ft.FilterQuality.HIGH,
            ),
            aspect_ratio=16 / 9,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor="#111111",
        )

    def view_pet_videos(self):
        opened = self.pet_video()
        if opened:
            return self.view_pet_player(opened)
        cards = [self.pet_video_card(video) for video in PET_VIDEOS]
        return ft.Column([
            ft.Text("Видео для животных", size=22, weight=ft.FontWeight.W_800, color=TEXT),
            ft.Text(
                "Ролики лежат в приложении и крутятся по кругу. Поставьте телефон рядом и побудьте рядом: лапой легко поцарапать стекло.",
                size=13, color=MUTED,
            ),
            *cards,
            ft.Container(height=12),
        ], spacing=10)

    def pet_video_card(self, video):
        return ft.Container(
            ft.Column([
                self.pet_thumb(video),
                ft.Text(video["title"], size=16, weight=ft.FontWeight.W_800, color=TEXT),
                ft.Text(video["text"], size=13, color=MUTED),
            ], spacing=8),
            bgcolor=SURFACE, padding=12, border_radius=20,
            border=ft.Border.all(width=1.5, color=BORDER),
            on_click=lambda e, v=video: self.open_pet_video(v["id"]),
        )

    def open_pet_video(self, video_id):
        self.pet_video_id = video_id
        self.pet_video_full = False
        self.render()

    def close_pet_video(self, e=None):
        self.pet_video_id = None
        self.pet_video_full = False
        self.render()

    def toggle_video_full(self, e=None):
        self.pet_video_full = not self.pet_video_full
        self.render()

    def video_uri(self, path: Path) -> str | None:
        real = path if path.is_file() else None
        if real is None:
            try:
                real = ensure_file("assets", "videos", path.name)
            except FileNotFoundError:
                real = None
        if real and real.is_file():
            return real.as_uri()
        return None

    def view_pet_player(self, video):
        uri = self.video_uri(self.pet_file(video, "file"))
        if uri:
            player = fv.Video(
                expand=True,
                playlist=[fv.VideoMedia(uri)],
                playlist_mode=fv.PlaylistMode.SINGLE,
                autoplay=True,
                volume=80,
                wakelock=True,
                fit=ft.BoxFit.CONTAIN,
                filter_quality=ft.FilterQuality.HIGH,
                fill_color="#111111",
                aspect_ratio=16 / 9,
                on_error=lambda e: self.toast("Не удалось воспроизвести видео"),
            )
            screen = ft.Container(
                player,
                expand=True if self.pet_video_full else False,
                aspect_ratio=None if self.pet_video_full else 16 / 9,
                border_radius=0 if self.pet_video_full else 16,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                bgcolor="#111111",
            )
        else:
            screen = ft.Text("Файл видео не найден.", size=14, color=DANGER)
        if self.pet_video_full:
            return ft.Column([
                ft.Container(
                    ft.Row([
                        ft.TextButton("‹ Свернуть", on_click=self.toggle_video_full, style=ft.ButtonStyle(color="white")),
                        ft.Text(video["title"], size=16, weight=ft.FontWeight.W_800, color="white",
                                expand=True, font_family="Nunito"),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor="#111111",
                    padding=ft.Padding.only(left=4, top=8, right=12, bottom=4),
                ),
                screen,
            ], spacing=0, expand=True)
        return ft.Column([
            ft.TextButton("‹ К видео", on_click=self.close_pet_video),
            ft.Text(video["title"], size=22, weight=ft.FontWeight.W_800, color=TEXT),
            screen,
            self.primary_btn("На весь экран", self.toggle_video_full),
            ft.Text(video["text"], size=14, color=MUTED),
            *([ft.Text(video["credit"], size=11, color=MUTED, font_family="Nunito")] if video.get("credit") else []),
            ft.Container(height=12),
        ], spacing=8)

    def make_five_game(self):
        def word_list(name):
            try:
                return ensure_file("assets", "games", name)
            except FileNotFoundError:
                return resource("assets", "games", name)

        guesses = five.load_lines(word_list("слова.txt"))
        answers = five.load_lines(word_list("ответы.txt"))
        extra = Path(r"C:\Users\Egor\Desktop\приложение\развлечения")
        if not guesses:
            guesses = five.load_lines(extra / "слова.txt")
        if not answers:
            answers = five.load_lines(extra / "ответы.txt")
        game = five.FiveLetters(guesses, answers)
        saved = self.state.get("fiveLetters") or {}
        today = date.today().isoformat()
        daily = saved.get("dailyGame") or (
            saved.get("game") if (saved.get("game") or {}).get("mode") != "random" else None
        )
        if saved.get("dailyDate") == today and daily:
            game.restore(daily)
            if game.status in ("win", "lose"):
                cal = self.state.setdefault("fiveLetters", {}).setdefault("calendar", {})
                cal.setdefault(today, game.status)
        else:
            game.start(mode="daily")
        return game

    def persist_five(self):
        if self.five_game.mode != "daily":
            self.save()
            return
        st = self.state.setdefault("fiveLetters", {})
        st.setdefault("calendar", {})
        st["dailyGame"] = self.five_game.dump()
        st["dailyDate"] = date.today().isoformat()
        self.save()

    def five_day_streak(self):
        """Сколько дней подряд угадано слово дня. Пропуск дня или проигрыш обрывают серию."""
        results = (self.state.get("fiveLetters") or {}).get("calendar") or {}
        today = date.today()
        today_result = results.get(today.isoformat())
        if today_result == "lose":
            return 0
        cursor = today if today_result == "win" else today - timedelta(days=1)
        n = 0
        while results.get(cursor.isoformat()) == "win":
            n += 1
            cursor -= timedelta(days=1)
        return n

    def toggle_five_cal(self, e=None):
        self.five_cal_open = not self.five_cal_open
        self.render()

    def shift_five_month(self, delta):
        year = self.five_month.year
        month = self.five_month.month + int(delta)
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        self.five_month = date(year, month, 1)
        self.render()

    def view_five_calendar(self):
        month = self.five_month
        results = (self.state.get("fiveLetters") or {}).get("calendar") or {}
        today = date.today()
        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month)
        week_rows = [
            ft.Row([
                ft.Text(name, size=11, color=MUTED, expand=True, text_align=ft.TextAlign.CENTER)
                for name in WEEKDAYS_RU
            ], spacing=4)
        ]
        for week in weeks:
            cells = []
            for day in week:
                if day.month != month.month:
                    cells.append(ft.Container(expand=True, height=36))
                    continue
                result = results.get(day.isoformat())
                border = None
                if day > today:
                    bg, fg = FIVE_CELL, "#B9B2A5"
                elif result == "win":
                    bg, fg = FIVE_HIT, FIVE_ON
                elif result == "lose" or day < today:
                    bg, fg = FIVE_MISS, FIVE_ON
                else:
                    bg, fg = FIVE_CELL, FIVE_INK
                    border = ft.Border.all(width=2, color=FIVE_HIT)
                cells.append(ft.Container(
                    ft.Text(str(day.day), size=13, weight=ft.FontWeight.W_800,
                            color=fg, text_align=ft.TextAlign.CENTER),
                    expand=True, height=36, bgcolor=bg, border_radius=18,
                    alignment=ft.Alignment.CENTER, border=border,
                ))
            week_rows.append(ft.Row(cells, spacing=4))
        title = f"{MONTHS_RU[month.month - 1]} {month.year}"
        return ft.Container(
            ft.Column([
                ft.Row([
                    ft.Container(
                        ft.Icon(ft.Icons.CHEVRON_LEFT, color=FIVE_INK, size=20),
                        width=36, height=36, border_radius=12, bgcolor=FIVE_CELL,
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda e: self.shift_five_month(-1),
                    ),
                    ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=FIVE_INK,
                            text_align=ft.TextAlign.CENTER, expand=True),
                    ft.Container(
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=FIVE_INK, size=20),
                        width=36, height=36, border_radius=12, bgcolor=FIVE_CELL,
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda e: self.shift_five_month(1),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                *week_rows,
                ft.Row([
                    ft.Text("зелёный — угадано", size=12, color=MUTED, expand=True),
                    ft.Text("серый — нет", size=12, color=MUTED),
                ]),
            ], spacing=8),
            bgcolor=FIVE_BG, padding=16, border_radius=24,
            border=ft.Border.all(width=1.5, color=BORDER),
        )

    def five_type(self, ch):
        self.five_game.type_letter(ch)
        self.persist_five()
        self.render()

    def five_back(self, e=None):
        self.five_game.backspace()
        self.persist_five()
        self.render()

    def five_submit(self, e=None):
        before = self.five_game.status
        result = self.five_game.submit()
        if before == "play" and self.five_game.status in ("win", "lose"):
            st = self.state.setdefault("fiveLetters", {})
            if self.five_game.mode == "daily":
                st.setdefault("calendar", {})[date.today().isoformat()] = self.five_game.status
                st["games"] = int(st.get("games") or 0) + 1
                if self.five_game.status == "win":
                    st["wins"] = int(st.get("wins") or 0) + 1
                streak = self.five_day_streak()
                st["streak"] = streak
                st["maxStreak"] = max(int(st.get("maxStreak") or 0), streak)
        if result == "unknown":
            self.toast("Нет такого слова")
        elif result == "short":
            self.toast("Не хватает букв")
        self.persist_five()
        self.render()

    def five_new(self, mode="random"):
        st = self.state.setdefault("fiveLetters", {})
        today = date.today().isoformat()
        if mode == "daily":
            if self.five_game.mode == "daily":
                if self.five_game.status == "win":
                    self.toast("Сегодняшнее слово уже угадано")
                elif self.five_game.status == "lose":
                    self.toast("Сегодня попытки закончились")
                return
            saved = st.get("dailyGame")
            if st.get("dailyDate") == today and saved:
                self.five_game.restore(saved)
            else:
                self.five_game.start(mode="daily")
            self.persist_five()
            self.render()
            return
        if self.five_game.mode == "daily":
            st["dailyGame"] = self.five_game.dump()
            st["dailyDate"] = today
            self.save()
        self.five_game.start(mode="random")
        self.render()

    def on_key(self, e):
        if self.tab != 3 or self.fun_tab != "letters" or self.form_pet or self.subview:
            return
        key = (e.key or "")
        if key in ("Enter", "Return", "Numpad Enter"):
            self.five_submit()
            return
        if key in ("Backspace", "Back Space"):
            self.five_back()
            return
        ch = key.lower()
        if len(ch) == 1 and "а" <= ch <= "я":
            self.five_type(five.normalize(ch))
            return
        mapped = five.LATIN_TO_RU.get(ch)
        if mapped:
            self.five_type(mapped)

    def view_more(self):
        if self.article_id:
            return self.view_article()
        donate_btn = lambda label: ft.Container(
            ft.Text(label, color=TEXT, weight=ft.FontWeight.W_700, size=14, text_align=ft.TextAlign.CENTER),
            bgcolor=SURFACE, padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=16, alignment=ft.Alignment.CENTER,
            border=ft.Border.all(width=2, color=BORDER),
            on_click=self.donate_soon, expand=True, height=42,
        )
        ordinary = ft.Container(
            ft.Column([
                ft.Text("Обычный", weight=ft.FontWeight.W_800, size=15, color=TEXT),
                ft.Text("0 ₽", size=22, weight=ft.FontWeight.W_800, color=TEXT),
                ft.Text("Расчёт нормы", size=13, color=MUTED),
                ft.Text("Подбор по породе", size=13, color=MUTED),
            ], spacing=4),
            bgcolor=BG, padding=14, border_radius=16, expand=True,
            border=ft.Border.all(width=1.5, color=BORDER),
        )
        pro = ft.Container(
            ft.Column([
                ft.Text("PRO", weight=ft.FontWeight.W_800, size=15, color=PRIMARY),
                ft.Text("299 ₽", size=22, weight=ft.FontWeight.W_800, color=TEXT),
                ft.Text("Лечебные рационы", size=13, color=MUTED),
                ft.Text("Экспорт данных", size=13, color=MUTED),
                ft.Container(
                    ft.Text("Оформить", color="white", weight=ft.FontWeight.W_700, size=13),
                    bgcolor=PRIMARY, padding=10, border_radius=14, alignment=ft.Alignment.CENTER,
                    on_click=self.donate_soon, height=36,
                ),
            ], spacing=4),
            bgcolor=BG, padding=14, border_radius=16, expand=True,
            border=ft.Border.all(width=1.5, color=PRIMARY),
        )
        return ft.Column([
            ft.Text("Поддержка проекта", size=13, weight=ft.FontWeight.W_800, color=MUTED),
            self.card(
                ft.Text(
                    "Обычный тариф бесплатен навсегда. PRO и донат пока нельзя оплатить — оплату ещё не подключили.",
                    size=13.5, color=MUTED,
                ),
                ft.Row([ordinary, pro], spacing=10),
                ft.Row([donate_btn("99 ₽"), donate_btn("299 ₽"), donate_btn("499 ₽")], spacing=8),
            ),
            ft.Text("Читать", size=13, weight=ft.FontWeight.W_800, color=MUTED),
            ft.Container(
                ft.Column([self.article_card(a) for a in ARTICLES], spacing=10),
                bgcolor=CHIP, padding=12, border_radius=24,
            ),
            ft.Text("Данные и настройки", size=13, weight=ft.FontWeight.W_800, color=MUTED),
            self.card(
                self.list_row("Экспорт данных", on_click=self.export_data),
                self.list_row("Импорт данных", on_click=self.import_data),
                self.list_row("Показать обучение заново", on_click=self.reset_onboard),
            ),
            ft.Text("О приложении", size=13, weight=ft.FontWeight.W_800, color=MUTED),
            self.card(
                ft.Text(
                    "Рекомендации приложения носят информационный характер и не заменяют консультацию ветеринарного врача.",
                    size=13.5, color=MUTED,
                ),
                self.list_row("Обратная связь", on_click=self.open_feedback),
                ft.Row([
                    ft.Text("Версия", weight=ft.FontWeight.W_700, expand=True, color=TEXT),
                    ft.Text("v1.0.0", color=MUTED),
                ]),
            ),
            self.credits_footer(),
            ft.Container(height=28),
        ], spacing=12)

    def article_card(self, article):
        lede = (article.get("text") or "").split(".")[0].strip()
        if lede and not lede.endswith("."):
            lede += "."
        return ft.Container(
            ft.Column([
                ft.Text(article["title"], size=16, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
                ft.Text(
                    lede, size=13.5, color=MUTED, font_family="Nunito",
                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text("Читать →", size=13, weight=ft.FontWeight.W_700, color=PRIMARY, font_family="Nunito"),
            ], spacing=6),
            bgcolor=SURFACE, padding=16, border_radius=18,
            on_click=lambda e, aid=article["id"]: self.open_article(aid),
        )

    def subview_back(self, e=None):
        prev = self.subview
        self.subview = None
        if prev == "bowl":
            self.feed_busy = False
        if prev in ("weight", "bowl", "weather", "events", "health"):
            self.tab = 0
            self.nav.selected_index = 0
            self.state["lastTab"] = 0
            self.save()
        elif prev in ("transition", "pack"):
            self.tab = 1
            self.nav.selected_index = 1
            self.state["lastTab"] = 1
            self.save()
        self.render()

    def parse_weight_date(self, entry):
        raw = str((entry or {}).get("date") or "").strip()
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    def weight_entries_on(self, diary, day):
        return [e for e in diary if self.parse_weight_date(e) == day]

    def weight_streak(self, diary):
        days = {self.parse_weight_date(e) for e in diary}
        days.discard(None)
        if not days:
            return 0
        today = date.today()
        cursor = today if today in days else today - timedelta(days=1)
        n = 0
        while cursor in days:
            n += 1
            cursor -= timedelta(days=1)
        return n

    def ru_days(self, n):
        n = abs(int(n)) % 100
        n1 = n % 10
        if 11 <= n <= 14:
            return "дней"
        if n1 == 1:
            return "день"
        if 2 <= n1 <= 4:
            return "дня"
        return "дней"

    def format_weight_date(self, day):
        return f"{WEEKDAYS_FULL_RU[day.weekday()]}, {day.day} {MONTHS_GEN_RU[day.month - 1]}"

    def shift_weight_month(self, delta):
        y = self.weight_month.year
        m = self.weight_month.month + int(delta)
        while m > 12:
            m -= 12
            y += 1
        while m < 1:
            m += 12
            y -= 1
        self.weight_month = date(y, m, 1)
        self.weight_adding = False
        self.render()

    def select_weight_day(self, day):
        self.weight_selected = day
        self.weight_adding = False
        self.weight_draft = ""
        self.render()

    def weight_add_reason(self, diary, day):
        if day is None:
            return "Сначала выберите сегодняшнюю дату"
        if day != date.today():
            return "Записать вес можно только за сегодня"
        if len(self.weight_entries_on(diary, day)) >= WEIGHT_MAX_PER_DAY:
            return "Сегодня уже 2 записи — больше нельзя"
        return None

    def start_weight_add(self, e=None):
        pet = self.active()
        if not pet:
            return
        diary = self.state.setdefault("weightDiary", {}).setdefault(pet["id"], [])
        reason = self.weight_add_reason(diary, self.weight_selected)
        if reason:
            self.toast(reason)
            return
        self.weight_adding = True
        last = diary[-1]["weightKg"] if diary else pet.get("weightKg")
        self.weight_draft = str(last or "")
        self.render()

    def cancel_weight_add(self, e=None):
        self.weight_adding = False
        self.weight_draft = ""
        self.render()

    def weight_day_cell(self, day, count, selected, species="dog"):
        today = date.today()
        is_today = day == today
        future = day > today
        number_color = PRIMARY if is_today else (MUTED if future else TEXT)
        bg = CHIP if selected else SURFACE
        border_color = PRIMARY if selected else (SUCCESS if count else BORDER)
        if future:
            face = ft.Container(width=26, height=26)
        else:
            face = self.face_img(species, count >= 1, size=26)
        return ft.Container(
            ft.Column([
                ft.Text(str(day.day), size=13, weight=ft.FontWeight.W_800, color=number_color,
                        text_align=ft.TextAlign.CENTER, font_family="Nunito"),
                ft.Text(WEEKDAYS_RU[day.weekday()], size=10, color=MUTED,
                        text_align=ft.TextAlign.CENTER, font_family="Nunito"),
                face,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
            expand=True,
            height=82,
            bgcolor=bg,
            border_radius=14,
            border=ft.Border.all(width=1.5, color=border_color),
            padding=ft.Padding.only(top=6, bottom=6),
            on_click=lambda e, d=day: self.select_weight_day(d),
            opacity=0.45 if future else 1,
        )

    def view_weight_diary(self):
        pet = self.active()
        if not pet:
            return ft.Column([
                ft.TextButton("‹ Назад", on_click=self.subview_back),
                ft.Text("Сначала добавьте питомца.", size=15, color=MUTED),
            ], spacing=12)
        diary = self.state.setdefault("weightDiary", {}).setdefault(pet["id"], [])
        selected = self.weight_selected or date.today()
        day_entries = self.weight_entries_on(diary, selected)
        streak = self.weight_streak(diary)
        who = "кошки" if pet.get("species") == "cat" else "собаки"
        pet_name = pet.get("name") or who
        reason = self.weight_add_reason(diary, selected)
        can_add = reason is None
        month = self.weight_month
        counts = {}
        for entry in diary:
            d = self.parse_weight_date(entry)
            if d:
                counts[d] = counts.get(d, 0) + 1

        species = pet.get("species")
        logged_today = counts.get(date.today(), 0) >= 1
        if logged_today:
            face_title = "Весёлая морда"
            face_sub = f"Вес {pet_name} сегодня записан — я рад."
        else:
            face_title = "Грустная морда"
            face_sub = f"Сегодня вес ещё не записан. Запиши — и морда {who} станет весёлой."

        mascot = self.card(
            ft.Row([
                self.face_img(species, logged_today, size=56),
                ft.Column([
                    ft.Text(face_title, size=18, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
                    ft.Text(face_sub, size=13, color=MUTED, font_family="Nunito"),
                ], spacing=2, expand=True),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

        if streak:
            fire_title = f"{streak} {self.ru_days(streak)} подряд"
            fire_sub = f"Вес {pet_name} записан каждый день. Пропуск гасит огонёк, вчера уже не дописать."
            fire_color = "#E85D04"
        else:
            fire_title = "Серия пока не началась"
            fire_sub = f"Запишите вес {who} сегодня. Пропущенный день обратно не записать."
            fire_color = MUTED

        fire = self.card(
            ft.Row([
                ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=fire_color, size=32),
                ft.Column([
                    ft.Text(fire_title, size=18, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
                    ft.Text(fire_sub, size=13, color=MUTED, font_family="Nunito"),
                ], spacing=2, expand=True),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

        cal_weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month)
        week_rows = [
            ft.Row([
                self.weight_day_cell(day, counts.get(day, 0), day == selected, species)
                if day.month == month.month else
                ft.Container(expand=True, height=82)
                for day in week
            ], spacing=6)
            for week in cal_weeks
        ]
        month_title = f"{MONTHS_RU[month.month - 1]} {month.year}"
        calendar_card = self.card(
            ft.Row([
                ft.Container(
                    ft.Icon(ft.Icons.CHEVRON_LEFT, color=TEXT, size=22),
                    width=36, height=36, border_radius=12, bgcolor=BG,
                    alignment=ft.Alignment.CENTER,
                    on_click=lambda e: self.shift_weight_month(-1),
                ),
                ft.Text(month_title, size=16, weight=ft.FontWeight.W_800, color=TEXT,
                        text_align=ft.TextAlign.CENTER, expand=True, font_family="Nunito"),
                ft.Container(
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT, size=22),
                    width=36, height=36, border_radius=12, bgcolor=BG,
                    alignment=ft.Alignment.CENTER,
                    on_click=lambda e: self.shift_weight_month(1),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row([
                ft.Text("грустная — нет записи", size=11, color=MUTED, expand=True),
                ft.Text("весёлая — вес записан", size=11, color=SUCCESS),
            ]),
            *week_rows,
        )

        plus = ft.Container(
            ft.Icon(ft.Icons.ADD, color="white", size=22),
            width=44, height=44, bgcolor=PRIMARY if can_add else MUTED,
            border_radius=22, alignment=ft.Alignment.CENTER,
            on_click=self.start_weight_add,
            opacity=1 if can_add else 0.55,
        )
        selected_logged = selected <= date.today() and bool(day_entries)
        selected_controls = [
            ft.Row([
                self.face_img(species, selected_logged, size=40) if selected <= date.today() else ft.Container(),
                ft.Column([
                    ft.Text(self.format_weight_date(selected), size=16, weight=ft.FontWeight.W_800,
                            color=TEXT, font_family="Nunito"),
                    ft.Text(
                        (
                            f"{len(day_entries)} из {WEIGHT_MAX_PER_DAY} записей сегодня"
                            if selected == date.today()
                            else "Новую запись сюда поставить нельзя"
                        ),
                        size=13, color=MUTED, font_family="Nunito",
                    ),
                ], spacing=2, expand=True),
                plus,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        ]
        if self.weight_adding and can_add:
            selected_controls.extend([
                ft.TextField(
                    label="Вес, кг",
                    value=self.weight_draft,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    border_radius=14,
                    bgcolor=BG, color=TEXT, border_color=BORDER,
                    on_change=lambda e: setattr(self, "weight_draft", e.control.value),
                    on_submit=self.add_weight_entry,
                ),
                self.primary_btn("Сохранить вес", self.add_weight_entry),
                self.outline_btn("Отмена", self.cancel_weight_add),
            ])
        selected_card = self.card(*selected_controls)

        entry_rows = []
        for entry in day_entries:
            when = entry.get("time") or ""
            label = f"{when} · {entry.get('weightKg')} кг" if when else f"{entry.get('weightKg')} кг"
            entry_rows.append(
                ft.Text(label, size=15, weight=ft.FontWeight.W_700, color=TEXT, font_family="Nunito")
            )
        if not entry_rows:
            entry_rows = [ft.Text("Пока нет записей за этот день", size=14, color=MUTED)]

        tip = (
            "Совет: вес лучше снимать утром до еды и вечером. "
            "Не больше двух записей в день — так динамика читается спокойнее, без скачков после миски."
        )
        if len(diary) >= 2:
            try:
                delta = float(diary[-1]["weightKg"]) - float(diary[-2]["weightKg"])
            except (TypeError, ValueError, KeyError):
                delta = 0
            if abs(delta) < 0.05:
                tip = "Вес почти не изменился — порцию можно не трогать. " + tip
            elif delta > 0:
                tip = "Вес вырос. Если худеть не планировали — всё ок; если да, чуть уменьшите порцию."
            else:
                tip = "Вес снизился. Если не худели специально — чуть увеличьте порцию."
        if self.weight_adding and can_add:
            limit_txt = "Нажмите «Сохранить вес» — запись появится в календаре."
        elif reason:
            limit_txt = reason
        else:
            limit_txt = "Нажмите плюс, чтобы записать вес за сегодня."

        return ft.Column([
            ft.TextButton("‹ К питомцу", on_click=self.subview_back),
            ft.Text(pet_name, size=22, weight=ft.FontWeight.W_800, color=TEXT),
            ft.Text(f"Сейчас в карточке: {pet.get('weightKg')} кг", size=15, color=MUTED),
            mascot,
            fire,
            calendar_card,
            selected_card,
            ft.Text(limit_txt, size=13, color=MUTED),
            self.card(
                ft.Text("Записи за день", size=13, weight=ft.FontWeight.W_800, color=MUTED),
                *entry_rows,
            ),
            ft.Text(tip, size=14, color=TEXT),
            ft.Container(height=60),
        ], spacing=12)

    def add_weight_entry(self, e=None):
        pet = self.active()
        if not pet:
            return
        day = date.today()
        if self.weight_selected != day:
            self.toast("Записать вес можно только за сегодня")
            return
        diary = self.state.setdefault("weightDiary", {}).setdefault(pet["id"], [])
        reason = self.weight_add_reason(diary, day)
        if reason:
            self.toast(reason)
            return
        raw = (self.weight_draft or "").replace(",", ".").strip()
        try:
            w = float(raw)
        except ValueError:
            self.toast("Введите вес числом")
            return
        if w < 0.3 or w > 120:
            self.toast("Проверьте вес")
            return
        entry = {
            "date": day.strftime("%d.%m.%Y"),
            "time": datetime.now().strftime("%H:%M"),
            "weightKg": round(w, 2),
        }
        diary.append(entry)
        pet["weightKg"] = round(w, 2)
        for i, p in enumerate(self.pets()):
            if p["id"] == pet["id"]:
                self.pets()[i] = pet
                break
        self.weight_draft = ""
        self.weight_adding = False
        self.save()
        self.toast("Вес сохранён")
        self.render()

    # ---------- календарь событий ----------

    def pet_events(self, pet):
        return self.state.setdefault("events", {}).setdefault(pet["id"], [])

    @staticmethod
    def event_day(ev):
        try:
            return date.fromisoformat(str(ev.get("date") or ""))
        except ValueError:
            return None

    def events_on(self, pet, day):
        items = [e for e in self.pet_events(pet) if self.event_day(e) == day]
        items.sort(key=lambda e: (e.get("time") or "99:99", e.get("title") or ""))
        return items

    def upcoming_events(self, pet, limit=5):
        today = date.today()
        items = [e for e in self.pet_events(pet) if (self.event_day(e) or date.min) >= today]
        items.sort(key=lambda e: (e.get("date") or "", e.get("time") or "99:99"))
        return items[:limit]

    def event_day_word(self, day):
        today = date.today()
        if day == today:
            return "сегодня"
        if day == today + timedelta(days=1):
            return "завтра"
        return f"{day.day} {MONTHS_GEN_RU[day.month - 1]}"

    def event_kind_info(self, key):
        kind = EVENT_KIND_BY_KEY.get(key) or EVENT_KIND_BY_KEY["other"]
        icon = getattr(ft.Icons, kind[2], ft.Icons.EVENT)
        return kind[1], icon, kind[3]

    def events_entry_card(self, pet):
        upcoming = self.upcoming_events(pet, 1)
        today_has = bool(self.events_on(pet, date.today()))
        if upcoming:
            ev = upcoming[0]
            day = self.event_day(ev)
            when = self.event_day_word(day) if day else ""
            if ev.get("time"):
                when += f", {ev['time']}"
            title, sub = ev.get("title") or "Событие", when
        else:
            title, sub = "Календарь", "Записать визит, прививку или лекарство"
        return ft.Container(
            ft.Row([
                ft.Container(
                    ft.Icon(ft.Icons.EVENT, color=PRIMARY, size=24),
                    width=44, height=44, border_radius=14, bgcolor=CHIP,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text("Ближайшее событие" if upcoming else "Календарь событий", size=12,
                            weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
                    ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(sub, size=12, color=PRIMARY_DARK if today_has else MUTED, font_family="Nunito",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=1, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=CHIP if today_has else SURFACE, padding=12, border_radius=20,
            border=ft.Border.all(width=1.5, color=PRIMARY if today_has else BORDER),
            on_click=lambda e, p=pet: self.open_events(p),
        )

    def open_events(self, pet):
        self.state["activePetId"] = pet["id"]
        self.tab = 0
        self.nav.selected_index = 0
        self.state["lastTab"] = 0
        self.save()
        self.subview = "events"
        self.event_month = date.today().replace(day=1)
        self.event_selected = date.today()
        self.event_adding = False
        self.event_title_draft = ""
        self.event_time_draft = ""
        self.form_pet = None
        self.render()

    def shift_event_month(self, delta):
        y = self.event_month.year
        m = self.event_month.month + int(delta)
        while m > 12:
            m -= 12
            y += 1
        while m < 1:
            m += 12
            y -= 1
        self.event_month = date(y, m, 1)
        self.render()

    def select_event_day(self, day):
        self.event_selected = day
        self.event_adding = False
        self.render()

    def start_event_add(self, e=None):
        self.event_adding = True
        self.event_kind = "vet"
        self.event_title_draft = ""
        self.event_time_draft = ""
        self.render()

    def cancel_event_add(self, e=None):
        self.event_adding = False
        self.render()

    def set_event_kind(self, key):
        self.event_kind = key
        self.render()

    def save_event(self, e=None):
        pet = self.active()
        if not pet:
            return
        kind_name = self.event_kind_info(self.event_kind)[0]
        title = (self.event_title_draft or "").strip()[:60] or kind_name
        raw_time = (self.event_time_draft or "").strip().replace(".", ":")
        when = ""
        if raw_time:
            try:
                parsed = datetime.strptime(raw_time, "%H:%M")
            except ValueError:
                self.toast("Время напишите так: 14:30 — или оставьте пустым")
                return
            when = parsed.strftime("%H:%M")
        self.pet_events(pet).append({
            "id": "e" + uuid.uuid4().hex[:8],
            "date": self.event_selected.isoformat(),
            "time": when,
            "kind": self.event_kind,
            "title": title,
        })
        self.event_adding = False
        self.save()
        self.toast("Событие записано")
        self.render()

    def delete_event(self, event_id):
        pet = self.active()
        if not pet:
            return
        events = self.pet_events(pet)
        self.state["events"][pet["id"]] = [e for e in events if e.get("id") != event_id]
        self.save()
        self.toast("Событие удалено")
        self.render()

    def event_day_cell(self, day, kinds, selected):
        today = date.today()
        is_today = day == today
        dots = [
            ft.Container(width=6, height=6, border_radius=3, bgcolor=self.event_kind_info(k)[2])
            for k in kinds[:3]
        ]
        return ft.Container(
            ft.Column([
                ft.Text(str(day.day), size=14, weight=ft.FontWeight.W_800,
                        color=PRIMARY if is_today else TEXT, font_family="Nunito",
                        text_align=ft.TextAlign.CENTER),
                ft.Row(dots, spacing=2, alignment=ft.MainAxisAlignment.CENTER, height=6),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            expand=True, height=54, alignment=ft.Alignment.CENTER,
            bgcolor=CHIP if selected else SURFACE, border_radius=14,
            border=ft.Border.all(width=1.5, color=PRIMARY if selected else (BORDER if not is_today else "#B9CDBF")),
            on_click=lambda e, d=day: self.select_event_day(d),
        )

    def event_row(self, ev):
        name, icon, color = self.event_kind_info(ev.get("kind"))
        time_txt = f"{ev['time']} · " if ev.get("time") else ""
        return ft.Row([
            ft.Container(
                ft.Icon(icon, color="white", size=18),
                width=36, height=36, border_radius=12, bgcolor=color,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column([
                ft.Text(ev.get("title") or name, size=15, weight=ft.FontWeight.W_700, color=TEXT,
                        font_family="Nunito", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{time_txt}{name}", size=12, color=MUTED, font_family="Nunito"),
            ], spacing=1, expand=True),
            ft.Container(
                ft.Icon(ft.Icons.DELETE_OUTLINE, color=MUTED, size=20),
                width=36, height=36, border_radius=12, alignment=ft.Alignment.CENTER,
                on_click=lambda e, eid=ev.get("id"): self.delete_event(eid),
            ),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def view_events(self):
        pet = self.active()
        if not pet:
            return ft.Column([
                ft.TextButton("‹ Назад", on_click=self.subview_back),
                ft.Text("Сначала добавьте питомца.", size=15, color=MUTED),
            ], spacing=12)
        name = pet.get("name") or ("Кошка" if pet.get("species") == "cat" else "Собака")
        selected = self.event_selected or date.today()
        month = self.event_month
        by_day = {}
        for ev in self.pet_events(pet):
            d = self.event_day(ev)
            if d:
                by_day.setdefault(d, []).append(ev.get("kind") or "other")

        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month)
        head = ft.Row([
            ft.Text(w, size=11, color=MUTED, expand=True, text_align=ft.TextAlign.CENTER,
                    font_family="Nunito")
            for w in WEEKDAYS_RU
        ], spacing=6)
        grid = [
            ft.Row([
                self.event_day_cell(day, by_day.get(day, []), day == selected)
                if day.month == month.month else ft.Container(expand=True, height=54)
                for day in week
            ], spacing=6)
            for week in weeks
        ]
        cal_card = self.card(
            ft.Row([
                ft.Container(
                    ft.Icon(ft.Icons.CHEVRON_LEFT, color=TEXT, size=22),
                    width=36, height=36, border_radius=12, bgcolor=BG,
                    alignment=ft.Alignment.CENTER,
                    on_click=lambda e: self.shift_event_month(-1),
                ),
                ft.Text(f"{MONTHS_RU[month.month - 1]} {month.year}", size=16,
                        weight=ft.FontWeight.W_800, color=TEXT, expand=True,
                        text_align=ft.TextAlign.CENTER, font_family="Nunito"),
                ft.Container(
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT, size=22),
                    width=36, height=36, border_radius=12, bgcolor=BG,
                    alignment=ft.Alignment.CENTER,
                    on_click=lambda e: self.shift_event_month(1),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            head,
            *grid,
        )

        day_events = self.events_on(pet, selected)
        day_title = f"{WEEKDAYS_FULL_RU[selected.weekday()].capitalize()}, {selected.day} {MONTHS_GEN_RU[selected.month - 1]}"
        plus = ft.Container(
            ft.Icon(ft.Icons.ADD, color="white", size=22),
            width=44, height=44, bgcolor=PRIMARY, border_radius=22,
            alignment=ft.Alignment.CENTER, on_click=self.start_event_add,
        )
        day_controls = [
            ft.Row([
                ft.Column([
                    ft.Text(day_title, size=16, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
                    ft.Text(
                        f"Событий: {len(day_events)}" if day_events else "На этот день ничего не записано",
                        size=13, color=MUTED, font_family="Nunito",
                    ),
                ], spacing=2, expand=True),
                plus,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        ]
        day_controls.extend(self.event_row(ev) for ev in day_events)

        if self.event_adding:
            chips = []
            for key, label, _icon, color in EVENT_KINDS:
                on = key == self.event_kind
                chips.append(ft.Container(
                    ft.Text(label, size=13, weight=ft.FontWeight.W_800,
                            color="white" if on else TEXT, font_family="Nunito"),
                    bgcolor=color if on else SURFACE,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_radius=14,
                    border=ft.Border.all(width=1.5, color=color),
                    on_click=lambda e, k=key: self.set_event_kind(k),
                ))
            day_controls.extend([
                ft.Text("Что записать", size=13, weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
                ft.Row(chips, wrap=True, spacing=6, run_spacing=6),
                ft.TextField(
                    label="Название (можно не писать)",
                    value=self.event_title_draft, max_length=60,
                    border_radius=14, bgcolor=BG, color=TEXT, border_color=BORDER,
                    on_change=lambda e: setattr(self, "event_title_draft", e.control.value),
                ),
                ft.TextField(
                    label="Время, например 14:30 (можно пусто)",
                    value=self.event_time_draft, keyboard_type=ft.KeyboardType.DATETIME,
                    border_radius=14, bgcolor=BG, color=TEXT, border_color=BORDER,
                    on_change=lambda e: setattr(self, "event_time_draft", e.control.value),
                    on_submit=self.save_event,
                ),
                self.primary_btn("Записать событие", self.save_event),
                self.outline_btn("Отмена", self.cancel_event_add),
            ])
        day_card = self.card(*day_controls)

        upcoming = self.upcoming_events(pet, 5)
        up_rows = []
        for ev in upcoming:
            d = self.event_day(ev)
            kname, icon, color = self.event_kind_info(ev.get("kind"))
            when = self.event_day_word(d) if d else ""
            if ev.get("time"):
                when += f", {ev['time']}"
            up_rows.append(ft.Container(
                ft.Row([
                    ft.Icon(icon, color=color, size=20),
                    ft.Column([
                        ft.Text(ev.get("title") or kname, size=14, weight=ft.FontWeight.W_700, color=TEXT,
                                font_family="Nunito", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(when, size=12, color=MUTED, font_family="Nunito"),
                    ], spacing=0, expand=True),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                on_click=lambda e, day=d: self._jump_to_event_day(day),
            ))
        if not up_rows:
            up_rows = [ft.Text("Впереди пока ничего нет", size=14, color=MUTED, font_family="Nunito")]

        return ft.Column([
            ft.TextButton("‹ К питомцу", on_click=self.subview_back),
            ft.Text(name, size=22, weight=ft.FontWeight.W_800, color=TEXT),
            ft.Text("Календарь событий: визиты, прививки, лекарства и всё, что не хочется забыть.",
                    size=14, color=MUTED),
            cal_card,
            day_card,
            self.card(
                ft.Text("Ближайшие", size=13, weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
                *up_rows,
            ),
            ft.Container(height=60),
        ], spacing=12)

    def _jump_to_event_day(self, day):
        if not day:
            return
        self.event_selected = day
        self.event_month = day.replace(day=1)
        self.event_adding = False
        self.render()

    # ---------- заметки о самочувствии ----------

    def pet_health(self, pet):
        return self.state.setdefault("health", {}).setdefault(pet["id"], {})

    def health_entry(self, pet, day):
        entry = self.pet_health(pet).get(day.isoformat())
        return entry if isinstance(entry, dict) else {}

    @staticmethod
    def health_concerns(entry):
        """Сколько тревожных признаков записано за день."""
        if not entry:
            return 0
        count = 0
        for key, _label, options in HEALTH_METRICS:
            chosen = entry.get(key)
            if any(val == chosen and bad for val, _l, bad in options):
                count += 1
        return count + len(entry.get("symptoms") or [])

    def health_level(self, entry):
        """None — записей нет, 0 — всё хорошо, 1 — есть повод присмотреться, 2 — тревожно."""
        if not entry or not any(entry.get(k) for k in ("appetite", "activity", "stool", "symptoms", "no_symptoms")):
            return None
        n = self.health_concerns(entry)
        return 0 if n == 0 else (1 if n == 1 else 2)

    @staticmethod
    def health_color(level):
        if level is None:
            return BORDER
        return PRIMARY if level == 0 else (HEALTH_HONEY if level == 1 else HEALTH_WARN)

    def health_alert(self, pet):
        """Подсказка, если тревожные признаки повторяются несколько дней."""
        today = date.today()
        bad_days = sum(
            1 for i in range(3)
            if self.health_concerns(self.health_entry(pet, today - timedelta(days=i))) > 0
        )
        if bad_days >= 2:
            return "Тревожные признаки уже несколько дней из последних трёх. Лучше показать питомца ветеринару."
        if self.health_concerns(self.health_entry(pet, today)) >= 2:
            return "Сегодня сразу несколько тревожных признаков. Понаблюдайте, и если не станет лучше, обратитесь к ветеринару."
        return ""

    @staticmethod
    def _health_clean(entry):
        """Убирает пустые поля; пустой день превращается в {}."""
        clean = {k: v for k, v in (entry or {}).items() if v}
        return clean if any(clean.get(k) for k in ("appetite", "activity", "stool", "symptoms", "no_symptoms", "note")) else {}

    def health_draft_entry(self, pet):
        """Черновик выбранного дня: меняется до нажатия «Записать»."""
        if getattr(self, "health_draft", None) is None or getattr(self, "health_draft_day", None) != self.health_day:
            self.health_draft = copy.deepcopy(self.health_entry(pet, self.health_day))
            self.health_draft_day = self.health_day
        return self.health_draft

    def health_dirty(self, pet):
        return self._health_clean(self.health_draft_entry(pet)) != self._health_clean(self.health_entry(pet, self.health_day))

    def save_health(self, e=None):
        pet = self.active()
        if not pet:
            return
        clean = self._health_clean(self.health_draft_entry(pet))
        key = self.health_day.isoformat()
        if clean:
            self.pet_health(pet)[key] = copy.deepcopy(clean)
        else:
            self.pet_health(pet).pop(key, None)
        self.health_draft = copy.deepcopy(clean)
        self.save()
        self.toast("Запись сохранена" if clean else "Нечего записывать — отметьте хотя бы один пункт")
        self.render()

    def health_entry_card(self, pet):
        today = date.today()
        entry = self.health_entry(pet, today)
        level = self.health_level(entry)
        alert = self.health_alert(pet)
        if alert:
            title, sub, sub_color = "Есть тревожные признаки", "Откройте и посмотрите записи", HEALTH_WARN
        elif level == 0:
            title, sub, sub_color = "Сегодня всё хорошо", "Запись за сегодня сделана", PRIMARY_DARK
        elif level is not None:
            title, sub, sub_color = "Сегодня есть повод присмотреться", "Запись за сегодня сделана", HEALTH_HONEY
        else:
            title, sub, sub_color = "Как сегодня питомец?", "Аппетит, активность, стул, симптомы", MUTED
        accent = HEALTH_WARN if alert else (PRIMARY if level is not None else BORDER)
        return ft.Container(
            ft.Row([
                ft.Container(
                    ft.Icon(ft.Icons.FAVORITE_BORDER, color=HEALTH_WARN if alert else PRIMARY, size=24),
                    width=44, height=44, border_radius=14, bgcolor=CHIP,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text("Самочувствие", size=12, weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
                    ft.Text(title, size=15, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(sub, size=12, color=sub_color, font_family="Nunito",
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=1, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SURFACE, padding=12, border_radius=20,
            border=ft.Border.all(width=1.5, color=accent),
            on_click=lambda e, p=pet: self.open_health(p),
        )

    def open_health(self, pet):
        self.state["activePetId"] = pet["id"]
        self.tab = 0
        self.nav.selected_index = 0
        self.state["lastTab"] = 0
        self.save()
        self.subview = "health"
        self.health_day = date.today()
        self.health_draft = None
        self.form_pet = None
        self.render()

    def select_health_day(self, day):
        self.health_day = min(day, date.today())
        self.health_draft = None
        self.render()

    def shift_health_day(self, delta):
        self.select_health_day(self.health_day + timedelta(days=int(delta)))

    def set_health_metric(self, key, value):
        pet = self.active()
        if not pet:
            return
        entry = self.health_draft_entry(pet)
        if entry.get(key) == value:
            entry.pop(key, None)
        else:
            entry[key] = value
        self.render()

    def toggle_health_symptom(self, key):
        pet = self.active()
        if not pet:
            return
        entry = self.health_draft_entry(pet)
        items = list(entry.get("symptoms") or [])
        if key in items:
            items.remove(key)
        else:
            items.append(key)
        entry.pop("no_symptoms", None)
        if items:
            entry["symptoms"] = items
        else:
            entry.pop("symptoms", None)
        self.render()

    def toggle_no_symptoms(self, e=None):
        pet = self.active()
        if not pet:
            return
        entry = self.health_draft_entry(pet)
        if entry.get("no_symptoms"):
            entry.pop("no_symptoms", None)
        else:
            entry["no_symptoms"] = True
            entry.pop("symptoms", None)
        self.render()

    def set_health_note(self, text):
        pet = self.active()
        if not pet:
            return
        text = (text or "").strip()[:300]
        entry = self.health_draft_entry(pet)
        if text:
            entry["note"] = text
        else:
            entry.pop("note", None)

    def clear_health_day(self, e=None):
        pet = self.active()
        if not pet:
            return
        self.pet_health(pet).pop(self.health_day.isoformat(), None)
        self.health_draft = {}
        self.health_draft_day = self.health_day
        self.save()
        self.toast("Запись за день удалена")
        self.render()

    def health_all_ok(self, e=None):
        """Быстрая отметка «всё в норме»: нормальные значения, без симптомов."""
        pet = self.active()
        if not pet:
            return
        entry = self.health_draft_entry(pet)
        entry.update({"appetite": "ok", "activity": "ok", "stool": "ok", "no_symptoms": True})
        entry.pop("symptoms", None)
        self.render()

    def health_status_chip(self, entry, dirty=False):
        level = self.health_level(entry)
        text = {
            None: "Состояние: не отмечено",
            0: "Состояние: всё в норме",
            1: "Состояние: стоит присмотреться",
            2: "Состояние: тревожно",
        }[level]
        color = self.health_color(level) if level is not None else MUTED
        return ft.Container(
            ft.Row([
                ft.Container(width=10, height=10, border_radius=5,
                             bgcolor=color if level is not None else None,
                             border=None if level is not None else ft.Border.all(width=1.5, color=MUTED)),
                ft.Text(text + (" (не записано)" if dirty and level is not None else ""),
                        size=14, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_radius=14,
            bgcolor=CHIP if level in (None, 0) else "#FBEDE8",
        )

    def health_to_vet(self, e=None):
        """Из подсказки сразу открывает запись визита к ветеринару на сегодня."""
        pet = self.active()
        if not pet:
            return
        self.open_events(pet)
        self.event_adding = True
        self.event_kind = "vet"
        self.render()

    def health_option_chip(self, label, selected, bad, on_click):
        color = HEALTH_WARN if bad else PRIMARY
        return ft.Container(
            ft.Text(label, size=13, weight=ft.FontWeight.W_800,
                    color="white" if selected else TEXT, font_family="Nunito"),
            bgcolor=color if selected else SURFACE,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_radius=14,
            border=ft.Border.all(width=1.5, color=color if selected else BORDER),
            on_click=on_click,
        )

    def health_day_cell(self, pet, day, selected):
        level = self.health_level(self.health_entry(pet, day))
        is_today = day == date.today()
        return ft.Container(
            ft.Column([
                ft.Text(WEEKDAYS_RU[day.weekday()], size=10, color=MUTED, font_family="Nunito",
                        text_align=ft.TextAlign.CENTER),
                ft.Text(str(day.day), size=14, weight=ft.FontWeight.W_800,
                        color=PRIMARY if is_today else TEXT, font_family="Nunito",
                        text_align=ft.TextAlign.CENTER),
                ft.Container(width=8, height=8, border_radius=4,
                             bgcolor=self.health_color(level) if level is not None else None,
                             border=None if level is not None else ft.Border.all(width=1, color=BORDER)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            expand=True, height=62, alignment=ft.Alignment.CENTER,
            bgcolor=CHIP if selected else SURFACE, border_radius=14,
            border=ft.Border.all(width=1.5, color=PRIMARY if selected else BORDER),
            on_click=lambda e, d=day: self.select_health_day(d),
        )

    def view_health(self):
        pet = self.active()
        if not pet:
            return ft.Column([
                ft.TextButton("‹ Назад", on_click=self.subview_back),
                ft.Text("Сначала добавьте питомца.", size=15, color=MUTED),
            ], spacing=12)
        name = pet.get("name") or ("Кошка" if pet.get("species") == "cat" else "Собака")
        today = date.today()
        day = min(self.health_day or today, today)
        self.health_day = day
        entry = self.health_draft_entry(pet)
        saved = self.health_entry(pet, day)
        dirty = self.health_dirty(pet)

        # лента последних 14 дней
        days = [today - timedelta(days=13 - i) for i in range(14)]
        strip = [
            ft.Row([self.health_day_cell(pet, d, d == day) for d in days[:7]], spacing=6),
            ft.Row([self.health_day_cell(pet, d, d == day) for d in days[7:]], spacing=6),
        ]
        legend = ft.Row([
            ft.Row([ft.Container(width=8, height=8, border_radius=4, bgcolor=c),
                    ft.Text(t, size=11, color=MUTED, font_family="Nunito")], spacing=4)
            for c, t in ((PRIMARY, "хорошо"), (HEALTH_HONEY, "присмотреться"), (HEALTH_WARN, "тревожно"))
        ], spacing=12, wrap=True, run_spacing=4)
        strip_card = self.card(
            ft.Text("Последние 14 дней", size=13, weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
            *strip, legend,
        )

        # выбранный день
        if day == today:
            day_name = "Сегодня"
        elif day == today - timedelta(days=1):
            day_name = "Вчера"
        else:
            day_name = WEEKDAYS_FULL_RU[day.weekday()].capitalize()
        day_title = f"{day_name}, {day.day} {MONTHS_GEN_RU[day.month - 1]}"
        can_next = day < today

        def arrow(icon, delta, enabled):
            return ft.Container(
                ft.Icon(icon, color=TEXT if enabled else BORDER, size=22),
                width=36, height=36, border_radius=12, bgcolor=BG, alignment=ft.Alignment.CENTER,
                on_click=(lambda e: self.shift_health_day(delta)) if enabled else None,
            )

        controls = [
            ft.Row([
                arrow(ft.Icons.CHEVRON_LEFT, -1, True),
                ft.Text(day_title, size=16, weight=ft.FontWeight.W_800, color=TEXT, expand=True,
                        text_align=ft.TextAlign.CENTER, font_family="Nunito"),
                arrow(ft.Icons.CHEVRON_RIGHT, 1, can_next),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.health_status_chip(entry, dirty),
            self.outline_btn("Всё в норме", self.health_all_ok),
            ft.Text("или отметьте по пунктам:", size=12, color=MUTED, font_family="Nunito"),
        ]
        for key, label, options in HEALTH_METRICS:
            chips = [
                self.health_option_chip(
                    opt_label, entry.get(key) == val, bad,
                    lambda e, k=key, v=val: self.set_health_metric(k, v),
                )
                for val, opt_label, bad in options
            ]
            controls.extend([
                ft.Text(label, size=13, weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
                ft.Row(chips, wrap=True, spacing=6, run_spacing=6),
            ])
        chosen = set(entry.get("symptoms") or [])
        controls.extend([
            ft.Text("Симптомы", size=13, weight=ft.FontWeight.W_800, color=MUTED, font_family="Nunito"),
            ft.Row([
                self.health_option_chip("Симптомов нет", bool(entry.get("no_symptoms")), False,
                                        self.toggle_no_symptoms),
                *[
                    self.health_option_chip(label, key in chosen, True,
                                            lambda e, k=key: self.toggle_health_symptom(k))
                    for key, label in HEALTH_SYMPTOMS
                ],
            ], wrap=True, spacing=6, run_spacing=6),
            ft.TextField(
                label="Заметка (что ел, как себя вёл)", value=entry.get("note") or "",
                multiline=True, min_lines=2, max_lines=4, max_length=300,
                border_radius=14, bgcolor=BG, color=TEXT, border_color=BORDER,
                on_change=lambda e: self.set_health_note(e.control.value),
            ),
        ])
        if dirty:
            controls.append(ft.Text("Есть изменения, которые ещё не записаны", size=12,
                                    color=HEALTH_HONEY, weight=ft.FontWeight.W_800, font_family="Nunito"))
        elif saved:
            controls.append(ft.Text("Запись за этот день сохранена", size=12, color=PRIMARY_DARK,
                                    weight=ft.FontWeight.W_800, font_family="Nunito"))
        controls.append(self.primary_btn("Записать", self.save_health))
        if saved:
            controls.append(self.outline_btn("Удалить запись за день", self.clear_health_day))
        day_card = self.card(*controls)

        blocks = [
            ft.TextButton("‹ К питомцу", on_click=self.subview_back),
            ft.Text(name, size=22, weight=ft.FontWeight.W_800, color=TEXT),
            ft.Text("Короткая ежедневная отметка: по ней видно, когда что-то пошло не так.",
                    size=14, color=MUTED),
        ]
        alert = self.health_alert(pet)
        if alert:
            blocks.append(ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=HEALTH_WARN, size=22),
                        ft.Text(alert, size=14, color=TEXT, font_family="Nunito", expand=True),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
                    self.primary_btn("Записать визит к ветеринару", self.health_to_vet),
                ], spacing=10),
                bgcolor="#FBEDE8", padding=14, border_radius=20,
                border=ft.Border.all(width=1.5, color=HEALTH_WARN),
            ))
        blocks.extend([
            strip_card,
            day_card,
            ft.Text("Это личные заметки, а не диагноз. При ухудшении состояния обратитесь к ветеринару.",
                    size=12, color=MUTED, font_family="Nunito"),
            ft.Container(height=60),
        ])
        return ft.Column(blocks, spacing=12)

    def view_transition(self):
        pet = self.active()
        if not pet:
            return ft.Column([
                ft.TextButton("‹ Назад", on_click=self.subview_back),
                ft.Text("Сначала выберите питомца.", size=15, color=MUTED),
            ], spacing=12)
        food_id = (self.state.get("selectedFoods") or {}).get(pet["id"])
        food = next((f for f in self.catalog["foods"] if f["id"] == food_id), None)
        if not food:
            breed = self.breed_of(pet)
            matched = matcher.match(pet, breed, self.catalog["foods"])
            options = []
            seen = set()
            for group in (matched["best"], matched["good"], matched["budget"], matched["medical"]):
                for item in group or []:
                    f = item["food"]
                    if f["id"] in seen:
                        continue
                    seen.add(f["id"])
                    options.append(ft.Container(
                        ft.Text(f["name"], weight=ft.FontWeight.W_700, size=14, color=TEXT),
                        bgcolor=SURFACE, padding=14, border_radius=16,
                        border=ft.Border.all(width=1.5, color=BORDER),
                        on_click=lambda e, food=f: self.pick_transition_food(food),
                    ))
                    if len(options) >= 6:
                        break
                if len(options) >= 6:
                    break
            return ft.Column([
                ft.TextButton("‹ К рациону", on_click=self.subview_back),
                ft.Text("Как перейти на новый корм", size=22, weight=ft.FontWeight.W_800, color=TEXT),
                ft.Text(
                    "Сначала выберите корм, на который переходите. Потом покажем, сколько старого и нового смешивать каждый день.",
                    size=14, color=MUTED,
                ),
                *options,
                ft.Text("Или откройте любой корм в рационе → «Как перейти на этот корм».", size=13, color=MUTED),
                ft.Container(height=40),
            ], spacing=10)
        days = []
        for day, text in nutrition.TRANSITION_DAYS:
            days.append(
                ft.Text(f"{day}. День {day} — {text}", size=15, color=TEXT, font_family="Nunito")
            )
        return ft.Column([
            ft.TextButton("‹ К рациону", on_click=self.subview_back),
            ft.Text("Переход за 7 дней", size=22, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
            ft.Text(f"Новый корм: {food['name']}", size=15, weight=ft.FontWeight.W_700, color=TEXT, font_family="Nunito"),
            ft.Text(
                "Не меняйте корм сразу целиком. Каждый день смешивайте старую и новую порцию так:",
                size=14, color=MUTED, font_family="Nunito",
            ),
            self.card(*days),
            ft.TextButton("Выбрать другой корм", on_click=lambda e: self.clear_transition_food()),
            ft.Text("Если есть хронический диагноз — смену лучше согласовать с врачом.", size=13, color=MUTED, font_family="Nunito"),
            ft.Container(height=40),
        ], spacing=12)

    def pick_transition_food(self, food):
        pet = self.active()
        if not pet:
            return
        self.state.setdefault("selectedFoods", {})[pet["id"]] = food["id"]
        self.save()
        self.render()

    def clear_transition_food(self):
        pet = self.active()
        if pet:
            self.state.setdefault("selectedFoods", {}).pop(pet["id"], None)
            self.save()
        self.render()

    def toggle_transition_day(self, key, value):
        pet = self.active()
        pid = pet["id"] if pet else "_"
        self.state.setdefault("transitionDone", {}).setdefault(pid, {})[key] = bool(value)
        self.save()

    def view_pack_check(self):
        pet = self.active()
        if not pet:
            return ft.Column([
                ft.TextButton("‹ К рациону", on_click=self.subview_back),
                ft.Text("Сначала добавьте питомца на первой вкладке.", size=15, color=MUTED),
            ], spacing=12)

        foods = [f for f in self.catalog["foods"] if f.get("species") == pet.get("species")]
        brands = sorted({f.get("brand") or "" for f in foods if f.get("brand")})
        brand_opts = [ft.DropdownOption(b, b) for b in brands]
        brand_dd = ft.Dropdown(
            label="Бренд",
            hint_text="Выберите бренд с пачки",
            value=self.pack_brand if self.pack_brand in brands else None,
            options=brand_opts,
            bgcolor=SURFACE, color=TEXT, border_color=BORDER,
            on_select=lambda e: self.set_pack_brand(e.control.value),
        )

        blocks = [
            ft.TextButton("‹ К рациону", on_click=self.subview_back),
            ft.Text(
                "Выберите бренд, который видите на полке, затем нажмите на корм — скажем, подходит ли он.",
                size=14, color=MUTED, font_family="Nunito",
            ),
            brand_dd,
        ]

        if self.pack_brand:
            brand_foods = [f for f in foods if f.get("brand") == self.pack_brand]
            breed = self.breed_of(pet)
            matched = matcher.match(pet, breed, brand_foods)
            by_id = {r["food"]["id"]: r for r in matched.get("all") or []}
            blocks.append(ft.Text("Корма этого бренда", size=13, weight=ft.FontWeight.W_800, color=MUTED))
            for f in brand_foods[:24]:
                item = by_id.get(f["id"])
                form = "влажный" if f.get("form") == "wet" else "сухой"
                blocks.append(ft.Container(
                    ft.Column([
                        ft.Text(f["name"], size=14, weight=ft.FontWeight.W_700, color=TEXT, font_family="Nunito"),
                        ft.Text(form, size=12, color=MUTED, font_family="Nunito"),
                    ], spacing=2),
                    bgcolor=SURFACE, padding=14, border_radius=16,
                    border=ft.Border.all(width=1.5, color=BORDER),
                    on_click=lambda e, food=f, it=item: self.show_pack_result(food, it),
                ))
            if not brand_foods:
                blocks.append(ft.Text("Для этого бренда пока нет кормов в каталоге.", color=MUTED))
        else:
            blocks.append(ft.Text("Сначала выберите бренд сверху.", size=14, color=MUTED))

        checks = [ft.Text(f"{i}. {c}", size=14, color=TEXT, font_family="Nunito") for i, c in enumerate(nutrition.PACK_CHECKS, 1)]
        blocks += [
            self.card(
                ft.Text("Если корма нет в списке — смотрите на пачке", size=13, weight=ft.FontWeight.W_800, color=MUTED),
                *checks,
            ),
            ft.Container(height=40),
        ]
        return ft.Column(blocks, spacing=12)

    def set_pack_brand(self, brand):
        self.pack_brand = brand
        self.render()

    def show_pack_result(self, food, item):
        pet = self.active()
        if item and item.get("score", 0) >= 45:
            mark, color = "Можно брать", SUCCESS
            why = item["reasons"][0] if item.get("reasons") else "подходит вашему питомцу"
        elif item:
            mark, color = "Сомнительно", ACCENT
            why = item["reasons"][0] if item.get("reasons") else "есть более удачные варианты"
        else:
            mark, color = "Лучше не брать", DANGER
            why = "не подходит по виду, аллергену или это лечебный корм без вашего диагноза"
        grams = nutrition.portion_grams(pet, food) if pet else 0
        form = "влажный" if food.get("form") == "wet" else "сухой"
        self.show_dialog_sheet(food["name"], [
            ft.Text(mark, size=20, weight=ft.FontWeight.W_800, color=color, font_family="Nunito"),
            ft.Text(why, size=15, color=TEXT, font_family="Nunito"),
            ft.Text(f"{food.get('brand')} · российский {form} · примерно {grams} г в день", size=14, color=MUTED),
            ft.Text(food.get("composition") or "", size=14, color=TEXT),
        ])
    def list_row(self, title, on_click=None):
        return ft.Container(
            ft.Row([
                ft.Text(title, weight=ft.FontWeight.W_700, expand=True, color=TEXT),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED),
            ]),
            padding=ft.Padding.symmetric(vertical=10),
            on_click=on_click,
        )

    def open_article(self, aid):
        self.article_id = aid
        self.render()

    def view_article(self):
        article = next((a for a in ARTICLES if a["id"] == self.article_id), None)
        if not article:
            self.article_id = None
            return self.view_more()
        return ft.Column([
            ft.TextButton("‹ Назад", on_click=lambda e: self.open_article(None)),
            ft.Container(
                ft.Column([
                    ft.Text(article["title"], size=22, weight=ft.FontWeight.W_800, color=TEXT, font_family="Nunito"),
                    ft.Text(article["text"], size=15, color=TEXT, font_family="Nunito"),
                ], spacing=12),
                bgcolor=SURFACE, padding=18, border_radius=22,
                border=ft.Border.all(width=1.5, color=BORDER),
            ),
            ft.Container(height=80),
        ], spacing=12)

    def donate_soon(self, e=None):
        self.toast("Оплата подключится позже — раздел в разработке.")

    def open_feedback(self, e=None):
        self.page.launch_url("mailto:feedback@normalap.app")

    def export_payload(self):
        return {
            "pets": self.state.get("pets"),
            "selectedFoods": self.state.get("selectedFoods"),
            "weightDiary": self.state.get("weightDiary"),
            "feedDiary": self.state.get("feedDiary"),
            "events": self.state.get("events"),
            "health": self.state.get("health"),
            "transitionDone": self.state.get("transitionDone"),
            "weatherCityId": self.state.get("weatherCityId"),
            "exportedAt": datetime.now().isoformat(),
        }

    async def export_data(self, e=None):
        raw = json.dumps(self.export_payload(), ensure_ascii=False, indent=2).encode("utf-8")
        if is_phone(self.page):
            saved = await self.picker.save_file(
                dialog_title="Сохранить данные НормаЛап",
                file_name="normalap-export.json",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["json"],
                src_bytes=raw,
            )
            if saved:
                self.toast("Файл сохранён")
            return
        dest = user_dir() / "normalap-export.json"
        dest.write_bytes(raw)
        self.toast("Файл сохранён в папку приложения")

    async def import_data(self, e=None):
        files = await self.picker.pick_files(
            dialog_title="Импорт данных НормаЛап",
            allowed_extensions=["json"],
            with_data=True,
        )
        if not files:
            return
        picked = files[0]
        try:
            if picked.bytes:
                data = json.loads(picked.bytes.decode("utf-8"))
            elif picked.path:
                data = json.loads(Path(picked.path).read_text(encoding="utf-8"))
            else:
                raise ValueError("empty")
        except Exception:
            self.toast("Не получилось прочитать файл")
            return
        if isinstance(data.get("pets"), list):
            self.state["pets"] = data["pets"]
        if data.get("selectedFoods"):
            self.state["selectedFoods"] = data["selectedFoods"]
        if data.get("weightDiary"):
            self.state["weightDiary"] = data["weightDiary"]
        if data.get("feedDiary"):
            self.state["feedDiary"] = data["feedDiary"]
        if isinstance(data.get("events"), dict):
            self.state["events"] = data["events"]
        if isinstance(data.get("health"), dict):
            self.state["health"] = data["health"]
        if data.get("transitionDone"):
            self.state["transitionDone"] = data["transitionDone"]
        if data.get("weatherCityId"):
            self.state["weatherCityId"] = data["weatherCityId"]
            self.state["weatherCache"] = None
        for pet in self.state.get("pets") or []:
            if pet.get("breedId") == "dog-18":
                pet["breedId"] = "dog-08"
        self.state["theme"] = "light"
        self.save()
        self.toast("Данные загружены")
        self.render()

    def reset_onboard(self, e=None):
        self.state["onboardingDone"] = False
        self.onboard_i = 0
        self.save()
        self.render()


def main(page: ft.Page):
    page.title = "НормаЛап"
    font_family = "Nunito" if bundled_exists("assets", "fonts", "Nunito.ttf") else "Calibri"
    if font_family == "Nunito":
        page.fonts = {"Nunito": "fonts/Nunito.ttf"}
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=PRIMARY, font_family=font_family)
    page.padding = 0
    if not is_phone(page):
        page.window.width = 420
        page.window.height = 860
        page.window.min_width = 380
        page.window.max_width = 520
        page.window.min_height = 640
        icon = resource("assets", "icons", "icon.png")
        if icon.is_file():
            page.window.icon = str(icon)
    Normalap(page)


if __name__ == "__main__":
    ft.run(main, assets_dir=str(resource("assets")))
