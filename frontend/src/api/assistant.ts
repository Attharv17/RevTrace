/**
 * RevTrace — Phase 7: AI Investigation Agent API client.
 * 
 * NOTE: Uses a 90-second timeout (LLM + multi-tool-call round trips can be slow).
 * All responses are structured InvestigationReport objects — never raw LLM text.
 */
import axios from "axios";
import type { AssistantHealthResponse, InvestigationReport, InvestigationRequest } from "@/types";

// Extended timeout for LLM calls (90s)
const llmClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  timeout: 90_000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

export const assistantApi = {
  /**
   * Submit an investigation question about a specific transaction.
   * Returns a structured report — never invents data.
   */
  investigate: async (request: InvestigationRequest): Promise<InvestigationReport> => {
    const response = await llmClient.post<InvestigationReport>(
      "/api/assistant/investigate",
      request
    );
    return response.data;
  },

  /**
   * Check if the LLM (Gemini) is configured and available.
   */
  health: async (): Promise<AssistantHealthResponse> => {
    const response = await llmClient.get<AssistantHealthResponse>("/api/assistant/health");
    return response.data;
  },
};
