import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, Search, Filter, Play, ExternalLink, RefreshCw } from 'lucide-react';
import { workspaceClient } from '../api/workspaceClient';
import { InvestigationSummary } from '../types/workspace';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/States';

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await workspaceClient.listInvestigations(50);
      setInvestigations(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load investigation history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredInvestigations = investigations.filter((inv) => {
    const matchesSearch =
      inv.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inv.investigation_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || inv.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="border-b border-zinc-800 pb-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-blue-400 uppercase tracking-wider mb-1">
            <History className="w-4 h-4 text-blue-500" />
            <span>Case Archive & Audit Catalog</span>
          </div>
          <h1 className="text-xl font-bold text-zinc-100 tracking-tight">
            Historical Investigations
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Review completed cases, inspect final outcomes, and launch deterministic investigation replay.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          icon={<RefreshCw className="w-3.5 h-3.5" />}
          isLoading={isLoading}
          onClick={fetchHistory}
        >
          Refresh Archive
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-zinc-900/60 p-3 rounded-lg border border-zinc-800">
        <div className="flex items-center gap-2 flex-1 min-w-[260px] bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-300">
          <Search className="w-4 h-4 text-zinc-500 shrink-0" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by threat title or investigation ID..."
            className="w-full bg-transparent focus:outline-none placeholder:text-zinc-600 text-xs"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-zinc-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 text-xs focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="investigating">Investigating</option>
            <option value="awaiting_review">Awaiting Review</option>
            <option value="completed">Completed</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Table or Empty State */}
      {isLoading ? (
        <LoadingState message="Fetching investigation archive..." className="min-h-[300px]" />
      ) : error ? (
        <ErrorState title="History Load Error" message={error} onRetry={fetchHistory} />
      ) : filteredInvestigations.length === 0 ? (
        <EmptyState
          title="No Historical Investigations Found"
          description="Investigations run through Threat Simulation will appear here for audit and replay."
          action={
            <Button variant="primary" size="sm" onClick={() => navigate('/simulate')}>
              Launch Simulation
            </Button>
          }
        />
      ) : (
        <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-950/60 text-zinc-400 font-mono text-[11px] uppercase">
                <th className="p-3">Investigation</th>
                <th className="p-3">Status</th>
                <th className="p-3">Confidence</th>
                <th className="p-3">Cycles</th>
                <th className="p-3">Created</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {filteredInvestigations.map((inv) => (
                <tr key={inv.investigation_id} className="hover:bg-zinc-850/50 transition-colors">
                  <td className="p-3">
                    <div className="font-semibold text-zinc-200">{inv.title}</div>
                    <div className="font-mono text-[10px] text-zinc-500">{inv.investigation_id.slice(0, 12)}...</div>
                  </td>
                  <td className="p-3">
                    <Badge
                      variant={
                        inv.status === 'completed'
                          ? 'success'
                          : inv.status === 'awaiting_review'
                          ? 'high'
                          : inv.status === 'investigating' || inv.status === 'active'
                          ? 'info'
                          : 'neutral'
                      }
                      size="sm"
                    >
                      {inv.status}
                    </Badge>
                  </td>
                  <td className="p-3 font-mono font-bold text-zinc-300">
                    {Math.round(inv.confidence * 100)}%
                  </td>
                  <td className="p-3 font-mono text-zinc-400">
                    {inv.planning_cycle_count} cycles
                  </td>
                  <td className="p-3 font-mono text-zinc-500 text-[11px]">
                    {new Date(inv.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={<ExternalLink className="w-3 h-3" />}
                        onClick={() => navigate(`/investigate/${inv.investigation_id}`)}
                        title="Open normal live workspace"
                      >
                        Open
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        icon={<Play className="w-3 h-3 fill-current" />}
                        onClick={() => navigate(`/investigate/${inv.investigation_id}?mode=replay`)}
                        title="Replay historical evolution step-by-step"
                      >
                        Replay
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
