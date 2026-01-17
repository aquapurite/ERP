'use client';

import { useState, useRef, useCallback } from 'react';
import Image from 'next/image';
import {
  X,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  Maximize2,
  Package,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@/components/ui/dialog';

interface ProductImage {
  id: string;
  image_url: string;
  thumbnail_url?: string;
  alt_text?: string;
  is_primary?: boolean;
}

interface ImageGalleryProps {
  images: ProductImage[];
  productName: string;
}

export default function ImageGallery({ images, productName }: ImageGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);
  const [zoomPosition, setZoomPosition] = useState({ x: 0, y: 0 });
  const imageContainerRef = useRef<HTMLDivElement>(null);

  const currentImage = images[selectedIndex] || images[0];

  const handlePrevious = useCallback(() => {
    setSelectedIndex((prev) => (prev > 0 ? prev - 1 : images.length - 1));
  }, [images.length]);

  const handleNext = useCallback(() => {
    setSelectedIndex((prev) => (prev < images.length - 1 ? prev + 1 : 0));
  }, [images.length]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!imageContainerRef.current) return;

    const rect = imageContainerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    setZoomPosition({ x, y });
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        handlePrevious();
      } else if (e.key === 'ArrowRight') {
        handleNext();
      } else if (e.key === 'Escape') {
        setIsLightboxOpen(false);
      }
    },
    [handlePrevious, handleNext]
  );

  if (images.length === 0) {
    return (
      <div className="aspect-square rounded-lg overflow-hidden bg-muted flex items-center justify-center">
        <Package className="h-24 w-24 text-gray-300" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Main Image with Zoom */}
      <div
        ref={imageContainerRef}
        className="relative aspect-square rounded-lg overflow-hidden bg-muted cursor-zoom-in group"
        onMouseEnter={() => setIsZoomed(true)}
        onMouseLeave={() => setIsZoomed(false)}
        onMouseMove={handleMouseMove}
        onClick={() => setIsLightboxOpen(true)}
      >
        {/* Base Image */}
        <Image
          src={currentImage.image_url}
          alt={currentImage.alt_text || productName}
          fill
          className="object-contain transition-opacity"
          sizes="(max-width: 768px) 100vw, 50vw"
          priority
        />

        {/* Zoomed Image Overlay */}
        {isZoomed && (
          <div
            className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
            style={{
              backgroundImage: `url(${currentImage.image_url})`,
              backgroundPosition: `${zoomPosition.x}% ${zoomPosition.y}%`,
              backgroundSize: '200%',
              backgroundRepeat: 'no-repeat',
            }}
          />
        )}

        {/* Zoom indicator */}
        <div className="absolute bottom-3 right-3 bg-black/60 text-white px-2 py-1 rounded text-xs flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <ZoomIn className="h-3 w-3" />
          Hover to zoom
        </div>

        {/* Fullscreen button */}
        <Button
          variant="secondary"
          size="icon"
          className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            setIsLightboxOpen(true);
          }}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>

        {/* Navigation arrows for multiple images */}
        {images.length > 1 && (
          <>
            <Button
              variant="secondary"
              size="icon"
              className="absolute left-3 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => {
                e.stopPropagation();
                handlePrevious();
              }}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              size="icon"
              className="absolute right-3 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => {
                e.stopPropagation();
                handleNext();
              }}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </>
        )}
      </div>

      {/* Thumbnails */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {images.map((image, index) => (
            <button
              key={image.id}
              onClick={() => setSelectedIndex(index)}
              className={`flex-shrink-0 h-20 w-20 rounded-lg overflow-hidden border-2 transition-all ${
                selectedIndex === index
                  ? 'border-primary ring-2 ring-primary/20'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <Image
                src={image.thumbnail_url || image.image_url}
                alt={image.alt_text || `${productName} - ${index + 1}`}
                width={80}
                height={80}
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      <Dialog open={isLightboxOpen} onOpenChange={setIsLightboxOpen}>
        <DialogContent
          className="max-w-[95vw] max-h-[95vh] w-full h-full p-0 bg-black/95"
          onKeyDown={handleKeyDown}
        >
          <DialogTitle className="sr-only">Product Image Gallery</DialogTitle>

          {/* Close button */}
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 right-4 z-50 text-white hover:bg-white/20"
            onClick={() => setIsLightboxOpen(false)}
          >
            <X className="h-6 w-6" />
          </Button>

          {/* Image counter */}
          <div className="absolute top-4 left-4 z-50 text-white text-sm bg-black/50 px-3 py-1 rounded-full">
            {selectedIndex + 1} / {images.length}
          </div>

          {/* Main lightbox image */}
          <div className="relative w-full h-full flex items-center justify-center p-8">
            <Image
              src={currentImage.image_url}
              alt={currentImage.alt_text || productName}
              fill
              className="object-contain"
              sizes="95vw"
              priority
            />
          </div>

          {/* Navigation */}
          {images.length > 1 && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="absolute left-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 h-12 w-12"
                onClick={handlePrevious}
              >
                <ChevronLeft className="h-8 w-8" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 h-12 w-12"
                onClick={handleNext}
              >
                <ChevronRight className="h-8 w-8" />
              </Button>
            </>
          )}

          {/* Thumbnail strip */}
          {images.length > 1 && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 p-2 bg-black/50 rounded-lg max-w-[90vw] overflow-x-auto">
              {images.map((image, index) => (
                <button
                  key={image.id}
                  onClick={() => setSelectedIndex(index)}
                  className={`flex-shrink-0 h-16 w-16 rounded overflow-hidden transition-all ${
                    selectedIndex === index
                      ? 'ring-2 ring-white'
                      : 'opacity-60 hover:opacity-100'
                  }`}
                >
                  <Image
                    src={image.thumbnail_url || image.image_url}
                    alt={image.alt_text || `${productName} - ${index + 1}`}
                    width={64}
                    height={64}
                    className="h-full w-full object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
