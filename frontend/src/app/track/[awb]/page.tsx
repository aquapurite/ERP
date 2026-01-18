'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Package,
  Truck,
  MapPin,
  CheckCircle,
  Clock,
  Phone,
  AlertTriangle,
  Home,
  Calendar,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { formatDate } from '@/lib/utils';
import { companyApi } from '@/lib/storefront/api';
import { CompanyInfo } from '@/types/storefront';

interface TrackingEvent {
  id: string;
  status: string;
  event_time: string;
  location?: string;
  city?: string;
  state?: string;
  description?: string;
}

interface PublicTrackingData {
  awb_number: string;
  status: string;
  status_description: string;
  expected_delivery_date?: string;
  actual_delivery_date?: string;
  destination_city: string;
  destination_state: string;
  destination_pincode: string;
  origin_city: string;
  payment_mode: 'PREPAID' | 'COD';
  product_name?: string;
  tracking_events: TrackingEvent[];
  support_phone?: string;
  support_email?: string;
}

const trackingApi = {
  getPublicTracking: async (awb: string): Promise<PublicTrackingData | null> => {
    // In production, this would call a public API endpoint
    // For demo, returning mock data
    await new Promise((r) => setTimeout(r, 800));

    if (!awb || awb === 'invalid') {
      return null;
    }

    return {
      awb_number: awb,
      status: 'IN_TRANSIT',
      status_description: 'Your package is on its way',
      expected_delivery_date: '2024-01-20',
      destination_city: 'Mumbai',
      destination_state: 'Maharashtra',
      destination_pincode: '400001',
      origin_city: 'Delhi',
      payment_mode: 'PREPAID',
      product_name: 'AquaPure RO+UV Pro Water Purifier',
      tracking_events: [
        { id: '1', status: 'IN_TRANSIT', event_time: '2024-01-18T14:30:00Z', city: 'Nagpur', state: 'Maharashtra', location: 'Nagpur Hub', description: 'Shipment in transit to destination' },
        { id: '2', status: 'SHIPPED', event_time: '2024-01-17T09:00:00Z', city: 'Delhi', state: 'Delhi', location: 'Delhi Distribution Center', description: 'Shipment dispatched from origin' },
        { id: '3', status: 'MANIFESTED', event_time: '2024-01-16T18:00:00Z', city: 'Delhi', state: 'Delhi', location: 'Delhi Warehouse', description: 'Shipment picked up and manifested' },
        { id: '4', status: 'PACKED', event_time: '2024-01-16T14:00:00Z', city: 'Delhi', state: 'Delhi', location: 'Delhi Warehouse', description: 'Order packed and ready for dispatch' },
        { id: '5', status: 'CREATED', event_time: '2024-01-16T10:00:00Z', description: 'Order placed successfully' },
      ],
      support_phone: '1800-123-4567',
      support_email: 'support@aquapure.com',
    };
  },
};

const statusIcons: Record<string, React.ReactNode> = {
  CREATED: <Package className="h-5 w-5" />,
  PACKED: <Package className="h-5 w-5" />,
  READY_FOR_PICKUP: <Clock className="h-5 w-5" />,
  MANIFESTED: <Truck className="h-5 w-5" />,
  SHIPPED: <Truck className="h-5 w-5" />,
  IN_TRANSIT: <Truck className="h-5 w-5" />,
  OUT_FOR_DELIVERY: <Truck className="h-5 w-5" />,
  DELIVERED: <CheckCircle className="h-5 w-5" />,
  RTO_INITIATED: <AlertTriangle className="h-5 w-5" />,
  RTO_IN_TRANSIT: <AlertTriangle className="h-5 w-5" />,
  RTO_DELIVERED: <AlertTriangle className="h-5 w-5" />,
};

const statusLabels: Record<string, string> = {
  CREATED: 'Order Created',
  PACKED: 'Packed',
  READY_FOR_PICKUP: 'Ready for Pickup',
  MANIFESTED: 'Picked Up',
  SHIPPED: 'Shipped',
  IN_TRANSIT: 'In Transit',
  OUT_FOR_DELIVERY: 'Out for Delivery',
  DELIVERED: 'Delivered',
  RTO_INITIATED: 'Return Initiated',
  RTO_IN_TRANSIT: 'Return in Transit',
  RTO_DELIVERED: 'Returned',
};

const statusColors: Record<string, string> = {
  CREATED: 'bg-gray-500',
  PACKED: 'bg-blue-500',
  READY_FOR_PICKUP: 'bg-cyan-500',
  MANIFESTED: 'bg-indigo-500',
  SHIPPED: 'bg-purple-500',
  IN_TRANSIT: 'bg-blue-600',
  OUT_FOR_DELIVERY: 'bg-yellow-500',
  DELIVERED: 'bg-green-500',
  RTO_INITIATED: 'bg-red-500',
  RTO_IN_TRANSIT: 'bg-red-500',
  RTO_DELIVERED: 'bg-orange-500',
};

