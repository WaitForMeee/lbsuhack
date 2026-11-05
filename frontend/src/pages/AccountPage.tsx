import { Navigate } from "react-router-dom";
import { useCurrentUser } from "../features/auth/hooks";

export function AccountPage() {
  const currentUser = useCurrentUser();
  const user = currentUser.data!;
  return <Navigate replace to={user.role === "student" ? "/student" : "/organization"} />;
}
