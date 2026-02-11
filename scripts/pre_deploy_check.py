#!/usr/bin/env python3
"""
Pre-Deployment Validation Script

Run this script before every deployment to catch common issues:
1. Codebase audit (hardcoded values, duplicates)
2. Frontend build check
3. Database schema validation
4. COA structure validation

Usage:
    python scripts/pre_deploy_check.py

Exit codes:
    0 = All checks passed
    1 = Errors found (DO NOT DEPLOY)
    2 = Warnings found (review before deploy)
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """Print a section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_pass(message: str):
    """Print a pass message."""
    print(f"{Colors.GREEN}✓ PASS:{Colors.END} {message}")


def print_fail(message: str):
    """Print a fail message."""
    print(f"{Colors.RED}✗ FAIL:{Colors.END} {message}")


def print_warn(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ WARN:{Colors.END} {message}")


def check_frontend_build() -> tuple:
    """
    Check if frontend builds successfully.
    Returns (passed, errors, warnings)
    """
    print_header("1. FRONTEND BUILD CHECK")

    frontend_dir = PROJECT_ROOT / "frontend"
    if not frontend_dir.exists():
        print_warn("Frontend directory not found - skipping")
        return True, 0, 1

    print("Running: pnpm build...")

    try:
        result = subprocess.run(
            ["pnpm", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print_pass("Frontend build successful")
            return True, 0, 0
        else:
            print_fail("Frontend build failed")
            print(f"\n{Colors.RED}Error output:{Colors.END}")
            print(result.stderr[:1000] if result.stderr else result.stdout[:1000])
            return False, 1, 0

    except subprocess.TimeoutExpired:
        print_fail("Frontend build timed out (>5 minutes)")
        return False, 1, 0
    except FileNotFoundError:
        print_warn("pnpm not found - skipping frontend build check")
        return True, 0, 1


def check_codebase_audit() -> tuple:
    """
    Run codebase audit for hardcoded values.
    Returns (passed, errors, warnings)
    """
    print_header("2. CODEBASE AUDIT")

    audit_script = PROJECT_ROOT / "scripts" / "audit_codebase.py"
    if not audit_script.exists():
        print_warn("Audit script not found - skipping")
        return True, 0, 1

    print("Running codebase audit...")

    try:
        # Import and run audit
        from scripts.audit_codebase import check_single_source_of_truth, check_validation_coverage

        errors = 0
        warnings = 0

        # Check single source of truth
        ssot_issues = check_single_source_of_truth()
        for issue in ssot_issues:
            if issue['severity'] == 'ERROR':
                print_fail(f"{issue['file']}: {issue['message']}")
                errors += 1
            else:
                print_warn(f"{issue['file']}: {issue['message']}")
                warnings += 1

        # Check validation coverage
        val_issues = check_validation_coverage()
        for issue in val_issues:
            if issue['severity'] == 'ERROR':
                print_fail(f"{issue['file']}: {issue['message']}")
                errors += 1
            elif issue['severity'] == 'WARNING':
                print_warn(f"{issue['file']}: {issue['message']}")
                warnings += 1

        if errors == 0 and warnings == 0:
            print_pass("Codebase audit passed")

        return errors == 0, errors, warnings

    except Exception as e:
        print_fail(f"Audit error: {e}")
        return False, 1, 0


def check_gst_accounts() -> tuple:
    """
    Check GST account codes via API.
    Returns (passed, errors, warnings)
    """
    print_header("3. GST/COA STRUCTURE CHECK")

    try:
        import requests

        BASE_URL = os.environ.get("API_URL", "https://aquapurite-erp-api.onrender.com")
        EMAIL = os.environ.get("ADMIN_EMAIL", "themanagingdirector@aquapurite.com")
        PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")

        print(f"Checking against: {BASE_URL}")

        # Login
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=30
        )

        if resp.status_code != 200:
            print_warn(f"Could not authenticate - skipping COA check")
            return True, 0, 1

        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch accounts
        resp = requests.get(f"{BASE_URL}/api/v1/accounting/accounts", headers=headers, timeout=30)
        if resp.status_code != 200:
            print_warn("Could not fetch accounts - skipping COA check")
            return True, 0, 1

        accounts = resp.json()
        if isinstance(accounts, dict) and 'items' in accounts:
            accounts = accounts['items']

        acc_by_code = {acc['account_code']: acc for acc in accounts}

        errors = 0
        warnings = 0

        # Critical checks
        critical_mappings = {
            '1200': ('Inventory', 'ASSET'),
            '1410': ('CGST Input', 'ASSET'),
            '1420': ('SGST Input', 'ASSET'),
            '1430': ('IGST Input', 'ASSET'),
            '1510': ('Land', 'ASSET'),  # Should NOT have GST
            '1520': ('Plant', 'ASSET'),  # Should NOT have GST
            '1530': ('Furniture', 'ASSET'),  # Should NOT have GST
            '2210': ('CGST Output', 'LIABILITY'),
            '2220': ('SGST Output', 'LIABILITY'),
            '2230': ('IGST Output', 'LIABILITY'),
        }

        for code, (expected_name_part, expected_type) in critical_mappings.items():
            if code not in acc_by_code:
                print_fail(f"Missing account: {code} ({expected_name_part})")
                errors += 1
                continue

            acc = acc_by_code[code]

            # Check type
            if acc['account_type'] != expected_type:
                print_fail(f"{code}: Wrong type - got {acc['account_type']}, expected {expected_type}")
                errors += 1

            # Check for GST at Fixed Asset codes
            if code in ['1510', '1520', '1530']:
                if 'GST' in acc['account_name'].upper() or 'CGST' in acc['account_name'].upper():
                    print_fail(f"{code}: Has GST name '{acc['account_name']}' but should be Fixed Asset")
                    errors += 1
                else:
                    print_pass(f"{code}: {acc['account_name']} (correct)")

        if errors == 0:
            print_pass("All GST/COA checks passed")

        return errors == 0, errors, warnings

    except Exception as e:
        print_warn(f"COA check error: {e}")
        return True, 0, 1


def check_import_syntax() -> tuple:
    """
    Check Python syntax by importing key modules.
    Returns (passed, errors, warnings)
    """
    print_header("4. PYTHON IMPORT CHECK")

    modules_to_check = [
        "app.main",
        "app.core.account_codes",
        "app.core.status_codes",
        "app.services.accounting_service",
        "app.services.auto_journal_service",
    ]

    errors = 0
    for module in modules_to_check:
        try:
            __import__(module)
            print_pass(f"Import {module}")
        except Exception as e:
            print_fail(f"Import {module}: {e}")
            errors += 1

    return errors == 0, errors, 0


def main():
    """Run all pre-deployment checks."""
    print(f"\n{Colors.BOLD}PRE-DEPLOYMENT VALIDATION{Colors.END}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Project: {PROJECT_ROOT}")

    total_errors = 0
    total_warnings = 0

    # Run all checks
    checks = [
        ("Frontend Build", check_frontend_build),
        ("Codebase Audit", check_codebase_audit),
        ("GST/COA Structure", check_gst_accounts),
        ("Python Imports", check_import_syntax),
    ]

    results = []
    for name, check_func in checks:
        try:
            passed, errors, warnings = check_func()
            results.append((name, passed, errors, warnings))
            total_errors += errors
            total_warnings += warnings
        except Exception as e:
            print_fail(f"{name} check failed with exception: {e}")
            results.append((name, False, 1, 0))
            total_errors += 1

    # Summary
    print_header("SUMMARY")

    for name, passed, errors, warnings in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {name}: {status} (errors: {errors}, warnings: {warnings})")

    print(f"\n{Colors.BOLD}Total:{Colors.END} {total_errors} errors, {total_warnings} warnings")

    # Exit code
    if total_errors > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ DEPLOYMENT BLOCKED - Fix errors before deploying!{Colors.END}")
        return 1
    elif total_warnings > 0:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ DEPLOYMENT ALLOWED - Review warnings before deploying{Colors.END}")
        return 2
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL CHECKS PASSED - Safe to deploy!{Colors.END}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
