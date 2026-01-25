import axios from 'axios';
import {
  StorefrontProduct,
  StorefrontCategory,
  StorefrontBrand,
  PaginatedResponse,
  ProductFilters,
  StockVerificationRequest,
  StockVerificationResponse,
  D2COrderRequest,
  D2COrderResponse,
  CompanyInfo,
} from '@/types/storefront';
import { useAuthStore, CustomerProfile, CustomerAddress } from './auth-store';

// Create a separate axios instance for storefront (no auth required)
const storefrontClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API base paths
const API_PATH = '/api/v1';
const STOREFRONT_PATH = '/api/v1/storefront';

// Products API - Uses public storefront endpoints
export const productsApi = {
  list: async (filters?: ProductFilters): Promise<PaginatedResponse<StorefrontProduct>> => {
    const params = new URLSearchParams();
    if (filters) {
      if (filters.category_id) params.append('category_id', filters.category_id);
      if (filters.brand_id) params.append('brand_id', filters.brand_id);
      if (filters.min_price) params.append('min_price', filters.min_price.toString());
      if (filters.max_price) params.append('max_price', filters.max_price.toString());
      if (filters.is_featured) params.append('is_featured', 'true');
      if (filters.is_bestseller) params.append('is_bestseller', 'true');
      if (filters.is_new_arrival) params.append('is_new_arrival', 'true');
      if (filters.search) params.append('search', filters.search);
      if (filters.sort_by) params.append('sort_by', filters.sort_by);
      if (filters.sort_order) params.append('sort_order', filters.sort_order);
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.size) params.append('size', filters.size.toString());
    }

    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products?${params.toString()}`);
    return data;
  },

  getBySlug: async (slug: string): Promise<StorefrontProduct> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products/${slug}`);
    return data;
  },

  getById: async (id: string): Promise<StorefrontProduct> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products/${id}`);
    return data;
  },

  getFeatured: async (limit = 8): Promise<StorefrontProduct[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products?is_featured=true&size=${limit}`);
    return data.items || [];
  },

  getBestsellers: async (limit = 8): Promise<StorefrontProduct[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products?is_bestseller=true&size=${limit}`);
    return data.items || [];
  },

  getNewArrivals: async (limit = 8): Promise<StorefrontProduct[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products?is_new_arrival=true&size=${limit}&sort_by=created_at&sort_order=desc`);
    return data.items || [];
  },

  getRelated: async (productId: string, categoryId?: string, limit = 4): Promise<StorefrontProduct[]> => {
    const params = new URLSearchParams();
    params.append('size', limit.toString());
    if (categoryId) params.append('category_id', categoryId);

    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products?${params.toString()}`);
    // Filter out the current product
    return (data.items || []).filter((p: StorefrontProduct) => p.id !== productId);
  },

  // Compare products - fetches full product details with specifications
  compare: async (productIds: string[]): Promise<{
    products: StorefrontProduct[];
    specifications: Record<string, string[]>;
    comparison_attributes: string[];
  }> => {
    if (productIds.length === 0) {
      return { products: [], specifications: {}, comparison_attributes: [] };
    }

    const params = new URLSearchParams();
    params.append('product_ids', productIds.join(','));

    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products/compare?${params.toString()}`);
      return data;
    } catch (error) {
      // Fallback: fetch products individually if compare endpoint not available
      const products = await Promise.all(
        productIds.map(async (id) => {
          try {
            const product = await productsApi.getById(id);
            return product;
          } catch {
            return null;
          }
        })
      );

      const validProducts = products.filter((p): p is StorefrontProduct => p !== null);

      // Extract all unique specification keys
      const allSpecs = new Set<string>();
      validProducts.forEach((p) => {
        p.specifications?.forEach((spec) => {
          allSpecs.add(spec.key);
        });
      });

      return {
        products: validProducts,
        specifications: {},
        comparison_attributes: Array.from(allSpecs),
      };
    }
  },
};

