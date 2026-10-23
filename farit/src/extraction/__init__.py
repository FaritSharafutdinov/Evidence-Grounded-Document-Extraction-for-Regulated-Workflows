"""S4 extraction battery: five simple extraction methods on one model (TASK-015).

Modules
-------
``backends``          one ``generate(messages, json_schema, max_tokens) -> (text, usage)``
                      interface over a local MLX model and a hub OpenAI-compatible server.
``methods``           the five methods M1..M5 (four LLM, one rule-based).
``run_battery``       CLI runner: predictions + per-call cost meta under ``farit/``.
``evaluate_battery``  scores every method x layer against gold v1.3 and writes the table.

Everything writes only inside ``farit/``; ``sdsbench/``, ``scripts/`` and ``data/``
are imported read-only.
"""