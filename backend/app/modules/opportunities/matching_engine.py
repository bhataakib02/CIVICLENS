"""Opportunity Matching Engine (prompt §31, §32, §33).

Provides transparent personalized scoring against citizen profiles (age, education, skills, experience, location, state, income, category).
Produces an explicit explanation breakdown ("Why this matches you").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.models.opportunity import Opportunity
from app.models.citizen_profile import CitizenProfile


@dataclass
class MatchBreakdown:
    overall_score: float  # 0.0 to 100.0
    skill_match: float
    education_match: float
    location_match: float
    experience_match: float
    eligibility_match: float
    deadline_urgency: float
    reasons: List[str] = field(default_factory=list)


class OpportunityMatchingEngine:
    """Computes transparent match scores and explanations for citizens."""

    def match(self, opportunity: Opportunity, profile: Optional[CitizenProfile]) -> MatchBreakdown:
        if not profile:
            return MatchBreakdown(
                overall_score=50.0,
                skill_match=50.0,
                education_match=50.0,
                location_match=50.0,
                experience_match=50.0,
                eligibility_match=50.0,
                deadline_urgency=50.0,
                reasons=["Generic match score (complete your profile for personalized recommendations)."],
            )

        reasons = []

        # 1. Skill Match (25%)
        user_skills = [s.lower().strip() for s in (profile.skills or [])]
        opp_skills = [s.lower().strip() for s in (opportunity.skills or [])]
        if opp_skills and user_skills:
            matching_skills = set(user_skills).intersection(set(opp_skills))
            skill_score = (len(matching_skills) / len(opp_skills)) * 100.0
            if matching_skills:
                reasons.append(f"Matches your skills: {', '.join(list(matching_skills)[:3])}")
        else:
            skill_score = 70.0  # default moderate match if skills unconstrained

        # 2. Education Match (20%)
        user_edu = (profile.highest_qualification or "").lower()
        opp_edu = [e.lower() for e in (opportunity.education_requirements or [])]
        if opp_edu:
            if any(user_edu in req or req in user_edu for req in opp_edu):
                education_score = 100.0
                reasons.append(f"Education requirement met ({profile.highest_qualification})")
            else:
                education_score = 40.0
        else:
            education_score = 80.0

        # 3. Location & State Match (20%)
        location_score = 50.0
        if opportunity.remote:
            location_score = 100.0
            reasons.append("Remote opportunity available anywhere")
        elif profile.addresses:
            user_states = [a.state.lower() for a in profile.addresses if a.state]
            opp_states = [s.lower() for s in (opportunity.state_requirements or [])]
            if not opp_states or any(st in opp_states for st in user_states):
                location_score = 90.0
                reasons.append("Location matches your registered state")

        # 4. Experience & Age Match (15%)
        experience_score = 75.0
        if profile.age:
            age_req = opportunity.age_requirements or {}
            min_age = age_req.get("min")
            max_age = age_req.get("max")
            if min_age and profile.age < min_age:
                experience_score -= 30.0
            elif max_age and profile.age > max_age:
                experience_score -= 30.0
            else:
                reasons.append(f"Age eligible ({profile.age} years)")

        # 5. Income / Category Eligibility Match (10%)
        eligibility_score = 80.0
        if profile.category and opportunity.category_requirements:
            cats = [c.lower() for c in opportunity.category_requirements]
            if profile.category.lower() in cats:
                eligibility_score = 100.0
                reasons.append(f"Reservation category eligible ({profile.category})")

        # 6. Deadline Urgency (10%)
        deadline_urgency = 50.0
        if opportunity.status.value == "CLOSING_SOON":
            deadline_urgency = 90.0
            reasons.append("Closing soon — apply promptly!")
        elif opportunity.status.value == "OPEN":
            deadline_urgency = 70.0

        # Weighted calculation
        overall = (
            (skill_score * 0.25)
            + (education_score * 0.20)
            + (location_score * 0.20)
            + (experience_score * 0.15)
            + (eligibility_score * 0.10)
            + (deadline_urgency * 0.10)
        )
        overall = round(min(max(overall, 0.0), 100.0), 1)

        return MatchBreakdown(
            overall_score=overall,
            skill_match=round(skill_score, 1),
            education_match=round(education_score, 1),
            location_match=round(location_score, 1),
            experience_match=round(experience_score, 1),
            eligibility_match=round(eligibility_score, 1),
            deadline_urgency=round(deadline_urgency, 1),
            reasons=reasons or ["Matches general eligibility criteria."],
        )
