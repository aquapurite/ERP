"""
SINGLE SOURCE OF TRUTH for Chart of Account Codes.

All account codes used in the system MUST be defined here.
DO NOT hardcode account codes anywhere else in the codebase.

This file serves as:
1. Central registry of all valid account codes
2. Documentation of the COA structure
3. Validation reference for startup checks
"""

from enum import Enum
from typing import Dict, NamedTuple


class AccountInfo(NamedTuple):
    """Account code metadata."""
    code: str
    name: str
    account_type: str  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    sub_type: str
    is_group: bool = False
    parent_code: str = None


class AccountCode(str, Enum):
    """
    Centralized account codes for the entire ERP system.

    USAGE:
        from app.core.account_codes import AccountCode

        # In services:
        cgst_code = AccountCode.CGST_INPUT.value  # "1410"

        # For validation:
        if code in AccountCode._value2member_map_:
            # Valid code
    """

    # ==================== ASSETS (1XXX) ====================

    # Cash & Bank (101X-102X)
    CASH = "1010"
    BANK_HDFC = "1020"
    BANK_ICICI = "1021"

    # Accounts Receivable (11XX)
    AR_CUSTOMERS = "1110"
    AR_DEALERS = "1120"

    # Inventory (12XX)
    INVENTORY = "1200"
    INVENTORY_FG = "1210"
    INVENTORY_SPARES = "1220"
    INVENTORY_TRANSIT = "1230"

    # Accounts Receivable General (13XX)
    ACCOUNTS_RECEIVABLE = "1300"

    # GST Input Credit (14XX)
    GST_INPUT = "1400"       # Parent group
    CGST_INPUT = "1410"
    SGST_INPUT = "1420"
    IGST_INPUT = "1430"

    # Fixed Assets (15XX)
    FIXED_ASSETS = "1500"    # Parent group
    LAND_BUILDING = "1510"
    PLANT_MACHINERY = "1520"
    FURNITURE_FIXTURES = "1530"
    VEHICLES = "1540"
    COMPUTER_EQUIPMENT = "1550"

    # Accumulated Depreciation (contra account)
    ACCUMULATED_DEPRECIATION = "1600"

    # TDS Receivable (17XX)
    TDS_RECEIVABLE = "1700"

    # ==================== LIABILITIES (2XXX) ====================

    # Accounts Payable (21XX)
    ACCOUNTS_PAYABLE = "2100"
    AP_VENDORS = "2110"
    AP_SERVICE = "2120"

    # GST Output Liability (22XX)
    GST_OUTPUT = "2200"      # Parent group
    CGST_OUTPUT = "2210"
    SGST_OUTPUT = "2220"
    IGST_OUTPUT = "2230"

    # TDS Payable (23XX)
    TDS_PAYABLE = "2300"

    # Advances & Provisions (24XX-26XX)
    TDS_PAYABLE_194C = "2400"
    ADVANCE_CUSTOMERS = "2500"
    PROVISION_WARRANTY = "2610"

    # ==================== EQUITY (3XXX) ====================

    SHARE_CAPITAL = "3100"
    RETAINED_EARNINGS = "3200"

    # ==================== REVENUE (4XXX) ====================

    SALES_REVENUE = "4000"   # Parent group
    SALES_PURIFIERS = "4110"
    SALES_SPARES = "4120"
    SALES_ACCESSORIES = "4130"
    SERVICE_REVENUE = "4100"
    SERVICE_INSTALLATION = "4210"
    SERVICE_AMC = "4220"
    SERVICE_CALL = "4230"
    DISCOUNT_RECEIVED = "4200"
    SALES_RETURNS = "4400"
    SALES_DISCOUNT = "4500"

    # ==================== EXPENSES (5XXX-6XXX) ====================

    # Cost of Goods Sold (5XXX)
    PURCHASE = "5000"
    COGS = "5100"
    COGS_PURIFIERS = "5100"
    COGS_SPARES = "5200"
    FREIGHT_INWARD = "5300"

    # Operating Expenses (6XXX)
    DISCOUNT_ALLOWED = "6100"
    FREIGHT_OUTWARD = "6410"
    WARRANTY_EXPENSE = "6600"
    DEPRECIATION_EXPENSE = "6700"
    ROUND_OFF = "6900"


