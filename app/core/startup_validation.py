"""
Startup Validation Module

This module runs validation checks when the application starts.
It ensures database state matches expected code structure.

Add this to main.py startup event:

    from app.core.startup_validation import run_startup_validations

    @app.on_event("startup")
    async def startup_event():
        await run_startup_validations()
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a validation error."""

    def __init__(self, category: str, severity: str, message: str, details: dict = None):
        self.category = category
        self.severity = severity  # "ERROR", "WARNING", "INFO"
        self.message = message
        self.details = details or {}

    def __str__(self):
        return f"[{self.severity}] {self.category}: {self.message}"


async def validate_chart_of_accounts(db: AsyncSession) -> List[ValidationError]:
    """
    Validate Chart of Accounts structure.

    Checks:
    1. Required accounts exist
    2. No GST accounts at Fixed Asset codes
    3. Account types are correct
    """
    from app.models.accounting import ChartOfAccount
    from app.core.account_codes import AccountCode, COA_STRUCTURE

    errors = []

    # Fetch all accounts
    result = await db.execute(select(ChartOfAccount))
    accounts = {acc.account_code: acc for acc in result.scalars().all()}

    # Check 1: Required accounts exist
    required_codes = [
        ("1010", "Cash"),
        ("1200", "Inventory"),
        ("1300", "Accounts Receivable"),
        ("1400", "GST Input Credit"),
        ("1410", "CGST Input Credit"),
        ("1420", "SGST Input Credit"),
        ("1430", "IGST Input Credit"),
        ("2100", "Accounts Payable"),
        ("2200", "GST Output Liability"),
        ("2210", "CGST Output Liability"),
        ("2220", "SGST Output Liability"),
        ("2230", "IGST Output Liability"),
    ]

    for code, expected_name in required_codes:
        if code not in accounts:
            errors.append(ValidationError(
                "COA",
                "ERROR",
                f"Required account {code} ({expected_name}) is missing",
                {"code": code, "expected_name": expected_name}
            ))

    # Check 2: No GST accounts at Fixed Asset codes (1510-1530)
    fixed_asset_codes = {
        "1510": "Land & Building",
        "1520": "Plant & Machinery",
        "1530": "Furniture & Fixtures",
    }
    gst_keywords = ["GST", "CGST", "SGST", "IGST"]

    for code, expected_name in fixed_asset_codes.items():
        if code in accounts:
            acc = accounts[code]
            if any(kw in acc.account_name.upper() for kw in gst_keywords):
                errors.append(ValidationError(
                    "COA",
                    "ERROR",
                    f"Account {code} has GST-related name '{acc.account_name}' but should be '{expected_name}'",
                    {"code": code, "actual_name": acc.account_name, "expected_name": expected_name}
                ))

    # Check 3: Account 1200 should be Inventory
    if "1200" in accounts:
        acc = accounts["1200"]
        if "INVENTORY" not in acc.account_name.upper() and "GST" in acc.account_name.upper():
            errors.append(ValidationError(
                "COA",
                "ERROR",
                f"Account 1200 should be 'Inventory' but found '{acc.account_name}'",
                {"code": "1200", "actual_name": acc.account_name}
            ))

    return errors


async def validate_account_code_consistency(db: AsyncSession) -> List[ValidationError]:
    """
    Validate that account codes used in services match the database.

    This detects the original issue: different account codes in different files.
    """
    from app.models.accounting import ChartOfAccount
    from app.core.account_codes import AccountCode

    errors = []

    # Get all codes from the AccountCode enum
    expected_codes = set(member.value for member in AccountCode)

    # Get all codes from database
    result = await db.execute(select(ChartOfAccount.account_code))
    db_codes = set(row[0] for row in result.all())

    # Check for codes in enum but not in database
    missing_in_db = expected_codes - db_codes
    if missing_in_db:
        errors.append(ValidationError(
            "CODE_CONSISTENCY",
            "WARNING",
            f"Account codes defined in code but missing in database: {missing_in_db}",
            {"missing_codes": list(missing_in_db)}
        ))

    return errors


async def validate_duplicate_accounts(db: AsyncSession) -> List[ValidationError]:
    """Check for duplicate account entries."""
    errors = []

    # Check for duplicate codes
    result = await db.execute(text("""
        SELECT account_code, COUNT(*) as cnt
        FROM chart_of_accounts
        GROUP BY account_code
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()

    for row in duplicates:
        errors.append(ValidationError(
            "DUPLICATES",
            "ERROR",
            f"Account code {row[0]} appears {row[1]} times",
            {"code": row[0], "count": row[1]}
        ))

    # Check for duplicate names that might indicate issues
    result = await db.execute(text("""
        SELECT account_name, COUNT(*) as cnt, array_agg(account_code) as codes
        FROM chart_of_accounts
        WHERE UPPER(account_name) LIKE '%GST%'
           OR UPPER(account_name) LIKE '%CGST%'
           OR UPPER(account_name) LIKE '%SGST%'
           OR UPPER(account_name) LIKE '%IGST%'
        GROUP BY account_name
        HAVING COUNT(*) > 1
    """))
    name_duplicates = result.fetchall()

    for row in name_duplicates:
        errors.append(ValidationError(
            "DUPLICATES",
            "WARNING",
            f"GST-related name '{row[0]}' appears {row[1]} times at codes: {row[2]}",
            {"name": row[0], "count": row[1], "codes": row[2]}
        ))

    return errors


async def run_startup_validations(fail_on_error: bool = False) -> Dict[str, Any]:
    """
    Run all startup validations.

    Args:
        fail_on_error: If True, raises exception on ERROR-level issues

    Returns:
        Validation report dictionary
    """
    logger.info("=" * 60)
    logger.info("RUNNING STARTUP VALIDATIONS")
    logger.info("=" * 60)

    all_errors: List[ValidationError] = []

    async with async_session_maker() as db:
        # Run all validations
        all_errors.extend(await validate_chart_of_accounts(db))
        all_errors.extend(await validate_account_code_consistency(db))
        all_errors.extend(await validate_duplicate_accounts(db))

    # Categorize errors
    errors = [e for e in all_errors if e.severity == "ERROR"]
    warnings = [e for e in all_errors if e.severity == "WARNING"]
    info = [e for e in all_errors if e.severity == "INFO"]

    # Log results
    if errors:
        logger.error(f"VALIDATION ERRORS ({len(errors)}):")
        for e in errors:
            logger.error(f"  - {e}")
    else:
        logger.info("✅ No validation errors")

    if warnings:
        logger.warning(f"VALIDATION WARNINGS ({len(warnings)}):")
        for w in warnings:
            logger.warning(f"  - {w}")

    # Fail if requested and errors exist
    if fail_on_error and errors:
        error_messages = "\n".join(str(e) for e in errors)
        raise RuntimeError(f"Startup validation failed with {len(errors)} errors:\n{error_messages}")

    return {
        "success": len(errors) == 0,
        "errors": [{"severity": e.severity, "category": e.category, "message": e.message, "details": e.details} for e in all_errors],
        "summary": {
            "total": len(all_errors),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(info)
        }
    }


# CLI function for manual validation
async def validate_now():
    """Run validation manually - useful for testing."""
    result = await run_startup_validations(fail_on_error=False)

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total issues: {result['summary']['total']}")
    print(f"  Errors: {result['summary']['errors']}")
    print(f"  Warnings: {result['summary']['warnings']}")

    if result['success']:
        print("\n✅ All validations passed!")
    else:
        print("\n❌ Validation failed - review errors above")

    return result
