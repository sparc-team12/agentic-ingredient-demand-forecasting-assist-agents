// Typed API functions for the Menu & Recipe Setup screen (ACRI-60), built
// on the shared `apiClient` (ACRI-66) — no direct `fetch` call from any
// component.
//
// `updateDish`/`updateRecipeLine` are full-replace (`PUT`), same convention
// as `ingredients-api.ts`.
import { apiClient } from "@/lib/api-client";

export interface RecipeLine {
  id: number;
  dish_id: number;
  ingredient_name: string;
  ingredient_id: number | null;
  quantity_per_serving: number;
  unit: string;
  ingredient_flagged: boolean;
}

export interface RecipeLineInput {
  ingredient_name: string;
  quantity_per_serving: number;
  unit: string;
}

export interface Dish {
  id: number;
  name: string;
  created_at: string;
  recipe_lines: RecipeLine[];
}

export interface DishInput {
  name: string;
}

export function listDishes(): Promise<Dish[]> {
  return apiClient.get<Dish[]>("/dishes");
}

export function createDish(input: DishInput): Promise<Dish> {
  return apiClient.post<Dish>("/dishes", input);
}

export function updateDish(id: number, input: DishInput): Promise<Dish> {
  return apiClient.put<Dish>(`/dishes/${id}`, input);
}

export function createRecipeLine(dishId: number, input: RecipeLineInput): Promise<RecipeLine> {
  return apiClient.post<RecipeLine>(`/dishes/${dishId}/recipe-lines`, input);
}

export function updateRecipeLine(
  dishId: number,
  lineId: number,
  input: RecipeLineInput,
): Promise<RecipeLine> {
  return apiClient.put<RecipeLine>(`/dishes/${dishId}/recipe-lines/${lineId}`, input);
}
