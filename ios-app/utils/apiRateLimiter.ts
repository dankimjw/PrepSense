/**
 * API Rate Limiter and Protection System
 * Prevents excessive API calls and protects API keys from abuse
 */

interface RateLimitConfig {
  maxRequestsPerMinute: number;
  maxRequestsPerHour: number;
  maxRequestsPerDay: number;
  cooldownPeriod: number; // milliseconds between requests
  burstLimit: number; // max requests in quick succession
}

interface RequestLog {
  timestamp: number;
  endpoint: string;
  cost?: number; // API cost if applicable
}

class APIRateLimiter {
  private requestLogs: RequestLog[] = [];
  private lastRequestTime: number = 0;
  private dailyCost: number = 0;
  private config: RateLimitConfig;
  private blocked: boolean = false;
  private blockReason: string = '';

  constructor(config?: Partial<RateLimitConfig>) {
    this.config = {
      maxRequestsPerMinute: 20,  // Conservative limits
      maxRequestsPerHour: 100,
      maxRequestsPerDay: 500,
      cooldownPeriod: 500, // 500ms between requests minimum
      burstLimit: 5, // max 5 requests in quick succession
      ...config
    };
  }

  /**
   * Check if a request can be made
   */
  canMakeRequest(endpoint: string): { allowed: boolean; reason?: string; waitTime?: number } {
    const now = Date.now();
    
    // Check if temporarily blocked
    if (this.blocked) {
      return { 
        allowed: false, 
        reason: `API temporarily blocked: ${this.blockReason}`,
        waitTime: 60000 // Wait 1 minute
      };
    }

    // Check cooldown period
    const timeSinceLastRequest = now - this.lastRequestTime;
    if (timeSinceLastRequest < this.config.cooldownPeriod) {
      return { 
        allowed: false, 
        reason: 'Too many requests too quickly',
        waitTime: this.config.cooldownPeriod - timeSinceLastRequest
      };
    }

    // Clean up old logs
    this.cleanupOldLogs();

    // Check rate limits
    const oneMinuteAgo = now - 60000;
    const oneHourAgo = now - 3600000;
    const oneDayAgo = now - 86400000;

    const requestsInLastMinute = this.requestLogs.filter(log => log.timestamp > oneMinuteAgo).length;
    const requestsInLastHour = this.requestLogs.filter(log => log.timestamp > oneHourAgo).length;
    const requestsInLastDay = this.requestLogs.filter(log => log.timestamp > oneDayAgo).length;

    // Check burst limit (requests in last 5 seconds)
    const fiveSecondsAgo = now - 5000;
    const recentBurst = this.requestLogs.filter(log => log.timestamp > fiveSecondsAgo).length;

    if (recentBurst >= this.config.burstLimit) {
      return { 
        allowed: false, 
        reason: `Burst limit exceeded (${recentBurst}/${this.config.burstLimit} in 5s)`,
        waitTime: 5000
      };
    }

    if (requestsInLastMinute >= this.config.maxRequestsPerMinute) {
      return { 
        allowed: false, 
        reason: `Minute limit exceeded (${requestsInLastMinute}/${this.config.maxRequestsPerMinute})`,
        waitTime: 60000 - (now - this.requestLogs[this.requestLogs.length - this.config.maxRequestsPerMinute].timestamp)
      };
    }

    if (requestsInLastHour >= this.config.maxRequestsPerHour) {
      return { 
        allowed: false, 
        reason: `Hourly limit exceeded (${requestsInLastHour}/${this.config.maxRequestsPerHour})`,
        waitTime: 3600000 - (now - this.requestLogs[this.requestLogs.length - this.config.maxRequestsPerHour].timestamp)
      };
    }

    if (requestsInLastDay >= this.config.maxRequestsPerDay) {
      this.blocked = true;
      this.blockReason = 'Daily limit exceeded';
      return { 
        allowed: false, 
        reason: `Daily limit exceeded (${requestsInLastDay}/${this.config.maxRequestsPerDay})`,
        waitTime: 86400000 - (now - this.requestLogs[this.requestLogs.length - this.config.maxRequestsPerDay].timestamp)
      };
    }

    return { allowed: true };
  }

