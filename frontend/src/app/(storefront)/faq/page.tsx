'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ChevronDown, HelpCircle, Package, Truck, CreditCard, RotateCcw, Shield, Phone } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQCategory {
  title: string;
  icon: React.ReactNode;
  items: FAQItem[];
}

const faqCategories: FAQCategory[] = [
  {
    title: 'Orders & Shopping',
    icon: <Package className="h-5 w-5" />,
    items: [
      {
        question: 'How do I place an order?',
        answer: 'Browse our products, add items to your cart, and proceed to checkout. You can pay using various payment methods including UPI, Credit/Debit cards, Net Banking, and Cash on Delivery (where available).',
      },
      {
        question: 'Can I modify or cancel my order?',
        answer: 'You can modify or cancel your order within 1 hour of placing it, provided it has not been shipped. Contact our customer support or use the "Cancel Order" option in your account.',
      },
      {
        question: 'How can I track my order?',
        answer: 'Once your order is shipped, you will receive an email/SMS with a tracking link. You can also track your order from "My Orders" section in your account.',
      },
      {
        question: 'What if I receive a damaged or wrong product?',
        answer: 'Please contact us within 48 hours of delivery with photos of the damaged/wrong product. We will arrange for a replacement or refund.',
      },
    ],
  },
  {
    title: 'Shipping & Delivery',
    icon: <Truck className="h-5 w-5" />,
    items: [
      {
        question: 'What are the delivery charges?',
        answer: 'We offer FREE delivery on all orders above ₹999. For orders below ₹999, a nominal delivery charge of ₹49-99 may apply depending on your location.',
      },
      {
        question: 'How long does delivery take?',
        answer: 'Standard delivery takes 3-7 business days depending on your location. Metro cities typically receive orders within 3-4 days, while remote areas may take up to 7 days.',
      },
      {
        question: 'Do you deliver to my area?',
        answer: 'We deliver to most serviceable pincodes across India. Enter your pincode on the product page to check delivery availability and estimated delivery time.',
      },
      {
        question: 'Can I schedule my delivery?',
        answer: 'Currently, we do not offer scheduled delivery. However, you can coordinate with our delivery partner once you receive the tracking details.',
      },
    ],
  },
  {
    title: 'Payment',
    icon: <CreditCard className="h-5 w-5" />,
    items: [
      {
        question: 'What payment methods do you accept?',
        answer: 'We accept UPI (Google Pay, PhonePe, Paytm), Credit Cards, Debit Cards, Net Banking, Wallets, and Cash on Delivery (COD) where available.',
      },
      {
        question: 'Is it safe to use my card on your website?',
        answer: 'Absolutely! Our payment gateway is PCI-DSS compliant and uses 256-bit SSL encryption. We do not store your card details.',
      },
      {
        question: 'Why was my payment declined?',
        answer: 'Payments may be declined due to incorrect card details, insufficient funds, bank security checks, or technical issues. Please try again or use a different payment method.',
      },
      {
        question: 'When will I receive my refund?',
        answer: 'Refunds are processed within 5-7 business days. The amount will be credited to your original payment method. COD refunds are processed via bank transfer.',
      },
    ],
  },
  {
    title: 'Returns & Refunds',
    icon: <RotateCcw className="h-5 w-5" />,
    items: [
      {
        question: 'What is your return policy?',
        answer: 'We offer a 7-day return policy for most products. Items must be unused, in original packaging, with all tags intact. Some products like filters and consumables are non-returnable.',
      },
      {
        question: 'How do I initiate a return?',
        answer: 'Go to "My Orders" in your account, select the order, and click "Return". Choose the reason and schedule a pickup. Our team will collect the item from your doorstep.',
      },
      {
        question: 'Can I exchange a product?',
        answer: 'Yes, you can exchange products within 7 days of delivery. Initiate a return and place a new order for the desired product.',
      },
      {
        question: 'Are there any non-returnable items?',
        answer: 'Yes, filters, membranes, UV lamps, and other consumables are non-returnable due to hygiene reasons. Damaged products during shipping are exceptions.',
      },
    ],
  },
  {
    title: 'Product & Installation',
    icon: <Shield className="h-5 w-5" />,
    items: [
      {
        question: 'Do you provide installation services?',
        answer: 'Yes, we provide FREE installation for all water purifiers. Our certified technician will contact you within 24-48 hours of delivery to schedule the installation.',
      },
      {
        question: 'What is covered under warranty?',
        answer: 'Our products come with 1-year standard warranty covering manufacturing defects. Extended warranty and AMC plans are available for additional coverage.',
      },
      {
        question: 'How do I claim warranty?',
        answer: 'Contact our service center with your order details and product serial number. Our technician will diagnose the issue and provide service under warranty if applicable.',
      },
      {
        question: 'How often should I change filters?',
        answer: 'Filter replacement depends on usage and water quality. Generally, sediment filters need replacement every 3-6 months, carbon filters every 6-12 months, and RO membranes every 2-3 years.',
      },
    ],
  },
  {
    title: 'Account & Support',
    icon: <Phone className="h-5 w-5" />,
    items: [
      {
        question: 'How do I create an account?',
        answer: 'Click on "Login" and enter your mobile number. You will receive an OTP to verify your number. That\'s it - your account is created!',
      },
      {
        question: 'How can I contact customer support?',
        answer: 'You can reach us via: Email: support@aquapurite.com, Phone: 1800-XXX-XXXX (Toll-free), or use the Contact form on our website.',
      },
      {
        question: 'What are your customer support hours?',
        answer: 'Our customer support is available Monday to Saturday, 9:00 AM to 6:00 PM IST. For urgent issues, you can email us anytime.',
      },
      {
        question: 'How do I update my account details?',
        answer: 'Login to your account and go to "Profile" to update your name and email. To change your phone number, use the "Change Phone" option which requires OTP verification.',
      },
    ],
  },
];

