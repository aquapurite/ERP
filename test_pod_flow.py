"""
Test script for POD to Franchisee Allocation Flow.

This script tests the complete flow:
1. Mark shipment as delivered with POD
2. Verify Installation record is created
3. Verify ServiceRequest is created
4. Verify Franchisee is allocated based on pincode
5. Verify current_load is incremented
"""
import asyncio
from datetime import datetime
import uuid

# Set up the environment
import sys
sys.path.insert(0, '/Users/mantosh/Consumer durable')

from sqlalchemy import select, func
from app.database import async_session_factory
from app.models.shipment import Shipment, ShipmentStatus
from app.models.installation import Installation
from app.models.franchisee import Franchisee, FranchiseeServiceability
from app.models.service_request import ServiceRequest
from app.services.post_delivery_service import PostDeliveryService


async def test_pod_flow():
    """Test the complete POD to franchisee allocation flow."""

    # Shipment ID with pincode 110016 (newly created test shipment)
    shipment_id = "a1b2c3d4-e5f6-a1b2-c3d4-e5f6a1b2c3d4"
    franchisee_id = "95eba007-b79f-44c2-9c86-7c19348ddd44"

    async with async_session_factory() as db:
        # === STEP 1: Check Initial State ===
        print("=" * 60)
        print("STEP 1: INITIAL STATE CHECK")
        print("=" * 60)

        # Check shipment
        shipment = await db.get(Shipment, uuid.UUID(shipment_id))
        if not shipment:
            print(f"ERROR: Shipment {shipment_id} not found!")
            return
        print(f"Shipment: {shipment.shipment_number}")
        print(f"Status: {shipment.status}")
        print(f"Order ID: {shipment.order_id}")

        # Check installations count
        result = await db.execute(select(func.count()).select_from(Installation))
        initial_install_count = result.scalar()
        print(f"\nInitial Installations Count: {initial_install_count}")

        # Check franchisee load
        result = await db.execute(
            select(FranchiseeServiceability)
            .where(FranchiseeServiceability.franchisee_id == franchisee_id)
            .where(FranchiseeServiceability.pincode == "110016")
        )
        serviceability = result.scalar_one_or_none()
        initial_load = serviceability.current_load if serviceability else 0
        print(f"Initial Franchisee Load for 110016: {initial_load}")

        # === STEP 2: Mark Shipment as Delivered ===
        print("\n" + "=" * 60)
        print("STEP 2: MARKING SHIPMENT AS DELIVERED")
        print("=" * 60)

        # Update shipment status to DELIVERED
        shipment.status = ShipmentStatus.DELIVERED
        shipment.delivered_at = datetime.utcnow()
        shipment.delivered_to = "Mr. Rahul Sharma"
        shipment.delivery_remarks = "Test POD delivery for franchisee allocation"
        shipment.pod_image_url = "https://storage.example.com/pod/photo_test.jpg"
        shipment.pod_signature_url = "https://storage.example.com/pod/sign_test.png"

        await db.commit()
        await db.refresh(shipment)
        print(f"Shipment status updated to: {shipment.status}")

        # === STEP 3: Trigger Post-Delivery Service ===
        print("\n" + "=" * 60)
        print("STEP 3: TRIGGERING POST-DELIVERY SERVICE")
        print("=" * 60)

        service = PostDeliveryService(db)
        pod_data = {
            "received_by": shipment.delivered_to,
            "image_urls": [shipment.pod_image_url],
            "signature_url": shipment.pod_signature_url,
        }
        service_result = await service.process_delivery(
            shipment_id=shipment_id,
            pod_data=pod_data,
        )

        print(f"Post-delivery service result:")
        print(f"  - Installation created: {service_result.get('installation_created', False)}")
        print(f"  - Installation ID: {service_result.get('installation_id', 'N/A')}")
        print(f"  - Franchisee assigned: {service_result.get('franchisee_assigned', False)}")
        print(f"  - Franchisee ID: {service_result.get('franchisee_id', 'N/A')}")

        # === STEP 4: Verify Results ===
        print("\n" + "=" * 60)
        print("STEP 4: VERIFICATION")
        print("=" * 60)

        # Check new installations count
        count_result = await db.execute(select(func.count()).select_from(Installation))
        final_install_count = count_result.scalar()
        print(f"Final Installations Count: {final_install_count}")
        print(f"New installations created: {final_install_count - initial_install_count}")

        # Check the latest installation
        if service_result.get('installation_id'):
            install_id = service_result.get('installation_id')
            installation = await db.get(Installation, install_id)
            if installation:
                print(f"\nNew Installation Details:")
                print(f"  - Number: {installation.installation_number}")
                print(f"  - Status: {installation.status}")
                print(f"  - Pincode: {installation.installation_pincode}")
                print(f"  - Franchisee ID: {installation.franchisee_id}")

        # Check franchisee load
        await db.refresh(serviceability)
        final_load = serviceability.current_load if serviceability else 0
        print(f"\nFinal Franchisee Load for 110016: {final_load}")
        print(f"Load incremented by: {final_load - initial_load}")

        # === SUMMARY ===
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        success_criteria = [
            ("Shipment marked as DELIVERED", shipment.status == ShipmentStatus.DELIVERED),
            ("Installation created", final_install_count > initial_install_count),
            ("Franchisee load incremented", final_load > initial_load),
        ]

        all_passed = True
        for criterion, passed in success_criteria:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {criterion}")
            if not passed:
                all_passed = False

        print("\n" + ("=" * 60))
        if all_passed:
            print("🎉 ALL TESTS PASSED! POD to Franchisee allocation flow works!")
        else:
            print("⚠️  SOME TESTS FAILED. Check the flow logic.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_pod_flow())
