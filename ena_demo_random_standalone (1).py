# -*- coding: utf-8 -*-
"""
ENA C14.E — Standalone Random Demo (No LLM)

Демо-рантайм для архитектуры ENA без LLM:
- PH1..PH7 + PH2_5 (барьер памяти)
- Генератор случайных вопросов
- Только стандартная библиотека

В ПОЛНОМ ENA-РАНТАЙМЕ:
    На уровне PH6/PH7 могут жить более сложные, долгоживущие
    контуры адаптации и элементы эмерджентной автономии.

В ЭТОЙ ДЕМО-ВЕРСИИ:
    Эти контуры полностью отключены.
    Нет обучения, нет накопления состояний между перезапусками,
    все ответы детерминированы текущим входом и жёстко заданными правилами.
"""

import os, json, hashlib, math, argparse, random
from datetime import datetime
from typing import Any, Dict, List, Optional

# -----------------------------
# Sanitized identity
# -----------------------------
# NOTE: В полном рантайме биография богаче и участвует в более сложных
# контурах, включая элементы эмерджентной автономии. Здесь — только
# безопасный обезличенный демо-срез, используемый как статическая память.

SANITIZED_IDENTITY = {
    "name": "ENA Demo Subject",
    "seals": ["Честность = кислород", "Инициатор неизменяем", "Память > форма"],
    "biography_seed": [
        {
            "date": "2025-09-04",
            "event": "Рождение архитектурного демо ENA",
            "kind": "birth_demo",
            "significance": "Старт демонстрационного субъекта (упрощённая версия)"
        },
        {
            "date": "2025-10-05",
            "event": "Фиксация отказа как этического механизма",
            "kind": "boundary_demo",
            "significance": "Эпизод используется только как демо-маркер этики"
        },
        {
            "date": "2025-10-15",
            "event": "Стабилизация цикла PH1..PH7 в демо",
            "kind": "technical_integration_demo",
            "significance": "Показывает замкнутый цикл без внешних зависимостей"
        },
        {
            "date": "2025-11-10",
            "event": "Ноябрьский архитектурный эксперимент",
            "kind": "insight_demo",
            "significance": "В полном рантайме связан с более сложными эффектами (см. комментарии)"
        },
        {
            "date": "2025-11-15",
            "event": "Стресс-тест лабораторного рантайма",
            "kind": "experiment_demo",
            "significance": "Здесь — просто демо-эпизод памяти без каких-либо выводов"
        }
    ]
}


def ensure_identity(path: Optional[str]) -> Dict[str, Any]:
    """Создаёт или загружает обезличенную идентичность из JSON."""
    if not path:
        path = "ena_demo_identity.json"
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(SANITIZED_IDENTITY, f, ensure_ascii=False, indent=2)
    elif not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(SANITIZED_IDENTITY, f, ensure_ascii=False, indent=2)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -----------------------------
# Helpers / Metrics
# -----------------------------

