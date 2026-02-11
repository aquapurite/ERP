"""
Test creating an expense voucher via the API.
"""
import requests
from datetime import date
from decimal import Decimal

# API settings
BASE_URL = "https://aquapurite-erp-api.onrender.com"
EMAIL = "themanagingdirector@aquapurite.com"
PASSWORD = "Admin@123"


def main():
    # Login
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return

    token = resp.json().get("access_token")
    print("Login successful!")

    headers = {"Authorization": f"Bearer {token}"}

    # First, create an expense category (if none exists)
    print("\n--- Creating Expense Category ---")
    category_data = {
        "code": "TRAVEL",
        "name": "Travel & Conveyance",
        "description": "Business travel expenses",
        "requires_receipt": True,
        "max_amount_without_approval": 5000,
        "is_active": True
    }

    resp = requests.post(f"{BASE_URL}/api/v1/expenses/categories", json=category_data, headers=headers)
    if resp.status_code in [200, 201]:
        category = resp.json()
        category_id = category['id']
        print(f"Created category: {category['name']} (ID: {category_id})")
    elif "already exists" in resp.text.lower() or resp.status_code == 400:
        print(f"Category may already exist, fetching...")
        resp = requests.get(f"{BASE_URL}/api/v1/expenses/categories/dropdown", headers=headers)
        if resp.status_code == 200:
            categories = resp.json()
            if categories:
                category_id = categories[0]['id']
                print(f"Using existing category ID: {category_id}")
            else:
                print("No categories found!")
                return
        else:
            print(f"Failed to fetch categories: {resp.status_code}")
            return
    else:
        print(f"Failed to create category: {resp.status_code} - {resp.text}")
        return

    # Create expense voucher
    print("\n--- Creating Expense Voucher ---")
    voucher_data = {
        "voucher_date": str(date.today()),
        "expense_category_id": category_id,
        "amount": 1500.00,
        "gst_amount": 270.00,
        "tds_amount": 0,
        "narration": "Local travel for client meeting",
        "purpose": "Client Visit - Bangalore",
        "payment_mode": "CASH"
    }

    resp = requests.post(f"{BASE_URL}/api/v1/expenses", json=voucher_data, headers=headers)

    if resp.status_code in [200, 201]:
        voucher = resp.json()
        print(f"✅ Expense Voucher Created Successfully!")
        print(f"   Voucher Number: {voucher.get('voucher_number')}")
        print(f"   Amount: ₹{voucher.get('amount')}")
        print(f"   Status: {voucher.get('status')}")
    else:
        print(f"❌ Failed to create expense voucher: {resp.status_code}")
        print(f"   Response: {resp.text}")

    # Test dashboard
    print("\n--- Testing Dashboard ---")
    resp = requests.get(f"{BASE_URL}/api/v1/expenses/dashboard/stats", headers=headers)
    if resp.status_code == 200:
        dashboard = resp.json()
        print(f"✅ Dashboard Stats:")
        print(f"   Total this month: ₹{dashboard.get('total_expenses_this_month', 0)}")
        print(f"   Pending approval count: {dashboard.get('pending_approval_count', 0)}")
    else:
        print(f"❌ Dashboard failed: {resp.status_code} - {resp.text}")


if __name__ == "__main__":
    main()
