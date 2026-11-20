import { Construction, type LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";

export function PlaceholderPage({
  title,
  description,
  icon: Icon,
}: {
  title: string;
  description: string;
  icon: LucideIcon;
}) {
  return (
    <Card className="flex min-h-[420px] flex-col items-center justify-center px-8 py-16 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
        <Icon className="h-8 w-8" />
      </div>
      <div className="mt-5 inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
        <Construction className="h-3.5 w-3.5" />
        Próximamente
      </div>
      <h2 className="mt-4 text-xl font-semibold text-slate-900">{title}</h2>
      <p className="mt-2 max-w-lg text-sm leading-6 text-slate-500">
        {description}
      </p>
    </Card>
  );
}
