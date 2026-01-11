'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ChevronDown, Search, HelpCircle, Package, Truck, CreditCard, Wrench, RefreshCw } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQCategory {
  id: string;
  title: string;
  icon: any;
  faqs: FAQItem[];
}

const faqCategories: FAQCategory[] = [
  {
    id: 'products',
    title: 'Products',
    icon: Package,
    faqs: [
      {
        question: 'What types of water purifiers do you offer?',
        answer: 'We offer a comprehensive range of water purifiers including RO (Reverse Osmosis), UV (Ultraviolet), UF (Ultrafiltration), and combination systems like RO+UV+UF. Each type is designed for different water quality conditions and purification needs.',
      },
      {
        question: 'How do I choose the right water purifier for my home?',
        answer: 'The right purifier depends on your water source (municipal, borewell, tanker) and TDS levels. For TDS above 500 ppm, RO purifiers are recommended. For TDS below 200 ppm, UV or UF purifiers work well. Our product pages include a PIN code checker to help you determine serviceability and recommendations based on your area.',
      },
      {
        question: 'Are all your products genuine and original?',
        answer: 'Yes, all our products are 100% genuine and sourced directly from manufacturers. We provide manufacturer warranty on all products, and you can verify authenticity through the serial numbers provided.',
      },
      {
        question: 'What is the warranty period on your products?',
        answer: 'Warranty periods vary by product. Most water purifiers come with 1-2 years manufacturer warranty on the machine and 6 months to 1 year on filters and consumables. Specific warranty details are mentioned on each product page.',
      },
    ],
  },
  {
    id: 'orders',
    title: 'Orders & Delivery',
    icon: Truck,
    faqs: [
      {
        question: 'How can I track my order?',
        answer: 'You can track your order by visiting our Track Order page and entering your order number along with the registered phone number. You\'ll also receive tracking updates via SMS and email.',
      },
      {
        question: 'What are the delivery charges?',
        answer: 'We offer FREE delivery on orders above ₹1,000. For orders below ₹1,000, a nominal shipping charge of ₹99 is applicable. Delivery charges may vary for remote locations.',
      },
      {
        question: 'How long does delivery take?',
        answer: 'Standard delivery takes 3-5 business days for most locations. Metro cities typically receive orders within 2-3 days. Remote areas may take 5-7 business days. You can check estimated delivery time by entering your PIN code.',
      },
      {
        question: 'Do you deliver to my area?',
        answer: 'We deliver to most PIN codes across India. You can check if we deliver to your area by entering your PIN code on the product page or cart page. If your area is not serviceable, please contact our support team for alternatives.',
      },
      {
        question: 'Can I change my delivery address after placing an order?',
        answer: 'Address changes can be made before the order is dispatched. Please contact our customer support immediately after placing the order. Once dispatched, address changes are not possible.',
      },
    ],
  },
  {
    id: 'payment',
    title: 'Payment',
    icon: CreditCard,
    faqs: [
      {
        question: 'What payment methods do you accept?',
        answer: 'We accept multiple payment methods including Credit/Debit Cards (Visa, Mastercard, RuPay), UPI (Google Pay, PhonePe, Paytm), Net Banking, and Cash on Delivery (COD). All online payments are 100% secure.',
      },
      {
        question: 'Is Cash on Delivery (COD) available?',
        answer: 'Yes, COD is available for most serviceable PIN codes. However, COD may not be available for certain high-value orders or specific locations. You can check COD availability during checkout.',
      },
      {
        question: 'Is it safe to pay online on your website?',
        answer: 'Absolutely! We use industry-standard SSL encryption and secure payment gateways. Your payment information is never stored on our servers. All transactions are processed through trusted payment partners.',
      },
      {
        question: 'Can I get a GST invoice?',
        answer: 'Yes, we provide GST invoices for all orders. If you need a GST invoice with your company details, please provide your GSTIN during checkout or contact support after placing the order.',
      },
    ],
  },
  {
    id: 'installation',
    title: 'Installation & Service',
    icon: Wrench,
    faqs: [
      {
        question: 'Do you provide installation services?',
        answer: 'Yes, we provide professional installation services for all water purifiers. Installation is free for most products and is scheduled within 48-72 hours of delivery in serviceable areas.',
      },
      {
        question: 'What is included in the installation service?',
        answer: 'Our installation service includes standard installation with basic accessories, demonstration of usage and maintenance, and initial water quality check. Additional plumbing work or accessories may incur extra charges.',
      },
      {
        question: 'How often should I service my water purifier?',
        answer: 'We recommend servicing your water purifier every 3-6 months depending on usage and water quality. Filter changes are typically required every 6-12 months. Regular maintenance ensures optimal performance and water quality.',
      },
      {
        question: 'Do you offer AMC (Annual Maintenance Contract)?',
        answer: 'Yes, we offer comprehensive AMC plans that include regular servicing, filter replacements, and priority support. AMC plans help reduce long-term maintenance costs and ensure consistent water quality.',
      },
    ],
  },
  {
    id: 'returns',
    title: 'Returns & Refunds',
    icon: RefreshCw,
    faqs: [
      {
        question: 'What is your return policy?',
        answer: 'We offer a 7-day return policy for most products. Items must be unused, in original packaging, with all accessories and documentation. Some products like filters and consumables are non-returnable for hygiene reasons.',
      },
      {
        question: 'How do I initiate a return?',
        answer: 'To initiate a return, contact our customer support with your order number and reason for return. Once approved, we\'ll arrange for pickup. Ensure the product is in its original condition with all accessories.',
      },
      {
        question: 'How long does it take to get a refund?',
        answer: 'Refunds are processed within 5-7 business days after we receive and inspect the returned product. The amount will be credited to the original payment method. COD orders are refunded via bank transfer.',
      },
      {
        question: 'What if I receive a damaged or defective product?',
        answer: 'If you receive a damaged or defective product, please contact us within 24 hours of delivery with photos of the damage. We\'ll arrange for a free replacement or full refund based on your preference.',
      },
    ],
  },
];

