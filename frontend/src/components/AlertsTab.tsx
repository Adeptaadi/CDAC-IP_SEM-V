import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldAlert, ArrowRight, RefreshCw } from 'lucide-react';

interface IncidentCandidateItem {
  id: string;
  title: string;
  description?: string;
  severity: string;
  confidence: number;
  status: string;
  created_at: string;
  metadata?: {
    entity_identifiers?: string[];
    mitre_tactics?: string[];
    mitre_techniques?: string[];
    event_count?: number;
    correlation_score?: number;
  };
}

interface AlertsTabProps {
  apiBase: string;
  onSelectInvestigation?: (id: string) => void;
  onRefreshInvestigations?: () => void;
  onPromoteCandidate?: (id: string) => void;
}

export const AlertsTab: React.FC<AlertsTabProps> = ({
  apiBase,
  onSelectInvestigation,
  onRefreshInvestigations,
  onPromoteCandidate,
}) => {
  const [candidates, setCandidates] = useState<IncidentCandidateItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [promotingId, setPromotingId] = useState<string | null>(null);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      // Fetch investigations with candidates or direct candidates
      const res = await axios.get(`${apiBase}/api/investigations`);
      const items: IncidentCandidateItem[] = res.data.map((inv: any) => ({
        id: inv.investigation_id,
        title: inv.title,
        severity: inv.confidence >= 0.8 ? 'critical' : inv.confidence >= 0.6 ? 'high' : 'medium',
        confidence: inv.confidence,
        status: inv.status,
        created_at: inv.created_at,
        metadata: {
          entity_identifiers: ['WS-01', '10.0.0.5'],
          mitre_tactics: ['Execution', 'Initial Access'],
          event_count: inv.planning_cycle_count || 1,
        },
      }));
      setCandidates(items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handlePromote = async (candidateId: string) => {
    setPromotingId(candidateId);
    try {
      const res = await axios.post(`${apiBase}/api/investigations/from-candidate/${candidateId}`);
      if (res.data?.investigation_id && onSelectInvestigation) {
        onSelectInvestigation(res.data.investigation_id);
      }
      if (onPromoteCandidate) {
        onPromoteCandidate(candidateId);
      }
      if (onRefreshInvestigations) {
        onRefreshInvestigations();
      }
      fetchAlerts();
    } catch (e) {
      console.error(e);
    } finally {
      setPromotingId(null);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-red-950 text-red-400 border-red-800';
      case 'high':
        return 'bg-orange-950 text-orange-400 border-orange-800';
      case 'medium':
        return 'bg-amber-950 text-amber-400 border-amber-800';
      default:
        return 'bg-blue-950 text-blue-400 border-blue-800';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-orange-400" />
            Detected Alerts & Correlated Incident Candidates (IS §5 & §6)
          </h2>
          <p className="text-xs text-gray-400">
            Triaged security detections and correlated multi-event incident clusters ready for investigation promotion.
          </p>
        </div>
        <button
          onClick={fetchAlerts}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs rounded border border-gray-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {candidates.length === 0 ? (
        <div className="p-8 border border-dashed border-gray-800 rounded-xl text-center text-gray-500 text-xs">
          No unhandled incident candidates in queue. All detections are under active investigation or triaged.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {candidates.map((cand) => (
            <div
              key={cand.id}
              className="bg-[#0e1424] border border-gray-800/80 hover:border-gray-700 rounded-lg p-3.5 transition flex flex-col md:flex-row md:items-center justify-between gap-3"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded border font-semibold ${getSeverityBadge(
                      cand.severity
                    )}`}
                  >
                    {cand.severity}
                  </span>
                  <span className="text-[10px] font-mono bg-gray-900 text-gray-300 border border-gray-700 px-2 py-0.5 rounded">
                    Confidence: {(cand.confidence * 100).toFixed(0)}%
                  </span>
                  <span className="text-[10px] font-mono text-gray-500">
                    Status: {cand.status}
                  </span>
                </div>
                <h3 className="text-xs font-semibold text-gray-200">{cand.title}</h3>
                {cand.description && <p className="text-[11px] text-gray-400">{cand.description}</p>}
                <div className="flex items-center gap-2 text-[10px] font-mono text-gray-400 pt-1">
                  <span>Detected: {new Date(cand.created_at).toLocaleTimeString()}</span>
                  <span>•</span>
                  <span>Entities: {(cand.metadata?.entity_identifiers || []).join(', ') || 'Target Host'}</span>
                </div>
              </div>

              <div className="shrink-0 flex items-center gap-2">
                <button
                  onClick={() => handlePromote(cand.id)}
                  disabled={promotingId === cand.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded transition shadow-sm"
                >
                  <span>{promotingId === cand.id ? 'Promoting...' : 'Promote to Hunt'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
