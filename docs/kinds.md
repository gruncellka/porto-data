# Kind mapping tables

Generated from live bundle data. Normative enum: `porto_data/schemas/kinds.schema.json`. Policy: [id.md](id.md).

Identity is always concrete **`id`**. Graph, prices, and rules use **`id`**. `kind` on services and features is cross-provider grouping only. Products have no kind.

## deutschepost

### products

| `id` |
|------|
| `grossbrief` |
| `kompaktbrief` |
| `maxibrief` |
| `maxibrief_ausland` |
| `standardbrief` |

### services

| `id` | services `kind` |
|------|----------------|
| `einschreiben` | `registered` |
| `einschreiben_einwurf` | `registered` |
| `einschreiben_rueckschein` | `registered_return_receipt` |
| `zusatzversicherung` | `insurance` |

### features

| `id` | features `kind` |
|------|----------------|
| `einliefernachweis` | `acceptance_proof` |
| `rueckschein` | `return_receipt` |
| `sendungsnummer` | `tracking` |
| `unterschrift_empfanger` | `recipient_signature` |
| `zustellnachweis` | `delivery_proof` |

## ukrposhta

### products

| `id` |
|------|
| `dokument` |
| `lyst_standartnyi` |

### services

| `id` | services `kind` |
|------|----------------|
| `elektronne_povidomlennia_vruchennia` | `return_receipt` |
| `mizhnarodne_zareiestrovane` | `registered` |
| `paperove_povidomlennia_vruchennia` | `return_receipt` |

### features

| `id` | features `kind` |
|------|----------------|
| `elektronne_povidomlennia_vruchennia` | `return_receipt` |
| `nomer_vidstezhennia` | `tracking` |
| `osobyste_vruchennia` | `recipient_signature` |
| `paperove_povidomlennia_vruchennia` | `return_receipt` |

## laposte

### products

| `id` |
|------|
| `lettre_recommandee_internationale_r_un` |
| `lettre_recommandee_r_deux` |
| `lettre_recommandee_r_trois` |
| `lettre_recommandee_r_un` |
| `lettre_services_plus` |
| `lettre_verte` |
| `lettre_verte_suivie` |

### services

| `id` | services `kind` |
|------|----------------|
| `avis_de_reception_international` | `return_receipt` |
| `avis_de_reception_national` | `return_receipt` |
| `option_suivi` | `tracking` |

### features

| `id` | features `kind` |
|------|----------------|
| `avis_reception` | `return_receipt` |
| `numero_suivi` | `tracking` |
| `preuve_depot` | `acceptance_proof` |
| `preuve_livraison` | `delivery_proof` |
| `signature_destinataire` | `recipient_signature` |

## swisspost

### products

| `id` |
|------|
| `a_post_grossbrief` |
| `a_post_standardbrief` |
| `b_post_grossbrief` |
| `b_post_standardbrief` |
| `international_grossbrief` |
| `international_maxibrief` |
| `international_standardbrief` |

### services

| `id` | services `kind` |
|------|----------------|
| `a_mail_plus` | `tracking` |
| `zuschlag_dicke` | `thickness` |

### features

| `id` | features `kind` |
|------|----------------|
| `brief_dicke_band` | `thickness` |
| `sendungsnummer` | `tracking` |