# Account code aliases for backward compatibility
# Maps the key names used in different services to the canonical enum
ACCOUNT_CODE_ALIASES: Dict[str, AccountCode] = {
    # From auto_journal_service.py
    "CGST_PAYABLE": AccountCode.CGST_OUTPUT,
    "SGST_PAYABLE": AccountCode.SGST_OUTPUT,
    "IGST_PAYABLE": AccountCode.IGST_OUTPUT,
    "CGST_RECEIVABLE": AccountCode.CGST_INPUT,
    "SGST_RECEIVABLE": AccountCode.SGST_INPUT,
    "IGST_RECEIVABLE": AccountCode.IGST_INPUT,
    "COST_OF_GOODS_SOLD": AccountCode.COGS,
    "BANK": AccountCode.BANK_HDFC,
}


def get_account_code(key: str) -> str:
    """
    Get account code by key name.

    Supports both enum names and aliases.

    Usage:
        code = get_account_code("CGST_INPUT")  # Returns "1410"
        code = get_account_code("CGST_PAYABLE")  # Returns "2210" (alias)
    """
    # Try enum first
    try:
        return AccountCode[key].value
    except KeyError:
        pass

    # Try alias
    if key in ACCOUNT_CODE_ALIASES:
        return ACCOUNT_CODE_ALIASES[key].value

    raise ValueError(f"Unknown account code key: {key}")


def validate_account_code(code: str) -> bool:
    """Check if an account code is valid."""
    return code in AccountCode._value2member_map_


def get_all_codes() -> Dict[str, str]:
    """Get all account codes as a dictionary."""
    return {member.name: member.value for member in AccountCode}


# ==================== VALIDATION FUNCTIONS ====================

async def validate_coa_structure(db_session) -> dict:
    """
    Validate that the database COA matches the expected structure.

    Call this at application startup to catch mismatches early.

    Returns:
        {
            "valid": bool,
            "missing": [list of missing codes],
            "extra": [list of unexpected codes with GST-related names],
            "mismatched": [list of codes with wrong names/types]
        }
    """
    from sqlalchemy import select
    from app.models.accounting import ChartOfAccount

    result = await db_session.execute(select(ChartOfAccount))
    db_accounts = {acc.account_code: acc for acc in result.scalars().all()}

    expected_codes = set(AccountCode._value2member_map_.keys())
    actual_codes = set(db_accounts.keys())

    missing = expected_codes - actual_codes

    # Check for GST-related accounts at wrong codes
    gst_keywords = ['GST', 'CGST', 'SGST', 'IGST']
    fixed_asset_codes = ['1510', '1520', '1530', '1540', '1550']
    problematic = []

    for code in fixed_asset_codes:
        if code in db_accounts:
            acc = db_accounts[code]
            if any(kw in acc.account_name.upper() for kw in gst_keywords):
                problematic.append({
                    "code": code,
                    "name": acc.account_name,
                    "issue": "Fixed Asset code has GST-related name"
                })

    return {
        "valid": len(missing) == 0 and len(problematic) == 0,
        "missing": list(missing),
        "problematic": problematic,
        "total_expected": len(expected_codes),
        "total_found": len(actual_codes)
    }


# ==================== COA STRUCTURE DEFINITION ====================

