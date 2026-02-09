import { BarChart3 } from "lucide-react";

export default function Header() {
  return (
    <header className="bg-surface border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-3">
        <BarChart3 className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-xl font-bold text-text">InsightsAI</h1>
          <p className="text-xs text-text-muted">
            Sales & Marketing Analytics
          </p>
        </div>
      </div>
    </header>
  );
}
