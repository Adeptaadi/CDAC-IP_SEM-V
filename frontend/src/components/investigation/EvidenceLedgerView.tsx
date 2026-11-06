import React, { useState, useMemo } from 'react';
import { Badge, BadgeVariant } from '../ui/Badge';
import { EmptyState } from '../ui/States';
import { KeyFinding } from '../../types/workspace';
import {
  Search,
  Filter,
  Shield,
  ChevronRight,
  Database,
  Tag,
} from 'lucide-react';

interface EvidenceLedgerViewProps {
  findings: KeyFinding[];
  onSelectFinding: (finding: KeyFinding) => void;
  selectedFindingId?: string | null;
}

export const EvidenceLedgerView: React.FC<EvidenceLedgerViewProps> = ({
  findings,
  onSelectFinding,
  selectedFindingId,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedTechnique, setSelectedTechnique] = useState<string>('all');
  const [selectedWorker, setSelectedWorker] = useState<string>('all');
  const [selectedEntityType, setSelectedEntityType] = useState<string>('all');

  // Extract unique MITRE techniques present in findings
  const uniqueTechniques = useMemo(() => {
    const set = new Set<string>();
    findings.forEach((f) => {
      if (f.mitre_technique_id) {
        set.add(f.mitre_technique_id);
      }
    });
    return Array.from(set).sort();
  }, [findings]);

  // Extract unique source workers
  const uniqueWorkers = useMemo(() => {
    const set = new Set<string>();
    findings.forEach((f) => {
      if (f.source_worker) {
        set.add(f.source_worker);
      }
    });
    return Array.from(set).sort();
  }, [findings]);

  // Filtered findings list
  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      // Search term
      const matchesSearch =
        f.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.finding_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (f.mitre_technique_id && f.mitre_technique_id.toLowerCase().includes(searchTerm.toLowerCase()));

      // Technique filter
      const matchesTechnique =
        selectedTechnique === 'all' || f.mitre_technique_id === selectedTechnique;

      // Worker filter
      const matchesWorker =
        selectedWorker === 'all' || f.source_worker === selectedWorker;

      // Entity type filter
      const matchesEntity =
        selectedEntityType === 'all' ||
        (f.entity_refs && Boolean(f.entity_refs[selectedEntityType]?.length));

      return matchesSearch && matchesTechnique && matchesWorker && matchesEntity;
    });
  }, [findings, searchTerm, selectedTechnique, selectedWorker, selectedEntityType]);

  const getProvenanceBadgeVariant = (status: string): BadgeVariant => {
    switch (status) {
      case 'direct':
        return 'success';
      case 'derived':
        return 'info';
      case 'limited':
        return 'high';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header and Filter Controls */}
      <div className="bg-zinc-900/60 p-4 rounded-lg border border-zinc-800 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400" />
              <span>Evidence Ledger & Grounded Findings</span>
              <span className="font-mono text-[10px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded border border-zinc-700">
                {filteredFindings.length} / {findings.length} item(s)
              </span>
            </h2>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Cryptographically and provenance-grounded evidence records emitted by worker executions.
            </p>
          </div>

          {/* Search box */}
          <div className="flex items-center gap-2 bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-300 min-w-[240px]">
            <Search className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search summary, technique, ID..."
              className="w-full bg-transparent focus:outline-none placeholder:text-zinc-600 text-xs"
            />
          </div>
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-zinc-800/60 text-xs">
          <div className="flex items-center gap-1.5 text-zinc-400">
            <Filter className="w-3 h-3 text-zinc-500" />
            <span className="text-[10px] font-mono uppercase">MITRE:</span>
            <select
              value={selectedTechnique}
              onChange={(e) => setSelectedTechnique(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 text-zinc-200 rounded px-2 py-1 text-xs focus:outline-none"
            >
              <option value="all">All Techniques ({findings.length})</option>
              {uniqueTechniques.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-zinc-400">
            <span className="text-[10px] font-mono uppercase">Worker:</span>
            <select
              value={selectedWorker}
              onChange={(e) => setSelectedWorker(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 text-zinc-200 rounded px-2 py-1 text-xs focus:outline-none"
            >
              <option value="all">All Workers</option>
              {uniqueWorkers.map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-zinc-400">
            <span className="text-[10px] font-mono uppercase">Entities:</span>
            <select
              value={selectedEntityType}
              onChange={(e) => setSelectedEntityType(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 text-zinc-200 rounded px-2 py-1 text-xs focus:outline-none"
            >
              <option value="all">All Entity Types</option>
              <option value="hosts">Hosts</option>
              <option value="ips">IP Addresses</option>
              <option value="users">Users</option>
              <option value="processes">Processes</option>
            </select>
          </div>
        </div>
      </div>

      {/* Findings List */}
      {filteredFindings.length === 0 ? (
        <EmptyState
          title="No Findings Match Filter"
          description="Try clearing search or technique filters to view all discovered evidence records."
        />
      ) : (
        <div className="space-y-2">
          {filteredFindings.map((finding) => {
            const isSelected = selectedFindingId === finding.finding_id;
            const hasMitre = Boolean(finding.mitre_technique_id);

            return (
              <div
                key={finding.finding_id}
                onClick={() => onSelectFinding(finding)}
                className={`p-3.5 rounded-lg border cursor-pointer transition-all duration-150 flex items-start justify-between gap-4 ${
                  isSelected
                    ? 'bg-blue-950/40 border-blue-500 shadow-md ring-1 ring-blue-500/50'
                    : 'bg-zinc-900/70 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/90'
                }`}
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-blue-400">
                      {finding.finding_id.slice(0, 8)}
                    </span>

                    <Badge variant="neutral" size="sm">
                      {finding.source_type}
                    </Badge>

                    {hasMitre && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono bg-blue-950/80 text-blue-300 border border-blue-800 px-2 py-0.5 rounded font-semibold">
                        <Shield className="w-2.5 h-2.5" />
                        {finding.mitre_technique_id}
                      </span>
                    )}

                    <Badge
                      variant={getProvenanceBadgeVariant(finding.provenance.provenance_status)}
                      size="sm"
                    >
                      {finding.provenance.provenance_status}
                    </Badge>

                    {finding.source_worker && (
                      <span className="text-[10px] font-mono text-zinc-500">
                        worker: <strong className="text-zinc-400">{finding.source_worker}</strong>
                      </span>
                    )}
                  </div>

                  {/* Summary */}
                  <p className="text-xs text-zinc-200 font-medium leading-relaxed">
                    {finding.summary}
                  </p>

                  {/* Entity Tags */}
                  {finding.entity_refs && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      {Object.entries(finding.entity_refs).map(([eType, items]) => {
                        if (!items || !items.length) return null;
                        return items.slice(0, 2).map((item) => (
                          <span
                            key={`${eType}-${item}`}
                            className="inline-flex items-center gap-1 text-[10px] font-mono bg-zinc-950 px-1.5 py-0.5 rounded border border-zinc-800 text-zinc-400"
                          >
                            <Tag className="w-2.5 h-2.5 text-zinc-500" />
                            <strong className="text-zinc-300">{eType}:</strong> {item}
                          </span>
                        ));
                      })}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0 pt-1 text-zinc-500 group-hover:text-zinc-300">
                  <span className="text-[10px] font-mono text-zinc-500">Inspect</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
