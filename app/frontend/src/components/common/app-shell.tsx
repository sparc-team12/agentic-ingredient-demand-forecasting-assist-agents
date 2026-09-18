// Shared visual shell: a top bar (brand, nav links, signed-in user +
// logout) wrapping every route's content. Purely presentational/navigation
// — introduces no new business logic. Nav links only render once
// authenticated (the top bar itself is still shown, unstyled-safe, on
// `/login`, where `useAuth().status` is not yet "authenticated").
//
// The "Data Setup" link points at the ACRI-59 hub (`/data-setup`), not
// directly at any one category screen — the hub is reached from the top
// nav, and it in turn links to each of the 4 category screens
// (`/data-setup/ingredients-suppliers`, `/data-setup/menu-recipe-setup`,
// `/data-setup/current-stock-setup`, `/data-setup/sales-history-import`),
// none of which are added to the top nav themselves.
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "@/hooks/use-auth";
import { SCREENS } from "@/lib/screens";

interface AppShellProps {
  children: ReactNode;
}

const DATA_SETUP_LINK = { path: "/data-setup", label: "Data Setup" };

export function AppShell({ children }: AppShellProps) {
  const { status, user, logout } = useAuth();
  const isAuthenticated = status === "authenticated";

  return (
    <div className="app-shell">
      <header className="topbar">
        <span className="topbar__brand">Ingredient Demand Forecasting Assistant</span>
        {isAuthenticated && (
          <nav className="topbar__nav" aria-label="Main">
            {SCREENS.map((screen) => (
              <NavLink
                key={screen.id}
                to={screen.path}
                className={({ isActive }) =>
                  isActive ? "topbar__link topbar__link--active" : "topbar__link"
                }
              >
                {screen.label}
              </NavLink>
            ))}
            <NavLink
              to={DATA_SETUP_LINK.path}
              className={({ isActive }) =>
                isActive ? "topbar__link topbar__link--active" : "topbar__link"
              }
            >
              {DATA_SETUP_LINK.label}
            </NavLink>
          </nav>
        )}
        {isAuthenticated && user && (
          <div className="topbar__user">
            <span>{user.email}</span>
            <button type="button" className="btn btn--small" onClick={() => void logout()}>
              Log out
            </button>
          </div>
        )}
      </header>
      <div className="app-shell__content">{children}</div>
    </div>
  );
}
