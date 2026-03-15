'use client';

import { useState, useEffect, useCallback } from 'react';
import { atpApi } from '@/lib/api';
import apiClient from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import {
  Search, Package, Warehouse, TrendingUp, TrendingDown,
  AlertTriangle, CheckCircle, XCircle,
} from 'lucide-react';

interface ATPWarehouseDetail {
  warehouse_id: string;
  warehouse_name: string;
  on_hand: number;
  reserved: number;
  allocated: number;
  available: number;
}

interface ATPResult {
  product_id: string;
  sku: string;
  product_name: string;
  current_stock: number;
  reserved: number;
  allocated: number;
  incoming_po: number;
  atp_quantity: number;
  by_warehouse: ATPWarehouseDetail[];
}

interface ProductItem {
  id: string;
  name: string;
  sku: string;
}

export default function ATPPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [atpResults, setAtpResults] = useState<ATPResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedATP, setSelectedATP] = useState<ATPResult | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  // Check quantity dialog
  const [checkProductId, setCheckProductId] = useState('');
  const [checkQty, setCheckQty] = useState(1);
  const [checkResult, setCheckResult] = useState<{ available: boolean; atp_quantity: number; shortfall: number } | null>(null);

  const searchProducts = useCallback(async () => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    try {
      const { data } = await apiClient.get('/products', { params: { search: searchTerm, page: 1, size: 20 } });
      const items: ProductItem[] = (data.items || []).map((p: Record<string, unknown>) => ({
        id: p.id as string,
        name: p.name as string,
        sku: p.sku as string,
      }));
      setProducts(items);

      // Auto-fetch ATP for all found products
      if (items.length > 0) {
        const results: ATPResult[] = [];
        for (const prod of items) {
          try {
            const atp = await atpApi.getATP(prod.id);
            results.push(atp);
          } catch {
            // skip failed
          }
        }
        setAtpResults(results);
      }
    } catch {
      toast.error('Failed to search products');
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  const handleCheckQty = async () => {
    if (!checkProductId) return;
    try {
      const res = await atpApi.checkATP({
        product_id: checkProductId,
        quantity_required: checkQty,
      });
      setCheckResult(res);
    } catch {
      toast.error('ATP check failed');
    }
  };

  const getStatusBadge = (qty: number) => {
    if (qty <= 0) return <Badge variant="destructive" className="gap-1"><XCircle className="h-3 w-3" /> Out of Stock</Badge>;
    if (qty <= 10) return <Badge variant="outline" className="text-orange-600 border-orange-600 gap-1"><AlertTriangle className="h-3 w-3" /> Low</Badge>;
    return <Badge variant="default" className="bg-green-600 gap-1"><CheckCircle className="h-3 w-3" /> Sufficient</Badge>;
  };

  const getRowBg = (qty: number) => {
    if (qty <= 0) return 'bg-red-50 dark:bg-red-950/20';
    if (qty <= 10) return 'bg-yellow-50 dark:bg-yellow-950/20';
    return '';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">ATP - Available to Promise</h1>
        <p className="text-muted-foreground">Real-time stock availability check (SAP CO09)</p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <Label className="mb-1 block">Search Product</Label>
              <Input
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="Enter product name or SKU..."
                onKeyDown={e => e.key === 'Enter' && searchProducts()}
              />
            </div>
            <Button onClick={searchProducts} disabled={loading}>
              <Search className="h-4 w-4 mr-2" />
              {loading ? 'Checking...' : 'Check ATP'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ATP Results Table */}
      {atpResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              ATP Results ({atpResults.length} products)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead className="text-right">On Hand</TableHead>
                  <TableHead className="text-right">Reserved</TableHead>
                  <TableHead className="text-right">Allocated</TableHead>
                  <TableHead className="text-right">
                    <span className="flex items-center gap-1 justify-end">
                      <TrendingUp className="h-3 w-3" /> Incoming PO
                    </span>
                  </TableHead>
                  <TableHead className="text-right font-bold">ATP Qty</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {atpResults.map(atp => (
                  <TableRow key={atp.product_id} className={getRowBg(atp.atp_quantity)}>
                    <TableCell className="font-medium max-w-[200px] truncate">{atp.product_name}</TableCell>
                    <TableCell className="font-mono text-sm">{atp.sku || '-'}</TableCell>
                    <TableCell className="text-right">{atp.current_stock}</TableCell>
                    <TableCell className="text-right text-orange-600">{atp.reserved}</TableCell>
                    <TableCell className="text-right text-blue-600">{atp.allocated}</TableCell>
                    <TableCell className="text-right text-green-600">{atp.incoming_po}</TableCell>
                    <TableCell className="text-right text-lg font-bold">{atp.atp_quantity}</TableCell>
                    <TableCell>{getStatusBadge(atp.atp_quantity)}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => { setSelectedATP(atp); setShowDetail(true); }}
                        >
                          <Warehouse className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setCheckProductId(atp.product_id);
                            setCheckQty(1);
                            setCheckResult(null);
                          }}
                        >
                          <Search className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Quick Quantity Check */}
      {checkProductId && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quantity Availability Check</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3 items-end">
              <div>
                <Label className="mb-1 block">Product</Label>
                <Input value={checkProductId} disabled className="w-[300px] font-mono text-sm" />
              </div>
              <div>
                <Label className="mb-1 block">Quantity Required</Label>
                <Input
                  type="number"
                  value={checkQty}
                  onChange={e => setCheckQty(parseInt(e.target.value) || 1)}
                  min={1}
                  className="w-[120px]"
                />
              </div>
              <Button onClick={handleCheckQty}>Check</Button>
              <Button variant="ghost" onClick={() => { setCheckProductId(''); setCheckResult(null); }}>Clear</Button>
            </div>
            {checkResult && (
              <div className="mt-4 p-4 rounded-lg border">
                {checkResult.available ? (
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-semibold">Available!</span>
                    <span>ATP Quantity: {checkResult.atp_quantity}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-red-600">
                    <XCircle className="h-5 w-5" />
                    <span className="font-semibold">Not Available</span>
                    <span>Shortfall: {checkResult.shortfall} units (ATP: {checkResult.atp_quantity})</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Warehouse Detail Dialog */}
      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Warehouse Breakdown: {selectedATP?.product_name}
            </DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-muted-foreground">On Hand</p>
                <p className="text-lg font-bold">{selectedATP?.current_stock}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-muted-foreground">Reserved</p>
                <p className="text-lg font-bold text-orange-600">{selectedATP?.reserved}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-muted-foreground">Incoming PO</p>
                <p className="text-lg font-bold text-green-600">{selectedATP?.incoming_po}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <p className="text-xs text-muted-foreground">ATP</p>
                <p className="text-lg font-bold">{selectedATP?.atp_quantity}</p>
              </CardContent>
            </Card>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Warehouse</TableHead>
                <TableHead className="text-right">On Hand</TableHead>
                <TableHead className="text-right">Reserved</TableHead>
                <TableHead className="text-right">Allocated</TableHead>
                <TableHead className="text-right">Available</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(selectedATP?.by_warehouse || []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-4 text-muted-foreground">
                    No warehouse data
                  </TableCell>
                </TableRow>
              ) : (
                (selectedATP?.by_warehouse || []).map(wh => (
                  <TableRow key={wh.warehouse_id} className={getRowBg(wh.available)}>
                    <TableCell className="font-medium">{wh.warehouse_name}</TableCell>
                    <TableCell className="text-right">{wh.on_hand}</TableCell>
                    <TableCell className="text-right text-orange-600">{wh.reserved}</TableCell>
                    <TableCell className="text-right text-blue-600">{wh.allocated}</TableCell>
                    <TableCell className="text-right font-bold">{wh.available}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </DialogContent>
      </Dialog>
    </div>
  );
}
