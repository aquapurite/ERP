'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Play,
  PlayCircle,
  Clock,
  Filter,
  Search,
  ChevronRight,
  BookOpen,
  Wrench,
  Settings,
  HelpCircle,
  Youtube,
  ThumbsUp,
  Eye,
  Star,
  Droplets,
  Shield,
  Phone,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

interface VideoGuide {
  id: string;
  title: string;
  description: string;
  category: 'installation' | 'maintenance' | 'troubleshooting' | 'tips';
  duration: string;
  thumbnail: string;
  videoUrl: string;
  youtubeId?: string;
  views: number;
  likes: number;
  products?: string[];
  featured?: boolean;
}

// Comprehensive video guides data with better organization
const videoGuides: VideoGuide[] = [
  // Installation Guides
  {
    id: '1',
    title: 'Complete RO Water Purifier Installation Guide',
    description: 'Professional step-by-step guide to install your AQUAPURITE RO water purifier at home. Covers wall mounting, plumbing connections, electrical setup, and first-time flushing procedure.',
    category: 'installation',
    duration: '12:45',
    thumbnail: 'https://images.unsplash.com/photo-1585351650024-3a6d61c1e3f5?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 45230,
    likes: 1250,
    products: ['Aquapurite Optima', 'Aquapurite Pro Max'],
    featured: true,
  },
  {
    id: '2',
    title: 'Under-Sink RO Installation Tutorial',
    description: 'How to install an under-sink water purifier. Perfect for modular kitchens where you want a clean, hidden installation without visible equipment.',
    category: 'installation',
    duration: '10:20',
    thumbnail: 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 23400,
    likes: 680,
  },
  // Maintenance Guides
  {
    id: '3',
    title: 'How to Change RO Membrane - DIY Guide',
    description: 'Learn how to replace the RO membrane in your water purifier. Includes when to change (every 12-18 months), tools needed, and detailed step-by-step replacement process.',
    category: 'maintenance',
    duration: '8:30',
    thumbnail: 'https://images.unsplash.com/photo-1581244277943-fe4a9c777189?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 32150,
    likes: 890,
    featured: true,
  },
  {
    id: '4',
    title: 'Sediment & Carbon Filter Replacement',
    description: 'Quick guide to replacing pre-filters (sediment and carbon) in your RO purifier. Recommended every 3-6 months depending on water quality for optimal performance.',
    category: 'maintenance',
    duration: '6:15',
    thumbnail: 'https://images.unsplash.com/photo-1530587191325-3db32d826c18?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 28900,
    likes: 720,
  },
  {
    id: '5',
    title: 'UV Lamp Replacement Guide',
    description: 'How to safely replace the UV lamp in UV/RO+UV water purifiers. Learn the signs that indicate UV lamp needs replacement and the correct replacement procedure.',
    category: 'maintenance',
    duration: '5:45',
    thumbnail: 'https://images.unsplash.com/photo-1585351650024-3a6d61c1e3f5?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 18500,
    likes: 450,
  },
  {
    id: '6',
    title: 'How to Clean Water Purifier Storage Tank',
    description: 'Essential monthly maintenance guide to clean the storage tank of your RO purifier. Ensures hygienic water storage and prevents bacterial growth.',
    category: 'maintenance',
    duration: '7:30',
    thumbnail: 'https://images.unsplash.com/photo-1564419320461-6870880221ad?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 21800,
    likes: 560,
  },
  // Troubleshooting Guides
  {
    id: '7',
    title: 'Water Purifier Not Working? Common Problems & Fixes',
    description: 'Complete troubleshooting guide for common RO purifier issues: no water flow, bad taste, leakage, motor not running, low pressure, and unusual sounds. Fix most issues yourself!',
    category: 'troubleshooting',
    duration: '15:20',
    thumbnail: 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 67400,
    likes: 2100,
    featured: true,
  },
  {
    id: '8',
    title: 'RO Purifier Leaking? How to Fix It',
    description: 'Identify and fix water leaks in your RO purifier. Covers common leak points including filter housings, membrane housing, fittings, and tank connections.',
    category: 'troubleshooting',
    duration: '9:45',
    thumbnail: 'https://images.unsplash.com/photo-1585351650024-3a6d61c1e3f5?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 34200,
    likes: 980,
  },
  {
    id: '9',
    title: 'Why Does My Purified Water Taste Bad?',
    description: 'Troubleshoot bad taste or odor in purified water. Learn about filter life, membrane issues, and storage tank hygiene that affect water taste.',
    category: 'troubleshooting',
    duration: '8:00',
    thumbnail: 'https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 29100,
    likes: 820,
  },
  // Tips & Educational Content
  {
    id: '10',
    title: 'Understanding TDS and Water Quality',
    description: 'What is TDS (Total Dissolved Solids)? How to measure it? What TDS level is safe for drinking? Complete guide to understanding water quality parameters.',
    category: 'tips',
    duration: '10:00',
    thumbnail: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 52300,
    likes: 1800,
  },
  {
    id: '11',
    title: 'Tips to Extend Water Purifier Life',
    description: 'Expert tips to maximize the lifespan of your water purifier. Includes maintenance schedule, dos and don\'ts, best practices, and when to call for professional service.',
    category: 'tips',
    duration: '9:15',
    thumbnail: 'https://images.unsplash.com/photo-1544027993-37dbfe43562a?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 34600,
    likes: 980,
  },
  {
    id: '12',
    title: 'RO vs UV vs UF: Which Purifier is Best for You?',
    description: 'Understand the differences between RO, UV, and UF water purification technologies. Learn which type is best suited for your water source and needs.',
    category: 'tips',
    duration: '11:30',
    thumbnail: 'https://images.unsplash.com/photo-1564419320461-6870880221ad?w=800&q=80',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 41200,
    likes: 1350,
  },
];

