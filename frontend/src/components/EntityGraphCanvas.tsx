import React, { useState } from 'react';
import { Server, Globe, User, Terminal, Network, ShieldCheck } from 'lucide-react';

interface EntityNode {
  id: string;
  label: string;
  type: 'host' | 'ip' | 'user' | 'process';
}

interface EntityEdge {
  source: string;
  target: string;
  evidence_id?: string;
}

interface EntityGraphProps {
  nodes: EntityNode[];
  edges: EntityEdge[];
  density: number;
}

export const EntityGraphCanvas: React.FC<EntityGraphProps> = ({ nodes, edges, density }) => {
  const [selectedNode, setSelectedNode] = useState<EntityNode | null>(null);

  if (nodes.length === 0) {
    return (
      <div className="h-64 border border-dashed border-gray-800 rounded-xl flex flex-col items-center justify-center text-gray-500 text-xs">
        <Network className="w-8 h-8 text-gray-600 mb-2 animate-pulse" />
        <p>No entity correlation graph data yet.</p>
        <p className="text-[11px] text-gray-600 mt-1">Run a Correlation Worker cycle to extract entities.</p>
      </div>
    );
  }

  // Circular layout coordinates for nodes
  const width = 460;
  const height = 280;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(centerX, centerY) - 45;

  const nodePositions: { [id: string]: { x: number; y: number } } = {};
  nodes.forEach((node, idx) => {
    const angle = (2 * Math.PI * idx) / nodes.length - Math.PI / 2;
    nodePositions[node.id] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'host':
        return <Server className="w-3.5 h-3.5 text-blue-400" />;
      case 'ip':
        return <Globe className="w-3.5 h-3.5 text-emerald-400" />;
      case 'user':
        return <User className="w-3.5 h-3.5 text-amber-400" />;
      case 'process':
        return <Terminal className="w-3.5 h-3.5 text-purple-400" />;
      default:
        return <ShieldCheck className="w-3.5 h-3.5 text-gray-400" />;
    }
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'host':
        return 'stroke-blue-500 fill-blue-950 text-blue-400';
      case 'ip':
        return 'stroke-emerald-500 fill-emerald-950 text-emerald-400';
      case 'user':
        return 'stroke-amber-500 fill-amber-950 text-amber-400';
      case 'process':
        return 'stroke-purple-500 fill-purple-950 text-purple-400';
      default:
        return 'stroke-gray-500 fill-gray-950 text-gray-400';
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-300">
            Cross-Source Entity Graph
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-gray-400">
            Density (δ): <strong className="text-blue-400 font-bold">{(density * 100).toFixed(1)}%</strong>
          </span>
          <span className="text-[10px] bg-gray-900 border border-gray-800 px-2 py-0.5 rounded text-gray-400 font-mono">
            {nodes.length} Nodes • {edges.length} Links
          </span>
        </div>
      </div>

      <div className="relative bg-[#090D16] border border-gray-800 rounded-xl overflow-hidden p-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-64 select-none">
          {/* Edges */}
          {edges.map((edge, i) => {
            const src = nodePositions[edge.source];
            const tgt = nodePositions[edge.target];
            if (!src || !tgt) return null;
            const isHighlighted =
              selectedNode &&
              (selectedNode.id === edge.source || selectedNode.id === edge.target);

            return (
              <line
                key={i}
                x1={src.x}
                y1={src.y}
                x2={tgt.x}
                y2={tgt.y}
                stroke={isHighlighted ? '#60a5fa' : '#374151'}
                strokeWidth={isHighlighted ? 2 : 1}
                strokeDasharray={isHighlighted ? 'none' : '3,3'}
                className="transition-all duration-300"
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;
            const isSelected = selectedNode?.id === node.id;

            return (
              <g
                key={node.id}
                className="cursor-pointer transition-transform duration-200 hover:scale-110"
                onClick={() => setSelectedNode(isSelected ? null : node)}
              >
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={isSelected ? 16 : 12}
                  className={`${getNodeColor(node.type)} stroke-2 transition-all`}
                />
                <text
                  x={pos.x}
                  y={pos.y + 20}
                  textAnchor="middle"
                  className="fill-gray-300 text-[9px] font-mono pointer-events-none"
                >
                  {node.label.length > 12 ? node.label.slice(0, 10) + '…' : node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Details Drawer */}
        {selectedNode && (
          <div className="absolute bottom-2 left-2 right-2 bg-gray-900/95 border border-gray-700 backdrop-blur p-2.5 rounded-lg flex items-center justify-between text-xs animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center gap-2">
              {getNodeIcon(selectedNode.type)}
              <div>
                <span className="font-mono font-semibold text-white">{selectedNode.label}</span>
                <span className="text-[10px] text-gray-400 font-mono ml-2 uppercase">
                  [{selectedNode.type}]
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-[10px] text-gray-400 hover:text-white px-2 py-0.5 rounded bg-gray-800"
            >
              Clear
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
