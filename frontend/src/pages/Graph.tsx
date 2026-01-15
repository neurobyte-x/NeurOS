/**
 * NeurOS 2.0 Knowledge Graph Page
 */

import KnowledgeGraph from '../components/KnowledgeGraph';

export default function KnowledgeGraphPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Graph</h1>
          <p className="text-gray-400 mt-1">
            Visualize connections between concepts you've learned
          </p>
        </div>
      </div>

      <KnowledgeGraph />

      {/* Help Section */}
      <div className="bg-gray-800 rounded-lg p-4 text-sm">
        <h3 className="font-medium text-white mb-2">How to use the Knowledge Graph</h3>
        <ul className="text-gray-400 space-y-1 list-disc list-inside">
          <li><strong>Drag</strong> nodes to rearrange the layout</li>
          <li><strong>Scroll</strong> to zoom in and out</li>
          <li><strong>Click</strong> on a node to see details</li>
          <li>Node <strong>size</strong> represents mastery level</li>
          <li>Node <strong>color</strong> represents the type of knowledge</li>
          <li>Edge <strong>color</strong> represents the relationship type</li>
        </ul>
      </div>
    </div>
  );
}
