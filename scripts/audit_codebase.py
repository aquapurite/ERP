"""
Codebase Audit Script

Checks for common issues that can cause database/code mismatches:
1. Hardcoded account codes not using the central definition
2. Hardcoded status values
3. Hardcoded enum values
4. Duplicate constant definitions
5. Missing validation

Run this periodically or as part of CI/CD to catch issues early.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Patterns to search for
PATTERNS = {
    "hardcoded_account_codes": {
        "pattern": r'["\']([1-6]\d{3})["\']',  # 4-digit codes like "1410"
        "description": "Hardcoded account codes (should use AccountCode enum)",
        "severity": "WARNING",
        "exclude_files": ["account_codes.py", "seed_accounting.py", "cleanup", "audit", "fix_gst"]
    },
    "hardcoded_status_values": {
        "pattern": r'status\s*[=!]=\s*["\']([A-Z_]+)["\']',
        "description": "Hardcoded status comparisons (consider using enums)",
        "severity": "INFO",
        "exclude_files": []
    },
    "duplicate_dict_definitions": {
        "pattern": r'(ACCOUNT_CODES|DEFAULT_ACCOUNTS|STATUS_CODES)\s*=\s*\{',
        "description": "Multiple dictionary definitions with similar names",
        "severity": "WARNING",
        "exclude_files": ["account_codes.py"]
    },
    "get_or_create_pattern": {
        "pattern": r'get_or_create.*account|create.*if.*not.*exist',
        "description": "get_or_create patterns that might create unvalidated entries",
        "severity": "WARNING",
        "exclude_files": []
    },
    "magic_numbers_finance": {
        "pattern": r'(?:gst|tax|tds|cgst|sgst|igst).*[=<>]\s*(\d+\.?\d*)',
        "description": "Magic numbers in financial calculations",
        "severity": "INFO",
        "exclude_files": []
    },
}


def search_file(file_path: Path, pattern: str) -> List[Tuple[int, str, str]]:
    """Search a file for a pattern. Returns list of (line_num, line, match)."""
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    matches.append((line_num, line.strip(), match.group(0)))
    except Exception as e:
        pass
    return matches


def audit_directory(directory: Path, file_extension: str = ".py") -> Dict[str, List]:
    """Audit all Python files in a directory."""
    results = defaultdict(list)

    for file_path in directory.rglob(f"*{file_extension}"):
        # Skip virtual environments and cache
        if any(skip in str(file_path) for skip in [".venv", "__pycache__", "node_modules", ".git"]):
            continue

        rel_path = file_path.relative_to(PROJECT_ROOT)

        for check_name, check_config in PATTERNS.items():
            # Skip excluded files
            if any(excl in str(file_path) for excl in check_config.get("exclude_files", [])):
                continue

            matches = search_file(file_path, check_config["pattern"])
            if matches:
                for line_num, line, match in matches:
                    results[check_name].append({
                        "file": str(rel_path),
                        "line": line_num,
                        "content": line[:100] + "..." if len(line) > 100 else line,
                        "match": match,
                        "severity": check_config["severity"]
                    })

    return results


def check_single_source_of_truth() -> List[Dict]:
    """Check if account codes are defined in multiple places."""
    issues = []

    # Files that should NOT have hardcoded account codes
    services_dir = PROJECT_ROOT / "app" / "services"
    account_codes_file = PROJECT_ROOT / "app" / "core" / "account_codes.py"

    # Check if central account_codes.py exists
    if not account_codes_file.exists():
        issues.append({
            "severity": "ERROR",
            "message": "Central account_codes.py not found!",
            "file": str(account_codes_file),
            "recommendation": "Create app/core/account_codes.py as single source of truth"
        })
        return issues

    # Check each service file for direct account code definitions
    for service_file in services_dir.glob("*.py"):
        if service_file.name == "__init__.py":
            continue

        with open(service_file, 'r') as f:
            content = f.read()

        # Check for dictionary definitions with account codes
        if re.search(r'(ACCOUNT_CODES|DEFAULT_ACCOUNTS)\s*=\s*\{[^}]*["\'][0-9]{4}["\']', content, re.DOTALL):
            # Check if it imports from account_codes
            if "from app.core.account_codes import" not in content:
                issues.append({
                    "severity": "WARNING",
                    "message": f"Service defines account codes directly without importing from account_codes.py",
                    "file": str(service_file.relative_to(PROJECT_ROOT)),
                    "recommendation": "Import AccountCode from app.core.account_codes and use enum values"
                })

    return issues


def check_validation_coverage() -> List[Dict]:
    """Check if validation is implemented properly."""
    issues = []

    # Check if startup validation exists
    validation_file = PROJECT_ROOT / "app" / "core" / "startup_validation.py"
    if not validation_file.exists():
        issues.append({
            "severity": "WARNING",
            "message": "Startup validation module not found",
            "file": "app/core/startup_validation.py",
            "recommendation": "Create startup validation to catch mismatches early"
        })

    # Check if main.py calls validation
    main_file = PROJECT_ROOT / "app" / "main.py"
    if main_file.exists():
        with open(main_file, 'r') as f:
            content = f.read()
        if "startup_validation" not in content and "run_startup_validations" not in content:
            issues.append({
                "severity": "INFO",
                "message": "Startup validation not called in main.py",
                "file": "app/main.py",
                "recommendation": "Add startup validation to application startup event"
            })

    return issues


def generate_report() -> str:
    """Generate a comprehensive audit report."""
    report = []
    report.append("=" * 70)
    report.append("CODEBASE AUDIT REPORT")
    report.append("=" * 70)

    # 1. Check single source of truth
    report.append("\n## 1. Single Source of Truth Check")
    report.append("-" * 50)
    ssot_issues = check_single_source_of_truth()
    if ssot_issues:
        for issue in ssot_issues:
            report.append(f"  [{issue['severity']}] {issue['file']}")
            report.append(f"    {issue['message']}")
            report.append(f"    Recommendation: {issue['recommendation']}")
    else:
        report.append("  ✅ Single source of truth properly implemented")

    # 2. Check validation coverage
    report.append("\n## 2. Validation Coverage Check")
    report.append("-" * 50)
    val_issues = check_validation_coverage()
    if val_issues:
        for issue in val_issues:
            report.append(f"  [{issue['severity']}] {issue['file']}")
            report.append(f"    {issue['message']}")
            report.append(f"    Recommendation: {issue['recommendation']}")
    else:
        report.append("  ✅ Validation properly implemented")

    # 3. Pattern-based audit
    report.append("\n## 3. Pattern-Based Audit")
    report.append("-" * 50)

    # Audit app directory
    app_results = audit_directory(PROJECT_ROOT / "app")

    for check_name, matches in app_results.items():
        config = PATTERNS[check_name]
        report.append(f"\n### {check_name}")
        report.append(f"    {config['description']}")
        report.append(f"    Found: {len(matches)} occurrences")

        if matches:
            # Show first 5 matches
            for match in matches[:5]:
                report.append(f"    [{match['severity']}] {match['file']}:{match['line']}")
                report.append(f"        {match['content']}")
            if len(matches) > 5:
                report.append(f"    ... and {len(matches) - 5} more")

    # 4. Summary
    report.append("\n" + "=" * 70)
    report.append("SUMMARY")
    report.append("=" * 70)

    total_errors = sum(1 for i in ssot_issues + val_issues if i.get("severity") == "ERROR")
    total_warnings = sum(1 for i in ssot_issues + val_issues if i.get("severity") == "WARNING")
    total_info = sum(1 for i in ssot_issues + val_issues if i.get("severity") == "INFO")

    for results in app_results.values():
        for r in results:
            if r["severity"] == "ERROR":
                total_errors += 1
            elif r["severity"] == "WARNING":
                total_warnings += 1
            else:
                total_info += 1

    report.append(f"  Errors: {total_errors}")
    report.append(f"  Warnings: {total_warnings}")
    report.append(f"  Info: {total_info}")

    if total_errors > 0:
        report.append("\n❌ AUDIT FAILED - Fix errors before deployment!")
    elif total_warnings > 0:
        report.append("\n⚠️ AUDIT PASSED WITH WARNINGS - Review before deployment")
    else:
        report.append("\n✅ AUDIT PASSED")

    return "\n".join(report)


def main():
    """Run the audit and print report."""
    report = generate_report()
    print(report)

    # Also write to file
    output_file = PROJECT_ROOT / "scripts" / "audit_report.txt"
    with open(output_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
