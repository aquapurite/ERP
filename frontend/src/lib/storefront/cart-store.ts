'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { StorefrontProduct, ProductVariant, CartItem } from '@/types/storefront';

interface CartStore {
  items: CartItem[];
  isOpen: boolean;

  // Actions
  addItem: (product: StorefrontProduct, quantity?: number, variant?: ProductVariant) => void;
  removeItem: (itemId: string) => void;
  updateQuantity: (itemId: string, quantity: number) => void;
  clearCart: () => void;
  toggleCart: () => void;
  openCart: () => void;
  closeCart: () => void;

  // Computed
  getItemCount: () => number;
  getSubtotal: () => number;
  getTax: () => number;
  getShipping: () => number;
  getTotal: () => number;
  getItemById: (itemId: string) => CartItem | undefined;
  isInCart: (productId: string, variantId?: string) => boolean;
}

const generateItemId = (productId: string, variantId?: string): string => {
  return variantId ? `${productId}-${variantId}` : productId;
};

const getItemPrice = (product: StorefrontProduct, variant?: ProductVariant): number => {
  if (variant?.selling_price) {
    return variant.selling_price;
  }
  return product.selling_price;
};

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],
      isOpen: false,

      addItem: (product, quantity = 1, variant) => {
        const itemId = generateItemId(product.id, variant?.id);
        const items = get().items;
        const existingItem = items.find((item) => item.id === itemId);

        if (existingItem) {
          // Update quantity if item exists
          set({
            items: items.map((item) =>
              item.id === itemId
                ? { ...item, quantity: item.quantity + quantity }
                : item
            ),
          });
        } else {
          // Add new item
          const newItem: CartItem = {
            id: itemId,
            product,
            variant,
            quantity,
            price: getItemPrice(product, variant),
          };
          set({ items: [...items, newItem] });
        }

        // Open cart drawer
        set({ isOpen: true });
      },

      removeItem: (itemId) => {
        set({ items: get().items.filter((item) => item.id !== itemId) });
      },

      updateQuantity: (itemId, quantity) => {
        if (quantity <= 0) {
          get().removeItem(itemId);
          return;
        }

        set({
          items: get().items.map((item) =>
            item.id === itemId ? { ...item, quantity } : item
          ),
        });
      },

      clearCart: () => {
        set({ items: [] });
      },

      toggleCart: () => {
        set({ isOpen: !get().isOpen });
      },

      openCart: () => {
        set({ isOpen: true });
      },

      closeCart: () => {
        set({ isOpen: false });
      },

      getItemCount: () => {
        return get().items.reduce((total, item) => total + item.quantity, 0);
      },

      getSubtotal: () => {
        return get().items.reduce(
          (total, item) => total + item.price * item.quantity,
          0
        );
      },

      getTax: () => {
        // Calculate GST (assuming 18% average)
        const subtotal = get().getSubtotal();
        return Math.round(subtotal * 0.18);
      },

      getShipping: () => {
        const subtotal = get().getSubtotal();
        // Free shipping over ₹999
        return subtotal >= 999 ? 0 : 99;
      },

      getTotal: () => {
        return get().getSubtotal() + get().getTax() + get().getShipping();
      },

      getItemById: (itemId) => {
        return get().items.find((item) => item.id === itemId);
      },

      isInCart: (productId, variantId) => {
        const itemId = generateItemId(productId, variantId);
        return get().items.some((item) => item.id === itemId);
      },
    }),
    {
      name: 'aquapurite-cart',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ items: state.items }), // Only persist items
    }
  )
);

// Helper hook for cart summary
export const useCartSummary = () => {
  const items = useCartStore((state) => state.items);
  const getSubtotal = useCartStore((state) => state.getSubtotal);
  const getTax = useCartStore((state) => state.getTax);
  const getShipping = useCartStore((state) => state.getShipping);
  const getTotal = useCartStore((state) => state.getTotal);
  const getItemCount = useCartStore((state) => state.getItemCount);

  return {
    items,
    itemCount: getItemCount(),
    subtotal: getSubtotal(),
    tax: getTax(),
    shipping: getShipping(),
    total: getTotal(),
  };
};
