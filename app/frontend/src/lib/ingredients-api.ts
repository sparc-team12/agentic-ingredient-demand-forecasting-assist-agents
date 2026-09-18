// Typed API functions for the Ingredients & Suppliers Setup screen
// (ACRI-61), built on the shared `apiClient` (ACRI-66) — no direct `fetch`
// call from any component. Mirrors the request/response shapes documented
// in `artifacts/development/acri-61/implementation-plan.md` §6.
//
// `updateSupplier`/`updateIngredient` are full-replace (`PUT`): the caller
// must always pass the complete current object (as pre-filled edit forms
// do), not a partial patch — omitted optional fields are cleared server-side
// (tech-lead review MINOR finding).
import { apiClient } from "@/lib/api-client";

export interface Supplier {
  id: number;
  name: string;
  lead_time_days: number;
  safety_margin_days: number | null;
}

export interface SupplierSummary {
  id: number;
  name: string;
  lead_time_days: number;
}

export interface SupplierInput {
  name: string;
  lead_time_days: number;
  safety_margin_days: number | null;
}

export interface Ingredient {
  id: number;
  name: string;
  unit: string;
  unit_cost: number;
  perishable: boolean;
  shelf_life_days: number | null;
  supplier_id: number | null;
  safety_margin_days_override: number | null;
  supplier: SupplierSummary | null;
  has_supplier: boolean;
  effective_safety_margin_days: number | null;
  safety_margin_source: "ingredient" | "supplier" | null;
  safety_margin_gap: boolean;
}

export interface IngredientInput {
  name: string;
  unit: string;
  unit_cost: number;
  perishable: boolean;
  shelf_life_days: number | null;
  supplier_id: number | null;
  safety_margin_days_override: number | null;
}

export function listSuppliers(): Promise<Supplier[]> {
  return apiClient.get<Supplier[]>("/suppliers");
}

export function createSupplier(input: SupplierInput): Promise<Supplier> {
  return apiClient.post<Supplier>("/suppliers", input);
}

export function updateSupplier(id: number, input: SupplierInput): Promise<Supplier> {
  return apiClient.put<Supplier>(`/suppliers/${id}`, input);
}

export function listIngredients(): Promise<Ingredient[]> {
  return apiClient.get<Ingredient[]>("/ingredients");
}

export function createIngredient(input: IngredientInput): Promise<Ingredient> {
  return apiClient.post<Ingredient>("/ingredients", input);
}

export function updateIngredient(id: number, input: IngredientInput): Promise<Ingredient> {
  return apiClient.put<Ingredient>(`/ingredients/${id}`, input);
}
