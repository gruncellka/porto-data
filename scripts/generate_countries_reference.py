#!/usr/bin/env python3
"""
Regenerate porto_data/global/jurisdictions.json from canonical membership sets.

Run from repo root:
  python scripts/generate_countries_reference.py

Assertions: EU member states are a subset of UN member states; 193 UN members.
"""

from __future__ import annotations

import json
from pathlib import Path

# UN member states (ISO 3166-1 alpha-2), 193 — update when membership changes
UN_MEMBER_STATES = frozenset(
    """\
AF AL DZ AD AO AG AR AM AU AT AZ BS BH BD BB BY BE BZ BJ BT BO BA BW BR BN BG BF BI \
CV KH CM CA CF TD CL CN CO KM CG CD CR CI HR CU CY CZ DK DJ DM DO EC EG SV GQ ER EE \
SZ ET FJ FI FR GA GM GE DE GH GR GD GT GN GW GY HT HN HU IS IN ID IR IQ IE IL IT JM \
JP JO KZ KE KI KP KR KW KG LA LV LB LS LR LY LI LT LU MG MW MY MV ML MT MH MR MU MX \
FM MD MC MN ME MA MZ MM NA NR NP NL NZ NI NE NG MK NO OM PK PW PA PG PY PE PH PL PT \
QA RO RU RW KN LC VC WS SM ST SA SN RS SC SL SG SK SI SB SO ZA SS ES LK SD SR SE CH \
SY TJ TZ TH TL TG TO TT TN TR TM TV UG UA AE GB US UY UZ VU VE VN YE ZM ZW""".split()
)

# EU member states (27)
EU_MEMBER_STATES = frozenset(
    "AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split()
)

def build_countries_document() -> dict[str, object]:
    """Return validated jurisdictions file payload (no I/O). Used by tests and main()."""
    assert len(UN_MEMBER_STATES) == 193, len(UN_MEMBER_STATES)
    assert EU_MEMBER_STATES <= UN_MEMBER_STATES, sorted(EU_MEMBER_STATES - UN_MEMBER_STATES)
    return {
        "$schema": "https://raw.githubusercontent.com/gruncellka/porto-data/refs/heads/main/porto_data/schemas/jurisdictions.schema.json",
        "file_type": "jurisdictions",
        "description": "Reference data for restriction resolver: EU and UN member-state lists (ISO 3166-1 alpha-2). Expands symbolic framework jurisdiction such as EU; not a full country catalog.",
        "unit": {
            "country_code": "ISO 3166-1 alpha-2",
            "region_code": "ISO 3166-2",
            "date": "ISO 8601",
        },
        "jurisdictions": {
            "eu": sorted(EU_MEMBER_STATES),
            "un": sorted(UN_MEMBER_STATES),
        },
    }


def main(out_path: Path | None = None) -> None:
    """Write jurisdictions.json. If out_path is None, uses repo porto_data/global default."""
    default = (
        Path(__file__).resolve().parent.parent
        / "porto_data"
        / "global"
        / "jurisdictions.json"
    )
    out = out_path if out_path is not None else default
    payload = build_countries_document()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
