"""Submission precondition validators (prompt §16, §43).

Pure checks that raise the CivicLens structured errors. Used by the workflow
before a submission transition. Never leak DB internals.
"""
from __future__ import annotations

from app.core.exceptions import AppError
from app.models.enums import ApplicationStatus
from app.modules.applications.requirements import Checklist

# Eligibility decisions permitted to proceed to submission (product policy §9).
SUBMITTABLE_DECISIONS = {"eligible", "likely_eligible"}


class NotEligibleError(AppError):
    status_code = 409
    code = "NOT_ELIGIBLE"
    message = "The application is not eligible for submission."


class DocumentsIncompleteError(AppError):
    status_code = 422
    code = "DOCUMENTS_INCOMPLETE"
    message = "Required documents are missing or not yet verified."

    def __init__(self, message: str | None = None, *, field_errors=None):
        super().__init__(message)
        self.field_errors = field_errors or []


class ApplicationAlreadySubmittedError(AppError):
    status_code = 409
    code = "APPLICATION_ALREADY_SUBMITTED"
    message = "This application has already been submitted."


class SubmissionFailedAppError(AppError):
    status_code = 502
    code = "SUBMISSION_FAILED"
    message = "The government submission provider failed. Please retry."


def validate_eligibility(snapshot: dict | None) -> None:
    decision = (snapshot or {}).get("decision")
    if decision not in SUBMITTABLE_DECISIONS:
        raise NotEligibleError(
            f"Eligibility decision '{decision}' does not permit submission."
        )


def validate_documents(checklist: Checklist) -> None:
    if not checklist.all_required_satisfied:
        unsatisfied = [
            {"field": i.document_type, "message": f"Required document is {i.status.value}."}
            for i in checklist.items
            if i.required and i.status.value != "VERIFIED"
        ]
        raise DocumentsIncompleteError(field_errors=unsatisfied)


def validate_submittable_state(status: ApplicationStatus) -> None:
    if status in (ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW,
                  ApplicationStatus.APPROVED, ApplicationStatus.COMPLETED,
                  ApplicationStatus.ACTION_REQUIRED, ApplicationStatus.INFO_REQUESTED):
        raise ApplicationAlreadySubmittedError()
