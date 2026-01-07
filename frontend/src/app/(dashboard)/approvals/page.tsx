'use client';

import { useQuery } from '@tanstack/react-query';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader, StatusBadge } from '@/components/common';
import { approvalsApi } from '@/lib/api';

export default function ApprovalsPage() {
  const { data: pending, isLoading } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: approvalsApi.getPending,
  });

  const approvalItems = [
    {
      type: 'Purchase Orders',
      items: pending?.purchase_orders ?? [],
      color: 'blue',
    },
    {
      type: 'Stock Transfers',
      items: pending?.transfers ?? [],
      color: 'purple',
    },
    {
      type: 'Vendor Onboarding',
      items: pending?.vendors ?? [],
      color: 'green',
    },
    {
      type: 'Journal Entries',
      items: pending?.journal_entries ?? [],
      color: 'orange',
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approvals"
        description="Review and approve pending requests"
      />

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-4">
        {approvalItems.map((item) => (
          <Card key={item.type}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{item.type}</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <div className="text-2xl font-bold">{item.items.length}</div>
              )}
              <p className="text-xs text-muted-foreground">pending approval</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pending Items */}
      <Card>
        <CardHeader>
          <CardTitle>Pending Approvals</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {approvalItems.map((category) =>
                category.items.map((item: { id: string; reference: string; amount: number; type: string }) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <StatusBadge status="PENDING" />
                        <span className="font-medium">{item.reference}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {category.type} - Amount: ₹{item.amount?.toLocaleString() ?? 0}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline">
                        <XCircle className="mr-1 h-4 w-4" />
                        Reject
                      </Button>
                      <Button size="sm">
                        <CheckCircle className="mr-1 h-4 w-4" />
                        Approve
                      </Button>
                    </div>
                  </div>
                ))
              )}
              {approvalItems.every((c) => c.items.length === 0) && (
                <div className="flex items-center justify-center h-32 text-muted-foreground">
                  No pending approvals
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
