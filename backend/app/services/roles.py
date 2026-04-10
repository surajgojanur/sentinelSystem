ROLE_CATALOG = [
    "Admin",
    "HR",
    "Intern",
    "Employee",
    "Developer",
    "Senior Developer",
    "Tech Lead",
    "Team Lead",
    "Manager",
    "Project Manager",
    "Product Manager",
    "QA Engineer",
    "UI/UX Designer",
    "DevOps Engineer",
    "Security",
    "Security Analyst",
    "Finance",
    "Analyst",
    "Operations",
    "Operations Manager",
    "Support Engineer",
    "Sales",
    "Marketing",
    "Recruiter",
]

MANAGER_ROLE_NAMES = {
    "admin",
    "hr",
    "manager",
    "team lead",
    "tech lead",
    "project manager",
    "product manager",
    "operations manager",
}


def normalize_role_name(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized == "hr":
        return "HR"
    if normalized == "ui/ux designer":
        return "UI/UX Designer"
    return normalized.title()


def is_manager_role(role_name: str | None) -> bool:
    return (role_name or "").strip().lower() in MANAGER_ROLE_NAMES
