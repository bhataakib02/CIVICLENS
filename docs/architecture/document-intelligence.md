# CivicLens — Document Intelligence Architecture

This document specifies the document processing pipeline from upload to fact verification.

---

## Document Pipeline Architecture

```mermaid
graph TD
    Upload[1. Upload Init] -->|Presigned URL| S3[Private S3 Bucket]
    Complete[2. Complete Upload] -->|Magic Bytes Header Check| Validate[Validation Passed]
    Validate -->|Enqueue Job| Worker[Celery Worker Cluster]
    Worker -->|OCR / PDF Extract| Parsing[Text & Layout Parsing]
    Parsing --> Extract[Entity & Fact Extraction]
    Extract --> Conf[Confidence Scoring]
    Conf --> Prov[Provenance Binding]
    Prov --> Evid[Application Evidence & Verified Facts]
```

---

## Machine Extracted vs. Human Verified Data

| Attribute | Machine Extracted Data | Human Verified Data |
|---|---|---|
| **Origin** | Automated Tesseract OCR / PDF Text Parser | CSC Operator / Admin Manual Review |
| **Trust Level** | Intermediate (requires confidence threshold >= 0.85) | Authoritative (manually confirmed) |
| **Database Flag** | `is_verified = False` | `is_verified = True`, `verified_by = operator_id` |
| **Eligibility Fact** | Used as candidate evidence for progressive profiling | Unlocks authoritative eligibility checks |