// Categories API - Uses public storefront endpoints
export const categoriesApi = {
  list: async (): Promise<StorefrontCategory[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/categories`);
    return data || [];
  },

  getTree: async (): Promise<StorefrontCategory[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/categories`);
    return data || [];
  },

  getBySlug: async (slug: string): Promise<StorefrontCategory> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/categories`);

    // Recursive function to search through category tree (including nested children)
    const findCategoryBySlug = (categories: StorefrontCategory[], targetSlug: string): StorefrontCategory | null => {
      for (const cat of categories) {
        if (cat.slug === targetSlug) {
          return cat;
        }
        // Search in children recursively
        if (cat.children && cat.children.length > 0) {
          const found = findCategoryBySlug(cat.children, targetSlug);
          if (found) return found;
        }
      }
      return null;
    };

    const category = findCategoryBySlug(data || [], slug);
    if (!category) throw new Error('Category not found');
    return category;
  },

  getById: async (id: string): Promise<StorefrontCategory> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/categories`);

    // Recursive function to search through category tree (including nested children)
    const findCategoryById = (categories: StorefrontCategory[], targetId: string): StorefrontCategory | null => {
      for (const cat of categories) {
        if (cat.id === targetId) {
          return cat;
        }
        // Search in children recursively
        if (cat.children && cat.children.length > 0) {
          const found = findCategoryById(cat.children, targetId);
          if (found) return found;
        }
      }
      return null;
    };

    const category = findCategoryById(data || [], id);
    if (!category) throw new Error('Category not found');
    return category;
  },

  getFeatured: async (): Promise<StorefrontCategory[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/categories`);
    return data || [];
  },
};

// Brands API - Uses public storefront endpoints
export const brandsApi = {
  list: async (): Promise<StorefrontBrand[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/brands`);
    return data || [];
  },

  getBySlug: async (slug: string): Promise<StorefrontBrand> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/brands`);
    const brand = (data || []).find((b: StorefrontBrand) => b.slug === slug);
    if (!brand) throw new Error('Brand not found');
    return brand;
  },

  getById: async (id: string): Promise<StorefrontBrand> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/brands`);
    const brand = (data || []).find((b: StorefrontBrand) => b.id === id);
    if (!brand) throw new Error('Brand not found');
    return brand;
  },
};

// Search API types
export interface SearchProductSuggestion {
  id: string;
  name: string;
  slug: string;
  image_url?: string;
  price: number;
  mrp: number;
}

export interface SearchCategorySuggestion {
  id: string;
  name: string;
  slug: string;
  image_url?: string;
  product_count: number;
}

export interface SearchBrandSuggestion {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
}

export interface SearchSuggestionsResponse {
  products: SearchProductSuggestion[];
  categories: SearchCategorySuggestion[];
  brands: SearchBrandSuggestion[];
  query: string;
}

// Inventory API
export const inventoryApi = {
  verifyStock: async (request: StockVerificationRequest): Promise<StockVerificationResponse> => {
    try {
      const { data } = await storefrontClient.post(`${API_PATH}/inventory/verify-stock`, request);
      return data;
    } catch {
      // Return default response if endpoint doesn't exist
      return {
        product_id: request.product_id,
        in_stock: true,
        available_quantity: 100,
        requested_quantity: request.quantity,
        message: 'Stock available',
      };
    }
  },

  verifyStockBulk: async (requests: StockVerificationRequest[]): Promise<StockVerificationResponse[]> => {
    try {
      const { data } = await storefrontClient.post(`${API_PATH}/inventory/verify-stock-bulk`, { items: requests });
      return data;
    } catch {
      // Return default responses if endpoint doesn't exist
      return requests.map(req => ({
        product_id: req.product_id,
        in_stock: true,
        available_quantity: 100,
        requested_quantity: req.quantity,
        message: 'Stock available',
      }));
    }
  },

  checkDelivery: async (pincode: string): Promise<{
    serviceable: boolean;
    estimate_days?: number;
    message?: string;
    cod_available?: boolean;
    shipping_cost?: number;
    zone?: string;
    city?: string;
    state?: string;
  }> => {
    // Use edge-based serviceability for instant response (<10ms)
    // Falls back to API only when edge data unavailable
    const { checkServiceability, checkServiceabilityWithFallback } = await import('./serviceability-store');

    // First try instant lookup from edge/localStorage
    const edgeResult = checkServiceability(pincode);

    if (edgeResult.serviceable) {
      return {
        serviceable: true,
        estimate_days: edgeResult.estimated_days || undefined,
        message: `Delivery available in ${edgeResult.estimated_days || 3-5} days`,
        cod_available: edgeResult.cod_available,
        shipping_cost: edgeResult.shipping_cost,
        zone: edgeResult.zone || undefined,
        city: edgeResult.city || undefined,
        state: edgeResult.state || undefined,
      };
    }

    // For non-cached pincodes, try API fallback
    try {
      const apiResult = await checkServiceabilityWithFallback(pincode);
      if (apiResult.serviceable) {
        return {
          serviceable: true,
          estimate_days: apiResult.estimated_days || undefined,
          message: `Delivery available in ${apiResult.estimated_days || 3-5} days`,
          cod_available: apiResult.cod_available,
          shipping_cost: apiResult.shipping_cost,
          zone: apiResult.zone || undefined,
          city: apiResult.city || undefined,
          state: apiResult.state || undefined,
        };
      }
    } catch {
      // Fallback failed, continue with not serviceable
    }

    return {
      serviceable: false,
      message: 'Delivery not available for this pincode',
    };
  },
};

