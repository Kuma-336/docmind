import { createContext, useContext, useReducer, useEffect } from 'react';

function genId() {
  return `s-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
}

const initialState = {
  currentSessionId: null,
  sessionList: [],       // [{ id, title, createdAt }]
  currentView: 'chat',   // 'chat' | 'documents'
  messages: [],
  isSending: false,
};

function reducer(state, action) {
  switch (action.type) {

    case 'INIT':
      return { ...state, ...action.payload };

    case 'NEW_SESSION': {
      const id = genId();
      const session = { id, title: '新对话', createdAt: Date.now() };
      return {
        ...state,
        currentSessionId: id,
        sessionList: [session, ...state.sessionList],
        messages: [],
      };
    }

    case 'SWITCH_SESSION':
      return { ...state, currentSessionId: action.payload, messages: [] };

    case 'SWITCH_VIEW':
      return { ...state, currentView: action.payload };

    case 'ADD_MESSAGE': {
      const msgs = [...state.messages, action.payload];
      const isFirstUser =
        action.payload.role === 'user' &&
        state.messages.filter((m) => m.role === 'user').length === 0;
      const sessionList = isFirstUser
        ? state.sessionList.map((s) =>
            s.id === state.currentSessionId
              ? { ...s, title: action.payload.content.slice(0, 22).trim() || '新对话' }
              : s
          )
        : state.sessionList;
      return { ...state, messages: msgs, sessionList };
    }

    // Append streaming token to last assistant message
    case 'APPEND_TOKEN': {
      const msgs = [...state.messages];
      const idx = msgs.length - 1;
      if (idx >= 0 && msgs[idx].role === 'assistant') {
        msgs[idx] = { ...msgs[idx], content: msgs[idx].content + action.payload };
      }
      return { ...state, messages: msgs };
    }

    // Mark a node as completed (from SSE progress event)
    case 'ADD_COMPLETED_NODE': {
      const msgs = [...state.messages];
      const idx = msgs.length - 1;
      if (idx >= 0 && msgs[idx].role === 'assistant') {
        const nodes = msgs[idx].completedNodes ?? [];
        msgs[idx] = {
          ...msgs[idx],
          completedNodes: nodes.includes(action.node) ? nodes : [...nodes, action.node],
          activeNode: action.activeNode ?? null,
        };
      }
      return { ...state, messages: msgs };
    }

    // Set summarizer as actively running (when first token arrives)
    case 'SET_ACTIVE_NODE': {
      const msgs = [...state.messages];
      const idx = msgs.length - 1;
      if (idx >= 0 && msgs[idx].role === 'assistant') {
        msgs[idx] = { ...msgs[idx], activeNode: action.payload };
      }
      return { ...state, messages: msgs };
    }

    // Finalise the last assistant message (done or error)
    case 'FINALIZE_ASSISTANT': {
      const msgs = [...state.messages];
      const idx = msgs.length - 1;
      if (idx >= 0 && msgs[idx].role === 'assistant') {
        msgs[idx] = { ...msgs[idx], ...action.payload, isStreaming: false };
      }
      return { ...state, messages: msgs };
    }

    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };

    case 'SET_SENDING':
      return { ...state, isSending: action.payload };

    default:
      return state;
  }
}

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    const raw = localStorage.getItem('docmind_sessions');
    let sessionList = [];
    try { sessionList = raw ? JSON.parse(raw) : []; } catch {}
    if (sessionList.length === 0) {
      const id = genId();
      sessionList = [{ id, title: '新对话', createdAt: Date.now() }];
    }
    dispatch({ type: 'INIT', payload: { sessionList, currentSessionId: sessionList[0].id } });
  }, []);

  useEffect(() => {
    if (state.sessionList.length > 0) {
      localStorage.setItem('docmind_sessions', JSON.stringify(state.sessionList));
    }
  }, [state.sessionList]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() { return useContext(AppContext); }
