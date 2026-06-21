import AgentPathIndicator from './AgentPathIndicator';

const IconFile = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
);

export default function MessageBubble({ message }) {
  const { role, content, agentPath = [], sources = [], isStreaming, completedNodes = new Set(), activeNode = null, isError } = message;

  if (role === 'user') {
    return (
      <div className="message-row user">
        <div className="message-bubble user">
          <div className="message-content">{content}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="message-row assistant">
      <div className="message-bubble assistant">
        {isError ? (
          <div className="message-error">{content}</div>
        ) : (
          <div className={`message-content ${isStreaming ? 'streaming' : ''}`}>
            {content || (isStreaming ? '' : '（无内容）')}
          </div>
        )}

        {sources.length > 0 && (
          <div className="message-sources">
            {sources.map((src) => (
              <span key={src} className="source-tag">
                <IconFile /> {src}
              </span>
            ))}
          </div>
        )}

        {/* Show indicator when streaming or when we have a completed path */}
        {(isStreaming || agentPath.length > 0) && !isError && (
          <AgentPathIndicator
            agentPath={agentPath}
            completedNodes={completedNodes}
            activeNode={activeNode}
            isStreaming={isStreaming}
          />
        )}
      </div>
    </div>
  );
}
