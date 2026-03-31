"""
ChipCycle - Grading logic for each task.

Provides deterministic scoring based on:
  - Correct issue identification (keyword fuzzy matching)
  - Severity accuracy
  - False positive detection
  - Fix recommendation quality
"""

from typing import Any, Dict, List, Tuple


# Map of common LLM variations to our standard keywords
SYNONYMS = {
    "increase size": "upsize",
    "widen": "upsize",
    "scale up": "upsize",
    "make larger": "upsize",
    "insert buffer": "buffer",
    "add buffer": "buffer",
    "buffering": "buffer",
    "max delay": "setup",
    "slow path": "setup",
    "min delay": "hold",
    "fast path": "hold",
    "cross clock": "cross-clock",
    "cdc": "cross-clock",
    "domain crossing": "cross-clock",
    "routing congestion": "congestion",
    "spacing violation": "spacing",
    "drc error": "drc",
    "power limit": "power budget",
}

def _normalize(text: str) -> str:
    """Lowercase, strip, and apply synonym replacements for robust matching."""
    text = text.lower().strip()
    for variant, standard in SYNONYMS.items():
        text = text.replace(variant, standard)
    return text


def _keyword_match(finding_text: str, keywords: List[str], threshold: int = 2) -> bool:
    """Check if a finding matches an issue by keyword overlap.

    Args:
        finding_text: Combined text from agent's finding (issue_type + location + description + root_cause).
        keywords: Target keywords for the real issue.
        threshold: Minimum number of keywords that must match.

    Returns:
        True if enough keywords are found in the finding text.
    """
    finding_lower = _normalize(finding_text)
    matches = sum(1 for kw in keywords if kw.lower() in finding_lower)
    return matches >= threshold


def _combine_finding_text(finding: Dict[str, Any]) -> str:
    """Combine all text fields from a finding into a single searchable string."""
    parts = []
    for key in ["issue_type", "location", "description", "root_cause", "recommended_fix", "severity"]:
        val = finding.get(key, "")
        if isinstance(val, str):
            parts.append(val)
    return " ".join(parts)


def _severity_score(submitted: str, expected: str) -> float:
    """Score severity accuracy. Returns 1.0 for exact match, 0.5 for adjacent, 0.0 for wrong."""
    severity_order = {"info": 0, "minor": 1, "major": 2, "critical": 3}
    s = severity_order.get(_normalize(submitted), -1)
    e = severity_order.get(_normalize(expected), -1)
    if s == -1 or e == -1:
        return 0.0
    if s == e:
        return 1.0
    if abs(s - e) == 1:
        return 0.5
    return 0.0


def _fix_quality(submitted_fix: str, expected_keywords: List[str]) -> float:
    """Score fix recommendation quality based on keyword presence."""
    if not submitted_fix:
        return 0.0
    fix_lower = _normalize(submitted_fix)
    matches = sum(1 for kw in expected_keywords if kw.lower() in fix_lower)
    if matches >= 3:
        return 1.0
    if matches >= 2:
        return 0.7
    if matches >= 1:
        return 0.4
    return 0.0


