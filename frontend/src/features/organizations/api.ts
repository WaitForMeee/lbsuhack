import { apiRequest } from "../../lib/api-client";
import type { Organization } from "./types";
export const getOrganizations = (query = "") => apiRequest<Organization[]>(`/organizations${query ? `?${query}` : ""}`);
export const getOrganization = (id: string) => apiRequest<Organization>(`/organizations/${id}`);
export const getMyOrganization = () => apiRequest<Organization>("/organizations/me");
export const updateMyOrganization = (payload: Omit<Organization, "id" | "type" | "prestige_score" | "prestige_history" | "published_event_count">) => apiRequest<Organization>("/organizations/me", { method: "PUT", body: JSON.stringify(payload) });
