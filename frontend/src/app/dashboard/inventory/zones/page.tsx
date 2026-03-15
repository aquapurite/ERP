'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Redirect to WMS Zones - the authoritative zones management page
export default function InventoryZonesRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/dashboard/wms/zones');
  }, [router]);
  return null;
}
