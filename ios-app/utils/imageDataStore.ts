// Temporary storage for image data during navigation
// This avoids passing large base64 data through URL parameters

class ImageDataStore {
  private static instance: ImageDataStore;
  private imageData: Map<string, string> = new Map();

  private constructor() {}

  static getInstance(): ImageDataStore {
    if (!ImageDataStore.instance) {
      ImageDataStore.instance = new ImageDataStore();
    }
    return ImageDataStore.instance;
  }

  storeImageData(key: string, data: string): void {
    this.imageData.set(key, data);
  }

  getImageData(key: string): string | undefined {
    return this.imageData.get(key);
  }

  deleteImageData(key: string): void {
    this.imageData.delete(key);
  }

  clear(): void {
    this.imageData.clear();
  }
}

export const imageDataStore = ImageDataStore.getInstance();