import { apiRequest } from "../../lib/api-client";
import type { Category } from "../events/types";
export interface StudentProfile { user_id: string; full_name: string; email: string; grade: number; region: string; bio: string; interests: Category[] }
export interface Achievement { id: string; title: string; description: string; issued_at: string; event_id: string; event_slug: string; event_image_url: string | null; organizer_name: string }
export const getProfile = () => apiRequest<StudentProfile>("/profiles/me");
export const updateProfile = (payload: Pick<StudentProfile, "full_name" | "grade" | "region" | "bio">) => apiRequest<StudentProfile>("/profiles/me", { method: "PUT", body: JSON.stringify(payload) });
export const updateInterests = (category_ids: string[]) => apiRequest<StudentProfile>("/profiles/me/interests", { method: "PUT", body: JSON.stringify({ category_ids }) });
export const getPortfolio = () => apiRequest<Achievement[]>("/profiles/me/portfolio");
