import { apiClient } from './client';
import { AssistantResponse } from '@/types/api';

export async function askAssistant(message: string, conversationId?: string): Promise<AssistantResponse> {
  return apiClient<AssistantResponse>('/assistant/messages', {
    method: 'POST',
    body: {
      message,
      conversation_id: conversationId || undefined
    }
  });
}
