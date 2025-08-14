/**
 * Simple Rate Limiter for Development
 * Just prevents accidental infinite loops, no strict limits
 */

class SimpleRateLimiter {
  private lastRequestTime: number = 0;
  private rapidFireCount: number = 0;
  private rapidFireWindow: number = 1000; // 1 second
  private maxRapidFire: number = 10; // Max 10 requests per second (very generous)

  /**
   * Check if request seems like an infinite loop
   */
  checkForInfiniteLoop(): boolean {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;

    // If less than 100ms between requests, it might be a loop
    if (timeSinceLastRequest < 100) {
      this.rapidFireCount++;
      
      // If we've had more than 10 super rapid requests, it's probably a loop
      if (this.rapidFireCount > this.maxRapidFire) {
        console.error('🚨 Possible infinite loop detected! Blocking requests for 5 seconds.');
        
        // Reset after 5 seconds
        setTimeout(() => {
          this.rapidFireCount = 0;
          console.log('✅ Request blocking lifted');
        }, 5000);
        
        return true; // Block the request
      }
    } else {
      // Reset counter if enough time has passed
      this.rapidFireCount = 0;
    }

    this.lastRequestTime = now;
    return false; // Allow the request
  }

  /**
   * Log API usage for debugging (no limits, just logging)
   */
  logUsage(endpoint: string): void {
    const timestamp = new Date().toISOString();
    console.log(`📊 API Call: ${endpoint} at ${timestamp}`);
  }
}

export const simpleRateLimiter = new SimpleRateLimiter();