const categoryInfo = {
  installation: {
    label: 'Installation',
    icon: Settings,
    color: 'bg-blue-100 text-blue-800',
  },
  maintenance: {
    label: 'Maintenance',
    icon: Wrench,
    color: 'bg-green-100 text-green-800',
  },
  troubleshooting: {
    label: 'Troubleshooting',
    icon: HelpCircle,
    color: 'bg-orange-100 text-orange-800',
  },
  tips: {
    label: 'Tips & Guides',
    icon: BookOpen,
    color: 'bg-purple-100 text-purple-800',
  },
};

function formatViews(views: number): string {
  if (views >= 1000000) {
    return `${(views / 1000000).toFixed(1)}M`;
  }
  if (views >= 1000) {
    return `${(views / 1000).toFixed(1)}K`;
  }
  return views.toString();
}

function VideoCard({
  video,
  onPlay,
}: {
  video: VideoGuide;
  onPlay: () => void;
}) {
  const category = categoryInfo[video.category];
  const CategoryIcon = category.icon;

  return (
    <Card className="overflow-hidden group cursor-pointer hover:shadow-lg transition-shadow" onClick={onPlay}>
      <div className="relative aspect-video bg-muted overflow-hidden">
        {/* Thumbnail Image */}
        {video.thumbnail.startsWith('http') ? (
          <img
            src={video.thumbnail}
            alt={video.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-primary/5" />
        )}
        {/* Play overlay */}
        <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center">
            <Play className="h-8 w-8 text-primary ml-1" />
          </div>
        </div>
        {/* Duration badge */}
        <Badge className="absolute bottom-2 right-2 bg-black/80 text-white border-0">
          <Clock className="h-3 w-3 mr-1" />
          {video.duration}
        </Badge>
        {video.featured && (
          <Badge className="absolute top-2 left-2 bg-primary border-0">
            <Star className="h-3 w-3 mr-1 fill-current" />
            Featured
          </Badge>
        )}
      </div>
      <CardContent className="p-4">
        <Badge variant="secondary" className={cn('mb-2', category.color)}>
          <CategoryIcon className="h-3 w-3 mr-1" />
          {category.label}
        </Badge>
        <h3 className="font-semibold line-clamp-2 mb-2 group-hover:text-primary transition-colors">
          {video.title}
        </h3>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          {video.description}
        </p>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Eye className="h-3.5 w-3.5" />
            {formatViews(video.views)} views
          </span>
          <span className="flex items-center gap-1">
            <ThumbsUp className="h-3.5 w-3.5" />
            {formatViews(video.likes)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export default function GuidesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [selectedVideo, setSelectedVideo] = useState<VideoGuide | null>(null);

  // Filter videos based on search and category
  const filteredVideos = videoGuides.filter((video) => {
    const matchesSearch =
      video.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      video.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      activeCategory === 'all' || video.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  // Get featured videos
  const featuredVideos = videoGuides.filter((v) => v.featured);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-4">
          <PlayCircle className="h-4 w-4" />
          Video Learning Center
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-4">
          Water Purifier Guides & Tutorials
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto mb-6">
          Learn how to install, maintain, and troubleshoot your AQUAPURITE water purifier with our comprehensive video guides. From basic setup to advanced maintenance - we&apos;ve got you covered!
        </p>

        {/* Quick Stats */}
        <div className="flex flex-wrap justify-center gap-6">
          <div className="flex items-center gap-2 text-sm">
            <PlayCircle className="h-4 w-4 text-primary" />
            <span><strong>{videoGuides.length}+</strong> Video Guides</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Eye className="h-4 w-4 text-primary" />
            <span><strong>400K+</strong> Views</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <ThumbsUp className="h-4 w-4 text-primary" />
            <span><strong>4.8★</strong> Average Rating</span>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="max-w-xl mx-auto mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search video guides..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Featured Videos */}
      {!searchQuery && activeCategory === 'all' && (
        <section className="mb-12">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Play className="h-5 w-5 text-primary" />
            Featured Videos
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {featuredVideos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                onPlay={() => setSelectedVideo(video)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Category Tabs */}
      <Tabs value={activeCategory} onValueChange={setActiveCategory} className="mb-8">
        <TabsList className="w-full justify-start flex-wrap h-auto gap-2 bg-transparent">
          <TabsTrigger
            value="all"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            All Videos
          </TabsTrigger>
          {Object.entries(categoryInfo).map(([key, { label, icon: Icon }]) => (
            <TabsTrigger
              key={key}
              value={key}
              className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <Icon className="h-4 w-4 mr-2" />
              {label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Video Grid */}
      {filteredVideos.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredVideos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onPlay={() => setSelectedVideo(video)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <PlayCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No videos found</h3>
          <p className="text-muted-foreground">
            Try adjusting your search or browse all categories.
          </p>
        </div>
      )}

      {/* Video Player Dialog */}
      <Dialog open={!!selectedVideo} onOpenChange={() => setSelectedVideo(null)}>
        <DialogContent className="sm:max-w-[800px] p-0">
          {selectedVideo && (
            <>
              <div className="aspect-video">
                <iframe
                  src={`${selectedVideo.videoUrl}?autoplay=1`}
                  title={selectedVideo.title}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
              <div className="p-4">
                <Badge
                  variant="secondary"
                  className={cn('mb-2', categoryInfo[selectedVideo.category].color)}
                >
                  {categoryInfo[selectedVideo.category].label}
                </Badge>
                <h3 className="text-lg font-semibold mb-2">{selectedVideo.title}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {selectedVideo.description}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Eye className="h-4 w-4" />
                      {formatViews(selectedVideo.views)} views
                    </span>
                    <span className="flex items-center gap-1">
                      <ThumbsUp className="h-4 w-4" />
                      {formatViews(selectedVideo.likes)} likes
                    </span>
                  </div>
                  {selectedVideo.youtubeId && (
                    <Button variant="outline" size="sm" asChild>
                      <a
                        href={`https://www.youtube.com/watch?v=${selectedVideo.youtubeId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Youtube className="h-4 w-4 mr-2" />
                        Watch on YouTube
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Maintenance Schedule Guide */}
      <Card className="mt-12">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-primary" />
            Recommended Maintenance Schedule
          </CardTitle>
          <CardDescription>
            Follow this schedule to keep your water purifier in optimal condition
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
              <p className="text-sm font-medium text-blue-900 mb-1">Every 3-6 Months</p>
              <p className="text-xs text-blue-700">Replace Sediment & Carbon Filters</p>
            </div>
            <div className="p-4 rounded-lg bg-green-50 border border-green-200">
              <p className="text-sm font-medium text-green-900 mb-1">Every 12 Months</p>
              <p className="text-xs text-green-700">Replace UV Lamp (if applicable)</p>
            </div>
            <div className="p-4 rounded-lg bg-orange-50 border border-orange-200">
              <p className="text-sm font-medium text-orange-900 mb-1">Every 18-24 Months</p>
              <p className="text-xs text-orange-700">Replace RO Membrane</p>
            </div>
            <div className="p-4 rounded-lg bg-purple-50 border border-purple-200">
              <p className="text-sm font-medium text-purple-900 mb-1">Monthly</p>
              <p className="text-xs text-purple-700">Clean Storage Tank</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* YouTube Channel CTA */}
      <Card className="mt-8 bg-gradient-to-r from-red-50 to-red-100 border-red-200">
        <CardContent className="py-8">
          <div className="flex flex-col md:flex-row items-center gap-6 text-center md:text-left">
            <div className="p-4 bg-red-500 rounded-full">
              <Youtube className="h-8 w-8 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-red-900 mb-2">
                Subscribe to Our YouTube Channel
              </h3>
              <p className="text-red-700">
                Get notified about new installation guides, maintenance tips, and product reviews. Join 25,000+ subscribers!
              </p>
            </div>
            <Button className="bg-red-600 hover:bg-red-700" asChild>
              <a
                href="https://www.youtube.com/@aquapurite"
                target="_blank"
                rel="noopener noreferrer"
              >
                Subscribe Now
                <ChevronRight className="h-4 w-4 ml-2" />
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Quick Contact Options */}
      <div className="mt-8 grid sm:grid-cols-2 gap-4">
        {/* WhatsApp Support */}
        <Card className="bg-green-50 border-green-200">
          <CardContent className="py-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-500 rounded-full">
                <Phone className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-green-900">Need Immediate Help?</h3>
                <p className="text-sm text-green-700">Chat with our support team on WhatsApp</p>
              </div>
              <Button variant="outline" className="border-green-300 text-green-700 hover:bg-green-100" asChild>
                <a
                  href="https://wa.me/919311939076?text=I need help with my water purifier"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Chat Now
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Book Service */}
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="py-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary rounded-full">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">Professional Service Needed?</h3>
                <p className="text-sm text-muted-foreground">Book a technician visit at your convenience</p>
              </div>
              <Button asChild>
                <Link href="/account/services">Book Service</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* FAQ Link */}
      <Card className="mt-8">
        <CardContent className="py-6">
          <div className="flex flex-col md:flex-row items-center gap-4 text-center md:text-left">
            <div className="p-3 bg-primary/10 rounded-full">
              <HelpCircle className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">Have More Questions?</h3>
              <p className="text-sm text-muted-foreground">
                Browse our comprehensive FAQ section for answers to common questions about products, orders, and services.
              </p>
            </div>
            <Button variant="outline" asChild>
              <Link href="/faq">View All FAQs</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
