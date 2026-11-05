import { apiRequest } from "../../lib/api-client";
import type { Category, EventItem, EventList, EventPayload, Registration, RegistrationStatus } from "./types";

export const getCategories = () => apiRequest<Category[]>("/categories");
export const getEvents = (query = "") => apiRequest<EventList>(`/events${query ? `?${query}` : ""}`);
export const getEvent = (slug: string) => apiRequest<EventItem>(`/events/${slug}`);
export const getRecommendations = () => apiRequest<EventList>("/recommendations");
export const createEvent = (payload: EventPayload) => apiRequest<EventItem>("/events", { method: "POST", body: JSON.stringify(payload) });
export const updateEvent = (id: string, payload: EventPayload) => apiRequest<EventItem>(`/events/${id}`, { method: "PUT", body: JSON.stringify(payload) });
export const eventAction = (id: string, action: "publish" | "unpublish" | "cancel") => apiRequest<EventItem>(`/events/${id}/${action}`, { method: "POST" });
export const registerForEvent = (id: string) => apiRequest<Registration>(`/events/${id}/registrations`, { method: "POST" });
export const getMyRegistrations = () => apiRequest<Registration[]>("/registrations/me");
export const cancelRegistration = (id: string) => apiRequest<Registration>(`/registrations/${id}/cancel`, { method: "POST" });
export const getEventRegistrations = (id: string) => apiRequest<Registration[]>(`/events/${id}/registrations`);
export const setRegistrationStatus = (id: string, status: RegistrationStatus) => apiRequest<Registration>(`/registrations/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