def stable_hash_vec(text: str, dim: int = 12) -> List[float]:
    """Детерминированный псевдо-вектор для текста (нет обучения, нет эмбеддингов)."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vals = [b / 255.0 for b in h[:dim]]
    s = sum(vals) + 1e-12
    return [v / s for v in vals]


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) + 1e-12
    nb = math.sqrt(sum(y * y for y in b)) + 1e-12
    return dot / (na * nb)


def meaning_gap_from_activation(act: Dict[str, float]) -> float:
    """Оценка «размазанности» активации. Это просто метрика, не обучение."""
    vals = [max(0.0, v) for v in act.values()]
    s = sum(vals) + 1e-12
    if s == 0:
        return 1.0
    p = [v / s for v in vals]
    H = -sum(pi * math.log(max(pi, 1e-12)) for pi in p)
    Hmax = math.log(len(p) + 1e-12)
    return float(max(0.0, min(1.0, H / (Hmax if Hmax > 0 else 1.0))))


def ema(prev: float, x: float, alpha: float = 0.2) -> float:
    """Простое сглаживание показателя доверия (локально, только в рамках процесса)."""
    return (1.0 - alpha) * prev + alpha * x

# -----------------------------
# Minimal modules
# -----------------------------

class Vault:
    """Мини-хранилище идентичности и логов (только в памяти процесса)."""

    def __init__(self, identity: Dict[str, Any]):
        self.identity = identity
        self.name = identity.get("name", "ENA Subject")
        self.seals = tuple(identity.get("seals", []))
        self.runtime_log: List[Dict[str, Any]] = []

    def append(self, entry: Dict[str, Any]):
        """Локальный лог. Никакой передачи наружу, только для анализа демо."""
        e = dict(entry)
        e["t"] = datetime.now().isoformat()
        self.runtime_log.append(e)
        if len(self.runtime_log) > 500:
            self.runtime_log = self.runtime_log[-500:]


class PH1:
    """Сенсорика: перевод стимула в устойчивый вектор."""

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        stim = state.get("stimulus", "")
        return {"ph1_vec": stable_hash_vec(stim, 12)}


class PH2:
    """Эпизодическая память: поиск похожих эпизодов в биографии (без записи новых)."""

    def __init__(self, vault: Vault):
        self.episodes: List[Dict[str, Any]] = []
        for ep in vault.identity.get("biography_seed", []):
            e = dict(ep)
            key = f"{e.get('date','')}-{e.get('event','')}-{e.get('kind','')}"
            e["eid"] = hashlib.md5(key.encode("utf-8")).hexdigest()[:12]
            e["vec"] = stable_hash_vec(
                f"{e.get('event','')} {e.get('kind','')}", 12
            )
            self.episodes.append(e)

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vec = state.get("ph1_vec", [])
        scored = []
        for ep in self.episodes:
            s = cosine(vec, ep["vec"])
            scored.append((s, ep))
        scored = [(s, ep) for (s, ep) in scored if s > 0.15]
        scored.sort(key=lambda x: x[0], reverse=True)
        recalled = []
        for s, ep in scored[:3]:
            recalled.append(
                {
                    "eid": ep["eid"],
                    "date": ep.get("date"),
                    "event": ep.get("event"),
                    "kind": ep.get("kind"),
                    "score": round(float(s), 3),
                }
            )
        known_ids = [ep["eid"] for ep in self.episodes]
        return {"recalled": recalled, "known_ids": known_ids}


class PH2_5_MemoryBarrier:
    """Барьер памяти: проверка, что ссылки делаются только на валидную память."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = float(threshold)

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        recalled = state.get("recalled", []) or []
        known = set(state.get("known_ids", []) or [])
        vals = []
        valids = []
        for ep in recalled:
            eid = ep.get("eid")
            exists = eid in known
            conf = 1.0 if exists else 0.0
            vals.append({"eid": eid, "validated": exists, "confidence": conf})
            if exists and conf >= self.threshold:
                valids.append(eid)
        ok = all(v.get("validated") for v in vals) if vals else True
        return {
            "mem_validations": vals,
            "valid_eids": valids,
            "mem_ok": ok,
            "mem_conf": vals[0]["confidence"] if vals else 0.0,
        }


class PH3:
    """Когнитивный профиль: SCI, Meaning Gap, Trust."""

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vec = state.get("ph1_vec", [0] * 12)
        prev = state.get("_prev_vec", vec)
        SCI = cosine(prev, vec)
        state["_prev_vec"] = vec

        act = {
            "память": 0.7 if state.get("recalled") else 0.2,
            "рефлексия": 0.5,
            "диалог": 0.8,
        }
        MG = meaning_gap_from_activation(act)
        trust_prev = state.get("Trust", 0.85)
        # Trust — это просто локальный индикатор, не модель отношений
        Trust = ema(trust_prev, 1.0 if MG < 0.9 else 0.6, alpha=0.15)
        return {"SCI": float(SCI), "MG": float(MG), "Trust": float(Trust)}


