import React, { useState } from 'react';
import { FileText } from 'lucide-react';

export interface ReportItem {
  report_id: string;
  executive_summary: string;
  technical_body: string;
  final_confidence: number;
  generated_at: string;
}

interface ReportViewerProps {
  reports: ReportItem[];
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ reports }) => {
  const [activeTab, setActiveTab] = useState<'exec' | 'tech'>('exec');

  if (reports.length === 0) {
    return (
      <div className="h-44 border border-dashed border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500 text-xs">
        <FileText className="w-7 h-7 text-gray-600 mb-2" />
        <p>No forensic reports generated yet.</p>
        <p className="text-[11px] text-gray-600 mt-1">Reporting Worker compiles twin-tier summaries upon hunt convergence.</p>
      </div>
    );
  }

  const latestReport = reports[reports.length - 1];

  return (
    <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between border-b border-gray-800 pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-purple-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
            Autonomous Incident Report (Twin-Tier)
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950 border border-emerald-800 px-2 py-0.5 rounded font-semibold">
            Conf: {(latestReport.final_confidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        <button
          onClick={() => setActiveTab('exec')}
          className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
            activeTab === 'exec'
              ? 'bg-purple-600 text-white shadow-md'
              : 'bg-gray-900 text-gray-400 hover:text-white'
          }`}
        >
          Executive Summary
        </button>
        <button
          onClick={() => setActiveTab('tech')}
          className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
            activeTab === 'tech'
              ? 'bg-blue-600 text-white shadow-md'
              : 'bg-gray-900 text-gray-400 hover:text-white'
          }`}
        >
          Technical Forensics Body
        </button>
      </div>

      {/* Content Body */}
      <div className="bg-gray-900/80 border border-gray-800/80 rounded-lg p-3.5 max-h-72 overflow-y-auto text-xs leading-relaxed text-gray-300 font-mono space-y-2 whitespace-pre-wrap">
        {activeTab === 'exec' ? latestReport.executive_summary : latestReport.technical_body}
      </div>

      <div className="text-[10px] text-gray-500 font-mono flex items-center justify-between pt-1">
        <span>Generated: {new Date(latestReport.generated_at).toLocaleString()}</span>
        <span>ID: {latestReport.report_id.slice(0, 8)}...</span>
      </div>
    </div>
  );
};
