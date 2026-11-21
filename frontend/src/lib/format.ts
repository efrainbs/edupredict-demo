export function initials(name: string): string {
  return name
    .replace(/^Prof\.\s*/i, "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function firstName(name: string): string {
  return (
    name.replace(/^Prof\.\s*/i, "").trim().split(/\s+/)[0] || name
  );
}

const dateTimeFormatter = new Intl.DateTimeFormat("es-PE", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return dateTimeFormatter.format(date);
}

export function relativeTime(value: string | null): string {
  if (!value) {
    return "Sin contacto";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Sin contacto";
  }

  const diff = Date.now() - date.getTime();
  if (diff < 0) {
    return formatDateTime(value);
  }

  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) {
    return "Hace un momento";
  }
  if (minutes < 60) {
    return `Hace ${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `Hace ${hours} h`;
  }

  const days = Math.floor(hours / 24);
  if (days < 7) {
    return `Hace ${days} ${days === 1 ? "día" : "días"}`;
  }

  const weeks = Math.floor(days / 7);
  if (weeks < 5) {
    return `Hace ${weeks} ${weeks === 1 ? "semana" : "semanas"}`;
  }

  const months = Math.floor(days / 30);
  if (months < 12) {
    return `Hace ${months} ${months === 1 ? "mes" : "meses"}`;
  }

  const years = Math.floor(days / 365);
  return `Hace ${years} ${years === 1 ? "año" : "años"}`;
}