function FAQAccordion({ faq, isOpen, onToggle }: { faq: FAQItem; isOpen: boolean; onToggle: () => void }) {
  return (
    <div className="border-b border-slate-700 last:border-0">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full py-4 text-left"
      >
        <span className="font-medium text-white pr-4">{faq.question}</span>
        <ChevronDown className={`w-5 h-5 text-amber-500 flex-shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="pb-4 text-slate-400 text-sm leading-relaxed">
          {faq.answer}
        </div>
      )}
    </div>
  );
}

export default function FAQPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('products');
  const [openFAQs, setOpenFAQs] = useState<{ [key: string]: boolean }>({});

  const toggleFAQ = (categoryId: string, index: number) => {
    const key = `${categoryId}-${index}`;
    setOpenFAQs(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const filteredCategories = searchQuery
    ? faqCategories.map(cat => ({
        ...cat,
        faqs: cat.faqs.filter(
          faq =>
            faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
            faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
        ),
      })).filter(cat => cat.faqs.length > 0)
    : faqCategories;

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-16 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900" />
        <div className="absolute top-10 left-10 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center">
            <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4">
              Help Center
            </Badge>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Frequently Asked{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                Questions
              </span>
            </h1>
            <p className="text-lg text-slate-300 mb-8">
              Find answers to common questions about our products, orders, delivery, and more.
            </p>

            {/* Search */}
            <div className="relative max-w-xl mx-auto">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <Input
                type="search"
                placeholder="Search for answers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-12 pr-4 h-12 bg-slate-800 border-slate-700 text-white placeholder:text-slate-400 focus:border-amber-500 focus:ring-amber-500/20"
              />
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Content */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          {searchQuery ? (
            // Search Results
            <div className="max-w-3xl mx-auto">
              {filteredCategories.length > 0 ? (
                <div className="space-y-8">
                  {filteredCategories.map(category => (
                    <div key={category.id}>
                      <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                        <category.icon className="w-5 h-5 text-amber-500" />
                        {category.title}
                      </h2>
                      <Card className="bg-slate-800/50 border-slate-700">
                        <CardContent className="p-6">
                          {category.faqs.map((faq, index) => (
                            <FAQAccordion
                              key={index}
                              faq={faq}
                              isOpen={openFAQs[`${category.id}-${index}`] || false}
                              onToggle={() => toggleFAQ(category.id, index)}
                            />
                          ))}
                        </CardContent>
                      </Card>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <HelpCircle className="w-16 h-16 mx-auto mb-4 text-slate-500" />
                  <h3 className="text-xl font-semibold text-white mb-2">No results found</h3>
                  <p className="text-slate-400 mb-4">
                    We couldn't find any FAQs matching "{searchQuery}"
                  </p>
                  <Link href="/contact" className="text-amber-500 hover:text-amber-400">
                    Contact our support team for help
                  </Link>
                </div>
              )}
            </div>
          ) : (
            // Category View
            <div className="grid lg:grid-cols-4 gap-8">
              {/* Category Sidebar */}
              <div className="lg:col-span-1">
                <Card className="bg-slate-800/50 border-slate-700 sticky top-24">
                  <CardContent className="p-4">
                    <h3 className="font-semibold text-white mb-4">Categories</h3>
                    <nav className="space-y-1">
                      {faqCategories.map(category => (
                        <button
                          key={category.id}
                          onClick={() => setActiveCategory(category.id)}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                            activeCategory === category.id
                              ? 'bg-amber-500/20 text-amber-500'
                              : 'text-slate-400 hover:text-white hover:bg-slate-700'
                          }`}
                        >
                          <category.icon className="w-4 h-4" />
                          <span className="text-sm font-medium">{category.title}</span>
                        </button>
                      ))}
                    </nav>
                  </CardContent>
                </Card>
              </div>

              {/* FAQ List */}
              <div className="lg:col-span-3">
                {faqCategories
                  .filter(cat => cat.id === activeCategory)
                  .map(category => (
                    <div key={category.id}>
                      <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
                          <category.icon className="w-5 h-5 text-amber-500" />
                        </div>
                        <h2 className="text-2xl font-bold text-white">{category.title}</h2>
                      </div>
                      <Card className="bg-slate-800/50 border-slate-700">
                        <CardContent className="p-6">
                          {category.faqs.map((faq, index) => (
                            <FAQAccordion
                              key={index}
                              faq={faq}
                              isOpen={openFAQs[`${category.id}-${index}`] || false}
                              onToggle={() => toggleFAQ(category.id, index)}
                            />
                          ))}
                        </CardContent>
                      </Card>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Still Need Help */}
      <section className="py-12 bg-slate-900/50">
        <div className="container mx-auto px-4">
          <Card className="bg-gradient-to-r from-amber-500/20 to-blue-500/20 border-amber-500/30">
            <CardContent className="p-8 text-center">
              <h2 className="text-2xl font-bold text-white mb-4">Still Have Questions?</h2>
              <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
                Can't find what you're looking for? Our support team is here to help you with any questions or concerns.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/contact" className="inline-flex items-center justify-center px-6 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold rounded-lg transition-colors">
                  Contact Support
                </Link>
                <Link href="/support" className="inline-flex items-center justify-center px-6 py-3 border border-slate-600 text-slate-300 hover:text-amber-500 hover:border-amber-500 font-semibold rounded-lg transition-colors">
                  Visit Help Center
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
