// Typed API function for the Data Setup Hub screen (ACRI-59), built on the
// shared `apiClient` (ACRI-66) — no direct `fetch` call from any component.
import { apiClient } from "@/lib/api-client";

export interface DataSetupCategoryStatus {
  id: string;
  label: string;
  path: string;
  loaded: boolean;
}

export interface DataSetupStatus {
  categories: DataSetupCategoryStatus[];
  all_loaded: boolean;
}

export function getDataSetupStatus(): Promise<DataSetupStatus> {
  return apiClient.get<DataSetupStatus>("/data-setup/status");
}
