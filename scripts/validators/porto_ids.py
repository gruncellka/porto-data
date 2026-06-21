"""Validate porto_id vocabulary and native-id cross-file references."""

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

PORTO_IDS_SCHEMA = "schemas/porto_ids.schema.json"
MAPPING_DOC = "docs/porto_id.md"
RESOLUTION_DOC = "docs/resolution.md"

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


def _load_porto_id_enums(root: Path) -> dict[str, set[str]]:
    """Load canonical porto_id enums from porto_ids.schema.json."""
    schema_path = root / PORTO_IDS_SCHEMA
    with open(schema_path, encoding="utf-8") as f:
        doc = json.load(f)
    defs = doc.get("definitions", {})
    out: dict[str, set[str]] = {}
    for key in ("product_porto_id", "service_porto_id", "feature_porto_id"):
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


def _porto_ids_by_entity(
    rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Map porto_id -> list of native ids for duplicate detection."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = row.get("porto_id")
        nid = row.get("id")
        if pid and nid:
            grouped[str(pid)].append(str(nid))
    return dict(grouped)


def _render_mapping_doc(providers_data: dict[str, dict[str, list[tuple[str, str]]]]) -> str:
    """Build porto_id.md from collected provider rows."""
    lines = [
        "# Porto ID mapping tables",
        "",
        "Generated from live bundle data. Normative enum: "
        "`porto_data/schemas/porto_ids.schema.json`. Policy: [id.md](id.md).",
        "",
        "Cross-file refs (graph, prices, rules) use **native `id`**. "
        "SDK input uses **`porto_id`** — see [resolution.md](resolution.md) when "
        "multiple native rows share one `porto_id`.",
        "",
    ]
    for provider in list_provider_ids():
        if provider not in providers_data:
            continue
        blocks = providers_data[provider]
        lines.append(f"## {provider}")
        lines.append("")
        for entity, rows in blocks.items():
            if not rows:
                continue
            lines.append(f"### {entity}")
            lines.append("")
            lines.append("| native `id` | `porto_id` |")
            lines.append("|-------------|------------|")
            for native_id, porto_id in sorted(rows):
                lines.append(f"| `{native_id}` | `{porto_id}` |")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def validate_porto_ids(*, write_mapping_doc: bool = True) -> int:
    """Validate porto_id usage and native-id refs across all providers."""
    root = get_project_root()
    repo_root = root.parent if (root.parent / "pyproject.toml").exists() else root
    mapping_path = repo_root / MAPPING_DOC

    print("Validating porto_id vocabulary and native-id references...\n")

    enums = _load_porto_id_enums(root)
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
            porto_id = p.get("porto_id")
            if native_id and porto_id:
                doc_data[pid]["products"].append((str(native_id), str(porto_id)))
            if porto_id and porto_id not in enums["product_porto_id"]:
                errors.append(
                    f"{pid}: product '{native_id}' porto_id '{porto_id}' "
                    f"not in canonical product enum"
                )

        for s in services.get("services", []):
            if not isinstance(s, dict):
                continue
            native_id = s.get("id")
            porto_id = s.get("porto_id")
            if native_id and porto_id:
                doc_data[pid]["services"].append((str(native_id), str(porto_id)))
            if porto_id and porto_id not in enums["service_porto_id"]:
                errors.append(
                    f"{pid}: service '{native_id}' porto_id '{porto_id}' "
                    f"not in canonical service enum"
                )

        for f in features.get("features", []):
            if not isinstance(f, dict):
                continue
            native_id = f.get("id")
            porto_id = f.get("porto_id")
            if native_id and porto_id:
                doc_data[pid]["features"].append((str(native_id), str(porto_id)))
            if porto_id and porto_id not in enums["feature_porto_id"]:
                errors.append(
                    f"{pid}: feature '{native_id}' porto_id '{porto_id}' "
                    f"not in canonical feature enum"
                )

        prod_dupes = _porto_ids_by_entity(products.get("products", []))
        for porto_id, native_ids in sorted(prod_dupes.items()):
            if len(native_ids) > 1:
                warnings.append(
                    f"{pid}: product porto_id '{porto_id}' maps to multiple native ids "
                    f"{native_ids} — disambiguate via zone/weight/services "
                    f"(see {RESOLUTION_DOC})"
                )

        svc_dupes = _porto_ids_by_entity(services.get("services", []))
        for porto_id, native_ids in sorted(svc_dupes.items()):
            if len(native_ids) > 1:
                warnings.append(
                    f"{pid}: service porto_id '{porto_id}' maps to native ids {native_ids} "
                    f"(expected for operator variants)"
                )

        for product_id in product_prices_doc.get("product_prices", []):
            if not isinstance(product_id, dict):
                continue
            ref = product_id.get("product_id")
            if not ref:
                continue
            ref_str = str(ref)
            if ref_str not in product_id_set:
                if ref_str in enums["product_porto_id"]:
                    errors.append(
                        f"{pid}: product_prices product_id '{ref_str}' is a porto_id; "
                        f"use native product id from {PRODUCTS_FILE}"
                    )
                else:
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
                if ref_str in enums["service_porto_id"]:
                    errors.append(
                        f"{pid}: service_prices service_id '{ref_str}' is a porto_id; "
                        f"use native service id from {SERVICES_FILE}"
                    )
                else:
                    errors.append(
                        f"{pid}: service_prices service_id '{ref_str}' not found in {SERVICES_FILE}"
                    )

        available = graph.get("services", [])
        for sid in available:
            sid_str = str(sid)
            if sid_str not in service_id_set:
                if sid_str in enums["service_porto_id"]:
                    errors.append(
                        f"{pid}: services '{sid_str}' is a porto_id; "
                        f"use native service id from {SERVICES_FILE} "
                        f"({GRAPH_FILE} -> services)"
                    )
                else:
                    errors.append(f"{pid}: services '{sid_str}' not found in {SERVICES_FILE}")

    for w in warnings:
        print(f"⚠️  WARNING: {w}")
    if warnings:
        print()

    for err in errors:
        print(f"❌ ERROR: {err}")
    if errors:
        print()
        print("❌ porto_id validation failed.")
        return 1

    if write_mapping_doc:
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        content = _render_mapping_doc(doc_data)
        if not mapping_path.exists() or mapping_path.read_text(encoding="utf-8") != content:
            mapping_path.write_text(content, encoding="utf-8")
            print(f"✓ Updated {mapping_path.relative_to(repo_root)}")
        else:
            print(f"✓ {mapping_path.relative_to(repo_root)} is current")

    print(f"✅ porto_id validation OK ({len(list_provider_ids())} providers).\n")
    return 0
