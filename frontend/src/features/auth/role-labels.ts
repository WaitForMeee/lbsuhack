import type { OrganizationType, UserRole } from "./types";

export const roleLabels: Record<UserRole, string> = {
  student: "Учащийся",
  institution_representative: "Представитель учреждения",
  organization_representative: "Представитель организации",
};

export const organizationTypeLabels: Record<OrganizationType, string> = {
  institution: "Образовательное учреждение",
  company: "Компания",
  academy: "Академия",
};
