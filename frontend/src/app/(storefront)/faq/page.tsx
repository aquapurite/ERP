'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { ChevronDown, HelpCircle, Package, Truck, CreditCard, RotateCcw, Shield, Phone, Search, Wrench, Award, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface FAQItem {
  question: string;
  answer: string;
  keywords?: string[];
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
        question: 'How do I place an order on Aquapurite?',
        answer: 'Placing an order is simple: Browse our water purifiers and spare parts, add items to your cart, and proceed to checkout. You can pay using UPI (Google Pay, PhonePe, Paytm), Credit/Debit cards, Net Banking, EMI options, or Cash on Delivery (COD) in select areas. You\'ll receive order confirmation via email and SMS.',
        keywords: ['order', 'buy', 'purchase', 'cart', 'checkout'],
      },
      {
        question: 'Can I modify or cancel my order after placing it?',
        answer: 'Yes, you can modify or cancel your order within 2 hours of placing it, provided it has not been shipped. Go to "My Orders" in your account and click "Cancel Order" or contact our support team at support@aquapurite.com. Once shipped, you can refuse delivery or initiate a return after receiving the product.',
        keywords: ['cancel', 'modify', 'change order', 'order cancellation'],
      },
      {
        question: 'How can I track my order status?',
        answer: 'Once your order is shipped, you\'ll receive tracking details via email and SMS. You can also track your order by: 1) Logging into your account and visiting "My Orders", 2) Using our Track Order page with your order number, or 3) Clicking the tracking link in your shipping notification. Real-time updates show when your package is out for delivery.',
        keywords: ['track', 'tracking', 'shipment', 'delivery status', 'where is my order'],
      },
      {
        question: 'What if I receive a damaged or wrong product?',
        answer: 'We\'re sorry if this happens! Please contact us within 48 hours of delivery with photos/videos of the damaged or incorrect product. Email support@aquapurite.com or call 1800-123-4567 with your order number. We\'ll arrange a free pickup and send the correct product or process a full refund within 5-7 business days.',
        keywords: ['damaged', 'wrong product', 'defective', 'broken'],
      },
      {
        question: 'Do you offer bulk orders or corporate purchases?',
        answer: 'Yes! We offer special pricing for bulk orders (5+ units) and corporate purchases. Contact our B2B team at corporate@aquapurite.com or call 1800-123-4567 for customized quotes, volume discounts, and dedicated account management. We serve offices, housing societies, hotels, and institutions.',
        keywords: ['bulk', 'corporate', 'wholesale', 'B2B', 'office'],
      },
    ],
  },
  {
    title: 'Shipping & Delivery',
    icon: <Truck className="h-5 w-5" />,
    items: [
      {
        question: 'What are the delivery charges for water purifiers?',
        answer: 'We offer FREE delivery on all water purifier orders across India. For spare parts and accessories, delivery is free on orders above ₹499. Orders below ₹499 have a nominal delivery charge of ₹49-79 depending on your location and package weight.',
        keywords: ['delivery charges', 'shipping cost', 'free delivery', 'shipping fees'],
      },
      {
        question: 'How long does delivery take?',
        answer: 'Delivery times vary by location: Metro cities (Delhi, Mumbai, Bangalore, etc.): 2-4 business days. Tier-2 cities: 4-6 business days. Remote/rural areas: 6-10 business days. Water purifiers are shipped via trusted logistics partners with real-time tracking. You\'ll receive estimated delivery date at checkout.',
        keywords: ['delivery time', 'shipping time', 'how long', 'when will I receive'],
      },
      {
        question: 'Do you deliver to my pincode/area?',
        answer: 'We deliver to 19,000+ pincodes across India. Enter your pincode on any product page to instantly check: delivery availability, estimated delivery date, and COD availability. If your pincode is not serviceable, try a nearby pincode or contact support for alternative options.',
        keywords: ['pincode', 'delivery area', 'serviceable', 'my location'],
      },
      {
        question: 'Can I choose a specific delivery date or time slot?',
        answer: 'Currently, we don\'t offer scheduled delivery slots at checkout. However, once shipped, you can coordinate with our delivery partner through the tracking link to request preferred delivery timing. For installation, our technician will contact you to schedule a convenient appointment.',
        keywords: ['schedule delivery', 'time slot', 'delivery date', 'preferred time'],
      },
      {
        question: 'What happens if I\'m not available during delivery?',
        answer: 'If you\'re unavailable, the delivery partner will attempt redelivery the next business day and contact you. After 3 failed attempts, the package returns to our warehouse. You can also authorize someone else to receive the delivery by providing their name and phone number via tracking page.',
        keywords: ['not available', 'missed delivery', 'redelivery', 'someone else receive'],
      },
    ],
  },
  {
    title: 'Payment & EMI',
    icon: <CreditCard className="h-5 w-5" />,
    items: [
      {
        question: 'What payment methods do you accept?',
        answer: 'We accept all major payment methods: UPI (Google Pay, PhonePe, Paytm, BHIM), Credit Cards (Visa, Mastercard, Amex, RuPay), Debit Cards, Net Banking (all major banks), Wallets (Paytm, Amazon Pay, Mobikwik), EMI (No-cost EMI on select banks), and Cash on Delivery (COD) in eligible areas.',
        keywords: ['payment methods', 'UPI', 'credit card', 'debit card', 'COD', 'cash on delivery'],
      },
      {
        question: 'Is it safe to pay online on your website?',
        answer: 'Absolutely! Your payments are 100% secure. We use Razorpay as our payment gateway, which is PCI-DSS Level 1 compliant (highest security certification). All transactions use 256-bit SSL encryption. We never store your complete card details on our servers.',
        keywords: ['safe payment', 'secure', 'payment security', 'SSL'],
      },
      {
        question: 'Do you offer No-Cost EMI options?',
        answer: 'Yes! We offer No-Cost EMI on water purifiers above ₹5,000. Available tenures: 3, 6, 9, and 12 months on select bank credit cards including HDFC, ICICI, SBI, Axis, Kotak, and more. The EMI amount is shown on product pages. No additional interest charges - you pay only the product price divided equally.',
        keywords: ['EMI', 'no cost EMI', 'installments', 'monthly payment'],
      },
      {
        question: 'Why was my payment declined?',
        answer: 'Payments may be declined due to: incorrect card details, insufficient balance, card limit exceeded, bank\'s fraud detection, 3D Secure/OTP timeout, or technical issues. Solutions: Double-check card details, try another card or payment method, contact your bank to authorize the transaction, or try after some time.',
        keywords: ['payment declined', 'payment failed', 'transaction failed'],
      },
      {
        question: 'When will I receive my refund?',
        answer: 'Refund timelines: UPI/Wallets: 1-3 business days, Debit/Credit Cards: 5-7 business days, Net Banking: 5-7 business days, EMI: 7-10 business days (processed as per bank policy), COD: Bank transfer within 7 business days after providing account details. You\'ll receive confirmation email when refund is processed.',
        keywords: ['refund', 'money back', 'refund time', 'when refund'],
      },
    ],
  },
  {
    title: 'Returns & Refunds',
    icon: <RotateCcw className="h-5 w-5" />,
    items: [
      {
        question: 'What is your return policy for water purifiers?',
        answer: 'We offer a 7-day return policy for water purifiers from the date of delivery. Conditions: Product must be unused and uninstalled, in original packaging with all accessories, tags, and manuals. Once installation is done, returns are only accepted for manufacturing defects (covered under warranty). Initiate returns from "My Orders" section.',
        keywords: ['return policy', 'return', '7 days', 'return period'],
      },
      {
        question: 'How do I initiate a return request?',
        answer: 'To return a product: 1) Log into your account, 2) Go to "My Orders" and select the order, 3) Click "Request Return" and choose a reason, 4) Upload photos if product is damaged, 5) Schedule pickup (free of charge), 6) Our team will collect the item within 2-3 business days. Refund is processed after quality check.',
        keywords: ['return request', 'how to return', 'initiate return'],
      },
      {
        question: 'Can I exchange my water purifier for a different model?',
        answer: 'Direct exchanges aren\'t available. For a different model: 1) Initiate a return for the current product (within 7 days, uninstalled), 2) Place a new order for the desired model. We recommend comparing models on our website or calling our experts at 1800-123-4567 before purchasing to choose the right purifier.',
        keywords: ['exchange', 'swap', 'different model', 'upgrade'],
      },
      {
        question: 'Which products cannot be returned?',
        answer: 'Non-returnable items include: Filters, membranes, and UV lamps (hygiene reasons), Installed water purifiers (warranty applies for defects), Products with broken seals or missing parts, Items damaged due to misuse or improper handling, Products purchased more than 7 days ago. Exception: Manufacturing defects are always covered.',
        keywords: ['non-returnable', 'cannot return', 'not eligible for return'],
      },
      {
        question: 'How long does the refund process take?',
        answer: 'After we receive and inspect your return: Quality check: 1-2 business days, Refund initiation: Within 24 hours of approval, Refund to your account: 5-7 business days (card/bank) or 1-3 days (UPI/wallet). Total time from pickup to refund: approximately 7-10 business days. Track refund status in "My Orders".',
        keywords: ['refund process', 'refund time', 'how long refund'],
      },
    ],
  },
  {
    title: 'Installation & Service',
    icon: <Wrench className="h-5 w-5" />,
    items: [
      {
        question: 'Is installation free with water purifier purchase?',
        answer: 'Yes! FREE professional installation is included with every water purifier purchase. Our certified technician will contact you within 24-48 hours of delivery to schedule installation at your convenience. Installation includes: mounting, connection to water source, electrical setup, water quality testing, and demonstration of product usage.',
        keywords: ['installation', 'free installation', 'setup', 'install'],
      },
      {
        question: 'How do I schedule or reschedule installation?',
        answer: 'After delivery, our technician will call you to schedule installation. To reschedule: Call our service helpline at 1800-123-4567, email service@aquapurite.com, or use the "Service Request" section in your account. Please reschedule at least 4 hours before the scheduled time. Installation is typically completed within 1-2 hours.',
        keywords: ['schedule installation', 'reschedule', 'installation appointment'],
      },
      {
        question: 'What do I need to prepare before installation?',
        answer: 'Before installation, please ensure: A water source (tap/pipeline) within 3 meters of installation spot, An electrical outlet within 3 meters (for electric purifiers), Clear wall space for mounting (60cm x 50cm minimum), Someone above 18 years present during installation. Our technician will bring all required installation hardware.',
        keywords: ['prepare installation', 'installation requirements', 'before installation'],
      },
      {
        question: 'How do I book a service or repair request?',
        answer: 'To book service: 1) Log into your account → "My Devices" → "Request Service", 2) Call 1800-123-4567 (toll-free), 3) WhatsApp us at +91-XXXXX-XXXXX, or 4) Email service@aquapurite.com. Provide your product serial number and describe the issue. A technician will visit within 24-48 hours in metro cities, 48-72 hours in other areas.',
        keywords: ['service request', 'repair', 'technician visit', 'book service'],
      },
      {
        question: 'How often should filters be replaced?',
        answer: 'Filter replacement schedule depends on usage and water quality: Sediment Filter: Every 3-6 months, Pre-Carbon Filter: Every 6-9 months, RO Membrane: Every 2-3 years, Post-Carbon Filter: Every 9-12 months, UV Lamp: Every 12 months (for UV models). Our purifiers have filter change indicators. Buy genuine replacement filters from our website.',
        keywords: ['filter replacement', 'change filter', 'how often filter', 'filter life'],
      },
    ],
  },
  {
    title: 'Warranty & AMC',
    icon: <Award className="h-5 w-5" />,
    items: [
      {
        question: 'What warranty do Aquapurite water purifiers come with?',
        answer: 'All Aquapurite water purifiers come with: 1-year comprehensive warranty covering manufacturing defects in motor, pump, and electrical components. 2-year warranty on RO membrane (select models). Warranty is valid from the date of installation. Register your product within 15 days of installation to activate warranty.',
        keywords: ['warranty', 'warranty period', 'what is covered', 'warranty duration'],
      },
      {
        question: 'What is covered under warranty?',
        answer: 'Warranty covers: Motor and pump failures, Electrical component defects, UV lamp failures (manufacturing defect), Solenoid valve issues, PCB/control panel defects. NOT covered: Filters and consumables (sediment, carbon, membrane), Physical damage or misuse, Damage due to voltage fluctuation (use stabilizer), Service at non-authorized centers.',
        keywords: ['warranty coverage', 'what is covered', 'warranty includes'],
      },
      {
        question: 'How do I claim warranty for my water purifier?',
        answer: 'To claim warranty: 1) Keep your invoice and warranty card handy, 2) Note your product serial number (on the unit), 3) Call 1800-123-4567 or raise a service request online, 4) Describe the issue - our team will diagnose if it\'s warranty-covered, 5) Technician visit is FREE for warranty claims. Parts replaced under warranty at no charge.',
        keywords: ['warranty claim', 'how to claim warranty', 'warranty service'],
      },
      {
        question: 'What is AMC (Annual Maintenance Contract)?',
        answer: 'AMC is our comprehensive maintenance plan that includes: 2-4 scheduled preventive maintenance visits per year, Priority service (technician visit within 24 hours), Discounted or free filter replacements (depending on plan), Free labor charges for repairs, Water quality testing at each visit. AMC plans start from ₹1,999/year. Recommended after warranty expires.',
        keywords: ['AMC', 'annual maintenance', 'maintenance contract', 'service plan'],
      },
      {
        question: 'How do I purchase or renew my AMC?',
        answer: 'To purchase AMC: 1) Log into your account → "My Devices" → "Buy AMC", 2) Choose from Basic (₹1,999), Standard (₹2,999), or Premium (₹4,499) plans, 3) Pay online and your AMC is activated immediately. For renewal, you\'ll receive reminders 30 days before expiry. Call 1800-123-4567 for AMC assistance or to understand which plan suits you best.',
        keywords: ['buy AMC', 'renew AMC', 'AMC price', 'AMC plans'],
      },
    ],
  },
  {
    title: 'Account & Support',
    icon: <Phone className="h-5 w-5" />,
    items: [
      {
        question: 'How do I create an account on Aquapurite?',
        answer: 'Creating an account is quick and easy: 1) Click "Login" at the top of the page, 2) Enter your mobile number, 3) Verify with OTP sent to your phone, 4) Done! Your account is created. You can also sign up during checkout. Account benefits: track orders, save addresses, view purchase history, manage warranties, and earn referral rewards.',
        keywords: ['create account', 'sign up', 'register', 'new account'],
      },
      {
        question: 'How can I contact Aquapurite customer support?',
        answer: 'Reach us through multiple channels: Phone: 1800-123-4567 (Toll-free, Mon-Sat 9 AM - 7 PM), Email: support@aquapurite.com (response within 24 hours), WhatsApp: +91-XXXXX-XXXXX, Live Chat: Available on website during business hours, Contact Form: Visit our Contact page. For urgent installation/service issues, calling is fastest.',
        keywords: ['contact support', 'customer service', 'helpline', 'support number'],
      },
      {
        question: 'What are your customer support hours?',
        answer: 'Customer Support Hours: Phone & Live Chat: Monday to Saturday, 9:00 AM - 7:00 PM IST, Sunday: 10:00 AM - 4:00 PM IST (limited support). Email support: 24/7 (response within 24 hours). Service technician scheduling: 7 days a week. Emergency water purifier issues? Email urgent@aquapurite.com for priority handling.',
        keywords: ['support hours', 'working hours', 'when available', 'support timing'],
      },
      {
        question: 'How do I update my profile or change my phone number?',
        answer: 'To update profile: Log in → Click your name → "Profile Settings". You can edit: Name, email, and addresses directly. To change phone number: Go to Profile → "Change Phone Number" → Enter new number → Verify with OTP. Note: Changing phone number affects login, so ensure you have access to the new number.',
        keywords: ['update profile', 'change phone', 'edit account', 'update details'],
      },
      {
        question: 'How does the Aquapurite Referral Program work?',
        answer: 'Earn ₹500 for every successful referral! How it works: 1) Share your unique referral code with friends/family, 2) They get 5% off their first water purifier purchase, 3) When they complete a purchase, you earn ₹500 in your Aquapurite wallet. No limit on referrals! Withdraw earnings to your bank or use as store credit. Find your code in "My Account" → "Referral".',
        keywords: ['referral', 'refer friend', 'earn money', 'referral code'],
      },
    ],
  },
];

