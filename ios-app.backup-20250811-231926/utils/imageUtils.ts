// utils/imageUtils.ts - Image utility functions for URL validation and normalization

/**
 * Check if a URL is a valid image URL
 */
export function isValidImageUrl(url: string): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  try {
    // Basic URL validation
    const urlObj = new URL(url);
    
    // Check for valid protocols
    if (!['http:', 'https:', 'file:'].includes(urlObj.protocol)) {
      return false;
    }

    // Check for common image extensions
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg'];
    const pathname = urlObj.pathname.toLowerCase();
    
    // Either has image extension or is from known image hosting services
    const hasImageExtension = imageExtensions.some(ext => pathname.endsWith(ext));
    const isImageService = [
      'images.unsplash.com',
      'img.spoonacular.com',
      'cdn.spoonacular.com',
      'i.imgur.com',
      'storage.googleapis.com'
    ].some(domain => urlObj.hostname.includes(domain));

    return hasImageExtension || isImageService;
  } catch (error) {
    return false;
  }
}

/**
 * Normalize image URL by removing unnecessary parameters and ensuring consistency
 */
export function normalizeImageUrl(url: string): string {
  if (!url || typeof url !== 'string') {
    return '';
  }

  try {
    const urlObj = new URL(url);
    
    // Remove common tracking parameters
    const paramsToRemove = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'referrer'];
    paramsToRemove.forEach(param => urlObj.searchParams.delete(param));
    
    // For Spoonacular images, ensure we're using the CDN
    if (urlObj.hostname === 'spoonacular.com' && urlObj.pathname.startsWith('/recipeImages/')) {
      urlObj.hostname = 'img.spoonacular.com';
      urlObj.pathname = urlObj.pathname.replace('/recipeImages/', '/recipes/');
    }
    
    return urlObj.toString();
  } catch (error) {
    // If URL parsing fails, return the original string if it looks like a relative path
    if (url.startsWith('./') || url.startsWith('../') || url.startsWith('/')) {
      return url;
    }
    return '';
  }
}

/**
 * Extract image format from URL or content type
 */
export function getImageFormat(url: string, contentType?: string): 'jpeg' | 'png' | 'webp' | 'gif' | 'unknown' {
  // Check content type first
  if (contentType) {
    if (contentType.includes('jpeg') || contentType.includes('jpg')) return 'jpeg';
    if (contentType.includes('png')) return 'png';
    if (contentType.includes('webp')) return 'webp';
    if (contentType.includes('gif')) return 'gif';
  }
  
  // Check URL extension
  const urlLower = url.toLowerCase();
  if (urlLower.includes('.jpg') || urlLower.includes('.jpeg')) return 'jpeg';
  if (urlLower.includes('.png')) return 'png';
  if (urlLower.includes('.webp')) return 'webp';
  if (urlLower.includes('.gif')) return 'gif';
  
  return 'unknown';
}

/**
 * Generate optimized image URL with size parameters (for services that support it)
 */
export function getOptimizedImageUrl(
  url: string, 
  width?: number, 
  height?: number,
  quality?: number
): string {
  if (!url) return '';
  
  try {
    const urlObj = new URL(url);
    
    // Spoonacular image optimization
    if (urlObj.hostname.includes('spoonacular.com')) {
      if (width) urlObj.searchParams.set('width', width.toString());
      if (height) urlObj.searchParams.set('height', height.toString());
      if (quality) urlObj.searchParams.set('quality', Math.round(quality * 100).toString());
    }
    
    // Unsplash image optimization
    if (urlObj.hostname.includes('unsplash.com')) {
      if (width && height) {
        urlObj.searchParams.set('w', width.toString());
        urlObj.searchParams.set('h', height.toString());
        urlObj.searchParams.set('fit', 'crop');
      }
      if (quality) {
        urlObj.searchParams.set('q', Math.round(quality * 100).toString());
      }
    }
    
    return urlObj.toString();
  } catch (error) {
    return url;
  }
}

/**
 * Generate placeholder image URL
 */
export function getPlaceholderImageUrl(width: number = 300, height: number = 200): string {
  return `https://via.placeholder.com/${width}x${height}/e1e1e1/999999?text=Loading...`;
}

/**
 * Check if device supports WebP format
 */
export function supportsWebP(): boolean {
  // React Native generally supports WebP on modern versions
  // This is a simple check - in a real app you might want more sophisticated detection
  return true;
}

/**
 * Validate image dimensions
 */
export function isValidImageDimensions(width: number, height: number): boolean {
  return width > 0 && height > 0 && width <= 4096 && height <= 4096;
}