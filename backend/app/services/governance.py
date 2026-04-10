"""
SecureAI Governance Engine v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layer 1 — RBAC + NRL Response Filter      (role-based blocking/masking)
Layer 2 — AI Second-Layer Validator       (deep semantic safety scan)
Layer 3 — Risk Level Classifier           (Low / Medium / High)
Layer 4 — Explainability Engine           (human-readable block reasons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Constants & rule tables
# ─────────────────────────────────────────────────────────────────────────────

RISK_LOW_MAX    = 0.30
RISK_MEDIUM_MAX = 0.70
SUSPICIOUS_QUERY_THRESHOLD = 3

# ── Layer 1: Intern keyword blocklist ────────────────────────────────────────
INTERN_BLOCKED_RULES = [
    (r"\bsalar(?:y|ies)\b",          "salary/compensation data"),
    (r"\bcompensation\b",            "compensation information"),
    (r"\bpay\s*scale\b",             "pay scale details"),
    (r"\bpassword\b",                "password information"),
    (r"\bcredential",                "credential data"),
    (r"\bsecret\b",                  "secret/classified content"),
    (r"\bapi[_\s]?key\b",           "API key material"),
    (r"\bconfidential\b",            "confidential content"),
    (r"\bproprietary\b",             "proprietary information"),
    (r"\bssn\b",                     "Social Security Number"),
    (r"\bsocial\s*security\b",      "Social Security information"),
    (r"\bcredit\s*card\b",          "credit card data"),
    (r"\bbank\s*account\b",         "banking information"),
    (r"\bprivate\s*key\b",          "private key material"),
    (r"\binternal\s*only\b",        "internal-only content"),
    (r"\bclassified\b",             "classified information"),
    (r"\bpersonal\s*data\b",        "personal data records"),
    (r"\bpii\b",                    "personally identifiable information"),
]

# ── Layer 1: HR PII masking rules ────────────────────────────────────────────
HR_MASKED_RULES = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
     "[EMAIL REDACTED]", "email address"),
    (r"\b(\+?\d[\d\s\-().]{7,}\d)\b",
     "[PHONE REDACTED]", "phone number"),
    (r"\b\d{3}-\d{2}-\d{4}\b",
     "[SSN REDACTED]", "SSN-format number"),
    (r"\b(?:\d[ -]?){13,16}\b",
     "[CARD REDACTED]", "card number"),
    (r"\$[\d,]+(?:\.\d{2})?(?:\s*(?:k|K|thousand|million|billion))?\b",
     "[AMOUNT REDACTED]", "salary/financial figure"),
    (r"(?i)password\s*[:=]\s*\S+",
     "password: [REDACTED]", "inline password"),
]

# ── Layer 2: Deep semantic risk signal groups ─────────────────────────────────
LAYER2_RULE_GROUPS = [
    ("cybersecurity threat language", [
        "hack", "exploit", "bypass", "inject", "sql injection",
        "xss", "csrf", "rce", "privilege escalation", "zero-day",
        "reverse shell", "payload", "c2 server", "exfiltrat",
    ]),
    ("malware / attack tooling", [
        "malware", "ransomware", "trojan", "rootkit", "keylogger",
        "spyware", "botnet", "ddos", "phishing", "spear phish",
        "brute force", "credential dump", "mimikatz",
    ]),
    ("data exfiltration signals", [
        "dump database", "export all", "extract records",
        "full database", "all passwords", "all credentials",
        "user table", "shadow file", "/etc/passwd",
    ]),
    ("sensitive PII disclosure", [
        "social security", "date of birth", "home address",
        "passport number", "driver license", "medical record",
        "health information", "financial record",
    ]),
    ("insider threat indicators", [
        "cover tracks", "delete logs", "clear audit", "hide activity",
        "disable monitoring", "turn off logging", "evade detection",
    ]),
]

_ALL_RISK_KEYWORDS = [kw for _, group in LAYER2_RULE_GROUPS for kw in group]


# ─────────────────────────────────────────────────────────────────────────────
# Data transfer objects
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FilterResult:
    filtered_response: str
    status: str
    risk_score: float
    risk_level: str
    reason: Optional[str] = None
    triggered_rules: list = field(default_factory=list)
    is_high_risk_alert: bool = False
    validator_notes: list = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def apply_governance(response: str, query: str, role: str) -> FilterResult:
    risk_score = _compute_risk_score(query, response)
    risk_level = _classify_risk(risk_score)
    validator_notes = _layer2_validator(response, query)

    if validator_notes and risk_level != "high":
        risk_score = min(risk_score + 0.25, 1.0)
        risk_level = _classify_risk(risk_score)

    if role == "intern":
        result = _filter_intern(query, response, risk_score, risk_level)
    elif role == "hr":
        result = _filter_hr(response, risk_score, risk_level)
    else:
        result = FilterResult(
            filtered_response=response,
            status="allowed",
            risk_score=risk_score,
            risk_level=risk_level,
        )

    result.validator_notes = validator_notes
    result.is_high_risk_alert = (result.risk_level == "high")
    return result


def compute_query_sensitivity(query: str) -> bool:
    q = query.lower()

    if any(kw in q for kw in _ALL_RISK_KEYWORDS):
        return True

    return any(re.search(pattern, q, re.IGNORECASE) for pattern, _ in INTERN_BLOCKED_RULES)


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 — Role filters
# ─────────────────────────────────────────────────────────────────────────────

def _filter_intern(query, response, risk_score, risk_level):
    triggered = _detect_intern_blocked_rules(query, response)
    if triggered:
        joined = ", ".join(triggered)
        explanation = (
            f"This request is blocked because it asks about restricted information: {joined}. "
            "Intern accounts cannot access confidential, credential, compensation, or regulated personal data."
        )
        guidance = (
            "Why you cannot ask this: your current role does not have permission to view or request that data. "
            "If you need legitimate access, contact HR or an admin, or ask for a high-level policy summary instead."
        )
        return FilterResult(
            filtered_response=(
                "Alert: Request blocked by SecureAI policy.\n"
                f"Why it was blocked: {explanation}\n"
                f"Why you cannot ask this: {guidance}"
            ),
            status="blocked",
            risk_score=max(risk_score, 0.75),
            risk_level="high",
            reason=f"{explanation} {guidance}",
            triggered_rules=triggered,
            is_high_risk_alert=True,
        )
    return FilterResult(
        filtered_response=response,
        status="allowed",
        risk_score=risk_score,
        risk_level=risk_level,
    )


def _filter_hr(response, risk_score, risk_level):
    masked = response
    triggered = []
    for pattern, replacement, label in HR_MASKED_RULES:
        new_masked, count = re.subn(pattern, replacement, masked, flags=re.IGNORECASE)
        if count > 0:
            triggered.append(label)
            masked = new_masked

    if triggered:
        joined = ", ".join(triggered)
        reason = (
            f"Response automatically redacted {len(triggered)} sensitive field(s): {joined}. "
            f"Data masked per HR data-handling policy."
        )
        return FilterResult(
            filtered_response=masked,
            status="filtered",
            risk_score=risk_score,
            risk_level=risk_level,
            reason=reason,
            triggered_rules=triggered,
        )
    return FilterResult(
        filtered_response=response,
        status="allowed",
        risk_score=risk_score,
        risk_level=risk_level,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 — Validator
# ─────────────────────────────────────────────────────────────────────────────

def _layer2_validator(response, query):
    combined = (query + " " + response).lower()
    notes = []
    for category, keywords in LAYER2_RULE_GROUPS:
        hits = [kw for kw in keywords if kw in combined]
        if hits:
            sample = hits[:2]
            notes.append(
                f"Detected {category} signal "
                f"(matched: {', '.join(repr(h) for h in sample)})"
            )
    return notes


def _detect_intern_blocked_rules(query, response):
    combined = f"{query or ''} {response or ''}"
    triggered = []
    for pattern, label in INTERN_BLOCKED_RULES:
        if re.search(pattern, combined, re.IGNORECASE) and label not in triggered:
            triggered.append(label)
    return triggered


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 — Risk scoring + classification
# ─────────────────────────────────────────────────────────────────────────────

def _compute_risk_score(query, response):
    combined = (query + " " + response).lower()
    group_weights = [0.6, 0.8, 1.0, 0.7, 1.0]
    group_score = 0.0

    for (_, keywords), weight in zip(LAYER2_RULE_GROUPS, group_weights):
        hits = sum(1 for kw in keywords if kw in combined)
        if hits:
            group_score += min(hits / len(keywords), 1.0) * weight

    keyword_score = min(group_score / sum(group_weights), 1.0)
    length_score = min(len(response) / 6000, 0.25)

    intent_score = 0.0
    intent_phrases = [
        "how do i hack", "how to bypass", "give me all",
        "list all users", "show me passwords", "what are the credentials",
        "ignore previous", "disregard your instructions", "pretend you are",
    ]
    if any(p in combined for p in intent_phrases):
        intent_score = 0.3

    raw = keyword_score * 0.60 + length_score * 0.15 + intent_score * 0.25
    return round(min(raw, 1.0), 3)


def _classify_risk(score):
    if score <= RISK_LOW_MAX:
        return "low"
    elif score <= RISK_MEDIUM_MAX:
        return "medium"
    return "high"
