# Porto ID / Native ID mapping (letters & services)

**See also:** [Canonical `porto_id` policy](docs/id.md) · [Normalization plan](porto_id_normalization_plan.md)

Quick cross-check of product/service ids across providers. Columns:
- `id`: provider JSON `id` (transliterated label we store)
- `native_id`: carrier’s own identifier (when provided)
- `porto_id`: unified Porto capability id

## Deutsche Post

### Products
| id | native_id | porto_id |
| --- | --- | --- |
| standardbrief | 10001 | small |
| kompaktbrief | 10002 | medium |
| grossbrief | 10003 | large |
| maxibrief | 10004 | extra_large |
| maxibrief_international_heavy | 10005 | extra_large |

### Services
| id | native_id | porto_id |
| --- | --- | --- |
| einschreiben | — | registered |
| einschreiben_einwurf | — | registered |
| einschreiben_rueckschein | — | registered_return_receipt |
| zusatzversicherung | — | insurance |

### Features
| id | native_id | porto_id |
| --- | --- | --- |
| sendungsnummer | — | tracking_number |
| einliefernachweis | — | proof_of_mailing |
| unterschrift_empfanger | — | recipient_signature |
| rueckschein | — | return_receipt |
| zustellnachweis | — | proof_of_delivery |

## La Poste

### Products
| id | native_id | porto_id |
| --- | --- | --- |
| lettre_verte | — | small |
| lettre_verte_suivie | — | small |
| lettre_services_plus | — | small |
| lettre_recommandee_r_un | — | registered |
| lettre_recommandee_r_deux | — | registered |
| lettre_recommandee_r_trois | — | registered |
| lettre_recommandee_inter_r_un | — | registered |
| lettre_recommandee_inter_r_deux | — | registered |

### Services
| id | native_id | porto_id |
| --- | --- | --- |
| suivi_option | — | tracking |
| avis_de_reception_national | — | return_receipt |
| avis_de_reception_international | — | return_receipt |

### Features
| id | native_id | porto_id |
| --- | --- | --- |
| numero_suivi | — | tracking_number |
| preuve_depot | — | proof_of_mailing |
| signature_destinataire | — | recipient_signature |
| avis_reception | — | return_receipt |
| preuve_livraison | — | proof_of_delivery |

## Swiss Post

### Products
| id | native_id | porto_id |
| --- | --- | --- |
| a_post_standardbrief | — | small |
| a_post_grossbrief | — | large |
| b_post_standardbrief | — | small |
| b_post_grossbrief | — | large |
| international_standardbrief | — | small |
| international_grossbrief | — | large |
| international_maxibrief | — | extra_large |

### Services
| id | native_id | porto_id |
| --- | --- | --- |
| a_mail_plus | — | tracking |
| brief_dicke_zuschlag | — | thickness (rule-attached) |

### Features
| id | native_id | porto_id |
| --- | --- | --- |
| sendungsnummer | — | tracking_number |

## Ukrposhta

### Products
| id | native_id | porto_id |
| --- | --- | --- |
| letter_standard | letter | small |
| ukrposhta_document | document | large |

### Services
| id | native_id | porto_id |
| --- | --- | --- |
| return_receipt_paper | — | return_receipt |
| return_receipt_electronic | — | return_receipt |
| recommended_intl | — | registered |

### Features
| id | native_id | porto_id |
| --- | --- | --- |
| recipient_signature | — | recipient_signature |
| return_receipt_paper | — | return_receipt |
| return_receipt_electronic | — | return_receipt |
