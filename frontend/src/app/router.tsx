import { RouterProvider, createBrowserRouter } from "react-router-dom";

import { AuthGate } from "../features/auth/components/AuthGate";
import { HomePage } from "../pages/HomePage";
import { EventsPage } from "../pages/EventsPage";
import { EventDetailPage } from "../pages/EventDetailPage";
import { OrganizationsPage } from "../pages/OrganizationsPage";
import { OrganizationDetailPage } from "../pages/OrganizationDetailPage";
import { RegisterPage } from "../pages/RegisterPage";
import { StudentCabinetPage } from "../pages/StudentCabinetPage";
import { OrganizationCabinetPage } from "../pages/OrganizationCabinetPage";
import { EventFormPage } from "../pages/EventFormPage";
import { EventRegistrationsPage } from "../pages/EventRegistrationsPage";
import { PartnershipsPage } from "../pages/PartnershipsPage";
import { LoginPage } from "../pages/LoginPage";
import { NotFoundPage } from "../pages/NotFoundPage";

const router = createBrowserRouter([
  { path: "/", element: <HomePage /> },
  { path: "/events", element: <EventsPage /> },
  { path: "/events/:slug", element: <EventDetailPage /> },
  { path: "/organizations", element: <OrganizationsPage /> },
  { path: "/organizations/:id", element: <OrganizationDetailPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/student", element: <AuthGate><StudentCabinetPage /></AuthGate> },
  { path: "/organization", element: <AuthGate><OrganizationCabinetPage /></AuthGate> },
  { path: "/organization/events/new", element: <AuthGate><EventFormPage /></AuthGate> },
  { path: "/organization/events/:id/edit", element: <AuthGate><EventFormPage /></AuthGate> },
  { path: "/organization/events/:id/registrations", element: <AuthGate><EventRegistrationsPage /></AuthGate> },
  { path: "/partnerships", element: <AuthGate><PartnershipsPage /></AuthGate> },
  { path: "*", element: <NotFoundPage /> },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
