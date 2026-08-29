"""Seed authoritative opportunity sources and sample verified opportunities."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.enums import (
    OpportunityAuthorityLevel,
    OpportunityDeadlineStatus,
    OpportunitySourceType,
    OpportunityType,
)
from app.models.opportunity import Opportunity, OpportunityLink, OpportunitySource
from app.modules.opportunities.ingestion.deduplicator import compute_content_hash


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def seed(session: Session) -> dict:
    # 1. Seed Sources
    sources_data = [
        {
            "name": "National Career Service (NCS)",
            "domain": "ncs.gov.in",
            "base_url": "https://www.ncs.gov.in",
            "source_type": OpportunitySourceType.CENTRAL_GOVERNMENT,
            "country": "IN",
            "authority_level": OpportunityAuthorityLevel.OFFICIAL,
            "crawl_frequency": "30_minutes",
            "enabled": True,
        },
        {
            "name": "myScheme Portal",
            "domain": "myscheme.gov.in",
            "base_url": "https://www.myscheme.gov.in",
            "source_type": OpportunitySourceType.CENTRAL_GOVERNMENT,
            "country": "IN",
            "authority_level": OpportunityAuthorityLevel.OFFICIAL,
            "crawl_frequency": "30_minutes",
            "enabled": True,
        },
        {
            "name": "National Scholarship Portal (NSP)",
            "domain": "scholarships.gov.in",
            "base_url": "https://scholarships.gov.in",
            "source_type": OpportunitySourceType.CENTRAL_GOVERNMENT,
            "country": "IN",
            "authority_level": OpportunityAuthorityLevel.OFFICIAL,
            "crawl_frequency": "1_hour",
            "enabled": True,
        },
        {
            "name": "Union Public Service Commission (UPSC)",
            "domain": "upsc.gov.in",
            "base_url": "https://upsc.gov.in",
            "source_type": OpportunitySourceType.PUBLIC_INSTITUTION,
            "country": "IN",
            "authority_level": OpportunityAuthorityLevel.OFFICIAL,
            "crawl_frequency": "1_hour",
            "enabled": True,
        },
        {
            "name": "India Government Portal",
            "domain": "india.gov.in",
            "base_url": "https://www.india.gov.in",
            "source_type": OpportunitySourceType.CENTRAL_GOVERNMENT,
            "country": "IN",
            "authority_level": OpportunityAuthorityLevel.OFFICIAL,
            "crawl_frequency": "3_hours",
            "enabled": True,
        },
        {
            "name": "Tata Consultancy Services Careers",
            "domain": "tcs.com",
            "base_url": "https://www.tcs.com/careers",
            "source_type": OpportunitySourceType.PRIVATE_COMPANY,
            "country": "IN",
            "authority_level": OpportunityAuthorityLevel.KNOWN_PRIVATE,
            "crawl_frequency": "6_hours",
            "enabled": True,
        },
    ]

    created_sources = []
    for s_data in sources_data:
        existing = session.query(OpportunitySource).filter(OpportunitySource.domain == s_data["domain"]).first()
        if not existing:
            src = OpportunitySource(**s_data)
            src.last_crawled_at = _utc_now() - timedelta(minutes=15)
            src.last_successful_crawl_at = _utc_now() - timedelta(minutes=15)
            session.add(src)
            session.flush()
            created_sources.append(src)
        else:
            created_sources.append(existing)

    session.commit()

    # 2. Seed Sample Verified Opportunities
    ncs_src = next((s for s in created_sources if s.domain == "ncs.gov.in"), created_sources[0])
    nsp_src = next((s for s in created_sources if s.domain == "scholarships.gov.in"), created_sources[0])
    tcs_src = next((s for s in created_sources if s.domain == "tcs.com"), created_sources[0])
    upsc_src = next((s for s in created_sources if s.domain == "upsc.gov.in"), created_sources[0])

    now = _utc_now()

    sample_opps = [
        {
            "type": OpportunityType.JOB,
            "title": "Assistant Engineer (Civil & Electrical) Recruitment 2026",
            "organization": "Central Public Works Department (CPWD)",
            "organization_type": "Government Ministry",
            "description": "Recruitment notification for Assistant Engineers across India. Candidates will be responsible for planning, executing, and supervising public infrastructure projects.",
            "summary": "Central Government engineering vacancies for B.Tech/BE graduates.",
            "location": "New Delhi, India",
            "locations": ["New Delhi", "Mumbai", "Kolkata", "Chennai", "Bengaluru"],
            "remote": False,
            "employment_type": "Full-time",
            "category": "Engineering",
            "sector": "Public Sector",
            "skills": ["Civil Engineering", "Project Management", "AutoCAD", "Structural Analysis"],
            "education_requirements": ["Graduate", "B.Tech", "B.E."],
            "experience_requirements": {"min_years": 0, "max_years": 3},
            "age_requirements": {"min": 21, "max": 30},
            "income_requirements": {},
            "citizenship_requirements": ["Indian National"],
            "gender_requirements": ["Any"],
            "state_requirements": [],
            "category_requirements": ["General", "OBC", "SC", "ST", "EWS"],
            "eligibility": ["Must hold a recognized Bachelor's Degree in Engineering.", "Age between 21 and 30 years as of closing date."],
            "benefits": ["Level 10 Pay Matrix (Rs. 56,100 - 1,77,500)", "Dearness Allowance", "HRA & Medical Benefits"],
            "salary_min": 56100.0,
            "salary_max": 177500.0,
            "stipend": None,
            "fee": "Rs. 100 (Exempted for Women/SC/ST/PwD)",
            "application_open_date": now - timedelta(days=10),
            "application_deadline": now + timedelta(days=4),  # Closing soon
            "published_at": now - timedelta(days=10),
            "status": OpportunityDeadlineStatus.CLOSING_SOON,
            "source_url": "https://www.ncs.gov.in/job-seeker/Pages/Search.aspx?id=CPWD-AE-2026",
            "application_url": "https://www.ncs.gov.in/apply/CPWD-AE-2026",
            "source_domain": "ncs.gov.in",
            "source_name": ncs_src.name,
            "source_type": ncs_src.source_type.value,
            "source_identifier": "CPWD-AE-2026",
            "source_id": ncs_src.id,
            "quality_score": 0.95,
            "extraction_confidence": 0.98,
            "is_canonical": True,
            "last_seen_at": now,
            "last_verified_at": now,
        },
        {
            "type": OpportunityType.SCHOLARSHIP,
            "title": "Central Sector Scheme of Scholarships for College and University Students 2026",
            "organization": "Department of Higher Education, Ministry of Education",
            "organization_type": "Central Ministry",
            "description": "Financial assistance to meritorious students from low-income families to meet a part of their day-to-day expenses while pursuing higher studies.",
            "summary": "Rs. 12,000 to Rs. 20,000 per annum scholarship for graduate & post-graduate students.",
            "location": "All India",
            "locations": ["All India"],
            "remote": True,
            "employment_type": "Scholarship",
            "category": "Education",
            "sector": "Government Scheme",
            "skills": [],
            "education_requirements": ["Higher Secondary (12th Passed)", "Undergraduate Student"],
            "experience_requirements": {},
            "age_requirements": {"min": 17, "max": 25},
            "income_requirements": {"max_annual_income": 450000.0},
            "citizenship_requirements": ["Indian National"],
            "gender_requirements": ["Any"],
            "state_requirements": [],
            "category_requirements": ["General", "OBC", "SC", "ST"],
            "eligibility": [
                "Top 20th percentile in Class 12th board exams.",
                "Family annual income below Rs. 4.5 Lakh.",
                "Pursuing regular degree course in recognized university/college.",
            ],
            "benefits": ["Rs. 12,000/year at graduation level for first 3 years", "Rs. 20,000/year at post-graduation level"],
            "salary_min": None,
            "salary_max": None,
            "stipend": "Rs. 12,000 - 20,000 / year",
            "fee": "Nil",
            "application_open_date": now - timedelta(days=20),
            "application_deadline": now + timedelta(days=15),
            "published_at": now - timedelta(days=20),
            "status": OpportunityDeadlineStatus.OPEN,
            "source_url": "https://scholarships.gov.in/scheme-detail/CS-2026",
            "application_url": "https://scholarships.gov.in/fresh-application-2026",
            "source_domain": "scholarships.gov.in",
            "source_name": nsp_src.name,
            "source_type": nsp_src.source_type.value,
            "source_identifier": "NSP-CS-2026",
            "source_id": nsp_src.id,
            "quality_score": 0.98,
            "extraction_confidence": 0.99,
            "is_canonical": True,
            "last_seen_at": now,
            "last_verified_at": now,
        },
        {
            "type": OpportunityType.INTERNSHIP,
            "title": "TCS National Qualifier Test (NQT) & Internship Drive 2026",
            "organization": "Tata Consultancy Services",
            "organization_type": "Private Enterprise",
            "description": "Exclusive internship opportunity for pre-final and final year engineering & science students with hands-on software project training and stipend.",
            "summary": "Software engineering internships in Bangalore, Pune, and Hyderabad with flexible hybrid mode.",
            "location": "Bengaluru, Karnataka",
            "locations": ["Bengaluru", "Pune", "Hyderabad", "Noida"],
            "remote": True,
            "employment_type": "Internship",
            "category": "Technology",
            "sector": "Information Technology",
            "skills": ["Python", "Java", "Data Structures", "Web Development", "SQL"],
            "education_requirements": ["B.Tech", "B.E.", "M.Tech", "MCA", "B.Sc CS"],
            "experience_requirements": {"max_years": 1},
            "age_requirements": {"min": 18, "max": 26},
            "income_requirements": {},
            "citizenship_requirements": ["Indian National"],
            "gender_requirements": ["Any"],
            "state_requirements": [],
            "category_requirements": [],
            "eligibility": [
                "Final year or recent graduate with minimum 60% in graduation.",
                "Basic proficiency in programming (Python/Java/C++).",
            ],
            "benefits": ["Monthly Stipend Rs. 25,000", "Pre-Placement Offer (PPO) opportunities", "Industry Mentorship"],
            "salary_min": None,
            "salary_max": None,
            "stipend": "Rs. 25,000 / month",
            "fee": "Nil",
            "application_open_date": now - timedelta(days=5),
            "application_deadline": now + timedelta(days=20),
            "published_at": now - timedelta(days=5),
            "status": OpportunityDeadlineStatus.OPEN,
            "source_url": "https://www.tcs.com/careers/nqt-internship-2026",
            "application_url": "https://www.tcs.com/careers/apply-internship-2026",
            "source_domain": "tcs.com",
            "source_name": tcs_src.name,
            "source_type": tcs_src.source_type.value,
            "source_identifier": "TCS-NQT-2026",
            "source_id": tcs_src.id,
            "quality_score": 0.90,
            "extraction_confidence": 0.95,
            "is_canonical": True,
            "last_seen_at": now,
            "last_verified_at": now,
        },
        {
            "type": OpportunityType.JOB,
            "title": "Civil Services Examination (CSE) 2026 Notification",
            "organization": "Union Public Service Commission (UPSC)",
            "organization_type": "Public Commission",
            "description": "Prestigious competitive examination for recruitment to administrative, diplomatic, police, and revenue civil services of India.",
            "summary": "UPSC Civil Services Prelims 2026 official notice.",
            "location": "All India",
            "locations": ["All India"],
            "remote": False,
            "employment_type": "Full-time",
            "category": "Administration",
            "sector": "Civil Services",
            "skills": ["Public Administration", "General Studies", "Analytical Reasoning"],
            "education_requirements": ["Graduate"],
            "experience_requirements": {},
            "age_requirements": {"min": 21, "max": 32},
            "income_requirements": {},
            "citizenship_requirements": ["Citizen of India"],
            "gender_requirements": ["Any"],
            "state_requirements": [],
            "category_requirements": [],
            "eligibility": ["Degree of a recognized University.", "Age 21 to 32 years with relaxation for reserved categories."],
            "benefits": ["IAS/IFS/IPS Cadre Pay Scale", "Government Housing & Security"],
            "salary_min": 56100.0,
            "salary_max": 250000.0,
            "stipend": None,
            "fee": "Rs. 100",
            "application_open_date": now - timedelta(days=12),
            "application_deadline": now + timedelta(days=2),  # Closing soon
            "published_at": now - timedelta(days=12),
            "status": OpportunityDeadlineStatus.CLOSING_SOON,
            "source_url": "https://upsc.gov.in/examinations/civil-services-2026",
            "application_url": "https://upsconline.nic.in/apply-cse-2026",
            "source_domain": "upsc.gov.in",
            "source_name": upsc_src.name,
            "source_type": upsc_src.source_type.value,
            "source_identifier": "UPSC-CSE-2026",
            "source_id": upsc_src.id,
            "quality_score": 0.99,
            "extraction_confidence": 1.0,
            "is_canonical": True,
            "last_seen_at": now,
            "last_verified_at": now,
        },
    ]

    seeded_count = 0
    for opp_data in sample_opps:
        chash = compute_content_hash(opp_data["organization"], opp_data["title"], str(opp_data["application_deadline"]))
        opp_data["content_hash"] = chash

        existing_opp = session.query(Opportunity).filter(Opportunity.content_hash == chash).first()
        if not existing_opp:
            opp = Opportunity(**opp_data)
            session.add(opp)
            session.flush()

            # Add primary official link
            link = OpportunityLink(
                opportunity_id=opp.id,
                url=opp.application_url or opp.source_url,
                domain=opp.source_domain,
                is_official=True,
                is_valid=True,
                verified_at=now,
                http_status=200,
            )
            session.add(link)
            seeded_count += 1

    session.commit()
    return {"sources_seeded": len(created_sources), "opportunities_seeded": seeded_count}


if __name__ == "__main__":
    from app.db.session import get_sessionmaker

    session = get_sessionmaker()()
    try:
        res = seed(session)
        print(f"Seeded opportunity discovery engine: {res}")
    finally:
        session.close()
