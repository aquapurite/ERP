'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Redirect to WMS Bins - the authoritative bins management page
export default function InventoryBinsRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/dashboard/wms/bins');
  }, [router]);
  return null;
}
