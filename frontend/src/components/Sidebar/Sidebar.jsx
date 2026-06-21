import { useApp } from '../../context/AppContext';
import './Sidebar.css';

const IconChat = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
);

const IconDocs = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
);

const IconPlus = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);

const IconHistory = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
);

export default function Sidebar() {
  const { state, dispatch } = useApp();

  function handleNewSession() {
    dispatch({ type: 'NEW_SESSION' });
    dispatch({ type: 'SWITCH_VIEW', payload: 'chat' });
  }

  function handleSwitchSession(id) {
    dispatch({ type: 'SWITCH_SESSION', payload: id });
    dispatch({ type: 'SWITCH_VIEW', payload: 'chat' });
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span>Doc</span>Mind
        </div>
        <button className="btn-new-chat" onClick={handleNewSession}>
          <IconPlus /> 新建对话
        </button>
      </div>

      <div className="sidebar-sessions">
        {state.sessionList.length > 0 && (
          <div className="sidebar-section-label">历史对话</div>
        )}
        {state.sessionList.map((s) => (
          <div
            key={s.id}
            className={`session-item ${s.id === state.currentSessionId ? 'active' : ''}`}
            onClick={() => handleSwitchSession(s.id)}
            title={s.title}
          >
            <IconHistory />
            <span className="session-title">{s.title}</span>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button
          className={`sidebar-nav-btn ${state.currentView === 'chat' ? 'active' : ''}`}
          onClick={() => dispatch({ type: 'SWITCH_VIEW', payload: 'chat' })}
        >
          <IconChat /> 对话
        </button>
        <button
          className={`sidebar-nav-btn ${state.currentView === 'documents' ? 'active' : ''}`}
          onClick={() => dispatch({ type: 'SWITCH_VIEW', payload: 'documents' })}
        >
          <IconDocs /> 文档管理
        </button>
      </div>
    </aside>
  );
}
