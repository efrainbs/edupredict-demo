import {
  CalendarClock,
  MessageSquare,
  Send,
  type LucideIcon,
} from "lucide-react";

import type { InterventionType } from "@/api/client";

export type InterventionOption = {
  value: InterventionType;
  label: string;
  icon: LucideIcon;
};

export const interventionTypes: InterventionOption[] = [
  { value: "seguimiento", label: "Seguimiento", icon: MessageSquare },
  { value: "reunion", label: "Reunión", icon: CalendarClock },
  { value: "mensaje", label: "Mensaje", icon: Send },
];

export const interventionByType = Object.fromEntries(
  interventionTypes.map((option) => [option.value, option]),
) as Record<InterventionType, InterventionOption>;
