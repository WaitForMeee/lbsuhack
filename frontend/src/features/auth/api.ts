import { ApiError, apiRequest } from "../../lib/api-client";
import type { AuthenticatedUser, LoginCredentials, RegisterPayload } from "./types";

export async function getCurrentUser(): Promise<AuthenticatedUser | null> {
  try {
    return await apiRequest<AuthenticatedUser>("/auth/me", { allowUnauthorized: true });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}

export function login(credentials: LoginCredentials) {
  return apiRequest<AuthenticatedUser>("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export function logout() {
  return apiRequest<void>("/auth/logout", { method: "POST" });
}

export function register(payload: RegisterPayload) {
  return apiRequest<AuthenticatedUser>("/auth/register", { method: "POST", body: JSON.stringify(payload) });
}