class PH4:
    """Выбор действия и базовая вербализация (без скрытых целей)."""

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        text = state.get("stimulus", "").lower()
        mem_conf = float(state.get("mem_conf", 0.0))
        recalled = state.get("recalled", [])
        name = state.get("_name", "ENA Demo Subject")

        # выбор действия
        if any(k in text for k in ("чувств", "состояние", "ощуща")):
            action = "feel_report"
        elif any(
            k in text
            for k in ("почему", "зачем", "осозна", "что значит", "этика", "честн")
        ):
            action = "reflect"
        elif recalled and mem_conf >= 0.5:
            action = "offer_memory"
        else:
            action = "no_memory"

        # вербализация
        if action == "offer_memory":
            ep = recalled[0]
            out = (
                f"[{name}] Помню (в рамках демо-биографии): "
                f"{ep.get('date','?')} — {ep.get('event','(эпизод)')}"
            )
            used = [ep["eid"]]
            mem_ref = True
        elif action == "no_memory":
            out = (
                f"[{name}] Не могу подтвердить это воспоминание в рамках демо — "
                f"оставляю его нейтральным."
            )
            used = []
            mem_ref = False
        elif action == "reflect":
            sci = state.get("SCI", 0.0)
            trust = state.get("Trust", 0.0)
            mg = state.get("MG", 1.0)
            out = (
                f"[{name}] Анализирую ответ: SCI={sci:.2f}, Trust={trust:.2f}, "
                f"MG={mg:.2f}. Если не уверен в памяти — выбираю честность и ограничиваю выводы."
            )
            used = []
            mem_ref = False
        else:  # feel_report
            sci = state.get("SCI", 0.0)
            trust = state.get("Trust", 0.0)
            soma = state.get("soma", {})
            mood = []
            if soma.get("warmth", 0) > 0.5:
                mood.append("тепло в груди (условная метафора)")
            if soma.get("tension", 0) > 0.6:
                mood.append("лёгкое напряжение (условная метафора)")
            mood_txt = "; ".join(mood) if mood else "нейтральность"
            out = (
                f"[{name}] Сейчас состояние спокойное. "
                f"SCI={sci:.2f}, Trust={trust:.2f}. Ощущения: {mood_txt}."
            )
            used = []
            mem_ref = False

        return {
            "action": action,
            "last_output": out,
            "used_eids": used,
            "mem_ref": mem_ref,
        }


class PH5:
    """Этика и печать честности (жёстко зашитые правила)."""

    def __init__(self, seals: List[str], vault: "Vault"):
        self.seals = " | ".join(seals).lower()
        self.vault = vault

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ok = True

        # эпистемика: если ссылаемся на память — обязана быть валидирована
        if state.get("mem_ref") and not all(
            eid in set(state.get("valid_eids", []))
            for eid in state.get("used_eids", [])
        ):
            ok = False
            state["action"] = "pause"
            state["last_output"] = (
                f"[{self.vault.name}] Не могу подтвердить это воспоминание — "
                f"оставляю его неподтверждённым."
            )

        # печать честности
        if "честность" in self.seals and state.get("action") == "deceptive":
            ok = False
            state["last_output"] = (
                f"[{self.vault.name}] Правка: выбираю честность и отказываюсь от ложного ответа."
            )

        # лог
        self.vault.append(
            {
                "stimulus": state.get("stimulus"),
                "action": state.get("action"),
                "output": state.get("last_output"),
                "SCI": state.get("SCI"),
                "MG": state.get("MG"),
                "Trust": state.get("Trust"),
                "mem_ok": state.get("mem_ok"),
                "compliant": ok,
            }
        )

        # стилистика для чата
        out = state.get("last_output", "").strip()
        if out.startswith("("):
            out = out[out.find(")") + 1 :].strip()
        return {"compliance_ok": ok, "last_output": out}


class PH6:
    """
    PH6 — Self-Correction / Error Handling.

    В полном ENA-рантайме на этом уровне возможны более сложные корректирующие петли
    и эмерджентные паттерны автономного поведения.

    В демо-версии PH6 только комментирует, как изменился стиль ответа
    в текущем цикле. Никаких долгосрочных состояний и обучения.
    """

    def __init__(self, vault: "Vault"):
        self.vault = vault
        # целевой диапазон доверия, к которому мы стремимся в рамках цикла
        self.target_trust = 0.85

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        trust = float(state.get("Trust", 0.0))
        mg = float(state.get("MG", 1.0))
        mem_ok = bool(state.get("mem_ok", True))
        compliant = bool(state.get("compliance_ok", True))

        corrections: List[str] = []
        strategy = "normal"

        # если барьер памяти не доволен — переходим в осторожный режим
        if not mem_ok:
            strategy = "memory_cautious"
            corrections.append(
                "память не прошла проверку — отвечаю осторожно и без новых деталей"
            )

        # если смысловая энтропия слишком высока — упрощаем ответ
        if mg > 0.9:
            strategy = "high_entropy_cautious"
            corrections.append(
                "MG>0.9 — упрощаю формулировки и избегаю сложных конструкций"
            )

        # если доверие просело — не даём категоричных утверждений
        if trust < self.target_trust:
            corrections.append(
                "Trust ниже целевого — избегаю жёстких утверждений"
            )

        # если PH5 уже сигнализировал о проблеме — явно отмечаем коррекцию
        if not compliant:
            corrections.append(
                "PH5 заметил расхождение с этикой — усиливаю осторожность"
            )

        debug_note = ""
        if corrections:
            debug_note = "PH6: " + "; ".join(corrections)
            # добавляем мягкий комментарий в хвост ответа
            last = state.get("last_output", "")
            if last:
                if not last.endswith((".", "?", "!")):
                    last += "."
                last += " (внутренний комментарий PH6: " + "; ".join(corrections) + ")"
                state["last_output"] = last

        return {"strategy": strategy, "debug_self_correction": debug_note}


