export type Product = {
  id: string;
  name: string;
  category: string;
  base_price: number; // minor units, BDT
  currency: string;
  description: string;
  emoji: string;
  rating: number;
  stock: number;
  colors?: string[];
  sizes?: string[];
  storages?: string[];
  rams?: string[];
};

export const FALLBACK_PRODUCTS: Product[] = [
  { id: "tshirt-classic", name: "Classic Cotton T-Shirt", category: "Apparel", base_price: 129900, currency: "BDT", description: "100% breathable cotton, unisex fit.", emoji: "👕", rating: 4.6, stock: 120, colors: ["Black", "White", "Navy", "Olive"], sizes: ["S", "M", "L", "XL", "XXL"] },
  { id: "shirt-oxford", name: "Premium Oxford Shirt", category: "Apparel", base_price: 249900, currency: "BDT", description: "Wrinkle-resistant oxford, slim fit.", emoji: "👔", rating: 4.8, stock: 80, colors: ["White", "Light Blue", "Pink", "Charcoal"], sizes: ["S", "M", "L", "XL", "XXL"] },
  { id: "mobile-nova", name: "Nova X5 Smartphone", category: "Electronics", base_price: 3499900, currency: "BDT", description: '6.7" AMOLED 120Hz, 50MP OIS, 5000mAh, 5G.', emoji: "📱", rating: 4.7, stock: 35, colors: ["Midnight Black", "Ocean Blue", "Pearl White"], storages: ["128GB", "256GB (+৳4,000)", "512GB (+৳8,000)"] },
  { id: "laptop-ultrabook", name: "AeroBook Ultra 14 Laptop", category: "Electronics", base_price: 12999900, currency: "BDT", description: '14" 2.8K OLED, 16GB RAM, 512GB SSD.', emoji: "💻", rating: 4.9, stock: 18, colors: ["Silver", "Space Grey"], storages: ["512GB", "1TB (+৳12,000)"], rams: ["16GB", "32GB (+৳10,000)"] },
];

const SURCHARGE: Record<string, number> = {
  "256GB (+৳4,000)": 400000,
  "512GB (+৳8,000)": 800000,
  "256GB (+৳3,500)": 350000,
  "1TB (+৳12,000)": 1200000,
  "32GB (+৳10,000)": 1000000,
  XXL: 20000,
  "36": 15000,
};

export function unitPrice(p: Product, opts: { size?: string; storage?: string; ram?: string }): number {
  return p.base_price + (SURCHARGE[opts.size || ""] || 0) + (SURCHARGE[opts.storage || ""] || 0) + (SURCHARGE[opts.ram || ""] || 0);
}
