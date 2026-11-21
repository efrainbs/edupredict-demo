import {
  AlertTriangle,
  CircleAlert,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import type { RiskLevel } from "@/api/client";
import { cn } from "@/lib/utils";

const riskStyles: Record<
  RiskLevel,
  { label: string; className: string; icon: LucideIcon }
> = {
  alto: {
    label: "Riesgo alto",
    className: "border-red-200 bg-red-50 text-red-700",
    icon: AlertTriangle,
  },
  medio: {
    label: "Riesgo medio",
    className: "border-amber-200 bg-amber-50 text-amber-700",
    icon: CircleAlert,
  },
  bajo: {
    label: "Riesgo bajo",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
    icon: ShieldCheck,
  },
};

export function RiskBadge({
  level,
  size = "sm",
  className,
}: {
  level: RiskLevel;
  size?: "sm" | "md";
  className?: string;
}) {
  const config = riskStyles[level];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-medium",
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-3 py-1 text-xs",
        config.className,
        className,
      )}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} />
      {config.label}
    </span>
  );
}
