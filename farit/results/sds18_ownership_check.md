# sds_18 — product/component ownership audit (K3)

**Date:** 2026-10-23 · **Scope:** targeted annotation audit requested by the supervisor
(steering note 2026-10-22, item 2: *"product/component ownership (sds_18)"*).
Read-only with respect to `data/`; automated evidence-resolution in
`farit/src/analysis/sds18_ownership_check.py`, raw output `farit/results/sds18_ownership_check.json`.

## Document structure (verified against the text layer)

`sds_18.pdf` is a **kit / multipart product**, not a single sheet. `p1–2` is the kit cover page;
`p3–14` is the complete SDS of component **Part A** (Document Group `22-1760-2`, "3M™ Plastic Repair,
Semi-Rigid PNs 04240 (Part A)"); `p15–24` is the complete SDS of component **Part B**
(Document Group `22-1785-9`). The cover says so verbatim:

> "This product is a kit or a multipart product which consists of multiple, independently packaged
> components. A Safety Data Sheet (SDS), Article Information Sheet (AIS), or Article Information
> Letter (AIL) for each of these components is included. […] The document numbers for components of
> this product are: 22-1785-9, 22-1760-2"  *(p1, verbatim)*

There is **no product-level CAS / formula / molecular weight** anywhere in the file: the only
`CAS` tokens are composition/regulatory rows (p5, p7, p10, p13), all ingredient-level.

## Evidence resolution (mechanical)

Every gold evidence/premise span resolves against the native layer at **score 100** (exact modulo
whitespace); OCR anchors present for all. All 9 ingredient rows resolve on p5. **0 broken refs.**

## Verdicts

| # | Field / claim | Owner level | Verdict | Note |
|---|---|---|---|---|
| 1 | `product_name` = "3M™ Semi-Rigid Plastic Repair PN 04240" | product (kit) | **correct** | value is the cover (kit) identifier, p1; `accepted_values` add Part A/B names |
| 2 | `supplier_name` = "3M" | product | **correct** | `MANUFACTURER: 3M` on p1 and p3 |
| 3 | `flash_point` = ">=290 ºF …" | product | **correct** | both parts report the same value; p8 (Part A) + p19 (Part B) — the headline gold v0→v1 correction |
| 4 | `product_cas_number` / `chemical_formula` / `molecular_weight` = NOT_APPLICABLE | product | **correct (historical bug fixed)** | the old ground truth recorded the **ingredient** CAS `101-68-8` as the product CAS; current gold does **not** — `101-68-8` appears only in ingredient/regulatory contexts (p5, p7, p13) |
| 5 | `substance_or_mixture` = MIXTURE (COMPOSITION_IMPLIED) | **product vs component — questionable** | **escalate** | premise is **Part A's** composition table (p5, component-level); the product's own form declaration sits on the cover (p1 "kit or a multipart product … multiple, independently packaged components") |
| 6 | `product_cas/formula/MW` premise = "Ingredient C.A.S. No. % by Wt" (p5) | **component evidence for a product-level claim — questionable** | **escalate** | same ownership question as #5: a component's composition header is used to justify a product-level N/A |
| 7 | `ingredients` (9 rows, Part A only) | component | **correct scope, incomplete coverage** | Part B's own composition table (p16, 4 rows) is deliberately not annotated (documented in the gold note) — product-as-kit composition is only Part A |
| 8 | alternative evidence | — | **gap** | `product_name` evidence omits p15 (Part B 1.1 identifier, already in `accepted_values`); `supplier_name` omits p15 (`MANUFACTURER: 3M`); `flash_point` correctly keeps both p8+p19 |

## Questions for Farit

1. **Form of a multipart kit.** The ontology has no "KIT/MULTIPART" form, so gold maps the kit to
   `MIXTURE` and derives N/A identifiers. Is `MIXTURE` the intended form for a *kit*, or should the
   form be `UNDETERMINED` (product is not itself a substance/mixture but a bundle of components)?
2. **Premise ownership.** Should the `substance_or_mixture` / identifier premises be the **cover-page
   kit declaration (p1, product-level)** rather than Part A's composition header (p5,
   component-level)? If yes → gold fix (the p5 premise also feeds the three ONTOLOGY fields).
3. **Part B coverage.** Keep the "annotate one component" policy (Part A only) for `ingredients`, and
   the p15 omission for `product_name`/`supplier_name` — or extend gold to both components?

## Bottom line

The one *confirmed* historical ownership error (ingredient CAS as product CAS) is **already fixed**
in the current gold — the supervisor's specific worry does not reproduce. What the audit *does* surface
is a genuine **evidence-ownership** nuance unique to this kit document: product-level form claims rest
on a component's composition table, while a product-level kit declaration exists on the cover. That is
a policy call → escalated to Farit (see `farit/tasks/TASK-016-sds18-ownership-audit.md`). No gold
change has been made; all numbers are read from the untouched corpus.