// Orders API
export const ordersApi = {
  createD2C: async (order: D2COrderRequest): Promise<D2COrderResponse> => {
    const { data } = await storefrontClient.post(`${API_PATH}/orders/d2c`, order);
    return data;
  },

  getByNumber: async (orderNumber: string, phone: string): Promise<D2COrderResponse> => {
    const { data } = await storefrontClient.get(`${API_PATH}/orders/track?order_number=${orderNumber}&phone=${phone}`);
    return data;
  },
};

// Payments API - Razorpay integration
export interface CreatePaymentOrderRequest {
  order_id: string;
  amount: number;
  customer_name: string;
  customer_email?: string;
  customer_phone: string;
  notes?: Record<string, string>;
}

export interface PaymentOrderResponse {
  razorpay_order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  order_id: string;
  customer_name: string;
  customer_email?: string;
  customer_phone: string;
}

export interface VerifyPaymentRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
  order_id: string;
}

export const paymentsApi = {
  createOrder: async (request: CreatePaymentOrderRequest): Promise<PaymentOrderResponse> => {
    const { data } = await storefrontClient.post(`${API_PATH}/payments/create-order`, request);
    return data;
  },

  verifyPayment: async (request: VerifyPaymentRequest): Promise<{ verified: boolean; message: string }> => {
    const { data } = await storefrontClient.post(`${API_PATH}/payments/verify`, request);
    return data;
  },
};

// Search API - Uses public storefront endpoints
export const searchApi = {
  products: async (query: string, limit = 10): Promise<StorefrontProduct[]> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products?search=${encodeURIComponent(query)}&size=${limit}`);
    return data.items || [];
  },

  suggestions: async (query: string): Promise<string[]> => {
    try {
      // Use products endpoint with search for suggestions
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/products?search=${encodeURIComponent(query)}&size=5`);
      return (data.items || []).map((p: StorefrontProduct) => p.name);
    } catch {
      return [];
    }
  },

  getSuggestions: async (query: string, limit = 6): Promise<SearchSuggestionsResponse> => {
    if (!query || query.length < 2) {
      return { products: [], categories: [], brands: [], query };
    }
    const { data } = await storefrontClient.get(
      `${STOREFRONT_PATH}/search/suggestions?q=${encodeURIComponent(query)}&limit=${limit}`
    );
    return data;
  },
};

// Company API (public info from ERP)
export const companyApi = {
  getInfo: async (): Promise<CompanyInfo> => {
    try {
      const { data } = await storefrontClient.get(`${API_PATH}/storefront/company`);
      return data;
    } catch {
      // Return default company info if API fails
      return {
        name: 'AQUAPURITE',
        trade_name: 'AQUAPURITE',
        email: 'support@aquapurite.com',
        phone: '1800-123-4567',
        website: 'https://aquapurite.com',
        address: '123 Industrial Area, Sector 62',
        city: 'Noida',
        state: 'Uttar Pradesh',
        pincode: '201301',
      };
    }
  },
};

