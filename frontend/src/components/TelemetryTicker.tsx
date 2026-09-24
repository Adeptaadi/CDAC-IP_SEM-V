import { Radio } from 'lucide-react';

interface TelemetryTickerProps {
  latestEvent?: any | null;
  totalEvents?: number;
  dispatchedEvents?: number;
  replayState?: string;
  scenarioName?: string | null;
  speed?: number;
}

export const TelemetryTicker: React.FC<TelemetryTickerProps> = ({
  latestEvent,
  totalEvents = 0,
  dispatchedEvents = 0,
  replayState = 'IDLE',
  scenarioName,
  speed = 1.0,
}) => {
  const isSuspicious =
    latestEvent &&
    (latestEvent.label?.toLowerCase().includes('attack') ||
      latestEvent.event_type?.toLowerCase().includes('powershell') ||
      latestEvent.process_name?.toLowerCase().includes('powershell') ||
      latestEvent.dst_port === 4444 ||
      latestEvent.dst_port === 8080 ||
      latestEvent.protocol === 'SYN_FLOOD');

  const progress = totalEvents > 0 ? Math.min(100, Math.round((dispatchedEvents / totalEvents) * 100)) : 0;

  return (
    <div className="bg-[#0a0e17] border-b border-gray-800 px-4 py-2 flex items-center justify-between gap-4 text-xs font-mono overflow-x-auto shadow-inner">
      {/* Left: Feed Status */}
      <div className="flex items-center gap-2.5 whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              replayState === 'PLAYING'
                ? 'bg-emerald-400 animate-ping'
                : replayState === 'PAUSED'
                ? 'bg-amber-400'
                : 'bg-gray-600'
            }`}
          />
          <span className="font-bold text-gray-300">TELEMETRY INGESTION:</span>
        </div>

        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-900 border border-gray-800 text-blue-400">
          {scenarioName ? scenarioName.toUpperCase() : 'CSE-CIC-IDS2018 FEED'}
        </span>

        <span className="text-gray-500 text-[11px]">
          ({dispatchedEvents} / {totalEvents} pkts • {progress}%)
        </span>
      </div>

      {/* Center: Latest Ingested Packet/Event Display */}
      <div className="flex-1 flex items-center gap-2 min-w-[280px] max-w-2xl bg-gray-950/80 border border-gray-800/80 px-3 py-1 rounded">
        <Radio className="w-3.5 h-3.5 text-blue-400 shrink-0 animate-pulse" />
        {latestEvent ? (
          <div className="flex items-center gap-2 truncate text-[11px]">
            <span className="text-gray-500">{latestEvent.timestamp || '00:00:00'}</span>
            <span className="text-gray-300 font-semibold truncate">
              {latestEvent.src_ip || '192.168.10.15'}:{latestEvent.src_port || '49152'} →{' '}
              {latestEvent.dst_ip || '172.31.0.10'}:{latestEvent.dst_port || '80'}
            </span>
            {latestEvent.protocol && (
              <span className="px-1 bg-gray-900 text-gray-400 text-[10px] rounded">
                {latestEvent.protocol}
              </span>
            )}
            {isSuspicious && (
              <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-red-950 text-red-400 border border-red-800 animate-pulse">
                ANOMALY FLAGGED
              </span>
            )}
          </div>
        ) : (
          <span className="text-gray-600 text-[11px] italic">
            Telemetry stream idle. Select scenario and start replay or run Auto-Hunt.
          </span>
        )}
      </div>

      {/* Right: Replay Speed & Health */}
      <div className="flex items-center gap-2 whitespace-nowrap text-[10px] text-gray-400">
        <span className="bg-gray-900 border border-gray-800 px-2 py-0.5 rounded text-gray-300">
          Replay: <strong>{speed}x</strong>
        </span>
      </div>
    </div>
  );
};
