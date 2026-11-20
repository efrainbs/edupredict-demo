import { useQuery } from "@tanstack/react-query";

import { api } from "./client";

export function useMeta() {
  return useQuery({
    queryKey: ["meta"],
    queryFn: api.meta,
    staleTime: Infinity,
  });
}