// Auth API - D2C customer authentication
export const authApi = {
  sendOTP: async (phone: string): Promise<{
    success: boolean;
    message: string;
    expires_in_seconds: number;
    resend_in_seconds: number;
  }> => {
    const { data } = await storefrontClient.post(`${API_PATH}/d2c/auth/send-otp`, { phone });
    return data;
  },

  verifyOTP: async (phone: string, otp: string): Promise<{
    success: boolean;
    message: string;
    access_token?: string;
    refresh_token?: string;
    customer?: CustomerProfile;
    is_new_customer: boolean;
  }> => {
    const { data } = await storefrontClient.post(`${API_PATH}/d2c/auth/verify-otp`, { phone, otp });
    return data;
  },

  refreshToken: async (refreshToken: string): Promise<{
    access_token: string;
    token_type: string;
  }> => {
    const { data } = await storefrontClient.post(
      `${API_PATH}/d2c/auth/refresh-token`,
      {},
      { headers: { Authorization: `Bearer ${refreshToken}` } }
    );
    return data;
  },

  getProfile: async (): Promise<CustomerProfile> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.get(`${API_PATH}/d2c/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  updateProfile: async (profile: { first_name?: string; last_name?: string; email?: string }): Promise<CustomerProfile> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.put(`${API_PATH}/d2c/auth/me`, profile, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  getAddresses: async (): Promise<CustomerAddress[]> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.get(`${API_PATH}/d2c/auth/addresses`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  addAddress: async (address: Omit<CustomerAddress, 'id'>): Promise<CustomerAddress> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.post(`${API_PATH}/d2c/auth/addresses`, address, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  deleteAddress: async (addressId: string): Promise<void> => {
    const token = useAuthStore.getState().accessToken;
    await storefrontClient.delete(`${API_PATH}/d2c/auth/addresses/${addressId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  updateAddress: async (addressId: string, address: Omit<CustomerAddress, 'id'>): Promise<CustomerAddress> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.put(`${API_PATH}/d2c/auth/addresses/${addressId}`, address, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  setDefaultAddress: async (addressId: string): Promise<CustomerAddress> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.put(`${API_PATH}/d2c/auth/addresses/${addressId}/default`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  // Wishlist
  getWishlist: async (): Promise<{
    items: Array<{
      id: string;
      product_id: string;
      product_name: string;
      product_slug: string;
      product_image?: string;
      product_price: number;
      product_mrp: number;
      variant_id?: string;
      variant_name?: string;
      price_when_added?: number;
      is_in_stock: boolean;
      price_dropped: boolean;
      created_at: string;
    }>;
    total: number;
  }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.get(`${API_PATH}/d2c/auth/wishlist`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  addToWishlist: async (productId: string, variantId?: string): Promise<{
    id: string;
    product_id: string;
    product_name: string;
    product_slug: string;
    product_image?: string;
    product_price: number;
    product_mrp: number;
    created_at: string;
  }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.post(`${API_PATH}/d2c/auth/wishlist`, {
      product_id: productId,
      variant_id: variantId,
    }, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  removeFromWishlist: async (productId: string): Promise<void> => {
    const token = useAuthStore.getState().accessToken;
    await storefrontClient.delete(`${API_PATH}/d2c/auth/wishlist/${productId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  checkWishlist: async (productId: string): Promise<{ in_wishlist: boolean }> => {
    const token = useAuthStore.getState().accessToken;
    if (!token) return { in_wishlist: false };
    const { data } = await storefrontClient.get(`${API_PATH}/d2c/auth/wishlist/check/${productId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  getOrders: async (page = 1, size = 10): Promise<{
    orders: Array<{
      id: string;
      order_number: string;
      status: string;
      total_amount: number;
      created_at: string;
      items_count: number;
    }>;
    total: number;
    page: number;
    size: number;
  }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.get(`${API_PATH}/d2c/auth/orders?page=${page}&size=${size}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  getOrderByNumber: async (orderNumber: string): Promise<{
    id: string;
    order_number: string;
    status: string;
    payment_status: string;
    payment_method: string;
    subtotal: number;
    tax_amount: number;
    shipping_amount: number;
    discount_amount: number;
    grand_total: number;
    created_at: string;
    shipped_at?: string;
    delivered_at?: string;
    shipping_address: {
      full_name: string;
      phone: string;
      email?: string;
      address_line1: string;
      address_line2?: string;
      city: string;
      state: string;
      pincode: string;
    };
    items: Array<{
      id: string;
      product_name: string;
      sku: string;
      quantity: number;
      unit_price: number;
      total_price: number;
    }>;
    tracking_number?: string;
    courier_name?: string;
  }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.get(`${API_PATH}/d2c/auth/orders/${orderNumber}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  logout: async (): Promise<void> => {
    const token = useAuthStore.getState().accessToken;
    try {
      await storefrontClient.post(`${API_PATH}/d2c/auth/logout`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // Ignore errors on logout
    }
  },
};

// Reviews API
export const reviewsApi = {
  getProductReviews: async (
    productId: string,
    page = 1,
    size = 10,
    sortBy: 'recent' | 'helpful' | 'rating_high' | 'rating_low' = 'recent',
    ratingFilter?: number
  ): Promise<{
    reviews: Array<{
      id: string;
      rating: number;
      title?: string;
      review_text?: string;
      is_verified_purchase: boolean;
      helpful_count: number;
      created_at: string;
      customer_name: string;
      admin_response?: string;
      admin_response_at?: string;
    }>;
    summary: {
      average_rating: number;
      total_reviews: number;
      rating_distribution: Record<string, number>;
      verified_purchase_count: number;
    };
    total: number;
    page: number;
    size: number;
  }> => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
      sort_by: sortBy,
    });
    if (ratingFilter) params.append('rating_filter', ratingFilter.toString());

    const { data } = await storefrontClient.get(
      `${API_PATH}/reviews/product/${productId}?${params.toString()}`
    );
    return data;
  },

  getReviewSummary: async (productId: string): Promise<{
    average_rating: number;
    total_reviews: number;
    rating_distribution: Record<string, number>;
    verified_purchase_count: number;
  }> => {
    const { data } = await storefrontClient.get(
      `${API_PATH}/reviews/product/${productId}/summary`
    );
    return data;
  },

  canReview: async (productId: string): Promise<{
    can_review: boolean;
    reason?: string;
    is_verified_purchase: boolean;
  }> => {
    const token = useAuthStore.getState().accessToken;
    if (!token) {
      return { can_review: false, reason: 'Login required', is_verified_purchase: false };
    }
    const { data } = await storefrontClient.get(
      `${API_PATH}/reviews/can-review/${productId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data;
  },

  createReview: async (
    productId: string,
    rating: number,
    title?: string,
    reviewText?: string
  ): Promise<{
    id: string;
    rating: number;
    title?: string;
    review_text?: string;
  }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.post(
      `${API_PATH}/reviews`,
      { product_id: productId, rating, title, review_text: reviewText },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data;
  },

  voteHelpful: async (reviewId: string, isHelpful: boolean): Promise<void> => {
    const token = useAuthStore.getState().accessToken;
    await storefrontClient.post(
      `${API_PATH}/reviews/${reviewId}/helpful`,
      { is_helpful: isHelpful },
      { headers: { Authorization: `Bearer ${token}` } }
    );
  },
};

// Coupons API
export interface CouponValidationRequest {
  code: string;
  cart_total: number;
  cart_items: number;
  product_ids?: string[];
  category_ids?: string[];
}

export interface CouponValidationResponse {
  valid: boolean;
  code: string;
  discount_type?: 'PERCENTAGE' | 'FIXED_AMOUNT' | 'FREE_SHIPPING';
  discount_value?: number;
  discount_amount?: number;
  message: string;
  name?: string;
  description?: string;
  minimum_order_amount?: number;
}

export interface ActiveCoupon {
  code: string;
  name: string;
  description?: string;
  discount_type: 'PERCENTAGE' | 'FIXED_AMOUNT' | 'FREE_SHIPPING';
  discount_value: number;
  minimum_order_amount?: number;
  max_discount_amount?: number;
  valid_until?: string;
  first_order_only: boolean;
}

export const couponsApi = {
  validate: async (request: CouponValidationRequest): Promise<CouponValidationResponse> => {
    const token = useAuthStore.getState().accessToken;
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const { data } = await storefrontClient.post(
      `${API_PATH}/coupons/validate`,
      request,
      { headers }
    );
    return data;
  },

  getActive: async (): Promise<ActiveCoupon[]> => {
    const token = useAuthStore.getState().accessToken;
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const { data } = await storefrontClient.get(`${API_PATH}/coupons/active`, { headers });
    return data;
  },
};

// Returns API
export interface ReturnItemRequest {
  order_item_id: string;
  quantity_returned: number;
  condition: 'UNOPENED' | 'OPENED_UNUSED' | 'USED' | 'DAMAGED' | 'DEFECTIVE';
  condition_notes?: string;
  customer_images?: string[];
}

export interface ReturnRequest {
  order_number: string;
  phone: string;
  return_reason: 'DAMAGED' | 'DEFECTIVE' | 'WRONG_ITEM' | 'NOT_AS_DESCRIBED' | 'CHANGED_MIND' | 'SIZE_FIT_ISSUE' | 'QUALITY_ISSUE' | 'OTHER';
  return_reason_details?: string;
  items: ReturnItemRequest[];
  pickup_address?: {
    full_name: string;
    phone: string;
    address_line1: string;
    address_line2?: string;
    city: string;
    state: string;
    pincode: string;
    country?: string;
  };
}

export interface ReturnItem {
  id: string;
  order_item_id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity_ordered: number;
  quantity_returned: number;
  condition: string;
  condition_notes?: string;
  inspection_result?: string;
  inspection_notes?: string;
  accepted_quantity?: number;
  unit_price: number;
  total_amount: number;
  refund_amount: number;
  serial_number?: string;
  customer_images?: string[];
}

export interface ReturnStatusHistory {
  id: string;
  from_status?: string;
  to_status: string;
  notes?: string;
  created_at: string;
}

export interface ReturnStatus {
  rma_number: string;
  status: string;
  status_message: string;
  requested_at: string;
  estimated_refund_date?: string;
  refund_amount?: number;
  refund_status?: string;
  tracking_number?: string;
  courier?: string;
  items: ReturnItem[];
  timeline: ReturnStatusHistory[];
}

export interface ReturnListItem {
  id: string;
  rma_number: string;
  order_id: string;
  order_number?: string;
  return_type: string;
  return_reason: string;
  status: string;
  status_message: string;
  requested_at: string;
  total_return_amount: number;
  net_refund_amount: number;
  items_count: number;
}

export const returnsApi = {
  requestReturn: async (request: ReturnRequest): Promise<ReturnStatus> => {
    const token = useAuthStore.getState().accessToken;
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const { data } = await storefrontClient.post(
      `${API_PATH}/returns/request`,
      request,
      { headers }
    );
    return data;
  },

  trackReturn: async (rmaNumber: string, phone: string): Promise<ReturnStatus> => {
    const { data } = await storefrontClient.get(
      `${API_PATH}/returns/track/${rmaNumber}?phone=${encodeURIComponent(phone)}`
    );
    return data;
  },

  getMyReturns: async (page = 1, size = 10): Promise<{
    items: ReturnListItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
  }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.get(
      `${API_PATH}/returns/my-returns?page=${page}&size=${size}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data;
  },

  cancelReturn: async (rmaNumber: string): Promise<{ message: string; rma_number: string }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.post(
      `${API_PATH}/returns/${rmaNumber}/cancel`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data;
  },
};

// Export all APIs
// Order Tracking API
export interface TimelineEvent {
  event_type: 'ORDER' | 'PAYMENT' | 'SHIPMENT' | 'DELIVERY' | 'RETURN';
  status: string;
  title: string;
  description?: string;
  timestamp: string;
  location?: string;
  metadata?: Record<string, any>;
}

export interface ShipmentInfo {
  shipment_id: string;
  tracking_number?: string;
  courier_name?: string;
  status: string;
  status_message: string;
  shipped_at?: string;
  estimated_delivery?: string;
  delivered_at?: string;
  current_location?: string;
  tracking_url?: string;
  tracking_events: Array<{
    status: string;
    message: string;
    location?: string;
    remarks?: string;
    timestamp?: string;
  }>;
}

export interface OrderTrackingResponse {
  order_number: string;
  order_id: string;
  status: string;
  status_message: string;
  payment_status: string;
  payment_method: string;
  placed_at: string;
  confirmed_at?: string;
  shipped_at?: string;
  delivered_at?: string;
  cancelled_at?: string;
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  total_amount: number;
  amount_paid: number;
  shipping_address: Record<string, any>;
  items: Array<{
    id: string;
    product_id: string;
    product_name: string;
    sku: string;
    quantity: number;
    unit_price: number;
    total_price: number;
  }>;
  timeline: TimelineEvent[];
  shipments: ShipmentInfo[];
  active_return?: {
    rma_number: string;
    status: string;
    requested_at: string;
    refund_amount: number;
  };
  can_cancel: boolean;
  can_return: boolean;
}

export const orderTrackingApi = {
  trackPublic: async (orderNumber: string, phone: string): Promise<OrderTrackingResponse> => {
    const { data } = await storefrontClient.get(
      `${API_PATH}/order-tracking/track/${orderNumber}?phone=${encodeURIComponent(phone)}`
    );
    return data;
  },

  trackMyOrder: async (orderNumber: string): Promise<OrderTrackingResponse> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.get(
      `${API_PATH}/order-tracking/my-order/${orderNumber}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data;
  },

  downloadInvoice: async (orderNumber: string): Promise<Blob> => {
    const token = useAuthStore.getState().accessToken;
    const response = await storefrontClient.get(
      `${API_PATH}/orders/${orderNumber}/invoice`,
      {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      }
    );
    return response.data;
  },

  reorder: async (orderNumber: string): Promise<{ items_added: number; message: string }> => {
    const token = useAuthStore.getState().accessToken;
    const { data } = await storefrontClient.post(
      `${API_PATH}/orders/${orderNumber}/reorder`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return data;
  },
};

// Abandoned Cart API
export interface CartItemSync {
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  price: number;
  variant_id?: string;
  variant_name?: string;
  image_url?: string;
}

export interface CartSyncRequest {
  session_id: string;
  items: CartItemSync[];
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  total_amount: number;
  coupon_code?: string;
  email?: string;
  phone?: string;
  customer_name?: string;
  checkout_step?: string;
  shipping_address?: Record<string, any>;
  selected_payment_method?: string;
  source?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  referrer_url?: string;
  user_agent?: string;
  device_type?: string;
  device_fingerprint?: string;
}

export interface CartSyncResponse {
  cart_id: string;
  session_id: string;
  status: string;
  items_count: number;
  total_amount: number;
  recovery_token?: string;
  message: string;
}

export interface RecoveredCartItem {
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  price: number;
  variant_id?: string;
  variant_name?: string;
  image_url?: string;
}

export interface RecoveredCartResponse {
  cart_id: string;
  items: RecoveredCartItem[];
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  total_amount: number;
  coupon_code?: string;
  shipping_address?: Record<string, any>;
  message: string;
}

export const abandonedCartApi = {
  sync: async (request: CartSyncRequest): Promise<CartSyncResponse> => {
    const token = useAuthStore.getState().accessToken;
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const { data } = await storefrontClient.post(
      `${API_PATH}/abandoned-cart/sync`,
      request,
      { headers }
    );
    return data;
  },

  recover: async (token: string): Promise<RecoveredCartResponse> => {
    const { data } = await storefrontClient.get(
      `${API_PATH}/abandoned-cart/recover/${token}`
    );
    return data;
  },

  markConverted: async (sessionId: string, orderId: string): Promise<void> => {
    const token = useAuthStore.getState().accessToken;
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    await storefrontClient.post(
      `${API_PATH}/abandoned-cart/mark-converted/${sessionId}?order_id=${orderId}`,
      {},
      { headers }
    );
  },
};

// Address Lookup API (Google Places + DigiPin)
export interface AddressSuggestion {
  place_id: string;
  description: string;
  main_text: string;
  secondary_text: string;
}

export interface AddressDetails {
  place_id?: string;
  formatted_address: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  latitude?: number;
  longitude?: number;
  digipin?: string;
}

export interface DigiPinInfo {
  digipin: string;
  latitude: number;
  longitude: number;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
}

export interface PincodeInfo {
  pincode: string;
  city?: string;
  state?: string;
  areas?: string[];
}

export const addressApi = {
  // Get address suggestions as user types
  autocomplete: async (query: string, sessionToken?: string): Promise<AddressSuggestion[]> => {
    if (query.length < 3) return [];
    const params = new URLSearchParams({ query });
    if (sessionToken) params.append('session_token', sessionToken);

    try {
      const { data } = await storefrontClient.get(`${API_PATH}/address/autocomplete?${params.toString()}`);
      return data.suggestions || [];
    } catch {
      return [];
    }
  },

  // Get full address details from place ID
  getPlaceDetails: async (placeId: string, sessionToken?: string): Promise<AddressDetails | null> => {
    const params = new URLSearchParams();
    if (sessionToken) params.append('session_token', sessionToken);

    try {
      const { data } = await storefrontClient.get(
        `${API_PATH}/address/place/${placeId}${params.toString() ? '?' + params.toString() : ''}`
      );
      return data;
    } catch {
      return null;
    }
  },

  // Get address from DigiPin code
  lookupDigiPin: async (digipin: string): Promise<DigiPinInfo | null> => {
    try {
      const { data } = await storefrontClient.get(`${API_PATH}/address/digipin/${digipin}`);
      return data;
    } catch {
      return null;
    }
  },

  // Get address from coordinates (for "Use my location")
  reverseGeocode: async (latitude: number, longitude: number): Promise<AddressDetails | null> => {
    try {
      const { data } = await storefrontClient.get(
        `${API_PATH}/address/reverse-geocode?latitude=${latitude}&longitude=${longitude}`
      );
      return data;
    } catch {
      return null;
    }
  },

  // Get city/state from pincode
  lookupPincode: async (pincode: string): Promise<PincodeInfo | null> => {
    if (!/^\d{6}$/.test(pincode)) return null;
    try {
      const { data } = await storefrontClient.get(`${API_PATH}/address/pincode/${pincode}`);
      return data;
    } catch {
      return null;
    }
  },

  // Generate DigiPin from coordinates
  encodeDigiPin: async (latitude: number, longitude: number): Promise<DigiPinInfo | null> => {
    try {
      const { data } = await storefrontClient.post(`${API_PATH}/address/encode-digipin`, {
        latitude,
        longitude,
      });
      return data;
    } catch {
      return null;
    }
  },
};

// CMS Content API - Public storefront content
export interface StorefrontBanner {
  id: string;
  title: string;
  subtitle?: string;
  image_url: string;
  mobile_image_url?: string;
  cta_text?: string;
  cta_link?: string;
  text_position: 'left' | 'center' | 'right';
  text_color: 'white' | 'dark';
}

export interface StorefrontUsp {
  id: string;
  title: string;
  description?: string;
  icon: string;
  icon_color?: string;
  link_url?: string;
  link_text?: string;
}

export interface StorefrontTestimonial {
  id: string;
  customer_name: string;
  customer_location?: string;
  customer_avatar_url?: string;
  customer_designation?: string;
  rating: number;
  content: string;
  title?: string;
  product_name?: string;
}

export interface StorefrontAnnouncement {
  id: string;
  text: string;
  link_url?: string;
  link_text?: string;
  announcement_type: 'INFO' | 'WARNING' | 'PROMO' | 'SUCCESS';
  background_color?: string;
  text_color?: string;
  is_dismissible: boolean;
}

export interface StorefrontPage {
  id: string;
  title: string;
  slug: string;
  content?: string;
  meta_title?: string;
  meta_description?: string;
  og_image_url?: string;
}

export interface FooterPage {
  id: string;
  title: string;
  slug: string;
}

export interface StorefrontMenuItem {
  id: string;
  menu_location: 'header' | 'footer_quick' | 'footer_service';
  title: string;
  url: string;
  icon?: string;
  target: '_self' | '_blank';
  children?: StorefrontMenuItem[];
}

export interface StorefrontFeatureBar {
  id: string;
  icon: string;
  title: string;
  subtitle?: string;
}

export interface StorefrontSettings {
  [key: string]: string | undefined;
}

// Mega Menu Types (CMS-managed navigation)
export interface StorefrontMegaMenuSubcategory {
  id: string;
  name: string;
  slug: string;
  image_url?: string;
  product_count: number;
}

export interface StorefrontMegaMenuItem {
  id: string;
  title: string;
  icon?: string;
  image_url?: string;
  menu_type: 'CATEGORY' | 'CUSTOM_LINK';
  url?: string;
  target: '_self' | '_blank';
  is_highlighted: boolean;
  highlight_text?: string;
  category_slug?: string;
  subcategories: StorefrontMegaMenuSubcategory[];
}

export const contentApi = {
  getBanners: async (): Promise<StorefrontBanner[]> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/banners`);
      return data || [];
    } catch {
      return [];
    }
  },

  getUsps: async (): Promise<StorefrontUsp[]> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/usps`);
      return data || [];
    } catch {
      return [];
    }
  },

  getTestimonials: async (): Promise<StorefrontTestimonial[]> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/testimonials`);
      return data || [];
    } catch {
      return [];
    }
  },

  getActiveAnnouncement: async (): Promise<StorefrontAnnouncement | null> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/announcements/active`);
      return data || null;
    } catch {
      return null;
    }
  },

  getPage: async (slug: string): Promise<StorefrontPage | null> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/pages/${slug}`);
      return data || null;
    } catch {
      return null;
    }
  },

  getFooterPages: async (): Promise<FooterPage[]> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/footer-pages`);
      return data || [];
    } catch {
      return [];
    }
  },

  getSettings: async (group?: string): Promise<StorefrontSettings> => {
    try {
      const params = group ? `?group=${group}` : '';
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/settings${params}`);
      return data || {};
    } catch {
      return {};
    }
  },

  getMenuItems: async (location?: string): Promise<StorefrontMenuItem[]> => {
    try {
      const params = location ? `?location=${location}` : '';
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/menu-items${params}`);
      return data || [];
    } catch {
      return [];
    }
  },

  getFeatureBars: async (): Promise<StorefrontFeatureBar[]> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/feature-bars`);
      return data || [];
    } catch {
      return [];
    }
  },

  getMegaMenu: async (): Promise<StorefrontMegaMenuItem[]> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/mega-menu`);
      return data || [];
    } catch {
      return [];
    }
  },
};

// Homepage Composite API - Single request for all homepage data
// Uses types from @/types/storefront for products, categories, brands
// Uses local CMS types for banners, usps, testimonials
export interface HomepageData {
  categories: import('@/types/storefront').StorefrontCategory[];
  featured_products: import('@/types/storefront').StorefrontProduct[];
  bestseller_products: import('@/types/storefront').StorefrontProduct[];
  new_arrivals: import('@/types/storefront').StorefrontProduct[];
  banners: StorefrontBanner[];
  brands: import('@/types/storefront').StorefrontBrand[];
  usps: StorefrontUsp[];
  testimonials: StorefrontTestimonial[];
}

export const homepageApi = {
  getData: async (): Promise<HomepageData> => {
    try {
      const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/homepage`);
      return data;
    } catch {
      // Return empty data on error
      return {
        categories: [],
        featured_products: [],
        bestseller_products: [],
        new_arrivals: [],
        banners: [],
        brands: [],
        usps: [],
        testimonials: [],
      };
    }
  },
};

export const storefrontApi = {
  products: productsApi,
  categories: categoriesApi,
  brands: brandsApi,
  inventory: inventoryApi,
  orders: ordersApi,
  payments: paymentsApi,
  search: searchApi,
  company: companyApi,
  auth: authApi,
  reviews: reviewsApi,
  coupons: couponsApi,
  returns: returnsApi,
  orderTracking: orderTrackingApi,
  abandonedCart: abandonedCartApi,
  address: addressApi,
  content: contentApi,
  homepage: homepageApi,
};

export default storefrontApi;
