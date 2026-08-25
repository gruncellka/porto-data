"""Validate service/feature kind vocabulary and concrete-id cross-file references."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from scripts.data_files import (
    GRAPH_FILE,
    PRODUCT_PRICES_FILE,
    PRODUCTS_FILE,
    PROVIDERS_DIR,
    SERVICE_PRICES_FILE,
    SERVICES_FILE,
    get_project_root,
    list_provider_ids,
)
from scripts.utils import load_json

KINDS_SCHEMA = "schemas/kinds.schema.json"
MAPPING_DOC = "docs/kinds.md"

REQUIRED_PROVIDER_SCHEMAS: tuple[str, ...] = (
    "schemas/marks.schema.json",
    "schemas/products.schema.json",
    "schemas/features.schema.json",
    "schemas/services.schema.json",
    "schemas/product_prices.schema.json",
    "schemas/service_prices.schema.json",
    "schemas/zones.schema.json",
    "schemas/weights.schema.json",
    "schemas/limits.schema.json",
    "schemas/graph.schema.json",
)


def _load_kind_enums(root: Path) -> dict[str, set[str]]:
    schema_path = root / KINDS_SCHEMA
    with open(schema_path, encoding="utf-8") as f:
        doc = json.load(f)
    defs = doc.get("definitions", {})
    out: dict[str, set[str]] = {}
    for key in ("service_kind", "feature_kind"):
        enum = defs.get(key, {}).get("enum", [])
        out[key] = set(enum)
    return out


def _service_ids(services: dict[str, Any] | None) -> set[str]:
    if not services:
        return set()
    return {
        str(s["id"]) for s in services.get("services", []) if isinstance(s, dict) and s.get("id")
    }


def _product_ids(products: dict[str, Any] | None) -> set[str]:
    if not products:
        return set()
    return {
        str(p["id"]) for p in products.get("products", []) if isinstance(p, dict) and p.get("id")
    }


def _kinds_by_entity(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind = row.get("kind")
        nid = row.get("id")
        if kind and nid:
            grouped[str(kind)].append(str(nid))
    return dict(grouped)


def _render_mapping_doc(providers_data: dict[str, dict[str, list[tuple[str, str]]]]) -> str:
    lines = [
        "# Kind mapping tables",
        "",
        "Generated from live bundle data. Normative enum: "
        "`porto_data/schemas/kinds.schema.json`. Policy: [id.md](id.md).",
        "",
        "Identity is always concrete **`id`**. Graph, prices, and rules use **`id`**. "
        "`kind` on services and features is cross-provider grouping only. Products have no kind.",
        "",
    ]
    for provider in list_provider_ids():
        if provider not in providers_data:
            continue
        blocks = providers_data[provider]
        lines.append(f"## {provider}")
        lines.append("")
        products = blocks.get("products") or []
        if products:
            lines.append("### products")
            lines.append("")
            lines.append("| `id` |")
            lines.append("|------|")
            for native_id, _ in sorted(products):
                lines.append(f"| `{native_id}` |")
            lines.append("")
        for entity in ("services", "features"):
            rows = blocks.get(entity) or []
            if not rows:
                continue
            lines.append(f"### {entity}")
            lines.append("")
            lines.append(f"| `id` | {entity} `kind` |")
            lines.append("|------|----------------|")
            for native_id, kind in sorted(rows):
                lines.append(f"| `{native_id}` | `{kind}` |")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def validate_kinds(*, write_mapping_doc: bool = True) -> int:
    """Validate kind usage and concrete-id refs across all providers."""
    root = get_project_root()
    repo_root = root.parent if (root.parent / "pyproject.toml").exists() else root
    mapping_path = repo_root / MAPPING_DOC

    print("Validating service/feature kinds and concrete-id references...\n")

    enums = _load_kind_enums(root)
    errors: list[str] = []
    warnings: list[str] = []
    doc_data: dict[str, dict[str, list[tuple[str, str]]]] = {}

    for pid in list_provider_ids():
        prov_dir = root / PROVIDERS_DIR / pid
        doc_data[pid] = {"products": [], "services": [], "features": []}

        try:
            products = load_json(prov_dir / PRODUCTS_FILE)
            services = load_json(prov_dir / SERVICES_FILE)
            features = load_json(prov_dir / "features.json")
            graph = load_json(prov_dir / GRAPH_FILE)
            prices_dir = prov_dir / "prices"
            product_prices_doc = load_json(prices_dir / PRODUCT_PRICES_FILE)
            service_prices_doc = load_json(prices_dir / SERVICE_PRICES_FILE)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            errors.append(f"{pid}: failed to load catalog files ({e})")
            continue

        product_id_set = _product_ids(products)
        service_id_set = _service_ids(services)

        for p in products.get("products", []):
            if not isinstance(p, dict):
                continue
            native_id = p.get("id")
            if isinstance(native_id, str) and native_id.endswith("_intl"):
                errors.append(
                    f"{pid}: product id '{native_id}' uses deprecated _intl suffix; "
                    f"use a local-language slug"
                )
            if p.get("porto_id") is not None:
                errors.append(
                    f"{pid}: product '{native_id}' must not have porto_id "
                    "(products have no size-bucket or kind field)"
                )
            if p.get("kind") is not None:
                errors.append(
                    f"{pid}: product '{native_id}' must not have kind "
                    "(no cross-provider product taxonomy)"
                )
            if native_id:
                doc_data[pid]["products"].append((str(native_id), ""))

        for s in services.get("services", []):
            if not isinstance(s, dict):
                continue
            native_id = s.get("id")
            kind = s.get("kind")
            if isinstance(native_id, str) and native_id.endswith("_intl"):
                errors.append(
                    f"{pid}: service id '{native_id}' uses deprecated _intl suffix; "
                    f"use a local-language slug"
                )
            if s.get("porto_id") is not None:
                errors.append(f"{pid}: service '{native_id}' must use kind, not porto_id")
            if native_id and kind:
                doc_data[pid]["services"].append((str(native_id), str(kind)))
            if kind and kind not in enums["service_kind"]:
                errors.append(
                    f"{pid}: service '{native_id}' kind '{kind}' not in canonical service_kind enum"
                )
            elif not kind:
                errors.append(f"{pid}: service '{native_id}' missing kind")

        feature_ids: set[str] = set()
        for f in features.get("features", []):
            if not isinstance(f, dict):
                continue
            native_id = f.get("id")
            kind = f.get("kind")
            if f.get("porto_id") is not None:
                errors.append(f"{pid}: feature '{native_id}' must use kind, not porto_id")
            if native_id and kind:
                doc_data[pid]["features"].append((str(native_id), str(kind)))
            if isinstance(native_id, str):
                feature_ids.add(native_id)
            if kind and kind not in enums["feature_kind"]:
                errors.append(
                    f"{pid}: feature '{native_id}' kind '{kind}' not in canonical feature_kind enum"
                )
            elif not kind:
                errors.append(f"{pid}: feature '{native_id}' missing kind")

        for s in services.get("services", []):
            if not isinstance(s, dict):
                continue
            for ref in s.get("features") or []:
                if not isinstance(ref, str):
                    continue
                if ref in feature_ids:
                    continue
                errors.append(
                    f"{pid}: service '{s.get('id')}' features[] {ref!r} "
                    f"must match a features.json id (not kind)"
                )

        svc_dupes = _kinds_by_entity(services.get("services", []))
        for kind, native_ids in sorted(svc_dupes.items()):
            if len(native_ids) > 1:
                warnings.append(
                    f"{pid}: service kind '{kind}' maps to ids {native_ids} "
                    "(expected for operator variants)"
                )

        for product_id in product_prices_doc.get("product_prices", []):
            if not isinstance(product_id, dict):
                continue
            ref = product_id.get("product_id")
            if not ref:
                continue
            ref_str = str(ref)
            if ref_str not in product_id_set:
                errors.append(
                    f"{pid}: product_prices product_id '{ref_str}' not found in {PRODUCTS_FILE}"
                )

        for sp in service_prices_doc.get("service_prices", []):
            if not isinstance(sp, dict):
                continue
            ref = sp.get("service_id")
            if not ref:
                continue
            ref_str = str(ref)
            if ref_str not in service_id_set:
                hint = ""
                if ref_str in enums["service_kind"]:
                    hint = " (kind is not a service id; use concrete id)"
                errors.append(
                    f"{pid}: service_prices service_id '{ref_str}' not found in {SERVICES_FILE}{hint}"
                )

        available = graph.get("services", [])
        for sid in available:
            sid_str = str(sid)
            if sid_str not in service_id_set:
                hint = ""
                if sid_str in enums["service_kind"]:
                    hint = " (kind is not a service id; use concrete id)"
                errors.append(
                    f"{pid}: graph services '{sid_str}' not found in {SERVICES_FILE}{hint}"
                )

    for w in warnings:
        print(f"⚠️  WARNING: {w}")
    if warnings:
        print()

    for err in errors:
        print(f"❌ ERROR: {err}")
    if errors:
        print()
        print("❌ kind validation failed.")
        return 1

    if write_mapping_doc:
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        content = _render_mapping_doc(doc_data)
        rel = mapping_path.relative_to(repo_root)
        if not mapping_path.exists() or mapping_path.read_text(encoding="utf-8") != content:
            mapping_path.write_text(content, encoding="utf-8")
            print(f"❌ ERROR: {rel} was out of date and has been regenerated.")
            print("   Commit the updated file (or run 'porto validate --type kinds' and review).")
            print()
            print("❌ kind validation failed (mapping doc drift).")
            return 1
        print(f"✓ {rel} is current")

    print(f"✅ kind validation OK ({len(list_provider_ids())} providers).\n")
    return 0