COA_STRUCTURE = {
    # This defines the expected COA hierarchy
    # Use this for seeding and validation

    "1000": AccountInfo("1000", "Assets", "ASSET", "ASSET", is_group=True),

    # Current Assets
    "1010": AccountInfo("1010", "Cash in Hand", "ASSET", "CASH", parent_code="1000"),
    "1020": AccountInfo("1020", "Bank - HDFC", "ASSET", "BANK", parent_code="1000"),

    # Receivables
    "1110": AccountInfo("1110", "Trade Receivables - Customers", "ASSET", "ACCOUNTS_RECEIVABLE", parent_code="1000"),
    "1120": AccountInfo("1120", "Trade Receivables - Dealers", "ASSET", "ACCOUNTS_RECEIVABLE", parent_code="1000"),
    "1300": AccountInfo("1300", "Accounts Receivable", "ASSET", "ACCOUNTS_RECEIVABLE", parent_code="1000"),

    # Inventory
    "1200": AccountInfo("1200", "Inventory", "ASSET", "INVENTORY", is_group=True, parent_code="1000"),
    "1210": AccountInfo("1210", "Finished Goods - Water Purifiers", "ASSET", "INVENTORY", parent_code="1200"),
    "1220": AccountInfo("1220", "Spare Parts Inventory", "ASSET", "INVENTORY", parent_code="1200"),
    "1230": AccountInfo("1230", "Goods in Transit", "ASSET", "INVENTORY", parent_code="1200"),

    # GST Input
    "1400": AccountInfo("1400", "GST Input Credit", "ASSET", "CURRENT_ASSET", is_group=True, parent_code="1000"),
    "1410": AccountInfo("1410", "CGST Input Credit", "ASSET", "CURRENT_ASSET", parent_code="1400"),
    "1420": AccountInfo("1420", "SGST Input Credit", "ASSET", "CURRENT_ASSET", parent_code="1400"),
    "1430": AccountInfo("1430", "IGST Input Credit", "ASSET", "CURRENT_ASSET", parent_code="1400"),

    # Fixed Assets
    "1500": AccountInfo("1500", "Fixed Assets", "ASSET", "FIXED_ASSET", is_group=True, parent_code="1000"),
    "1510": AccountInfo("1510", "Land & Building", "ASSET", "FIXED_ASSET", parent_code="1500"),
    "1520": AccountInfo("1520", "Plant & Machinery", "ASSET", "FIXED_ASSET", parent_code="1500"),
    "1530": AccountInfo("1530", "Furniture & Fixtures", "ASSET", "FIXED_ASSET", parent_code="1500"),
    "1540": AccountInfo("1540", "Vehicles", "ASSET", "FIXED_ASSET", parent_code="1500"),
    "1550": AccountInfo("1550", "Computer & IT Equipment", "ASSET", "FIXED_ASSET", parent_code="1500"),
    "1600": AccountInfo("1600", "Accumulated Depreciation", "ASSET", "FIXED_ASSET", parent_code="1500"),

    # Liabilities
    "2000": AccountInfo("2000", "Liabilities", "LIABILITY", "LIABILITY", is_group=True),
    "2100": AccountInfo("2100", "Accounts Payable", "LIABILITY", "ACCOUNTS_PAYABLE", parent_code="2000"),
    "2110": AccountInfo("2110", "Trade Payables - Vendors", "LIABILITY", "ACCOUNTS_PAYABLE", parent_code="2100"),

    # GST Output
    "2200": AccountInfo("2200", "GST Liabilities", "LIABILITY", "TAX_PAYABLE", is_group=True, parent_code="2000"),
    "2210": AccountInfo("2210", "CGST Output Liability", "LIABILITY", "TAX_PAYABLE", parent_code="2200"),
    "2220": AccountInfo("2220", "SGST Output Liability", "LIABILITY", "TAX_PAYABLE", parent_code="2200"),
    "2230": AccountInfo("2230", "IGST Output Liability", "LIABILITY", "TAX_PAYABLE", parent_code="2200"),

    # TDS
    "2300": AccountInfo("2300", "TDS Payable", "LIABILITY", "TAX_PAYABLE", parent_code="2000"),
}
