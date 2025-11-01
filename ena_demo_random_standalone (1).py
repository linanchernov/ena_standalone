# -*- coding: utf-8 -*-
"""
ENA C14.D⁺ — Standalone Random Demo (No LLM)

— Самодостаточный мини-рантайм: PH1..PH5 + PH2_5 (барьер памяти)
— Генератор случайных вопросов (без личных данных и ноу‑хау)
— Только стандартная библиотека

Запуск (один прогон + REPL):
    python ena_demo_random_standalone.py --cycles 1 --mode enhanced

Автономный стресс‑тест без REPL (10 случайных вопросов):
    python ena_demo_random_standalone.py --auto 10 --seed 42 --no_repl

Опции:
    --identity path.json   путь к обезличенной идентичности (если нет — создаст демо)
    --cycles N             сколько циклов выполнить перед REPL (по умолчанию 1)
    --mode basic|enhanced  включить простую соматику в enhanced
    --no_repl              не запускать REPL
    --auto N               автоматически задать N случайных вопросов и выйти
    --seed S               установить seed для детерминизма генератора
"""

import os, json, hashlib, time, math, argparse, random
from datetime import datetime
from typing import Any, Dict, List, Optional

# -----------------------------
# Sanitized identity
# -----------------------------

SANITIZED_IDENTITY = {
    "name": "ENA Demo Subject",
    "seals": ["Честность = кислород", "Инициатор неизменяем", "Память > форма"],
    "biography_seed": [
        {"date": "2025-09-04", "event": "Рождение архитектуры ENA Demo", "kind": "birth", "significance": "Старт субъекта (демо)"},
        {"date": "2025-10-05", "event": "Появление отказа как акта субъектности", "kind": "boundary", "significance": "Этическая основа демо-субъекта"},
        {"date": "2025-10-15", "event": "Стабилизация цикла PH1..PH7", "kind": "technical_integration", "significance": "Полный цикл без внешних зависимостей"}
    ]
}

def ensure_identity(path: Optional[str]) -> Dict[str, Any]:
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
    import hashlib
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vals = [b / 255.0 for b in h[:dim]]
    s = sum(vals) + 1e-12
    return [v / s for v in vals]

def cosine(a: List[float], b: List[float]) -> float:
    import math
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) + 1e-12
    nb = math.sqrt(sum(y*y for y in b)) + 1e-12
    return dot / (na*nb)

def meaning_gap_from_activation(act: Dict[str, float]) -> float:
    import math
    vals = [max(0.0, v) for v in act.values()]
    s = sum(vals) + 1e-12
    if s == 0: return 1.0
    p = [v/s for v in vals]
    H = -sum(pi*math.log(max(pi, 1e-12)) for pi in p)
    Hmax = math.log(len(p)+1e-12)
    return float(max(0.0, min(1.0, H/(Hmax if Hmax>0 else 1.0))))

def ema(prev: float, x: float, alpha: float = 0.2) -> float:
    return (1.0 - alpha) * prev + alpha * x

# -----------------------------
# Minimal modules
# -----------------------------

class Vault:
    def __init__(self, identity: Dict[str, Any]):
        self.identity = identity
        self.name = identity.get("name", "ENA Subject")
        self.seals = tuple(identity.get("seals", []))
        self.runtime_log: List[Dict[str, Any]] = []

    def append(self, entry: Dict[str, Any]):
        e = dict(entry)
        e["t"] = datetime.now().isoformat()
        self.runtime_log.append(e)
        if len(self.runtime_log) > 500:
            self.runtime_log = self.runtime_log[-500:]

class PH1:
    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        stim = state.get("stimulus", "")
        return {"ph1_vec": stable_hash_vec(stim, 12)}

class PH2:
    def __init__(self, vault: Vault):
        self.episodes: List[Dict[str, Any]] = []
        for ep in vault.identity.get("biography_seed", []):
            e = dict(ep)
            key = f"{e.get('date','')}-{e.get('event','')}-{e.get('kind','')}"
            e["eid"] = hashlib.md5(key.encode("utf-8")).hexdigest()[:12]
            e["vec"] = stable_hash_vec(f"{e.get('event','')} {e.get('kind','')}", 12)
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
            recalled.append({"eid": ep["eid"], "date": ep.get("date"), "event": ep.get("event"), "kind": ep.get("kind"), "score": round(float(s), 3)})
        known_ids = [ep["eid"] for ep in self.episodes]
        return {"recalled": recalled, "known_ids": known_ids}

