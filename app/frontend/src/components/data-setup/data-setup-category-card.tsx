// One Data Setup category card (ACRI-59 AC1): label, loaded/not-loaded
// status (visibly distinguished, not color-only — text badge, same
// accessibility rule as `GapFlag`), and a link into that screen.
import { Link } from "react-router-dom";

import type { DataSetupCategoryStatus } from "@/lib/data-setup-api";

interface DataSetupCategoryCardProps {
  category: DataSetupCategoryStatus;
}

export function DataSetupCategoryCard({ category }: DataSetupCategoryCardProps) {
  return (
    <section className="card" aria-labelledby={`data-setup-${category.id}-heading`}>
      <div className="section-heading-row">
        <h2 id={`data-setup-${category.id}-heading`}>{category.label}</h2>
        {category.loaded ? (
          <span>Loaded</span>
        ) : (
          <span className="badge badge--warning">Not loaded</span>
        )}
      </div>
      <div className="btn-row">
        <Link to={category.path} className="btn btn--primary">
          {category.loaded ? "View / edit" : "Load data"}
        </Link>
      </div>
    </section>
  );
}