def grade_finding(
    finding: Dict[str, Any],
    real_issues: List[Dict[str, Any]],
    red_herrings: List[Dict[str, Any]],
    already_found: List[str],
) -> Tuple[float, str, str]:
    """Grade a single submitted finding.

    Returns:
        (reward, matched_issue_id, feedback_message)
    """
    finding_text = _combine_finding_text(finding)

    # Check if it matches a red herring (false positive)
    for rh in red_herrings:
        if _keyword_match(finding_text, rh["keywords"], threshold=2):
            return (
                -0.10,
                "",
                f"FALSE POSITIVE: This is not a real issue. {rh['why_not_issue']}",
            )

    # Try to match against real issues
    best_match = None
    best_match_count = 0

    for issue in real_issues:
        if issue["id"] in already_found:
            continue
        finding_lower = _normalize(finding_text)
        match_count = sum(1 for kw in issue["keywords"] if kw.lower() in finding_lower)
        if match_count > best_match_count and match_count >= 2:
            best_match = issue
            best_match_count = match_count

    if best_match is None:
        # Check if it's a duplicate of already found issue
        for issue in real_issues:
            if issue["id"] in already_found:
                finding_lower = _normalize(finding_text)
                match_count = sum(1 for kw in issue["keywords"] if kw.lower() in finding_lower)
                if match_count >= 2:
                    return (-0.05, "", "DUPLICATE: You already reported this issue.")
        # No match at all
        return (-0.05, "", "NO MATCH: This finding does not correspond to any known issue in the design.")

    # Matched a real issue — calculate reward
    reward = 0.15  # Base reward for correct identification

    # Severity accuracy bonus
    submitted_severity = finding.get("severity", "")
    if submitted_severity:
        sev_score = _severity_score(submitted_severity, best_match["severity"])
        reward += 0.05 * sev_score

    # Fix recommendation bonus
    submitted_fix = finding.get("recommended_fix", "")
    if submitted_fix:
        fix_score = _fix_quality(submitted_fix, best_match["keywords"])
        reward += 0.10 * fix_score

    feedback = f"CORRECT: Identified '{best_match['description'][:80]}...'"
    return (reward, best_match["id"], feedback)


def grade_review(
    review: Dict[str, Any],
    real_issues: List[Dict[str, Any]],
    found_issue_ids: List[str],
    task_difficulty: str,
) -> Tuple[float, str]:
    """Grade the final review submission.

    Returns:
        (reward, feedback_message)
    """
    reward = 0.0
    feedback_parts = []

    # Coverage bonus: how many issues were found
    total = len(real_issues)
    found = len(found_issue_ids)
    coverage = found / total if total > 0 else 0.0
    reward += 0.10 * coverage
    feedback_parts.append(f"Coverage: {found}/{total} issues identified ({coverage:.0%})")

    # For hard task: check blocking classification
    if task_difficulty == "hard":
        decision = _normalize(review.get("decision", ""))
        blocking_issues = review.get("blocking_issues", [])

        # The correct decision is "no-go" since there are blocking issues
        if decision in ("no-go", "no_go", "nogo", "not ready", "fail"):
            reward += 0.05
            feedback_parts.append("Correct tapeout decision: NO-GO")
        elif decision in ("go", "ready", "pass"):
            reward -= 0.05
            feedback_parts.append("WRONG tapeout decision: Design is NOT ready (setup violations + power exceed)")

    feedback = " | ".join(feedback_parts)
    return (reward, feedback)


def compute_episode_score(
    found_issue_ids: List[str],
    false_positives: int,
    total_issues: int,
    accumulated_reward: float,
    task_difficulty: str,
) -> float:
    """Compute the final 0.0-1.0 episode score.

    Weighting depends on task difficulty:
      Easy:   0.80 * detection_rate + 0.20 * precision
      Medium: 0.50 * detection_rate + 0.25 * precision + 0.25 * (analysis_quality via accumulated_reward)
      Hard:   0.35 * detection_rate + 0.25 * precision + 0.25 * analysis + 0.15 * triage_quality
    """
    detection_rate = len(found_issue_ids) / total_issues if total_issues > 0 else 0.0

    total_submissions = len(found_issue_ids) + false_positives
    precision = len(found_issue_ids) / total_submissions if total_submissions > 0 else 1.0

    # Normalize accumulated reward to 0-1 range (rough estimate)
    max_possible_reward = total_issues * 0.30 + 0.15  # all issues full score + review bonus
    analysis_quality = min(1.0, max(0.0, accumulated_reward / max_possible_reward)) if max_possible_reward > 0 else 0.0

    if task_difficulty == "easy":
        score = 0.80 * detection_rate + 0.20 * precision
    elif task_difficulty == "medium":
        score = 0.50 * detection_rate + 0.25 * precision + 0.25 * analysis_quality
    else:  # hard
        score = 0.35 * detection_rate + 0.25 * precision + 0.25 * analysis_quality + 0.15 * (1.0 if detection_rate > 0.7 else detection_rate)

    return round(max(0.0, min(1.0, score)), 4)
