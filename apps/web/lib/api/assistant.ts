import { apiClient } from './client';
import { AssistantResponse } from '@/types/api';

export async function askAssistant(query: string, conversationId?: string): Promise<AssistantResponse> {
  return apiClient<AssistantResponse>('/assistant/query', {
    method: 'POST',
    body: {
      query,
      conversation_id: conversationId || undefined
    }
  });
}
