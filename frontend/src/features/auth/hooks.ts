import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getCurrentUser, login, logout, register } from "./api";

export const currentUserQueryKey = ["auth", "current-user"] as const;

export function useCurrentUser() {
  return useQuery({ queryKey: currentUserQueryKey, queryFn: getCurrentUser });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: login,
    onSuccess: (user) => queryClient.setQueryData(currentUserQueryKey, user),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSuccess: () => queryClient.setQueryData(currentUserQueryKey, null),
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: register, onSuccess: (user) => queryClient.setQueryData(currentUserQueryKey, user) });
}