  /**
   * Log a request
   */
  logRequest(endpoint: string, cost?: number): void {
    const now = Date.now();
    this.requestLogs.push({
      timestamp: now,
      endpoint,
      cost
    });
    this.lastRequestTime = now;

    if (cost) {
      this.dailyCost += cost;
    }

    // Check if we're approaching limits and warn
    this.checkLimitsAndWarn();
  }

  /**
   * Get current usage statistics
   */
  getUsageStats(): {
    requestsInLastMinute: number;
    requestsInLastHour: number;
    requestsInLastDay: number;
    dailyCost: number;
    isBlocked: boolean;
    limitsApproaching: boolean;
  } {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const oneHourAgo = now - 3600000;
    const oneDayAgo = now - 86400000;

    const requestsInLastMinute = this.requestLogs.filter(log => log.timestamp > oneMinuteAgo).length;
    const requestsInLastHour = this.requestLogs.filter(log => log.timestamp > oneHourAgo).length;
    const requestsInLastDay = this.requestLogs.filter(log => log.timestamp > oneDayAgo).length;

    const limitsApproaching = 
      requestsInLastMinute > this.config.maxRequestsPerMinute * 0.8 ||
      requestsInLastHour > this.config.maxRequestsPerHour * 0.8 ||
      requestsInLastDay > this.config.maxRequestsPerDay * 0.8;

    return {
      requestsInLastMinute,
      requestsInLastHour,
      requestsInLastDay,
      dailyCost: this.dailyCost,
      isBlocked: this.blocked,
      limitsApproaching
    };
  }

  /**
   * Reset daily limits (call at midnight)
   */
  resetDaily(): void {
    const now = Date.now();
    const oneDayAgo = now - 86400000;
    this.requestLogs = this.requestLogs.filter(log => log.timestamp > oneDayAgo);
    this.dailyCost = 0;
    this.blocked = false;
    this.blockReason = '';
  }

  /**
   * Emergency stop - blocks all requests
   */
  emergencyStop(reason: string = 'Emergency stop activated'): void {
    this.blocked = true;
    this.blockReason = reason;
    console.error(`🚨 API EMERGENCY STOP: ${reason}`);
  }

  /**
   * Resume after emergency stop
   */
  resume(): void {
    this.blocked = false;
    this.blockReason = '';
    console.log('✅ API rate limiter resumed');
  }

  private cleanupOldLogs(): void {
    const now = Date.now();
    const oneDayAgo = now - 86400000;
    this.requestLogs = this.requestLogs.filter(log => log.timestamp > oneDayAgo);
  }

  private checkLimitsAndWarn(): void {
    const stats = this.getUsageStats();
    
    if (stats.requestsInLastDay > this.config.maxRequestsPerDay * 0.9) {
      console.warn(`⚠️ API Warning: 90% of daily limit used (${stats.requestsInLastDay}/${this.config.maxRequestsPerDay})`);
    } else if (stats.requestsInLastHour > this.config.maxRequestsPerHour * 0.9) {
      console.warn(`⚠️ API Warning: 90% of hourly limit used (${stats.requestsInLastHour}/${this.config.maxRequestsPerHour})`);
    }

    // Check cost threshold (example: $5 daily limit)
    if (this.dailyCost > 5) {
      this.emergencyStop(`Daily cost exceeded: $${this.dailyCost.toFixed(2)}`);
    }
  }
}

// Create singleton instance
const apiRateLimiter = new APIRateLimiter({
  maxRequestsPerMinute: 20,
  maxRequestsPerHour: 100,
  maxRequestsPerDay: 500,
  cooldownPeriod: 500,
  burstLimit: 5
});

// Reset daily limits at midnight
const scheduleReset = () => {
  const now = new Date();
  const night = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() + 1, // tomorrow
    0, 0, 0 // midnight
  );
  const msToMidnight = night.getTime() - now.getTime();

  setTimeout(() => {
    apiRateLimiter.resetDaily();
    scheduleReset(); // Schedule next reset
  }, msToMidnight);
};

scheduleReset();

export default apiRateLimiter;
export { APIRateLimiter };