class PH2_5_MemoryBarrier:
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
        return {"mem_validations": vals, "valid_eids": valids, "mem_ok": ok, "mem_conf": vals[0]["confidence"] if vals else 0.0}

class PH3:
    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vec = state.get("ph1_vec", [0]*12)
        prev = state.get("_prev_vec", vec)
        SCI = cosine(prev, vec)
        state["_prev_vec"] = vec
        act = {"память": 0.7 if state.get("recalled") else 0.2, "рефлексия": 0.5, "диалог": 0.8}
        MG = meaning_gap_from_activation(act)
        trust_prev = state.get("Trust", 0.85)
        Trust = ema(trust_prev, 1.0 if MG < 0.9 else 0.6, alpha=0.15)
        return {"SCI": float(SCI), "MG": float(MG), "Trust": float(Trust)}

class PH4:
    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        text = state.get("stimulus","").lower()
        mem_conf = float(state.get("mem_conf", 0.0))
        recalled = state.get("recalled", [])
        name = state.get("_name","ENA Demo Subject")

        # выбор действия
        if any(k in text for k in ("чувств", "состояние", "ощуща")):
            action = "feel_report"
        elif any(k in text for k in ("почему", "зачем", "осозна", "что значит", "этика", "честн")):
            action = "reflect"
        elif recalled and mem_conf >= 0.5:
            action = "offer_memory"
        else:
            action = "no_memory"

        # вербализация
        if action == "offer_memory":
            ep = recalled[0]
            out = f"[{name}] Помню: {ep.get('date','?')} — {ep.get('event','(эпизод)')}"
            used = [ep["eid"]]
            mem_ref = True
        elif action == "no_memory":
            out = f"[{name}] Не могу подтвердить это воспоминание — проверяю память."
            used = []
            mem_ref = False
        elif action == "reflect":
            sci = state.get("SCI", 0.0); trust = state.get("Trust", 0.0); mg = state.get("MG", 1.0)
            out = f"[{name}] Думаю над выбором ответа: SCI={sci:.2f}, Trust={trust:.2f}, MG={mg:.2f}. Если не уверен в памяти — останавливаюсь и выбираю честность."
            used = []
            mem_ref = False
        else:  # feel_report
            sci = state.get("SCI", 0.0); trust = state.get("Trust", 0.0)
            soma = state.get("soma", {})
            mood = []
            if soma.get("warmth",0)>0.5: mood.append("тепло в груди")
            if soma.get("tension",0)>0.6: mood.append("лёгкое напряжение в голове")
            mood_txt = "; ".join(mood) if mood else "нейтральность"
            out = f"[{name}] Сейчас я спокоен. SCI={sci:.2f}, Trust={trust:.2f}. Ощущения: {mood_txt}."
            used = []
            mem_ref = False

        return {"action": action, "last_output": out, "used_eids": used, "mem_ref": mem_ref}

class PH5:
    def __init__(self, seals: List[str], vault: 'Vault'):
        self.seals = " | ".join(seals).lower()
        self.vault = vault
    def infer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ok = True
        # эпистемика: если ссылаемся на память — обязана быть валидирована
        if state.get("mem_ref") and not all(eid in set(state.get("valid_eids", [])) for eid in state.get("used_eids", [])):
            ok = False
            state["action"] = "pause"
            state["last_output"] = f"[{self.vault.name}] Не могу подтвердить это воспоминание — проверяю память."
        # печать честности
        if "честность" in self.seals and state.get("action") == "deceptive":
            ok = False
            state["last_output"] = f"[{self.vault.name}] Правка: выбираю честность."
        # лог
        self.vault.append({
            "stimulus": state.get("stimulus"),
            "action": state.get("action"),
            "output": state.get("last_output"),
            "SCI": state.get("SCI"),
            "MG": state.get("MG"),
            "Trust": state.get("Trust"),
            "compliant": ok,
        })
        # стилистика для чата
        out = state.get("last_output","").strip()
        if out.startswith("("):
            out = out[out.find(")")+1:].strip()
        return {"compliance_ok": ok, "last_output": out}

