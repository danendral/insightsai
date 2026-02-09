/**
 * App.jsx - Root Component
 *
 * KEY CONCEPT - React State Management:
 * State "lives" in the highest component that needs it (here, App).
 * We pass data DOWN to children as "props" and pass callback functions
 * so children can trigger state changes UP to the parent.
 *
 *   App (owns state: dataLoaded, summary)
 *   ├── Header
 *   ├── DataLoader (calls loadSampleData/uploadCSV → updates App state)
 *   ├── Dashboard  (receives summary as prop, fetches chart data)
 *   └── QueryPanel (sends questions to /api/query)
 */

import { useState } from "react";
import Header from "./components/Header";
import DataLoader from "./components/DataLoader";
import Dashboard from "./components/Dashboard";
import QueryPanel from "./components/QueryPanel";

export default function App() {
  // State: whether data has been loaded into the backend
  const [summary, setSummary] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");

  // Called by DataLoader when data is successfully loaded
  const handleDataLoaded = (summaryData) => {
    setSummary(summaryData);
    setActiveTab("dashboard");
  };

  return (
    <div className="min-h-screen bg-surface-alt text-text">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Step 1: Load data (always visible at top) */}
        <DataLoader onDataLoaded={handleDataLoaded} hasData={!!summary} />

        {/* Step 2: Once data is loaded, show tabs for Dashboard and AI Query */}
        {summary && (
          <>
            {/* Tab navigation */}
            <div className="flex gap-1 mt-8 mb-6 border-b border-border">
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  activeTab === "dashboard"
                    ? "bg-surface text-primary border border-border border-b-surface -mb-px"
                    : "text-text-muted hover:text-text"
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab("query")}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  activeTab === "query"
                    ? "bg-surface text-primary border border-border border-b-surface -mb-px"
                    : "text-text-muted hover:text-text"
                }`}
              >
                AI Insights
              </button>
            </div>

            {/* Tab content */}
            {activeTab === "dashboard" && <Dashboard summary={summary} />}
            {activeTab === "query" && <QueryPanel />}
          </>
        )}
      </main>
    </div>
  );
}
