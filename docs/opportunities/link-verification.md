# Link Extraction & Verification Policy

## Link Classification
- `NOTIFICATION`: Official PDF/HTML announcement notice.
- `APPLY`: Direct online application form / portal.
- `REGISTRATION`: User account registration link.
- `LOGIN`: Existing applicant portal login.
- `DOWNLOAD`: Syllabus, guidelines, or brochure download.
- `RESULT`: Exam or selection result notification.

## Verification Requirements
- Pre-checks HTTP status (< 400), open redirect safety, TLS certificate, and domain ownership.
- Official `.gov.in`, `.nic.in`, `.edu.in` or primary source domain preferred as canonical apply destination.
- Invalid or dead links (404/500/timeout) marked `is_valid = False` with warning banner on citizen UI.