export default function PublicTrackingPage() {
  const params = useParams();
  const awb = params.awb as string;
  const [company, setCompany] = useState<CompanyInfo | null>(null);

  // Fetch company info for support contact
  useEffect(() => {
    companyApi.getInfo().then(setCompany).catch(() => null);
  }, []);

  const { data: tracking, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['public-tracking', awb],
    queryFn: () => trackingApi.getPublicTracking(awb),
    enabled: !!awb,
    refetchOnWindowFocus: false,
  });

  // Use company info for support contact, falling back to tracking data
  const supportPhone = company?.phone || tracking?.support_phone || '1800-123-4567';
  const supportEmail = company?.email || tracking?.support_email || 'support@aquapurite.com';

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading tracking information...</p>
        </div>
      </div>
    );
  }

  if (!tracking) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Shipment Not Found</h2>
            <p className="text-muted-foreground mb-4">
              We couldn't find any shipment with AWB number: <strong>{awb}</strong>
            </p>
            <p className="text-sm text-muted-foreground">
              Please check the tracking number and try again. If you need assistance, contact our support.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isDelivered = tracking.status === 'DELIVERED';
  const isRTO = tracking.status.startsWith('RTO');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">Track Shipment</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-6">
        {/* Status Card */}
        <Card className="overflow-hidden">
          <div className={`${statusColors[tracking.status]} p-6 text-white`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-90">AWB Number</div>
                <div className="text-2xl font-bold font-mono">{tracking.awb_number}</div>
              </div>
              <div className="text-right">
                <div className="text-sm opacity-90">Status</div>
                <div className="text-xl font-semibold flex items-center gap-2">
                  {statusIcons[tracking.status]}
                  {statusLabels[tracking.status]}
                </div>
              </div>
            </div>
            <p className="mt-2 opacity-90">{tracking.status_description}</p>
          </div>
          <CardContent className="p-6">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <MapPin className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Destination</div>
                  <div className="font-medium">
                    {tracking.destination_city}, {tracking.destination_state}
                  </div>
                  <div className="text-sm text-muted-foreground">{tracking.destination_pincode}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Calendar className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">
                    {isDelivered ? 'Delivered On' : 'Expected Delivery'}
                  </div>
                  <div className="font-medium">
                    {isDelivered
                      ? formatDate(tracking.actual_delivery_date!)
                      : tracking.expected_delivery_date
                      ? formatDate(tracking.expected_delivery_date)
                      : 'To be updated'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Package className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Payment</div>
                  <div className="font-medium">
                    {tracking.payment_mode === 'COD' ? 'Cash on Delivery' : 'Prepaid'}
                  </div>
                </div>
              </div>
            </div>

            {tracking.product_name && (
              <>
                <Separator className="my-4" />
                <div className="flex items-center gap-3">
                  <Package className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <div className="text-sm text-muted-foreground">Product</div>
                    <div className="font-medium">{tracking.product_name}</div>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Tracking Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-0">
              {tracking.tracking_events.map((event, index) => {
                const isFirst = index === 0;
                const isLast = index === tracking.tracking_events.length - 1;

                return (
                  <div key={event.id} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          isFirst
                            ? `${statusColors[event.status]} text-white`
                            : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {statusIcons[event.status] || <Package className="h-5 w-5" />}
                      </div>
                      {!isLast && <div className="w-0.5 flex-1 bg-gray-200 my-1" />}
                    </div>
                    <div className={`flex-1 pb-6 ${isFirst ? '' : 'opacity-75'}`}>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-900">
                          {statusLabels[event.status] || event.status.replace(/_/g, ' ')}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(event.event_time)}
                        </span>
                      </div>
                      {event.description && (
                        <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                      )}
                      {(event.location || event.city) && (
                        <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                          <MapPin className="h-3 w-3" />
                          {[event.location, event.city, event.state].filter(Boolean).join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Help Section */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h3 className="font-semibold text-gray-900">Need Help?</h3>
                <p className="text-sm text-muted-foreground">
                  Contact our support team for assistance with your shipment
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-2">
                <Button variant="outline" asChild>
                  <a href={`tel:${supportPhone.replace(/[^0-9+]/g, '')}`}>
                    <Phone className="mr-2 h-4 w-4" />
                    {supportPhone}
                  </a>
                </Button>
                <Button variant="outline" asChild>
                  <a href={`mailto:${supportEmail}`}>
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Email Support
                  </a>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground pb-8">
          <p>Powered by Consumer Durable ERP</p>
          <p className="mt-1">Last updated: {new Date().toLocaleString()}</p>
        </div>
      </main>
    </div>
  );
}
