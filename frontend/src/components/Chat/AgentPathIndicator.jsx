/**
 * AgentPathIndicator — visualises the multi-agent execution flow in real-time.
 *
 * Props:
 *   agentPath      string[]   Final agent_path from "done" event
 *   completedNodes string[]   Nodes that have fired a "progress" event during streaming
 *   activeNode     string|null  Node currently running
 *   isStreaming    bool
 */

const NODES = [
  { key: 'supervisor', label: 'Supervisor', icon: '⚙' },
  { key: 'rag',        label: 'RAG',        icon: '⊛' },
  { key: 'search',     label: 'Search',     icon: '⊕' },
  { key: 'summarizer', label: 'Summarizer', icon: '✦' },
];

const AGENT_TO_NODE = {
  rag_agent:        'rag',
  search_agent:     'search',
  summarizer_agent: 'summarizer',
};

function nodeStatus(key, { agentPath, completedNodes, activeNode, isStreaming }) {
  if (isStreaming) {
    if (completedNodes.includes(key)) return 'completed';
    if (activeNode === key) return 'active';
    return 'pending';
  }
  // Finished — use agentPath to determine which nodes actually ran
  const executed = new Set(['supervisor', ...agentPath.map((a) => AGENT_TO_NODE[a]).filter(Boolean)]);
  return executed.has(key) ? 'completed' : 'skipped';
}

export default function AgentPathIndicator({
  agentPath = [],
  completedNodes = [],
  activeNode = null,
  isStreaming = false,
}) {
  return (
    <div className="agent-path">
      <div className="agent-path-label">Agent 执行路径</div>
      <div className="agent-nodes">
        {NODES.map((node, i) => {
          const status = nodeStatus(node.key, { agentPath, completedNodes, activeNode, isStreaming });
          return (
            <div key={node.key} className="agent-node">
              <div className={`agent-node-badge ${status}`} title={status}>
                <span>{node.icon}</span>
                <span>{node.label}</span>
                {status === 'completed' && <span className="agent-check">✓</span>}
                {status === 'active'    && <span className="agent-dot" />}
              </div>
              {i < NODES.length - 1 && <span className="agent-arrow">→</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
