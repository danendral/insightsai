/**
 * DataLoader Component
 *
 * Handles two ways to load data:
 * 1. Click "Load Sample Data" → GET /api/sample
 * 2. Upload a CSV file → POST /api/upload (with FormData)
 *
 * KEY CONCEPT - React Events & State:
 * - useState tracks loading/error states
 * - Event handlers (onClick, onChange) trigger API calls
 * - After success, we call props.onDataLoaded() to notify the parent (App)
 */

import { useState, useRef } from "react";
import { Upload, Database, CheckCircle } from "lucide-react";
import { loadSampleData, uploadCSV, getDataSummary } from "@/lib/api";

export default function DataLoader({ onDataLoaded, hasData }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleLoadSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await loadSampleData();
      onDataLoaded(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    try {
      await uploadCSV(file);
      // After upload, fetch the summary
      const summary = await getDataSummary();
      onDataLoaded(summary);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      // Reset the file input so the same file can be re-uploaded
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="bg-surface rounded-xl border border-border p-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-text flex items-center gap-2">
            {hasData ? (
              <>
                <CheckCircle className="h-5 w-5 text-green-500" />
                Data Loaded
              </>
            ) : (
              "Get Started"
            )}
          </h2>
          <p className="text-sm text-text-muted mt-1">
            {hasData
              ? "You can load different data at any time."
              : "Load the sample dataset or upload your own CSV file."}
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleLoadSample}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover disabled:opacity-50 transition-colors"
          >
            <Database className="h-4 w-4" />
            {loading ? "Loading..." : "Load Sample Data"}
          </button>

          <label className="inline-flex items-center gap-2 px-4 py-2 border border-border text-sm font-medium rounded-lg hover:bg-surface-alt cursor-pointer transition-colors">
            <Upload className="h-4 w-4" />
            Upload CSV
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {error && (
        <p className="mt-3 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
          {error}
        </p>
      )}
    </div>
  );
}
