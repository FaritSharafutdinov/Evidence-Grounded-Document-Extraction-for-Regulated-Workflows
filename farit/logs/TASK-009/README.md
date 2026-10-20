# Логи TASK-009: zero-score investigation (S3)

Дата: 2026-10-20. Модель финальной трассировки: `mlx-community/Qwen2.5-7B-Instruct-4bit` (та же, что в baseline).
Все прогоны: из корня репо, `~/ds_env/bin/python farit/src/analysis/zero_score_trace.py`.
Кэш (`farit/data/llm_cache/reranker_*.jsonl`) только читался; `llm_reranker.py` не менялся.

## Формат логов

- `trace_<model>_<doc>_<field>_<layer>.log` — диагностические блоки `[1]..[6]` на каждую
  (instance, page) + SUMMARY-таблица в конце (формат описан в docstring
  `farit/src/analysis/zero_score_trace.py`). Каждый блок:
  1. полный промпт (build_prompt) + sha256;
  2. chat template (apply_chat_template) — полный текст;
  3. топ-10 токенов последней позиции (rank, id, logit, logprob_f32, logprob_f64, token);
  4. резолюция token ids Yes/No (все 8 варианта + fallback'и, single-token-флаги);
  5. yes/no logprob (f32-путь и f64-пересчёт) → exp → probabilities → score,
     score_f32 (frozen math) vs score_f64 + прямая проверка score_page_mlx();
  6. greedy-генерация 5 токенов + согласованность со скором;
  7. сравнение float32/float64 + кэш-скаор этой записи.
- `*_stdout.log` — полный stdout соответствующего прогона (дублирует trace-лог + прогресс).
- `q4_cache_replay_stdout.log` — Q4: реплей 3 кэш-записей (zero/one/mid) с сравнением байт-в-байт.
- `microexp_fp16_collapse.log` — три микро-эксперимента без модели: (1) синтетический softmax
  не схлопывается; (2) device fp16 softmax на реальных логитах — детерминирован и обнуляет
  хвост; (3) формула лестницы кэш-скоров.
- `ntl_sds03_p1_native.npy` — сырые lm_head-логиты (float32-контейнер значений float16),
  sds_03.pdf:molecular_weight, страница 1, native. Использовался в микро-экспериментах.

## Прогнанные кейсы (7B, native)

| Кейс | Страниц | cache-скоры |
|------|---------|-------------|
| sds_03.pdf:molecular_weight | 1–11 | все 0.0 (вырожденный) |
| sds_01.pdf:chemical_formula | 1–9 | все 0.0 (вырожденный) |
| sds_19.pdf:product_name | 1–7 | p1=1.0 (gold, контроль), p4=5.93e-8 (плечо fp16), p2,3,5,6,7=0.0 |

## Команды воспроизведения

```bash
cd Evidence-Grounded-Document-Extraction-for-Regulated-Workflows

# отладка на 0.5B (одна страница)
~/ds_env/bin/python farit/src/analysis/zero_score_trace.py \
    --instance "sds_03.pdf:molecular_weight" \
    --model mlx-community/Qwen2.5-0.5B-Instruct-4bit --layer native --pages 5

# финальные трассировки (7B, по 3 кейсам)
~/ds_env/bin/python farit/src/analysis/zero_score_trace.py \
    --instance "sds_03.pdf:molecular_weight" \
    --model mlx-community/Qwen2.5-7B-Instruct-4bit --layer native
# (аналогично для sds_01/chemical_formula и sds_19/product_name)

# Q4: реплей кэша
~/ds_env/bin/python farit/src/analysis/zero_score_trace.py --q4 \
    --model mlx-community/Qwen2.5-7B-Instruct-4bit
```

## Файлы

- `trace_mlx-community_Qwen2.5-0.5B-Instruct-4bit_sds_03_molecular_weight_native.log` — отладка 0.5B (стр. 5)
- `trace_mlx-community_Qwen2.5-7B-Instruct-4bit_sds_03_molecular_weight_native.log` — кейс 1 (11 стр, 7B)
- `trace_mlx-community_Qwen2.5-7B-Instruct-4bit_sds_01_chemical_formula_native.log` — кейс 2 (9 стр, 7B)
- `trace_mlx-community_Qwen2.5-7B-Instruct-4bit_sds_19_product_name_native.log` — кейс 3 / контроль (7 стр, 7B)
- `trace_qwen7b_*_stdout.log` × 3 — stdout трёх 7B-прогонов
- `q4_cache_replay_stdout.log` — Q4 реплей (zero/one/mid)
- `microexp_fp16_collapse.log` — протокол микро-экспериментов
- `ntl_sds03_p1_native.npy` — сохранённые логиты (для оффлайн-анализа device-softmax)
