// Root application component (ACRI-66). Defines the app's routing: `/login`
// is public, the gated screens are each wrapped in `RequireAuth` (AC1), and
// `/` redirects based on auth state. `/data-setup` (ACRI-59) is the Data
// Setup hub; `/data-setup/ingredients-suppliers` (ACRI-61),
// `/data-setup/menu-recipe-setup` (ACRI-60), `/data-setup/current-stock-setup`
// (ACRI-62), and `/data-setup/sales-history-import` (ACRI-63) are the 4
// category screens it links to. Only the hub is on the top nav (see
// `components/common/app-shell.tsx`) — the 4 category screens are reached
// from the hub, not the top nav.
import { Navigate, Route, Routes } from "react-router-dom";

import { RequireAuth } from "@/components/auth/require-auth";
import { AppShell } from "@/components/common/app-shell";
import { useAuth } from "@/hooks/use-auth";
import ChatAgentRoute from "@/routes/chat-agent";
import CurrentStockSetupRoute from "@/routes/current-stock-setup";
import DataSetupHubRoute from "@/routes/data-setup-hub";
import IngredientDetailRoute from "@/routes/ingredient-detail";
import IngredientsSuppliersSetupRoute from "@/routes/ingredients-suppliers-setup";
import LoginRoute from "@/routes/login";
import MenuRecipeSetupRoute from "@/routes/menu-recipe-setup";
import PurchaseOrderDraftRoute from "@/routes/purchase-order-draft";
import RiskDashboardRoute from "@/routes/risk-dashboard";
import SalesHistoryImportRoute from "@/routes/sales-history-import";

function RootRedirect() {
  const { status } = useAuth();
  if (status === "loading") {
    return <p>Loading…</p>;
  }
  return <Navigate to={status === "authenticated" ? "/risk-dashboard" : "/login"} replace />;
}

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/login" element={<LoginRoute />} />
        <Route
          path="/risk-dashboard"
          element={
            <RequireAuth>
              <RiskDashboardRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/ingredient-detail"
          element={
            <RequireAuth>
              <IngredientDetailRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/chat-agent"
          element={
            <RequireAuth>
              <ChatAgentRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/purchase-order-draft"
          element={
            <RequireAuth>
              <PurchaseOrderDraftRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/data-setup"
          element={
            <RequireAuth>
              <DataSetupHubRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/data-setup/ingredients-suppliers"
          element={
            <RequireAuth>
              <IngredientsSuppliersSetupRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/data-setup/menu-recipe-setup"
          element={
            <RequireAuth>
              <MenuRecipeSetupRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/data-setup/current-stock-setup"
          element={
            <RequireAuth>
              <CurrentStockSetupRoute />
            </RequireAuth>
          }
        />
        <Route
          path="/data-setup/sales-history-import"
          element={
            <RequireAuth>
              <SalesHistoryImportRoute />
            </RequireAuth>
          }
        />
      </Routes>
    </AppShell>
  );
}