function FAQAccordion({ item, isOpen, onToggle }: { item: FAQItem; isOpen: boolean; onToggle: () => void }) {
  return (
    <div className="border-b last:border-b-0">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full py-4 text-left hover:text-primary transition-colors"
      >
        <span className="font-medium pr-4">{item.question}</span>
        <ChevronDown
          className={cn(
            'h-5 w-5 text-muted-foreground shrink-0 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>
      <div
        className={cn(
          'overflow-hidden transition-all duration-200',
          isOpen ? 'max-h-96 pb-4' : 'max-h-0'
        )}
      >
        <p className="text-muted-foreground">{item.answer}</p>
      </div>
    </div>
  );
}

export default function FAQPage() {
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({});

  const toggleItem = (categoryIndex: number, itemIndex: number) => {
    const key = `${categoryIndex}-${itemIndex}`;
    setOpenItems((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
          <HelpCircle className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-3xl font-bold mb-4">Frequently Asked Questions</h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Find answers to common questions about our products, orders, shipping, and more.
          Can&apos;t find what you&apos;re looking for?{' '}
          <Link href="/contact" className="text-primary hover:underline">
            Contact us
          </Link>
        </p>
      </div>

      {/* FAQ Categories */}
      <div className="grid gap-6 md:grid-cols-2 max-w-5xl mx-auto">
        {faqCategories.map((category, categoryIndex) => (
          <Card key={categoryIndex}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="p-2 bg-primary/10 rounded-lg text-primary">
                  {category.icon}
                </span>
                {category.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="divide-y">
                {category.items.map((item, itemIndex) => (
                  <FAQAccordion
                    key={itemIndex}
                    item={item}
                    isOpen={openItems[`${categoryIndex}-${itemIndex}`] || false}
                    onToggle={() => toggleItem(categoryIndex, itemIndex)}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Contact CTA */}
      <div className="text-center mt-12 p-8 bg-muted rounded-lg max-w-2xl mx-auto">
        <h2 className="text-xl font-semibold mb-2">Still have questions?</h2>
        <p className="text-muted-foreground mb-4">
          Our customer support team is here to help you.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/contact"
            className="inline-flex items-center justify-center px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Contact Support
          </Link>
          <a
            href="tel:1800XXXXXXX"
            className="inline-flex items-center justify-center px-6 py-3 border rounded-lg hover:bg-muted/50 transition-colors"
          >
            <Phone className="h-4 w-4 mr-2" />
            1800-XXX-XXXX
          </a>
        </div>
      </div>
    </div>
  );
}
