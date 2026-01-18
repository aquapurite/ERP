'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, X, Loader2, ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFileUpload } from '@/hooks/use-file-upload';
import { UploadCategory } from '@/lib/api/upload';

interface ImageUploadProps {
  value?: string;
  onChange: (url: string | undefined) => void;
  category?: UploadCategory;
  label?: string;
  description?: string;
  className?: string;
  disabled?: boolean;
  aspectRatio?: 'square' | 'video' | 'wide' | 'logo';
}

const aspectRatioClasses = {
  square: 'aspect-square',
  video: 'aspect-video',
  wide: 'aspect-[3/1]',
  logo: 'aspect-[4/1]',
};

export function ImageUpload({
  value,
  onChange,
  category = 'logos',
  label,
  description,
  className,
  disabled = false,
  aspectRatio = 'square',
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { upload, remove, isUploading, progress } = useFileUpload({
    category,
    onSuccess: (result) => {
      onChange(result.url);
      setPreview(null);
    },
    onError: () => {
      setPreview(null);
    },
  });

  const handleFileSelect = useCallback(
    async (file: File) => {
      // Show preview immediately
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);

      // Upload file
      await upload(file);
    },
    [upload]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
      // Reset input value so same file can be selected again
      e.target.value = '';
    },
    [handleFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (disabled || isUploading) return;

      const file = e.dataTransfer.files?.[0];
      if (file && file.type.startsWith('image/')) {
        handleFileSelect(file);
      }
    },
    [disabled, isUploading, handleFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleRemove = useCallback(async () => {
    if (value) {
      await remove(value);
      onChange(undefined);
    }
  }, [value, remove, onChange]);

  const handleClick = useCallback(() => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click();
    }
  }, [disabled, isUploading]);

  const displayUrl = preview || value;

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <label className="text-sm font-medium text-gray-700">{label}</label>
      )}

      <div
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={cn(
          'relative border-2 border-dashed rounded-lg transition-colors cursor-pointer',
          aspectRatioClasses[aspectRatio],
          displayUrl
            ? 'border-gray-200 bg-gray-50'
            : 'border-gray-300 hover:border-blue-400 bg-gray-50 hover:bg-blue-50',
          disabled && 'opacity-50 cursor-not-allowed',
          isUploading && 'pointer-events-none'
        )}
      >
        {displayUrl ? (
          <>
            {/* Image Preview */}
            <img
              src={displayUrl}
              alt="Preview"
              className="absolute inset-0 w-full h-full object-contain rounded-lg"
            />

            {/* Uploading Overlay */}
            {isUploading && (
              <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center rounded-lg">
                <Loader2 className="h-8 w-8 text-white animate-spin" />
                <span className="mt-2 text-white text-sm">{progress}%</span>
              </div>
            )}

            {/* Remove Button */}
            {!isUploading && !disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove();
                }}
                className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </>
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {isUploading ? (
              <>
                <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
                <span className="mt-2 text-sm text-gray-600">{progress}%</span>
              </>
            ) : (
              <>
                <div className="p-3 bg-gray-100 rounded-full mb-2">
                  <ImageIcon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="flex items-center gap-1 text-sm">
                  <Upload className="h-4 w-4 text-blue-500" />
                  <span className="text-blue-500 font-medium">Upload</span>
                  <span className="text-gray-500">or drag and drop</span>
                </div>
                <p className="mt-1 text-xs text-gray-400">
                  PNG, JPG, WebP, SVG up to 5MB
                </p>
              </>
            )}
          </div>
        )}
      </div>

      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/svg+xml"
        onChange={handleInputChange}
        className="hidden"
        disabled={disabled || isUploading}
      />
    </div>
  );
}
