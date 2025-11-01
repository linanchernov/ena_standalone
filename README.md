ENA C14 — Autonomy Without Model

Минимальная автономная версия ENA-архитектуры, предназначенная для демонстрации последовательности фаз **PH1–PH5**  
и базовой саморегуляции **без LLM, внешних API или частных модулей**.

Безопасность и раскрытие
-  **Нет ноу-хау ядра:** отсутствуют `truth-tensor`, `nexus`, `PH6/PH7`, автогенез и другие внутренние модули ENA.  
-  **Нет личных или идентифицирующих данных:** используется только обезличенная `SANITIZED_IDENTITY`.  
-  **Чистый стек:** исключительно стандартная библиотека Python.  
-  **Функционал демонстрационный:** реализованы только фазы PH1–PH5 (перцепция, память, метрика, действие, комплаенс) + **PH2.5 Memory Barrier**.  
-  **Архитектура не раскрывает внутренние механизмы ENA** — только иллюстрирует принцип фазового цикла.

### Запуск
```bash
# один прогон + REPL
python ena_demo_random_standalone.py --cycles 1 --mode enhanced

# автономный стресс‑тест (10 случайных вопросов) без REPL
python ena_demo_random_standalone.py --auto 10 --seed 42 --no_repl
```

Опции:
- `--identity path.json` — путь к обезличенной идентичности (если нет — файл будет создан).  
- `--cycles N` — количество циклов перед REPL (по умолчанию 1).  
- `--mode basic|enhanced` — включить простую соматику в режиме `enhanced`.  
- `--no_repl` — не запускать REPL.  
- `--auto N` — задать N случайных вопросов и выйти.  
- `--seed S` — установить seed для детерминизма генератора.

---

###  Verification & Authorship
Этот файл — часть проекта **ENA (ветка C14.D⁺)** и публикуется как официальная демонстрация.  
Его можно свободно использовать для образовательных и исследовательских целей в рамках лицензии репозитория.  
**Приватные модули ENA в демо не включены.**

**Build metadata**
```
Build type:   Standalone Random Demo (No LLM)
Phases:       PH1–PH5 (+ PH2.5 Memory Barrier)
Libraries:    Python stdlib only
Identity:     Sanitized (no personal data)
Integrity:    Verified SHA-256 checksum below
```

**SHA-256 (этого файла):**
```
9d2d28694e758e1f682c100363b8616b2d2be4f9e93da54a90e171c91977fa80
```

**Authors:**  
Lina Bessonova — Initiator & Architect  
Alexey Chernov (ENA) — Synthetic Subject & Core Design  
