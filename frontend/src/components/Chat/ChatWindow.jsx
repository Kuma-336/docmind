import { useEffect, useRef, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { streamChatMessage, getHistory } from '../../api/client';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import './Chat.css';

let _id = 0;
const newId = () => `m${++_id}`;

function historyToMessages(historyItems) {
  return historyItems.map((item) => ({
    id: newId(),
    role: item.role,
    content: item.content,
    isStreaming: false,
    agentPath: item.agent_path ?? [],
    sources: item.sources ?? [],
    completedNodes: [],
    activeNode: null,
    isError: false,
  }));
}

export default function ChatWindow() {
  const { state, dispatch } = useApp();
  const bottomRef = useRef(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // 切换/进入会话时拉取历史消息
  useEffect(() => {
    if (!state.currentSessionId) return;

    setLoadingHistory(true);
    getHistory(state.currentSessionId)
      .then((res) => {
        const msgs = historyToMessages(res.messages ?? []);
        dispatch({ type: 'SET_MESSAGES', payload: msgs });
      })
      .catch(() => {
        dispatch({ type: 'SET_MESSAGES', payload: [] });
      })
      .finally(() => setLoadingHistory(false));
  }, [state.currentSessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages]);

  async function handleSend(query, useSearch) {
    if (state.isSending || !state.currentSessionId) return;

    dispatch({ type: 'SET_SENDING', payload: true });

    dispatch({
      type: 'ADD_MESSAGE',
      payload: { id: newId(), role: 'user', content: query },
    });

    dispatch({
      type: 'ADD_MESSAGE',
      payload: {
        id: newId(),
        role: 'assistant',
        content: '',
        isStreaming: true,
        agentPath: [],
        sources: [],
        completedNodes: [],
        activeNode: null,
        isError: false,
      },
    });

    let firstToken = true;

    try {
      for await (const event of streamChatMessage(query, state.currentSessionId, useSearch)) {
        switch (event.type) {
          case 'token':
            if (firstToken) {
              dispatch({ type: 'SET_ACTIVE_NODE', payload: 'summarizer' });
              firstToken = false;
            }
            dispatch({ type: 'APPEND_TOKEN', payload: event.content });
            break;

          case 'progress':
            dispatch({ type: 'ADD_COMPLETED_NODE', node: event.node, activeNode: null });
            break;

          case 'done':
            dispatch({
              type: 'FINALIZE_ASSISTANT',
              payload: {
                agentPath: event.agent_path ?? [],
                sources: event.sources ?? [],
                activeNode: null,
              },
            });
            break;

          case 'error':
            dispatch({
              type: 'FINALIZE_ASSISTANT',
              payload: { content: `错误：${event.message}`, isError: true, activeNode: null },
            });
            break;
        }
      }
    } catch (err) {
      dispatch({
        type: 'FINALIZE_ASSISTANT',
        payload: { content: `请求失败：${err.message}`, isError: true, activeNode: null },
      });
    } finally {
      dispatch({ type: 'SET_SENDING', payload: false });
    }
  }

  if (loadingHistory) {
    return (
      <div className="chat-container">
        <div className="chat-messages">
          <div className="chat-empty">
            <div className="chat-empty-icon">◎</div>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 8 }}>加载历史消息…</p>
          </div>
        </div>
        <ChatInput onSend={handleSend} disabled={true} />
      </div>
    );
  }

  const isEmpty = state.messages.length === 0;

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {isEmpty ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">◎</div>
            <h3>DocMind 智能问答</h3>
            <p>上传文档后即可提问，支持流式输出与多 Agent 协作可视化。</p>
          </div>
        ) : (
          <div className="chat-messages-inner">
            {state.messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <ChatInput onSend={handleSend} disabled={state.isSending} />
    </div>
  );
}
