import React from 'react';
import { Clock } from 'lucide-react';

export interface TimelineEventItem {
  event_id: string;
  summary: string;
  mitre_technique_id?: string;
  sequence_position?: number;
  occurred_at: string;
}

interface AttackTimelineProps {
  events: TimelineEventItem[];
}

export const AttackTimeline: React.FC<AttackTimelineProps> = ({ events }) => {
  if (events.length === 0) {
    return (
      <div className="h-48 border border-dashed border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500 text-xs">
        <Clock className="w-7 h-7 text-gray-600 mb-2" />
        <p>No attack timeline events reconstructed yet.</p>
        <p className="text-[11px] text-gray-600 mt-1">Detection and Investigation workers will populate this sequence.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-300">
            Reconstructed Attack Timeline
          </span>
        </div>
        <span className="text-[10px] bg-gray-900 border border-gray-800 px-2 py-0.5 rounded text-gray-400 font-mono">
          {events.length} Events Sequenced
        </span>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-blue-500 before:via-purple-500 before:to-emerald-500">
        {events.map((evt, idx) => (
          <div key={evt.event_id || idx} className="relative group">
            {/* Dot icon */}
            <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[#111827] border-2 border-blue-500 flex items-center justify-center group-hover:scale-125 transition-transform">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            </div>

            <div className="bg-[#111827] border border-gray-800 hover:border-gray-700 p-3 rounded-xl transition-all space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-gray-400">
                  Step {evt.sequence_position ?? idx + 1} • {new Date(evt.occurred_at).toLocaleTimeString()}
                </span>
                {evt.mitre_technique_id && (
                  <span className="bg-purple-950 text-purple-300 border border-purple-800 px-1.5 py-0.5 rounded font-mono text-[10px] font-semibold">
                    {evt.mitre_technique_id}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-200 leading-relaxed font-medium">
                {evt.summary}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
