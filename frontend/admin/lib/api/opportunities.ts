import { apiClient } from './client';

export interface OpportunitySource {
  id: string;
  name: string;
  domain: string;
  base_url: string;
  source_type: string;
  country: string;
  state?: string | null;
  authority_level: string;
  crawl_frequency: string;
  enabled: boolean;
  last_crawled_at?: string | null;
  last_successful_crawl_at?: string | null;
  last_error_at?: string | null;
  last_error?: string | null;
  created_at: string;
}

export interface CrawlRun {
  id: string;
  source_id: string;
  status: string;
  pages_fetched: number;
  pages_changed: number;
  opportunities_found: number;
  opportunities_updated: number;
  duplicates_detected: number;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface CrawlMetrics {
  active_sources: number;
  verified_sources: number;
  last_crawl_time?: string | null;
  last_verification_time?: string | null;
  crawl_success_rate: number;
  broken_links_count: number;
  review_queue_count: number;
}

export async function getAdminOpportunitySources(): Promise<OpportunitySource[]> {
  return apiClient<OpportunitySource[]>('/admin/opportunity-sources');
}

export async function createAdminOpportunitySource(data: Partial<OpportunitySource>): Promise<OpportunitySource> {
  return apiClient<OpportunitySource>('/admin/opportunity-sources', {
    method: 'POST',
    body: data,
  });
}

export async function triggerManualCrawl(sourceId: string): Promise<any> {
  return apiClient(`/admin/opportunity-sources/${sourceId}/crawl`, {
    method: 'POST',
  });
}

export async function getCrawlRuns(): Promise<CrawlRun[]> {
  return apiClient<CrawlRun[]>('/admin/crawl-runs');
}

export async function getOpportunityQualityQueue(): Promise<any[]> {
  return apiClient<any[]>('/admin/opportunity-quality');
}

export async function getBrokenLinksReport(): Promise<any[]> {
  return apiClient<any[]>('/admin/broken-links');
}

export async function getCrawlMetrics(): Promise<CrawlMetrics> {
  return apiClient<CrawlMetrics>('/admin/opportunity-sources/metrics/crawl-runs');
}
