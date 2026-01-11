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
    const category = (data || []).find((c: StorefrontCategory) => c.slug === slug);
    if (!category) throw new Error('Category not found');
    return category;
  },

  getById: async (id: string): Promise<StorefrontCategory> => {
    const { data } = await storefrontClient.get(`${STOREFRONT_PATH}/categories`);
    const category = (data || []).find((c: StorefrontCategory) => c.id === id);
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
  }> => {
    try {
      const { data } = await storefrontClient.get(`${API_PATH}/serviceability/check/${pincode}`);
      return {
        serviceable: data.is_serviceable,
        estimate_days: data.estimated_delivery_days,
        message: data.message,
        cod_available: data.cod_available,
        shipping_cost: data.minimum_shipping_cost,
      };
    } catch {
      // Return not serviceable if API fails
      return {
        serviceable: false,
        message: 'Unable to check delivery. Please try again.',
      };
    }
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

// Export all APIs
export const storefrontApi = {
  products: productsApi,
  categories: categoriesApi,
  brands: brandsApi,
  inventory: inventoryApi,
  orders: ordersApi,
  search: searchApi,
  company: companyApi,
};

export default storefrontApi;
