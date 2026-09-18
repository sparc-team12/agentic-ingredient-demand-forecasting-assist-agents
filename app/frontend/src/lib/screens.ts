// Static metadata for the 4 gated screens (ACRI-66). Each entry is used by
// `RequireAuth`-wrapped routes and by `StubScreen` to know which backend
// stub endpoint to call. No business logic lives here — real per-screen
// behavior lands in later, dedicated stories.

export interface ScreenMeta {
  id: string;
  path: string;
  label: string;
  backendPath: string;
}

export const SCREENS: readonly ScreenMeta[] = [
  {
    id: "risk-dashboard",
    path: "/risk-dashboard",
    label: "Risk Dashboard",
    backendPath: "/screens/risk-dashboard",
  },
  {
    id: "ingredient-detail",
    path: "/ingredient-detail",
    label: "Ingredient Detail",
    backendPath: "/screens/ingredient-detail",
  },
  {
    id: "chat-agent",
    path: "/chat-agent",
    label: "Chat Agent",
    backendPath: "/screens/chat-agent",
  },
  {
    id: "purchase-order-draft",
    path: "/purchase-order-draft",
    label: "Purchase Order Draft",
    backendPath: "/screens/purchase-order-draft",
  },
];