function FAQAccordion({ item, isOpen, onToggle }: { item: FAQItem; isOpen: boolean; onToggle: () => void }) {
  return (
    <div className="border-b last:border-b-0">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full py-4 text-left hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded"
        aria-expanded={isOpen}
      >
        <span className="font-medium pr-4">{item.question}</span>
        <ChevronDown
          className={cn(
            'h-5 w-5 text-muted-foreground shrink-0 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
          aria-hidden="true"
        />
      </button>
      <div
        className={cn(
          'overflow-hidden transition-all duration-200',
          isOpen ? 'max-h-[500px] pb-4' : 'max-h-0'
        )}
        role="region"
        aria-hidden={!isOpen}
      >
        <p className="text-muted-foreground leading-relaxed">{item.answer}</p>
      </div>
    </div>
  );
}

export default function FAQPage() {
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [expandAll, setExpandAll] = useState(false);

  const toggleItem = (categoryIndex: number, itemIndex: number) => {
    const key = `${categoryIndex}-${itemIndex}`;
    setOpenItems((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleExpandAll = () => {
    if (expandAll) {
      setOpenItems({});
    } else {
      const allOpen: Record<string, boolean> = {};
      faqCategories.forEach((cat, catIndex) => {
        cat.items.forEach((_, itemIndex) => {
          allOpen[`${catIndex}-${itemIndex}`] = true;
        });
      });
      setOpenItems(allOpen);
    }
    setExpandAll(!expandAll);
  };

  // Filter FAQs based on search query
  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) return faqCategories;

    const query = searchQuery.toLowerCase();
    return faqCategories
      .map((category) => ({
        ...category,
        items: category.items.filter(
          (item) =>
            item.question.toLowerCase().includes(query) ||
            item.answer.toLowerCase().includes(query) ||
            item.keywords?.some((kw) => kw.toLowerCase().includes(query))
        ),
      }))
      .filter((category) => category.items.length > 0);
  }, [searchQuery]);

  const totalFAQs = faqCategories.reduce((sum, cat) => sum + cat.items.length, 0);
  const filteredFAQs = filteredCategories.reduce((sum, cat) => sum + cat.items.length, 0);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
          <HelpCircle className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-4" style={{ textWrap: 'balance' } as React.CSSProperties}>
          Frequently Asked Questions
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto mb-6">
          Find instant answers to common questions about Aquapurite water purifiers, orders, installation, warranty, and more.
          Can&apos;t find what you&apos;re looking for?{' '}
          <Link href="/contact" className="text-primary hover:underline font-medium">
            Contact our support team
          </Link>
        </p>

        {/* Search Bar */}
        <div className="max-w-xl mx-auto relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search FAQs... (e.g., 'warranty', 'installation', 'EMI')"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 h-12 text-base"
            aria-label="Search frequently asked questions"
          />
        </div>

        {/* Search Results Info & Expand/Collapse */}
        <div className="flex items-center justify-center gap-4 mt-4">
          {searchQuery && (
            <p className="text-sm text-muted-foreground">
              Showing {filteredFAQs} of {totalFAQs} questions
            </p>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExpandAll}
            className="text-sm"
          >
            {expandAll ? (
              <>
                <ChevronUp className="h-4 w-4 mr-1" />
                Collapse All
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-1" />
                Expand All
              </>
            )}
          </Button>
        </div>
      </div>

      {/* FAQ Categories */}
      {filteredCategories.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 max-w-5xl mx-auto">
          {filteredCategories.map((category, categoryIndex) => {
            const originalCategoryIndex = faqCategories.findIndex(c => c.title === category.title);
            return (
              <Card key={categoryIndex} className="overflow-hidden">
                <CardHeader className="bg-muted/30">
                  <CardTitle className="flex items-center gap-2">
                    <span className="p-2 bg-primary/10 rounded-lg text-primary">
                      {category.icon}
                    </span>
                    {category.title}
                    <span className="ml-auto text-sm font-normal text-muted-foreground">
                      {category.items.length} {category.items.length === 1 ? 'question' : 'questions'}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="divide-y">
                    {category.items.map((item, itemIndex) => {
                      const originalItemIndex = faqCategories[originalCategoryIndex]?.items.findIndex(
                        i => i.question === item.question
                      ) ?? itemIndex;
                      return (
                        <FAQAccordion
                          key={itemIndex}
                          item={item}
                          isOpen={openItems[`${originalCategoryIndex}-${originalItemIndex}`] || false}
                          onToggle={() => toggleItem(originalCategoryIndex, originalItemIndex)}
                        />
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-lg text-muted-foreground mb-4">
            No FAQs found for &quot;{searchQuery}&quot;
          </p>
          <p className="text-sm text-muted-foreground mb-6">
            Try different keywords or browse all categories
          </p>
          <Button variant="outline" onClick={() => setSearchQuery('')}>
            Clear Search
          </Button>
        </div>
      )}

      {/* Contact CTA */}
      <div className="text-center mt-12 p-8 bg-gradient-to-br from-primary/5 to-primary/10 rounded-2xl max-w-2xl mx-auto border border-primary/10">
        <h2 className="text-xl font-semibold mb-2">Still have questions?</h2>
        <p className="text-muted-foreground mb-6">
          Our expert support team is ready to help you with any questions about water purifiers, orders, or service.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/contact"
            className="inline-flex items-center justify-center px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium shadow-sm"
          >
            Contact Support
          </Link>
          <a
            href="tel:18001234567"
            className="inline-flex items-center justify-center px-6 py-3 border-2 border-primary/20 rounded-lg hover:bg-primary/5 transition-colors font-medium"
          >
            <Phone className="h-4 w-4 mr-2" />
            1800-123-4567
          </a>
        </div>
        <p className="text-xs text-muted-foreground mt-4">
          Available Mon-Sat, 9 AM - 7 PM IST | Sunday 10 AM - 4 PM
        </p>
      </div>
    </div>
  );
}
