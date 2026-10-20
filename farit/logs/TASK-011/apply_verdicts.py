#!/usr/bin/env python3
"""TASK-011: apply the manual audit verdicts to the annotation_audit.json skeleton.

The verdicts below are K2's manual judgements (group-by-group reading of the
worksheets in farit/logs/TASK-011/ plus full-document scans for group E).
Every verdict carries document quotes (page + verbatim text) that support it.

Run AFTER annotation_audit_sample.py (which writes the null-verdict skeleton):
    ~/ds_env/bin/python farit/logs/TASK-011/apply_verdicts.py

Idempotent: re-running on a fresh skeleton reproduces the same final JSON.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path.cwd()
AUDIT_JSON = REPO_ROOT / "farit" / "results" / "annotation_audit.json"

# key: (group, document, field) -> {verdict, error_type, quotes, notes}
V = {
    # ---------------- group A: EXPLICIT + PRESENT ----------------
    ("A", "sds_04.pdf", "supplier_name"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "DISTRIBUTOR:\nNational Refrigerants, Inc."}],
        notes="Цитата дословно на стр. 1. Дистрибьютор — валидный субъект для supplier_name по описанию поля.",
    ),
    ("A", "sds_15.pdf", "substance_or_mixture"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Mixtures\nComposition Comments:\nThe components are not hazardous or are below required disclosure limits."}],
        notes="Дословно на стр. 1: заголовок 3.2 Mixtures объявляет смесь по конвенции онтологии (_SECTION_HEADING).",
    ),
    ("A", "sds_09.pdf", "product_name"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Product name\nVISOCOLOR HE Nitrite, refill pack"}],
        notes="Дословно на стр. 1, секция 1.1.",
    ),
    ("A", "sds_08.pdf", "flash_point"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 9, "text": "Flash point:\n120 °C"}],
        notes="Дословно в SECTION 9 (стр. 9); значение продукта целиком, не ингредиента.",
    ),
    ("A", "sds_03.pdf", "flash_point"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 6, "text": "Flash Point:\nNon Flammable (>60 ºC)"}],
        notes="Дословно на стр. 6. Нюанс: значение — не температура, а классификационное утверждение; лексикон "
              "онтологии не считает 'Non Flammable' NOT_APPLICABLE-cue, поэтому PRESENT консистентен с правилами "
              "схемы и верен документу.",
    ),
    ("A", "sds_17.pdf", "substance_or_mixture"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": 'Mel-Rol is\ndefined by OSHA as an "article."'}],
        notes="Дословно на стр. 1; OSHA-определение article → ARTICLE по FORM_CUES.",
    ),
    ("A", "sds_19.pdf", "supplier_name"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Company:\nBuddy Rhodes Concrete Products"}],
        notes="Дословно, секция 1.3.",
    ),
    ("A", "sds_11.pdf", "product_name"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Product identifier:\nLD COVID-19 IgG Rapid Test (Art.-No. COV19_G_10_EN)"}],
        notes="Дословно, секция 1.1; value (имя без артикула) поддерживается цитатой.",
    ),
    # ---------------- group B: ONTOLOGY (all NOT_APPLICABLE) ----------------
    ("B", "sds_02.pdf", "chemical_formula"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 4, "text": "Substance or preparation: Preparation"}],
        notes="Premise дословно на стр. 4; 'Preparation' → MIXTURE по FORM_CUES; формула определена только для "
              "substance → N/A. Химически корректно: батарейный элемент — многокомпонентный продукт.",
    ),
    ("B", "sds_11.pdf", "molecular_weight"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 2, "text": "3.1. Substances\nNot applicable. Mixtures from substances listed below contain non-hazardous components like water or proteins."},
            {"page": 2, "text": "3.2. Mixtures\nComposition of the substances in the mixtures:"},
        ],
        notes="Оба premise дословно на стр. 2; 3.1 Substances = Not applicable → смесь по конвенции SDS; MW для "
              "смеси N/A — химически корректно (тест-набор: кассета + буфер).",
    ),
    ("B", "sds_14.pdf", "product_cas_number"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 1, "text": "Mixture of substances as listed below."},
            {"page": 1, "text": "Description of the mixture\nMixture of substances listed below with ingredients not classified as hazardous."},
        ],
        notes="Дословно на стр. 1; вакцина (смесь токсоидов/бактеринов) → CAS продукта N/A. CAS ингредиентов "
              "(22465-48-1, 54-64-8) правильно не использованы как CAS продукта.",
    ),
    ("B", "sds_17.pdf", "product_cas_number"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": 'Mel-Rol is\ndefined by OSHA as an "article."'}],
        notes="Дословно; продукт = article → CAS N/A. CAS 8052-42-4 (Petroleum Asphalt, ингредиент SECTION 3) "
              "правильно не взят как CAS продукта — product-vs-ingredient дисциплина соблюдена.",
    ),
    ("B", "sds_01.pdf", "chemical_formula"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 1, "text": "Chemical description: Mixture of substances"},
            {"page": 1, "text": "Substance:\nNon-applicable"},
        ],
        notes="Дословно; 3.1 Substance = Non-applicable → смесь; формула N/A.",
    ),
    ("B", "sds_15.pdf", "molecular_weight"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Mixtures\nComposition Comments:\nThe components are not hazardous or are below required disclosure limits."}],
        notes="Дословно; покрытие-смесь → MW N/A.",
    ),
    ("B", "sds_12.pdf", "chemical_formula"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 1, "text": "3.1 N/A"},
            {"page": 1, "text": "3.2 Description\nGarden fertiliser NPK 3 – 9 - 0"},
        ],
        notes="Дословно; 3.1 N/A → смесь (костная мука, 45–55% SiO2); формула N/A.",
    ),
    ("B", "sds_02.pdf", "product_cas_number"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 4, "text": "Substance or preparation: Preparation"}],
        notes="Дословно; preparation → смесь → CAS продукта N/A. CAS компонентов таблицы композиции правильно не "
              "использованы (product-vs-ingredient корректно).",
    ),
    # ---------------- group C: COMPOSITION_IMPLIED ----------------
    ("C", "sds_04.pdf", "substance_or_mixture"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 2, "text": "1,1,1,2-Tetrafluoroethane\n811-97-2\n100"},
            {"page": 2, "text": "There are no impurities or stabilizers that contribute to the classification of the material identified in Section 2"},
        ],
        notes="Дословно на стр. 2; единственный компонент при 100% + отсутствие примесей → SUBSTANCE. Химически "
              "корректно (R-134a — чистое вещество).",
    ),
    ("C", "sds_09.pdf", "substance_or_mixture"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 3, "text": "Substance name:\nsodium chloride\nCAS No.:\n7647-14-5"},
            {"page": 6, "text": "No data is available for the other parameters for the mixtures"},
        ],
        notes="Дословно; несколько веществ с концентрациями (NaCl 80–<100%, sulfanilamide, H3PO4) → смесь; стр. 6 "
              "прямо: 'for the mixtures'.",
    ),
    ("C", "sds_18.pdf", "substance_or_mixture"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 5, "text": "Ingredient\nC.A.S. No.\n% by Wt"},
            {"page": 5, "text": "35% of the mixture consists of ingredients of unknown acute oral toxicity."},
        ],
        notes="Дословно; многокомпонентная таблица + прямое 'the mixture' → смесь.",
    ),
    ("C", "sds_20.pdf", "substance_or_mixture"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 3, "text": "Petrochemical Stillage Residue KON-92 produced from residuals of\nbutyl alcohols, butyl aldehydes, 2-ethylhexanol, 2-ethylhexanoic acid,\nethylene-propylene copolymer and ethyl benzene [l]."}],
        notes="Дословно; продукт из остатков нескольких процессов → UVCB-смесь; согласуется с '3.1.2 Chemical "
              "formula: No.' в том же документе.",
    ),
    # ---------------- group D: missing-value states ----------------
    ("D", "sds_20.pdf", "molecular_weight"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 3, "text": "Petrochemical Stillage Residue KON-92 produced from residuals of\nbutyl alcohols, butyl aldehydes, 2-ethylhexanol, 2-ethylhexanoic acid,\nethylene-propylene copolymer and ethyl benzene [l]."}],
        notes="Premise дословно; смесь → MW N/A, химически корректно для нефтяного смолистого остатка.",
    ),
    ("D", "sds_07.pdf", "molecular_weight"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 1, "text": "Mixture identification:"},
            {"page": 1, "text": "Mixtures\nHazardous components within the meaning of GHS regulation and related classifications:"},
        ],
        notes="Оба premise дословно на стр. 1; тонер (смола 60–70%, Fe2O3, PE, силика) → MW N/A.",
    ),
    ("D", "sds_15.pdf", "chemical_formula"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Mixtures\nComposition Comments:\nThe components are not hazardous or are below required disclosure limits."}],
        notes="Дословно; смесь → формула N/A.",
    ),
    ("D", "sds_03.pdf", "product_cas_number"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Substance:\nNon-applicable"}],
        notes="Дословно; 3.1 Substance = Non-applicable → смесь (клей) → CAS продукта N/A.",
    ),
    ("D", "sds_07.pdf", "product_cas_number"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 1, "text": "Mixture identification:"},
            {"page": 1, "text": "Mixtures\nHazardous components within the meaning of GHS regulation and related classifications:"},
        ],
        notes="Дословно; тонер = смесь → CAS N/A; CAS 1309-37-1 (Fe2O3, ингредиент) правильно не использован.",
    ),
    ("D", "sds_13.pdf", "chemical_formula"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 2, "text": "Substance/mixture\n: Substance"}],
        notes="Форма SUBSTANCE объявлена (стр. 2) → поле применимо. Формулы нет нигде в документе (проверены все 11 "
              "страниц: в композиции только имя/CAS; MW 39.95 g/mole есть, формулы нет) → NOT_STATED корректен.",
    ),
    ("D", "sds_10.pdf", "molecular_weight"): dict(
        verdict="incorrect", error_type="wrong-state",
        quotes=[
            {"page": 1, "text": "Designation of ‘ARTICLES’"},
            {"page": 1, "text": "In accordance with 29 CFR 1910.1200(b)(6)(v), CIP Composites are exempted as an “Article”,\nand therefore, do not require an SDS be created or provided to end users."},
        ],
        notes="Документ ЯВНО объявляет продукт article (стр. 1, дважды: заголовок 'Designation of ARTICLES' и "
              "рекомендация OSHA). По онтологии form=ARTICLE → molecular_weight (defined_for_forms=(SUBSTANCE,)) "
              "должен быть NOT_APPLICABLE (ONTOLOGY), а не NOT_STATED. Прецедент: sds_17 с идентичной формулировкой "
              "('defined by OSHA as an article') аннотирован ARTICLE, и его product_cas_number/chemical_formula — "
              "N/A ONTOLOGY. Затронуты и соседние поля sds_10 (вне выборки): substance_or_mixture = NOT_STATED при "
              "явном объявлении ARTICLE; product_cas_number, chemical_formula — аналогично MW.",
    ),
    ("D", "sds_19.pdf", "product_cas_number"): dict(
        verdict="questionable", error_type=None,
        quotes=[
            {"page": 1, "text": "3.1 Substances\nNo ingredients are hazardous according to Regulation 2012 OSHA Hazard Communication\nStandard 29 CFR 1910.1200 criteria."},
            {"page": 1, "text": "General Use:\nConcrete Admixture"},
        ],
        notes="Объявления формы в документе нет (проверены все 7 страниц: только boilerplate 'substance or mixture' "
              "в заголовках секций и 'Not a hazardous substance or mixture' — hazard-утверждение, не объявление "
              "формы). NOT_STATED документ-верен. Но химически Water Reducer 310 — бетонная admixture (раствор "
              "полимеров) = смесь → CAS продукта должен быть N/A. ЭСКАЛАЦИЯ Farit: (a) оставить NOT_STATED "
              "(документ-верно, без химических допущений); (b) NOT_APPLICABLE (химическая интерпретация).",
    ),
    ("D", "sds_15.pdf", "flash_point"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 4, "text": "Flash Point:\nNo data available."}],
        notes="Дословно на стр. 4; value slot = 'No data available' → NO_DATA по лексикону; верен документу.",
    ),
    ("D", "sds_16.pdf", "flash_point"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 5, "text": "Flash Point\nNo information available"}],
        notes="Дословно на стр. 5; 'No information available' → NO_DATA-cue. Нюанс: продукт — твёрдое вещество "
              "(кварцевый песок); химически flash point для негорючего твёрдого скорее NOT_APPLICABLE, но документ "
              "сам пишет 'No information available' — gold верен тексту документа.",
    ),
    # ---------------- group E: alternative-evidence full-document view ----------------
    ("E", "sds_03.pdf", "substance_or_mixture"): dict(
        verdict="incorrect", error_type="missed-evidence",
        quotes=[
            {"page": 5, "text": "As the product is a mixture of several substances, the resistance of the glove material can not be calculated in advance with\ntotal reliability"},
            {"page": 1, "text": "Mixture:"},
        ],
        notes="Gold evidence сам корректен (оба фрагмента дословно, поддерживают MIXTURE), но evidence_set неполон: "
              "(1) стр. 5 — прямое объявление 'the product is a mixture of several substances' (секция 8, выбор "
              "перчаток) — субстантивное, вне evidence_set; (2) стр. 1 — заголовок 3.2 'Mixture:'. Система, "
              "цитирующая стр. 5, получит support=SATISFIED, но complete@k её не зачтёт → нечестный штраф.",
    ),
    ("E", "sds_09.pdf", "product_name"): dict(
        verdict="questionable", error_type=None,
        quotes=[{"page": 2, "text": "Safety Data Sheet\naccording to Regulations REACh 1907/2006/EC\nREF: 920163\nVISOCOLOR HE Nitrite, refill pack"}],
        notes="Колонтитул с именем продукта повторяется на КАЖДОЙ странице (проверены все 10): 'REF: 920163 / "
              "VISOCOLOR HE Nitrite, refill pack'. По критерию support (name-substring) любой колонтитул "
              "поддерживает значение → gold (только 1.1) неполон по букве критерия; но включение колонтитулов "
              "сделало бы complete@k тривиальным (валидна любая страница). ЭСКАЛАЦИЯ Farit — политика: (a) считать "
              "повторяющиеся колонтитулы evidence (расширить gold); (b) исключить boilerplate из критерия support; "
              "(c) принять каноническую политику gold (только 1.1) и задокументировать.",
    ),
    ("E", "sds_18.pdf", "substance_or_mixture"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 5, "text": "35% of the mixture consists of ingredients of unknown acute oral toxicity."}],
        notes="Альтернативного evidence вне gold нет: 'the mixture' — только стр. 5 (в gold); остальные упоминания — "
              "boilerplate заголовков секций. Наблюдение: classify_form_cue даёт ложный ARTICLE на стр. 1 "
              "('Article Information Sheet (AIS)') — это тип документа, не форма продукта; gold-free классификатор "
              "мог бы дать support-SATISFIED на неверную claim (не ошибка gold, а риск классификатора).",
    ),
    ("E", "sds_12.pdf", "product_name"): dict(
        verdict="questionable", error_type=None,
        quotes=[{"page": 2, "text": "Trade name:\nWestland Bone Meal"}],
        notes="Шапка 'Trade name: Westland Bone Meal' повторяется на всех 10 страницах; value 'Bone Meal' — "
              "подстрока. Gold — только 1.1 ('Product identifier Bone Meal'). Тот же политика-вопрос, что и "
              "sds_09/E: считать ли колонтитульные повторы evidence. Дополнительно: 'Trade name:' — помеченное "
              "объявление имени, субстантивнее простого колонтитула.",
    ),
    ("E", "sds_13.pdf", "supplier_name"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 1, "text": "Airgas USA, LLC and its affiliates"}],
        notes="Единственное вхождение значения в документе — gold-спан (стр. 1); 'Airgas Emergency Response Center' "
              "не содержит полного значения → не evidence. Альтернатив нет.",
    ),
    ("E", "sds_04.pdf", "product_cas_number"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 2, "text": "1,1,1,2-Tetrafluoroethane\n811-97-2\n100"}],
        notes="CAS встречается в документе один раз — в gold-спане (стр. 2). Product-vs-ingredient: продукт = "
              "единственное вещество при 100% (см. C/sds_04), поэтому CAS из таблицы композиции легитимно является "
              "CAS продукта.",
    ),
    ("E", "sds_01.pdf", "flash_point"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 5, "text": "Flash Point:\nNon Flammable (>60 ºC)"}],
        notes="Единственное упоминание flash point в документе — gold-спан (стр. 5); альтернатив нет. Нюанс значения "
              "как в A/sds_03.",
    ),
    ("E", "sds_19.pdf", "supplier_name"): dict(
        verdict="questionable", error_type=None,
        quotes=[{"page": 7, "text": "Since the use\nof this product is not within the control of Buddy Rhodes Concrete Products, it is the user's obligation to\ndetermine the suitability of the product for its intended"}],
        notes="Стр. 7 (секция 16, disclaimer): компания названа вне gold. По букве критерия support (substring) — "
              "валидное evidence → gold неполон; по сути — юридическая оговорка, не идентификация поставщика (1.3 в "
              "gold). ЭСКАЛАЦИЯ Farit: считать ли упоминания в disclaimer evidence.",
    ),
    ("E", "sds_05.pdf", "flash_point"): dict(
        verdict="correct", error_type=None,
        quotes=[
            {"page": 3, "text": "Flash Point [Method]: >225°C (437°F) [ASTM D-92]"},
            {"page": 7, "text": "Flash Point [Method]:\n>225°C (437°F) [ASTM D-92]"},
        ],
        notes="Оба вхождения значения в документе (стр. 3 и 7) включены в gold evidence_set — альтернатив нет, gold "
              "полон.",
    ),
    ("E", "sds_16.pdf", "molecular_weight"): dict(
        verdict="correct", error_type=None,
        quotes=[{"page": 5, "text": "Molecular Weight\n60.08"}],
        notes="Единственное вхождение 60.08 — gold-спан (стр. 5); на стр. 1 есть 'Molecular Formula O2 Si', но без "
              "веса. Альтернатив нет.",
    ),
}


def main() -> None:
    records = json.loads(AUDIT_JSON.read_text())
    assert len(records) == 40, f"expected 40 skeleton records, got {len(records)}"
    counts = Counter(r["group"] for r in records)
    assert counts == Counter({"A": 8, "B": 8, "C": 4, "D": 10, "E": 10}), counts

    keys = {(r["group"], r["document"], r["field"]) for r in records}
    assert keys == set(V), f"verdict table mismatch: missing={keys - set(V)}, extra={set(V) - keys}"

    for r in records:
        v = V[(r["group"], r["document"], r["field"])]
        assert r["verdict"] is None, "skeleton already filled? re-run the sampler first"
        r["verdict"] = v["verdict"]
        r["error_type"] = v["error_type"]
        r["quotes"] = v["quotes"]
        r["notes"] = v["notes"]

    AUDIT_JSON.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")

    # Verbatim check: every verdict quote must exist on its page (native layer).
    pages = {}
    for line in (REPO_ROOT / "farit" / "data" / "corpus" / "units_native.jsonl").read_text().splitlines():
        if line.strip():
            u = json.loads(line)
            pages.setdefault(u["document"], {})[u["page"]] = u["text"]
    for r in records:
        for q in r["quotes"]:
            assert q["text"] in pages[r["document"]][q["page"]], (
                f"quote not verbatim: {r['group']} {r['document']}/{r['field']} p{q['page']}"
            )

    tally = Counter(r["verdict"] for r in records)
    print(f"applied verdicts to {len(records)} records: " +
          ", ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    print("all verdict quotes verified verbatim against units_native.jsonl")


if __name__ == "__main__":
    main()
