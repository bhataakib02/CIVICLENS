import { apiClient } from './client';

export interface OpportunityLink {
  id: string;
  url: string;
  domain: string;
  link_type: string;
  is_official: boolean;
  is_valid: boolean;
  http_status?: number | null;
  redirect_target?: string | null;
}

export interface MatchBreakdown {
  overall_score: number;
  skill_match: number;
  education_match: number;
  location_match: number;
  experience_match: number;
  eligibility_match: number;
  deadline_urgency: number;
  reasons: string[];
}

export interface Opportunity {
  id: string;
  type: string;
  title: string;
  organization: string;
  organization_type?: string | null;
  description: string;
  summary?: string | null;
  location?: string | null;
  locations?: string[];
  remote: boolean;
  employment_type?: string | null;
  category?: string | null;
  sector?: string | null;
  skills?: string[];
  education_requirements?: string[];
  eligibility?: string[];
  benefits?: string[];
  salary_min?: number | null;
  salary_max?: number | null;
  stipend?: string | null;
  fee?: string | null;
  application_open_date?: string | null;
  application_deadline?: string | null;
  event_date?: string | null;
  published_at?: string | null;
  status: 'UPCOMING' | 'OPEN' | 'CLOSING_SOON' | 'CLOSED' | 'DATE_UNKNOWN';
  source_url: string;
  application_url?: string | null;
  source_domain: string;
  source_name: string;
  source_type: string;
  quality_score: number;
  last_verified_at: string;
  links?: OpportunityLink[];
  match_breakdown?: MatchBreakdown | null;
}

export interface OpportunityPage {
  items: Opportunity[];
  total: number;
  page: number;
  page_size: number;
  indexed_sources: number;
  verified_sources: number;
  last_crawl_time?: string | null;
  last_verification_time?: string | null;
}

export async function getOpportunities(params: {
  q?: string;
  type?: string;
  location?: string;
  remote?: boolean;
  closing_soon?: boolean;
  is_government?: boolean;
  page?: number;
  page_size?: number;
}): Promise<OpportunityPage> {
  const query = new URLSearchParams();
  if (params.q) query.set('query', params.q);
  if (params.type) query.set('type', params.type);
  if (params.location) query.set('location', params.location);
  if (params.remote !== undefined) query.set('remote', String(params.remote));
  if (params.closing_soon) query.set('closing_soon', 'true');
  if (params.is_government !== undefined) query.set('is_government', String(params.is_government));
  if (params.page) query.set('page', String(params.page));
  if (params.page_size) query.set('page_size', String(params.page_size));

  const queryStr = query.toString();
  return apiClient<OpportunityPage>(`/opportunities${queryStr ? `?${queryStr}` : ''}`);
}

export async function searchOpportunitiesNaturalLanguage(q: string): Promise<OpportunityPage> {
  return apiClient<OpportunityPage>(`/opportunities/search?q=${encodeURIComponent(q)}`);
}

export async function getOpportunityDetail(id: string): Promise<Opportunity> {
  return apiClient<Opportunity>(`/opportunities/${id}`);
}

export async function getRecommendedOpportunities(limit = 10): Promise<Opportunity[]> {
  return apiClient<Opportunity[]>(`/opportunities/recommended?limit=${limit}`);
}

export async function trackOpportunityApplication(id: string, status: string, notes?: string): Promise<any> {
  return apiClient(`/opportunities/${id}/track`, {
    method: 'POST',
    body: { status, notes },
  });
}
