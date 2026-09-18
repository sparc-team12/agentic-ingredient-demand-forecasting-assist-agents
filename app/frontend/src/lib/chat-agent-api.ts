// Typed API function for the Chat Agent's HTTP contract (ACRI-45
// explanation-on-demand, ACRI-49..52 what-if scenarios), built on the
// shared `apiClient` (ACRI-66) — no direct `fetch` call from any
// component.
import { apiClient } from "@/lib/api-client";

export type ChatAgentIntent = "explanation" | "what_if" | "unparseable";

export interface ChatAgentRequest {
  message: string;
  ingredient_id: number | null;
}

export interface ChatAgentResponse {
  reply: string;
  intent: ChatAgentIntent | string;
}

export function askChatAgent(request: ChatAgentRequest): Promise<ChatAgentResponse> {
  return apiClient.post<ChatAgentResponse>("/chat-agent/ask", request);
}