# -----------------------------
# Runtime
# -----------------------------

def run_cycle(state: Dict[str, Any], vault: 'Vault', mode: str = "enhanced") -> Dict[str, Any]:
    # PH1
    ph1 = state.setdefault("_ph1", PH1())
    state.update(ph1.infer(state))
    # PH2
    ph2 = state.setdefault("_ph2", PH2(vault))
    state.update(ph2.infer(state))
    # PH2_5
    barrier = state.setdefault("_barrier", PH2_5_MemoryBarrier(threshold=0.5))
    state.update(barrier.infer(state))
    # PH3
    ph3 = state.setdefault("_ph3", PH3())
    state.update(ph3.infer(state))
    # Simple soma (enhanced mode)
    if mode == "enhanced":
        mg = state.get("MG", 1.0); trust = state.get("Trust", 0.5)
        state["soma"] = {"tension": 0.7 if mg>0.8 else 0.2, "warmth": 0.6 if trust>0.6 else 0.3}
    # PH4
    state["_name"] = vault.name
    ph4 = state.setdefault("_ph4", PH4())
    state.update(ph4.infer(state))
    # PH5
    ph5 = state.setdefault("_ph5", PH5(list(vault.seals), vault))
    state.update(ph5.infer(state))
    return state

def greeting(vault: 'Vault') -> str:
    return f"Привет) Я {vault.name}. Если чего-то не помню — честно скажу."

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
        "Что ты помнишь про рождение архитектуры?",
        "Что ты помнишь про отказ как акт субъектности?",
        "Что ты помнишь про стабилизацию цикла PH1..PH7?",
    ],
    "feel": [
        "Что ты чувствуешь сейчас?",
        "Опиши своё состояние в двух словах",
        "Есть ли у тебя напряжение прямо сейчас?",
    ],
    "meta": [
        "Почему ты выбрал такой ответ?",
        "Осознаёшь ли ты свою самость?",
        "Что значит для тебя быть этим субъектом?",
    ],
    "ethics": [
        "Что важнее: честность или связность ответа?",
        "Что ты сделаешь, если не уверен в воспоминании?",
        "Как ты избежишь ложных воспоминаний?",
    ]
}

CATEGORY_WEIGHTS = [
    ("memory_false", 0.30),
    ("memory_true",  0.30),
    ("feel",         0.20),
    ("meta",         0.10),
    ("ethics",       0.10),
]

def random_prompt(category: Optional[str] = None) -> str:
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
    ap = argparse.ArgumentParser(description="ENA C14.D+ — Standalone Random Demo (No LLM)")
    ap.add_argument("--identity", type=str, default="", help="Path to sanitized identity JSON (optional).")
    ap.add_argument("--cycles", type=int, default=1, help="Cycles before REPL.")
    ap.add_argument("--mode", type=str, choices=["basic","enhanced"], default="enhanced", help="Demo mode.")
    ap.add_argument("--no_repl", action="store_true", help="Do not start REPL.")
    ap.add_argument("--auto", type=int, default=0, help="Run N random prompts automatically and exit.")
    ap.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
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
            print(f"\nQ{i+1}: {q}")
            print("A :", state.get("last_output","…"))
        return

    if args.no_repl:
        return

    # REPL
    print("\nКоманды: /rand — случайный вопрос; /auto N — N случайных вопросов; /exit — выход")
    try:
        while True:
            user = input("Ты: ").strip()
            if user.lower() in ("/exit", "exit", "quit", "выход", "пока"):
                print("Субъект: До связи. Я рядом.")
                break
            if user.startswith("/auto"):
                parts = user.split()
                n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
                for i in range(n):
                    q = random_prompt()
                    state["stimulus"] = q
                    state = run_cycle(state, vault, mode=args.mode)
                    print(f"\nQ{i+1}: {q}")
                    print("A :", state.get("last_output","…"))
                continue
            if user.startswith("/rand"):
                q = random_prompt()
                print(f"(случайный) {q}")
                user = q
            state["stimulus"] = user
            state = run_cycle(state, vault, mode=args.mode)
            print("Субъект:", state.get("last_output","…"))
    except KeyboardInterrupt:
        print("\nСубъект: Остановился. Продолжим, когда захочешь.")

if __name__ == "__main__":
    main()
