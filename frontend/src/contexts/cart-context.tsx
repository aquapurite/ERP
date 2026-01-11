'use client';

import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

export interface CartItem {
  id: string;
  productId: string;
  name: string;
  slug: string;
  sku: string;
  image?: string;
  price: number;
  mrp: number;
  quantity: number;
  maxQuantity?: number;
}

interface CartState {
  items: CartItem[];
  itemCount: number;
  subtotal: number;
  discount: number;
  shipping: number;
  total: number;
  deliveryPincode: string;
  isServiceable: boolean;
  estimatedDelivery: string;
  shippingCost: number;
}

type CartAction =
  | { type: 'ADD_ITEM'; payload: CartItem }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'UPDATE_QUANTITY'; payload: { id: string; quantity: number } }
  | { type: 'CLEAR_CART' }
  | { type: 'SET_DELIVERY'; payload: { pincode: string; isServiceable: boolean; estimatedDelivery: string; shippingCost: number } }
  | { type: 'LOAD_CART'; payload: CartItem[] };

const initialState: CartState = {
  items: [],
  itemCount: 0,
  subtotal: 0,
  discount: 0,
  shipping: 0,
  total: 0,
  deliveryPincode: '',
  isServiceable: false,
  estimatedDelivery: '',
  shippingCost: 0,
};

function calculateTotals(items: CartItem[], shippingCost: number = 0): Pick<CartState, 'itemCount' | 'subtotal' | 'discount' | 'shipping' | 'total'> {
  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const mrpTotal = items.reduce((sum, item) => sum + (item.mrp * item.quantity), 0);
  const discount = mrpTotal - subtotal;
  const shipping = subtotal >= 1000 ? 0 : shippingCost; // Free shipping above Rs 1000
  const total = subtotal + shipping;

  return { itemCount, subtotal, discount, shipping, total };
}

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'ADD_ITEM': {
      const existingIndex = state.items.findIndex(item => item.id === action.payload.id);
      let newItems: CartItem[];

      if (existingIndex > -1) {
        newItems = state.items.map((item, index) =>
          index === existingIndex
            ? { ...item, quantity: Math.min(item.quantity + action.payload.quantity, item.maxQuantity || 10) }
            : item
        );
      } else {
        newItems = [...state.items, action.payload];
      }

      return {
        ...state,
        items: newItems,
        ...calculateTotals(newItems, state.shippingCost),
      };
    }

    case 'REMOVE_ITEM': {
      const newItems = state.items.filter(item => item.id !== action.payload);
      return {
        ...state,
        items: newItems,
        ...calculateTotals(newItems, state.shippingCost),
      };
    }

    case 'UPDATE_QUANTITY': {
      const newItems = state.items.map(item =>
        item.id === action.payload.id
          ? { ...item, quantity: Math.max(1, Math.min(action.payload.quantity, item.maxQuantity || 10)) }
          : item
      ).filter(item => item.quantity > 0);

      return {
        ...state,
        items: newItems,
        ...calculateTotals(newItems, state.shippingCost),
      };
    }

    case 'CLEAR_CART': {
      return {
        ...initialState,
        deliveryPincode: state.deliveryPincode,
        isServiceable: state.isServiceable,
        estimatedDelivery: state.estimatedDelivery,
        shippingCost: state.shippingCost,
      };
    }

    case 'SET_DELIVERY': {
      const newState = {
        ...state,
        deliveryPincode: action.payload.pincode,
        isServiceable: action.payload.isServiceable,
        estimatedDelivery: action.payload.estimatedDelivery,
        shippingCost: action.payload.shippingCost,
      };
      return {
        ...newState,
        ...calculateTotals(state.items, action.payload.shippingCost),
      };
    }

    case 'LOAD_CART': {
      return {
        ...state,
        items: action.payload,
        ...calculateTotals(action.payload, state.shippingCost),
      };
    }

    default:
      return state;
  }
}

interface CartContextValue extends CartState {
  addItem: (item: Omit<CartItem, 'quantity'> & { quantity?: number }) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
  setDelivery: (pincode: string, isServiceable: boolean, estimatedDelivery: string, shippingCost: number) => void;
}

const CartContext = createContext<CartContextValue | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, initialState);

  // Load cart from localStorage on mount
  useEffect(() => {
    const savedCart = localStorage.getItem('aquapurite_cart');
    if (savedCart) {
      try {
        const parsed = JSON.parse(savedCart);
        if (Array.isArray(parsed.items)) {
          dispatch({ type: 'LOAD_CART', payload: parsed.items });
        }
        if (parsed.deliveryPincode) {
          dispatch({
            type: 'SET_DELIVERY',
            payload: {
              pincode: parsed.deliveryPincode,
              isServiceable: parsed.isServiceable || false,
              estimatedDelivery: parsed.estimatedDelivery || '',
              shippingCost: parsed.shippingCost || 0,
            },
          });
        }
      } catch {
        // Invalid saved cart, ignore
      }
    }
  }, []);

  // Save cart to localStorage on changes
  useEffect(() => {
    localStorage.setItem('aquapurite_cart', JSON.stringify({
      items: state.items,
      deliveryPincode: state.deliveryPincode,
      isServiceable: state.isServiceable,
      estimatedDelivery: state.estimatedDelivery,
      shippingCost: state.shippingCost,
    }));
  }, [state.items, state.deliveryPincode, state.isServiceable, state.estimatedDelivery, state.shippingCost]);

  const addItem = (item: Omit<CartItem, 'quantity'> & { quantity?: number }) => {
    dispatch({ type: 'ADD_ITEM', payload: { ...item, quantity: item.quantity || 1 } });
  };

  const removeItem = (id: string) => {
    dispatch({ type: 'REMOVE_ITEM', payload: id });
  };

  const updateQuantity = (id: string, quantity: number) => {
    dispatch({ type: 'UPDATE_QUANTITY', payload: { id, quantity } });
  };

  const clearCart = () => {
    dispatch({ type: 'CLEAR_CART' });
  };

  const setDelivery = (pincode: string, isServiceable: boolean, estimatedDelivery: string, shippingCost: number) => {
    dispatch({ type: 'SET_DELIVERY', payload: { pincode, isServiceable, estimatedDelivery, shippingCost } });
  };

  return (
    <CartContext.Provider
      value={{
        ...state,
        addItem,
        removeItem,
        updateQuantity,
        clearCart,
        setDelivery,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
