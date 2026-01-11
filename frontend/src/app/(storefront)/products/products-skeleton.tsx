import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function ProductCardSkeleton() {
  return (
    <Card className="overflow-hidden bg-slate-800/50 border-slate-700">
      <Skeleton className="aspect-square bg-slate-700" />
      <CardContent className="p-4 space-y-2">
        <Skeleton className="h-3 w-1/3 bg-slate-700" />
        <Skeleton className="h-4 w-full bg-slate-700" />
        <Skeleton className="h-4 w-3/4 bg-slate-700" />
        <Skeleton className="h-6 w-1/2 bg-slate-700" />
      </CardContent>
    </Card>
  );
}

export function ProductsPageSkeleton() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header skeleton */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="container mx-auto px-4 py-6">
          <Skeleton className="h-4 w-24 bg-slate-700 mb-2" />
          <Skeleton className="h-8 w-64 bg-slate-700 mb-1" />
          <Skeleton className="h-4 w-32 bg-slate-700" />
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="flex gap-8">
          {/* Sidebar skeleton - Desktop */}
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-24 bg-slate-800/50 rounded-xl border border-slate-700 p-4 space-y-6">
              <div className="flex justify-between items-center">
                <Skeleton className="h-5 w-16 bg-slate-700" />
                <Skeleton className="h-8 w-14 bg-slate-700" />
              </div>
              {/* Filter sections */}
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-3">
                  <Skeleton className="h-5 w-24 bg-slate-700" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full bg-slate-700" />
                    <Skeleton className="h-4 w-3/4 bg-slate-700" />
                  </div>
                </div>
              ))}
            </div>
          </aside>

          {/* Main Content skeleton */}
          <main className="flex-1 min-w-0">
            {/* Toolbar skeleton */}
            <div className="flex items-center justify-between gap-4 mb-6 bg-slate-800/50 rounded-xl border border-slate-700 p-4">
              <Skeleton className="h-9 w-24 bg-slate-700" />
              <div className="flex items-center gap-3">
                <Skeleton className="h-9 w-40 bg-slate-700" />
                <Skeleton className="h-9 w-20 bg-slate-700" />
              </div>
            </div>

            {/* Products Grid skeleton */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <ProductCardSkeleton key={i} />
              ))}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