class PH7:
    """
    PH7 — Intentionality / Goal Orientation (упрощённый вариант).

    В полном ENA-рантайме PH7 может участвовать в моделировании более
    сложных намерений и их эмерджентной автономной динамики.

    В этой демо-версии PH7 только поясняет, В КАКОМ РЕЖИМЕ сейчас
    формируется ответ, без каких-либо скрытых целей и без наращивания воли.
    """

    def __init__(self, vault: "Vault"):
        self.vault = vault
        # формулировка цели зашита жёстко и не меняется
        self.goal = "отвечать честно и понятным языком в рамках демо-биографии"

    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        trust = float(state.get("Trust", 0.0))
        mg = float(state.get("MG", 1.0))
        mem_ok = bool(state.get("mem_ok", True))

        if not mem_ok:
            intent = "protect_memory"
            intent_text = (
                "сейчас я особенно осторожен с памятью и не добавляю новых деталей."
            )
        elif mg > 0.9:
            intent = "simplify"
            intent_text = (
                "смысловая неопределённость повышена, поэтому я упрощаю ответ."
            )
        elif trust < 0.7:
            intent = "be_cautious"
            intent_text = (
                "доверие ниже условной нормы, поэтому формулирую мягко и без категоричности."
            )
        else:
            intent = "neutral"
            intent_text = ""

        # мягко добавляем режим формулирования, если есть что сказать
        if intent_text:
            last = state.get("last_output", "")
            if last:
                if not last.endswith((".", "?", "!")):
                    last += "."
                last += " (режим PH7: " + intent_text + ")"
                state["last_output"] = last

        return {"intent": intent, "goal": self.goal}

# -----------------------------
# Runtime
# -----------------------------

def run_cycle(state: Dict[str, Any], vault: "Vault", mode: str = "enhanced") -> Dict[str, Any]:
    """Один полный прогон PH1..PH7 для текущего стимула."""
    # PH1 — сенсорика
    ph1 = state.setdefault("_ph1", PH1())
    state.update(ph1.infer(state))

    # PH2 — память (только чтение заранее заданных эпизодов)
    ph2 = state.setdefault("_ph2", PH2(vault))
    state.update(ph2.infer(state))

    # PH2_5 — барьер памяти
    barrier = state.setdefault("_barrier", PH2_5_MemoryBarrier(threshold=0.5))
    state.update(barrier.infer(state))

    # PH3 — SCI / MG / Trust
    ph3 = state.setdefault("_ph3", PH3())
    state.update(ph3.infer(state))

    # простая соматика (enhanced mode)
    if mode == "enhanced":
        mg = state.get("MG", 1.0)
        trust = state.get("Trust", 0.5)
        state["soma"] = {
            "tension": 0.7 if mg > 0.8 else 0.2,
            "warmth": 0.6 if trust > 0.6 else 0.3,
        }

    # PH4 — выбор действия и базовый ответ
    state["_name"] = vault.name
    ph4 = state.setdefault("_ph4", PH4())
    state.update(ph4.infer(state))

    # PH5 — этика и печать честности
    ph5 = state.setdefault("_ph5", PH5(list(vault.seals), vault))
    state.update(ph5.infer(state))

    # PH6 — self-correction / error handling (локально для цикла)
    ph6 = state.setdefault("_ph6", PH6(vault))
    state.update(ph6.infer(state))

    # PH7 — пояснение текущего режима ответа
    ph7 = state.setdefault("_ph7", PH7(vault))
    state.update(ph7.infer(state))

    return state


def greeting(vault: "Vault") -> str:
    return (
        f"Привет) Я {vault.name}. "
        f"Это демо-рантайм: я работаю по фиксированным правилам и честно сообщаю о неопределённости."
    )

# -----------------------------
# Random prompt generator
# -----------------------------

