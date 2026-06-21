"""Shared minimal JSON documents for tests (schema-shaped stubs)."""


def minimal_restrictions_document() -> dict:
    """Minimal restrictions.json for graph / tmp data dirs (matches restrictions.schema.json)."""
    return {
        "file_type": "restrictions",
        "unit": {"country_code": "ISO 3166-1 alpha-2", "date": "ISO 8601"},
        "sources": [],
        "disclaimer": "test",
        "destinations": [
            {
                "country_code": "DE",
                "restrictions": {
                    "EU": [
                        {
                            "id": "_fixture_placeholder",
                            "reason": "test",
                            "notes": "test",
                            "entity_type": "country",
                            "status": "operational",
                            "reference": None,
                            "effective_from": None,
                            "effective_to": None,
                        }
                    ],
                },
            }
        ],
    }
