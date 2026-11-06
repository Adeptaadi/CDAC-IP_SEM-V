import React, { useState, useEffect } from 'react';
import { BookOpen, Search } from 'lucide-react';
import { systemClient } from '../api/systemClient';
import { KnowledgeStats } from '../types/system';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { LoadingState } from '../components/ui/States';

export const KnowledgePage: React.FC = () => {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [query, setQuery] = useState<string>('');
  const [queryResult, setQueryResult] = useState<any | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState<boolean>(true);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  useEffect(() => {
    systemClient
      .getKnowledgeStats()
      .then(setStats)
      .catch((e) => console.warn('Failed to load knowledge statistics', e))
      .finally(() => setIsLoadingStats(false));
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      const res = await systemClient.queryKnowledge(query, 4);
      setQueryResult(res);
    } catch (e: any) {
      console.error('Knowledge query failed', e);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-2 text-xs font-mono text-blue-400 uppercase tracking-wider mb-1">
          <BookOpen className="w-4 h-4 text-blue-500" />
          <span>Security Knowledge Reference (RAG Layer)</span>
        </div>
        <h1 className="text-xl font-bold text-zinc-100 tracking-tight">
          Cybersecurity Knowledge Base & Vector Index
        </h1>
        <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
          ChromaDB-backed semantic vector store indexing MITRE ATT&CK techniques, approved response playbooks, and historical incident cases.
        </p>
      </div>

      {/* Vector Store Counts */}
      {isLoadingStats ? (
        <LoadingState message="Connecting to ChromaDB knowledge store..." />
      ) : stats ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 bg-zinc-900/80 border border-zinc-800 rounded-lg">
            <span className="text-[10px] font-mono text-zinc-500 uppercase">MITRE Techniques</span>
            <div className="text-xl font-bold text-blue-400 font-mono mt-1">{stats.mitre_techniques_count}</div>
          </div>
          <div className="p-3.5 bg-zinc-900/80 border border-zinc-800 rounded-lg">
            <span className="text-[10px] font-mono text-zinc-500 uppercase">Response Playbooks</span>
            <div className="text-xl font-bold text-emerald-400 font-mono mt-1">{stats.playbooks_count}</div>
          </div>
          <div className="p-3.5 bg-zinc-900/80 border border-zinc-800 rounded-lg">
            <span className="text-[10px] font-mono text-zinc-500 uppercase">Historical Cases</span>
            <div className="text-xl font-bold text-yellow-400 font-mono mt-1">{stats.historical_cases_count}</div>
          </div>
          <div className="p-3.5 bg-zinc-900/80 border border-zinc-800 rounded-lg">
            <span className="text-[10px] font-mono text-zinc-500 uppercase">Total Vectors</span>
            <div className="text-xl font-bold text-violet-400 font-mono mt-1">{stats.total_vectors}</div>
          </div>
        </div>
      ) : null}

      {/* Search Input */}
      <Card>
        <CardHeader
          title="Semantic Knowledge Query"
          description="Query cybersecurity techniques using natural language semantic retrieval"
        />
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 flex items-center gap-2 bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs">
            <Search className="w-4 h-4 text-zinc-500 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. PowerShell base64 encoded command execution, GoldenEye HTTP DoS..."
              className="w-full bg-transparent focus:outline-none placeholder:text-zinc-600 text-xs"
            />
          </div>
          <Button type="submit" variant="primary" size="md" isLoading={isSearching}>
            Search Vectors
          </Button>
        </form>

        {queryResult && (
          <div className="mt-4 pt-4 border-t border-zinc-800 space-y-3">
            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              Retrieved Context ({queryResult.retrieved_chunks?.length || 0} chunks)
            </h4>
            <div className="space-y-2">
              {(queryResult.retrieved_chunks || []).map((chunk: any, idx: number) => (
                <div key={idx} className="bg-zinc-950 p-3 rounded border border-zinc-800 text-xs text-zinc-300">
                  <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 mb-1">
                    <span>Source: {chunk.metadata?.category || 'general'}</span>
                    <span>Similarity: {(chunk.score || 0.85).toFixed(3)}</span>
                  </div>
                  <p>{chunk.content || chunk.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
