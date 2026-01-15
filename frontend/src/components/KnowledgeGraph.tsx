/**
 * NeurOS 2.0 Knowledge Graph Visualization Component
 * Uses D3.js force-directed graph layout
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../lib/api';

interface GraphNode {
  id: number;
  label: string;
  node_type: string;
  domain: string | null;
  mastery_level: number;
  description: string | null;
  access_count: number;
}

interface GraphEdge {
  id: number;
  source: number;
  target: number;
  relationship_type: string;
  strength: number;
}

interface D3Node extends d3.SimulationNodeDatum {
  id: number;
  label: string;
  node_type: string;
  domain: string | null;
  mastery_level: number;
  radius: number;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  relationship_type: string;
  strength: number;
}

const NODE_COLORS: Record<string, string> = {
  concept: '#3b82f6',      // blue
  technique: '#10b981',    // green
  pattern: '#8b5cf6',      // purple
  algorithm: '#f59e0b',    // amber
  data_structure: '#ef4444', // red
  tool: '#06b6d4',         // cyan
  domain: '#ec4899',       // pink
};

const EDGE_COLORS: Record<string, string> = {
  prerequisite: '#ef4444',
  related: '#6b7280',
  contrast: '#f59e0b',
  contains: '#3b82f6',
  applies_to: '#10b981',
  example_of: '#8b5cf6',
};

export default function KnowledgeGraph() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [domain, setDomain] = useState<string>('');

  const { data: graphData, isLoading, refetch } = useQuery({
    queryKey: ['knowledge-graph', domain],
    queryFn: () => graphApi.getGraph(domain || undefined),
  });

  const drawGraph = useCallback(() => {
    if (!svgRef.current || !graphData) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Transform data for D3
    const nodes: D3Node[] = graphData.nodes.map((n: GraphNode) => ({
      ...n,
      radius: 8 + n.mastery_level * 4,
    }));

    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    const links: D3Link[] = graphData.edges
      .filter((e: GraphEdge) => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map((e: GraphEdge) => ({
        source: nodeMap.get(e.source)!,
        target: nodeMap.get(e.target)!,
        relationship_type: e.relationship_type,
        strength: e.strength,
      }));

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    const container = svg.append('g');

    // Create force simulation
    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force('link', d3.forceLink<D3Node, D3Link>(links)
        .id(d => d.id)
        .distance(100)
        .strength(d => d.strength * 0.5))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide<D3Node>().radius(d => d.radius + 10));

    // Draw edges
    const link = container.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', d => EDGE_COLORS[d.relationship_type] || '#6b7280')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => d.strength * 2);

    // Draw nodes
    const node = container.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag<SVGGElement, D3Node>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // Node circles
    node.append('circle')
      .attr('r', d => d.radius)
      .attr('fill', d => NODE_COLORS[d.node_type] || '#6b7280')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (_, d) => {
        const originalNode = graphData.nodes.find((n: GraphNode) => n.id === d.id);
        setSelectedNode(originalNode || null);
      });

    // Node labels
    node.append('text')
      .text(d => d.label.length > 15 ? d.label.slice(0, 15) + '...' : d.label)
      .attr('x', d => d.radius + 5)
      .attr('y', 4)
      .attr('font-size', '12px')
      .attr('fill', '#e5e7eb')
      .style('pointer-events', 'none');

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as D3Node).x!)
        .attr('y1', d => (d.source as D3Node).y!)
        .attr('x2', d => (d.target as D3Node).x!)
        .attr('y2', d => (d.target as D3Node).y!);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [graphData]);

  useEffect(() => {
    drawGraph();
  }, [drawGraph]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => drawGraph();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [drawGraph]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500" />
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      {/* Controls */}
      <div className="p-4 border-b border-gray-700 flex items-center gap-4">
        <h2 className="text-lg font-semibold text-white">Knowledge Graph</h2>
        
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Domain:</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm text-white"
          >
            <option value="">All Domains</option>
            {graphData?.statistics?.domains?.map((d: string) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="ml-auto flex items-center gap-4 text-sm text-gray-400">
          <span>{graphData?.statistics?.total_nodes || 0} nodes</span>
          <span>{graphData?.statistics?.total_edges || 0} edges</span>
        </div>
      </div>

      {/* Legend */}
      <div className="p-3 border-b border-gray-700 flex flex-wrap gap-4">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2 text-xs">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-gray-400 capitalize">{type.replace('_', ' ')}</span>
          </div>
        ))}
      </div>

      {/* Graph Canvas */}
      <div className="relative" style={{ height: '500px' }}>
        <svg
          ref={svgRef}
          className="w-full h-full bg-gray-950"
          style={{ cursor: 'grab' }}
        />

        {/* Selected Node Panel */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-72 bg-gray-800 rounded-lg shadow-xl p-4 border border-gray-700">
            <div className="flex justify-between items-start mb-3">
              <h3 className="font-medium text-white">{selectedNode.label}</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Type</span>
                <span className="text-white capitalize">{selectedNode.node_type.replace('_', ' ')}</span>
              </div>
              {selectedNode.domain && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Domain</span>
                  <span className="text-white">{selectedNode.domain}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-400">Mastery</span>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className={`w-4 h-4 rounded ${
                        level <= selectedNode.mastery_level
                          ? 'bg-indigo-500'
                          : 'bg-gray-700'
                      }`}
                    />
                  ))}
                </div>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Access Count</span>
                <span className="text-white">{selectedNode.access_count}</span>
              </div>
              {selectedNode.description && (
                <p className="text-gray-300 mt-2 pt-2 border-t border-gray-700">
                  {selectedNode.description}
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Empty State */}
      {graphData?.nodes?.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <p className="text-lg mb-2">No knowledge nodes yet</p>
            <p className="text-sm">Create entries to build your knowledge graph</p>
          </div>
        </div>
      )}
    </div>
  );
}
