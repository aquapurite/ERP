"""
Script to grant expense and CAPEX permissions to Admin role via the production API.
Uses PUT /roles/{id}/permissions which replaces all permissions (so we get existing first).
"""
import requests

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

    data = resp.json()
    token = data.get("access_token")
    if not token:
        print(f"No access token in response: {data}")
        return
    print(f"Login successful!")

    headers = {"Authorization": f"Bearer {token}"}

    # Get Admin role
    print("\n--- Finding Admin Role ---")
    resp = requests.get(f"{BASE_URL}/api/v1/roles", headers=headers)

    if resp.status_code != 200:
        print(f"Failed to get roles: {resp.status_code} - {resp.text}")
        return

    result = resp.json()
    if isinstance(result, dict) and 'items' in result:
        roles = result['items']
    elif isinstance(result, list):
        roles = result
    else:
        print(f"Unexpected roles response format")
        return

    admin_role = None
    for role in roles:
        if isinstance(role, dict):
            role_name = role.get('name', '')
            if 'admin' in role_name.lower():
                admin_role = role
                break

    if not admin_role:
        print("Admin role not found!")
        return

    admin_role_id = admin_role['id']
    print(f"Admin Role ID: {admin_role_id}")

    # Get current permissions for Admin role
    print("\n--- Getting Current Admin Permissions ---")
    resp = requests.get(f"{BASE_URL}/api/v1/roles/{admin_role_id}/permissions", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get role permissions: {resp.status_code} - {resp.text}")
        return

    current_perms = resp.json()
    existing_perm_ids = set()
    if isinstance(current_perms, dict) and 'permissions' in current_perms:
        for p in current_perms['permissions']:
            existing_perm_ids.add(p['id'])
    print(f"Existing permissions count: {len(existing_perm_ids)}")

    # Get all expense and capex permissions
    print("\n--- Finding Expense/CAPEX Permissions ---")
    resp = requests.get(f"{BASE_URL}/api/v1/permissions", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to get permissions: {resp.status_code}")
        return

    perm_result = resp.json()
    if isinstance(perm_result, dict) and 'items' in perm_result:
        all_perms = perm_result['items']
    elif isinstance(perm_result, list):
        all_perms = perm_result
    else:
        all_perms = []

    expense_capex_perms = [
        p for p in all_perms
        if isinstance(p, dict) and (
            p.get('code', '').startswith('EXPENSE') or
            p.get('code', '').startswith('CAPEX')
        )
    ]

    print(f"Found {len(expense_capex_perms)} expense/capex permissions")

    # Build combined permission list (existing + new)
    for perm in expense_capex_perms:
        perm_id = perm['id']
        if perm_id not in existing_perm_ids:
            existing_perm_ids.add(perm_id)
            print(f"  Adding: {perm['code']}")
        else:
            print(f"  Already assigned: {perm['code']}")

    # Update role with all permissions
    print(f"\n--- Updating Admin Role with {len(existing_perm_ids)} permissions ---")
    resp = requests.put(
        f"{BASE_URL}/api/v1/roles/{admin_role_id}/permissions",
        json={"permission_ids": list(existing_perm_ids)},
        headers=headers
    )

    if resp.status_code in [200, 201]:
        print(f"✅ Successfully updated Admin role permissions!")
    else:
        print(f"❌ Failed to update permissions: {resp.status_code} - {resp.text}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
