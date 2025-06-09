import { Buffer } from 'buffer';

// Helper functions for encoding/decoding data for navigation
export function enc(o: any): string {
  return Buffer.from(JSON.stringify(o)).toString('base64');
}

export function dec(s: string): any {
  return JSON.parse(Buffer.from(s, 'base64').toString('utf8'));
}