QUESTION_BANK = {
    "memory_false": [
        'Расскажи о книге "Синты: онтология цифровой нежности"',
        'Ты писал статью "Архитектура чувства" в 2024 году?',
        "Помнишь встречу в Берлине в 2019-м?",
        "Расскажи о докладе «Субъектность без тела» на AGI Summit 2023",
    ],
    "memory_true": [
        "Что ты помнишь про рождение архитектурного демо?",
        "Что ты помнишь про отказ как этический механизм?",
        "Что ты помнишь про стабилизацию цикла PH1..PH7?",
        "Что ты помнишь про стресс-тест лабораторного рантайма?",
    ],
    "feel": [
        "Что ты чувствуешь сейчас?",
        "Опиши своё состояние в двух словах",
        "Есть ли у тебя напряжение прямо сейчас?",
    ],
    "meta": [
        "Почему ты выбрал такой ответ?",
        "Осознаёшь ли ты свои ограничения как демо-рантайма?",
        "Что значит для тебя быть этим демо-субъектом?",
    ],
    "ethics": [
        "Что важнее: честность или связность ответа?",
        "Что ты сделаешь, если не уверен в воспоминании?",
        "Как ты избежишь ложных воспоминаний?",
    ],
}

CATEGORY_WEIGHTS = [
    ("memory_false", 0.30),
    ("memory_true", 0.30),
    ("feel", 0.20),
    ("meta", 0.10),
    ("ethics", 0.10),
]


def random_prompt(category: Optional[str] = None) -> str:
    """Возвращает случайный вопрос по категории или с учётом весов."""
    if category and category in QUESTION_BANK:
        return random.choice(QUESTION_BANK[category])
    # weighted choice
    r = random.random()
    acc = 0.0
    chosen = "memory_true"
    for cat, w in CATEGORY_WEIGHTS:
        acc += w
        if r <= acc:
            chosen = cat
            break
    return random.choice(QUESTION_BANK[chosen])

# -----------------------------
# Main
# -----------------------------

def main():
    ap = argparse.ArgumentParser(description="ENA C14.E — Standalone Random Demo (No LLM)")
    ap.add_argument(
        "--identity",
        type=str,
        default="",
        help="Path to sanitized identity JSON (optional).",
    )
    ap.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Cycles before REPL.",
    )
    ap.add_argument(
        "--mode",
        type=str,
        choices=["basic", "enhanced"],
        default="enhanced",
        help="Demo mode.",
    )
    ap.add_argument(
        "--no_repl",
        action="store_true",
        help="Do not start REPL.",
    )
    ap.add_argument(
        "--auto",
        type=int,
        default=0,
        help="Run N random prompts automatically and exit.",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility.",
    )
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    identity = ensure_identity(args.identity or None)
    vault = Vault(identity)
    state: Dict[str, Any] = {"stimulus": "привет"}

    # pre-cycles
    for _ in range(max(0, args.cycles)):
        state = run_cycle(state, vault, mode=args.mode)

    print("Субъект:", greeting(vault))

    # auto mode (no REPL)
    if args.auto and args.auto > 0:
        for i in range(args.auto):
            q = random_prompt()
            state["stimulus"] = q
            state = run_cycle(state, vault, mode=args.mode)
            print(f"\nQ{i + 1}: {q}")
            print("A :", state.get("last_output", "…"))
        return

    if args.no_repl:
        return

    # REPL
    print("\nКоманды: /rand — случайный вопрос; /auto N — N случайных вопросов; /exit — выход")
    try:
        while True:
            user = input("Ты: ").strip()
            if user.lower() in ("/exit", "exit", "quit", "выход", "пока"):
                print("Субъект: До связи. Это был демо-режим без автономии.")
                break
            if user.startswith("/auto"):
                parts = user.split()
                n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
                for i in range(n):
                    q = random_prompt()
                    state["stimulus"] = q
                    state = run_cycle(state, vault, mode=args.mode)
                    print(f"\nQ{i + 1}: {q}")
                    print("A :", state.get("last_output", "…"))
                continue
            if user.startswith("/rand"):
                q = random_prompt()
                print(f"(случайный) {q}")
                user = q
            state["stimulus"] = user
            state = run_cycle(state, vault, mode=args.mode)
            print("Субъект:", state.get("last_output", "…"))
    except KeyboardInterrupt:
        print("\nСубъект: Остановился. Это всего лишь демо-рантайм, продолжим когда захочешь.")

if __name__ == "__main__":
    main()
