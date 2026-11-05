import { apiRequest } from "../../lib/api-client";
export interface OrgBrief { id: string; name: string; type: string; prestige_score: number }
export interface Response { id: string; responder: OrgBrief; message: string; status: "pending" | "accepted" | "rejected" | "withdrawn"; created_at: string }
export interface Opportunity { id: string; creator: OrgBrief; target: OrgBrief | null; direction: "institution_seeks_organization" | "organization_seeks_institution"; title: string; description: string; topic: string; format: string; target_audience: string; conditions: string; desired_start: string | null; desired_end: string | null; status: "open" | "closed" | "cancelled"; created_at: string; responses: Response[] }
export interface Partnership { id: string; title: string; organization_a: OrgBrief; organization_b: OrgBrief; organization_a_confirmed: boolean; organization_b_confirmed: boolean; status: "active" | "completed"; completed_at: string | null; created_at: string }
export const getOpportunities = (mode = "") => apiRequest<Opportunity[]>(`/partnership-opportunities${mode ? `?${mode}=true` : ""}`);
export const createOpportunity = (payload: unknown) => apiRequest<Opportunity>("/partnership-opportunities", { method: "POST", body: JSON.stringify(payload) });
export const respondToOpportunity = (id: string, message: string) => apiRequest<Opportunity>(`/partnership-opportunities/${id}/responses`, { method: "POST", body: JSON.stringify({ message }) });
export const updateResponse = (id: string, status: Response["status"]) => apiRequest<Opportunity>(`/partnership-responses/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });
export const getPartnerships = () => apiRequest<Partnership[]>("/partnerships");
export const confirmPartnership = (id: string) => apiRequest<Partnership>(`/partnerships/${id}/confirm-completion`, { method: "POST" });
