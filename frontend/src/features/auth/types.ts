export type UserRole =
  | "student"
  | "institution_representative"
  | "organization_representative";

export type OrganizationType = "institution" | "company" | "academy";

export interface OrganizationSummary {
  id: string;
  name: string;
  type: OrganizationType;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: string | null;
  organization: OrganizationSummary | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  grade?: number;
  region: string;
  organization_name?: string;
  organization_type?: OrganizationType;
  organization_description?: string;
}
