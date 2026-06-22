# Porto ID mapping tables

Generated from live bundle data. Normative enum: `porto_data/schemas/porto_ids.schema.json`. Policy: [id.md](id.md).

Cross-file refs (graph, prices, rules) use **native `id`**. SDK input uses **`porto_id`** — see [resolution.md](resolution.md) when multiple native rows share one `porto_id`.

## deutschepost

### products

| native `id` | `porto_id` |
|-------------|------------|
| `grossbrief` | `large` |
| `kompaktbrief` | `medium` |
| `maxibrief` | `extra_large` |
| `maxibrief_international_heavy` | `extra_large` |
| `standardbrief` | `small` |

### services

| native `id` | `porto_id` |
|-------------|------------|
| `einschreiben` | `registered` |
| `einschreiben_einwurf` | `registered` |
| `einschreiben_rueckschein` | `registered_return_receipt` |
| `zusatzversicherung` | `insurance` |

### features

| native `id` | `porto_id` |
|-------------|------------|
| `einliefernachweis` | `proof_of_mailing` |
| `rueckschein` | `return_receipt` |
| `sendungsnummer` | `tracking_number` |
| `unterschrift_empfanger` | `recipient_signature` |
| `zustellnachweis` | `proof_of_delivery` |

## ukrposhta

### products

| native `id` | `porto_id` |
|-------------|------------|
| `dokument` | `large` |
| `lyst_standartnyi` | `small` |

### services

| native `id` | `porto_id` |
|-------------|------------|
| `recommended_international` | `registered` |
| `return_receipt_electronic` | `return_receipt` |
| `return_receipt_paper` | `return_receipt` |

### features

| native `id` | `porto_id` |
|-------------|------------|
| `recipient_signature` | `recipient_signature` |
| `return_receipt_electronic` | `return_receipt` |
| `return_receipt_paper` | `return_receipt` |

## laposte

### products

| native `id` | `porto_id` |
|-------------|------------|
| `lettre_recommandee_inter_r_deux` | `registered` |
| `lettre_recommandee_inter_r_un` | `registered` |
| `lettre_recommandee_r_deux` | `registered` |
| `lettre_recommandee_r_trois` | `registered` |
| `lettre_recommandee_r_un` | `registered` |
| `lettre_services_plus` | `small` |
| `lettre_verte` | `small` |
| `lettre_verte_suivie` | `small` |

### services

| native `id` | `porto_id` |
|-------------|------------|
| `avis_de_reception_international` | `return_receipt` |
| `avis_de_reception_national` | `return_receipt` |
| `suivi_option` | `tracking` |

### features

| native `id` | `porto_id` |
|-------------|------------|
| `avis_reception` | `return_receipt` |
| `numero_suivi` | `tracking_number` |
| `preuve_depot` | `proof_of_mailing` |
| `preuve_livraison` | `proof_of_delivery` |
| `signature_destinataire` | `recipient_signature` |

## swisspost

### products

| native `id` | `porto_id` |
|-------------|------------|
| `a_post_grossbrief` | `large` |
| `a_post_standardbrief` | `small` |
| `b_post_grossbrief` | `large` |
| `b_post_standardbrief` | `small` |
| `international_grossbrief` | `large` |
| `international_maxibrief` | `extra_large` |
| `international_standardbrief` | `small` |

### services

| native `id` | `porto_id` |
|-------------|------------|
| `a_mail_plus` | `tracking` |
| `brief_dicke_zuschlag` | `thickness` |

### features

| native `id` | `porto_id` |
|-------------|------------|
| `brief_dicke_band` | `thickness_surcharge` |
| `sendungsnummer` | `tracking_number` |
