export type EventStatus = "draft" | "published" | "cancelled";
export type RegistrationStatus = "pending" | "approved" | "rejected" | "cancelled" | "attended";
export interface Category { id: string; slug: string; name: string }
export interface EventItem {
  id: string; slug: string; title: string; summary: string; description: string; image_url: string | null;
  starts_at: string; ends_at: string; registration_deadline: string | null; format: "offline" | "online" | "hybrid";
  region: string; venue: string | null; address: string | null; meeting_url: string | null; target_audience: string;
  min_grade: number; max_grade: number; participation_terms: string; capacity: number | null; requires_approval: boolean;
  status: EventStatus; organizer: { id: string; name: string; type: string }; categories: Category[];
  registration_count: number; my_registration_status: RegistrationStatus | null;
}
export interface EventList { items: EventItem[]; total: number }
export interface EventPayload { title: string; summary: string; description: string; image_url: string | null; starts_at: string; ends_at: string; registration_deadline: string | null; format: EventItem["format"]; region: string; venue: string | null; address: string | null; meeting_url: string | null; target_audience: string; min_grade: number; max_grade: number; participation_terms: string; capacity: number | null; requires_approval: boolean; category_ids: string[] }
export interface Registration { id: string; event_id: string; event_slug: string; event_title: string; event_image_url: string | null; event_starts_at: string; organizer_name: string; student_id: string; student_name: string; student_email: string; status: RegistrationStatus; created_at: string }
