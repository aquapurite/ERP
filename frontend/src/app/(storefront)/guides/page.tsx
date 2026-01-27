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

// Mock video guides data
const videoGuides: VideoGuide[] = [
  {
    id: '1',
    title: 'Complete RO Water Purifier Installation Guide',
    description: 'Step-by-step guide to install your Aquapurite RO water purifier at home. Includes wall mounting, plumbing connections, and first-time setup.',
    category: 'installation',
    duration: '12:45',
    thumbnail: '/images/guides/ro-installation.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 45230,
    likes: 1250,
    products: ['Aquapurite Optima', 'Aquapurite Pro Max'],
    featured: true,
  },
  {
    id: '2',
    title: 'How to Change RO Membrane - DIY Guide',
    description: 'Learn how to replace the RO membrane in your water purifier. When to change, what tools you need, and step-by-step replacement process.',
    category: 'maintenance',
    duration: '8:30',
    thumbnail: '/images/guides/membrane-change.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 32150,
    likes: 890,
    featured: true,
  },
  {
    id: '3',
    title: 'Sediment & Carbon Filter Replacement',
    description: 'Quick guide to replacing pre-filters (sediment and carbon) in your RO purifier. Recommended every 3-6 months for best performance.',
    category: 'maintenance',
    duration: '6:15',
    thumbnail: '/images/guides/filter-change.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 28900,
    likes: 720,
  },
  {
    id: '4',
    title: 'Water Purifier Not Working? Common Problems & Fixes',
    description: 'Troubleshooting guide for common RO purifier issues: no water flow, bad taste, leakage, motor not running, and more.',
    category: 'troubleshooting',
    duration: '15:20',
    thumbnail: '/images/guides/troubleshooting.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 67400,
    likes: 2100,
    featured: true,
  },
  {
    id: '5',
    title: 'UV Lamp Replacement Guide',
    description: 'How to safely replace the UV lamp in UV/RO+UV water purifiers. Signs that indicate UV lamp needs replacement.',
    category: 'maintenance',
    duration: '5:45',
    thumbnail: '/images/guides/uv-lamp.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 18500,
    likes: 450,
  },
  {
    id: '6',
    title: 'Understanding TDS and Water Quality',
    description: 'What is TDS? How to measure it? What TDS level is safe for drinking? Complete guide to understanding water quality.',
    category: 'tips',
    duration: '10:00',
    thumbnail: '/images/guides/tds-guide.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 52300,
    likes: 1800,
  },
  {
    id: '7',
    title: 'How to Clean Water Purifier Storage Tank',
    description: 'Monthly maintenance guide to clean the storage tank of your RO purifier for hygienic water storage.',
    category: 'maintenance',
    duration: '7:30',
    thumbnail: '/images/guides/tank-cleaning.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 21800,
    likes: 560,
  },
  {
    id: '8',
    title: 'Tips to Extend Water Purifier Life',
    description: 'Expert tips to maximize the lifespan of your water purifier. Maintenance schedule, dos and don\'ts, and best practices.',
    category: 'tips',
    duration: '9:15',
    thumbnail: '/images/guides/extend-life.jpg',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    youtubeId: 'dQw4w9WgXcQ',
    views: 34600,
    likes: 980,
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
    <Card className="overflow-hidden group cursor-pointer" onClick={onPlay}>
      <div className="relative aspect-video bg-muted">
        {/* Placeholder thumbnail */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
          <PlayCircle className="h-16 w-16 text-primary/50 group-hover:text-primary group-hover:scale-110 transition-all" />
        </div>
        {/* Duration badge */}
        <Badge className="absolute bottom-2 right-2 bg-black/70 text-white">
          <Clock className="h-3 w-3 mr-1" />
          {video.duration}
        </Badge>
        {video.featured && (
          <Badge className="absolute top-2 left-2 bg-primary">Featured</Badge>
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
            {formatViews(video.views)}
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
          Video Guides
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-4">
          Installation & Maintenance Guides
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Learn how to install, maintain, and troubleshoot your water purifier with our step-by-step video guides.
        </p>
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

      {/* YouTube Channel CTA */}
      <Card className="mt-12 bg-gradient-to-r from-red-50 to-red-100 border-red-200">
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
                Get notified about new installation guides, maintenance tips, and product reviews.
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

      {/* Need Help */}
      <Card className="mt-8">
        <CardContent className="py-6">
          <div className="flex flex-col md:flex-row items-center gap-4 text-center md:text-left">
            <div className="p-3 bg-primary/10 rounded-full">
              <HelpCircle className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">Can&apos;t find what you&apos;re looking for?</h3>
              <p className="text-sm text-muted-foreground">
                Contact our support team for personalized assistance.
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" asChild>
                <a
                  href="https://wa.me/919311939076?text=I need help with my water purifier"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  WhatsApp Support
                </a>
              </Button>
              <Link href="/account/services">
                <Button>Book Service</Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
