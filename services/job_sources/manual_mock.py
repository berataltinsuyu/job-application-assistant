from services.job_sources.base import JobSourceAdapter


class ManualMockJobSourceAdapter(JobSourceAdapter):
    source_name = "manual_mock"

    def search_jobs(self, alert_profile: dict) -> list[dict]:
        # Phase 2A intentionally uses a mock/manual source only.
        # Future source adapters must respect public access, robots.txt, rate limits, and terms.
        # Do not implement login bypass, CAPTCHA bypass, proxy evasion, or aggressive scraping.
        return [
            {
                "source": self.source_name,
                "source_job_id": "mock-backend-api-001",
                "title": "Junior Backend API Developer",
                "company": "Example Software Studio",
                "location": "Remote",
                "work_model": "Remote",
                "seniority": "Junior",
                "job_type": "Full-time",
                "description": (
                    "Build and maintain REST APIs, write SQL queries, validate data flows, "
                    "document requirements, and collaborate with product and operations teams."
                ),
                "url": "https://example.com/jobs/mock-backend-api-001",
                "posted_at": "2026-06-01",
            },
            {
                "source": self.source_name,
                "source_job_id": "mock-data-analyst-002",
                "title": "Data Analyst",
                "company": "Example Analytics Group",
                "location": "Istanbul, Turkey",
                "work_model": "Hybrid",
                "seniority": "Entry level",
                "job_type": "Full-time",
                "description": (
                    "Analyze business metrics, prepare dashboards, perform SQL data validation, "
                    "and communicate insights to cross-functional stakeholders."
                ),
                "url": "https://example.com/jobs/mock-data-analyst-002",
                "posted_at": "2026-06-03",
            },
            {
                "source": self.source_name,
                "source_job_id": "mock-business-ops-003",
                "title": "Business Operations Specialist",
                "company": "Example Operations Ltd",
                "location": "Ankara, Turkey",
                "work_model": "On-site",
                "seniority": "Junior",
                "job_type": "Full-time",
                "description": (
                    "Support process improvement, requirement analysis, documentation, "
                    "operational reporting, and coordination across business teams."
                ),
                "url": "https://example.com/jobs/mock-business-ops-003",
                "posted_at": "2026-06-05",
            },
            {
                "source": self.source_name,
                "source_job_id": "mock-frontend-004",
                "title": "Frontend Developer Intern",
                "company": "Example Digital Products",
                "location": "Remote",
                "work_model": "Remote",
                "seniority": "Intern",
                "job_type": "Internship",
                "description": (
                    "Create responsive user interfaces with JavaScript, React, HTML, CSS, "
                    "component testing, and accessibility-minded implementation."
                ),
                "url": "https://example.com/jobs/mock-frontend-004",
                "posted_at": "2026-06-08",
            },
            {
                "source": self.source_name,
                "source_job_id": "mock-risk-005",
                "title": "Risk Operations Analyst",
                "company": "Example Financial Services",
                "location": "Remote",
                "work_model": "Remote",
                "seniority": "Entry level",
                "job_type": "Full-time",
                "description": (
                    "Review payment operations, monitor risk indicators, support fraud checks, "
                    "prepare technical documentation, and improve operational controls."
                ),
                "url": "https://example.com/jobs/mock-risk-005",
                "posted_at": "2026-06-10",
            },
        ]
