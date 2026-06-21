import { useState, useRef, useEffect } from 'react';
import Spinner from '../common/Spinner';

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('');
  const [useSearch, setUseSearch] = useState(false);
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 180)}px`;
  }, [text]);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const q = text.trim();
    if (!q || disabled) return;
    onSend(q, useSearch);
    setText('');
  }

  return (
    <div className="chat-input-area">
      <div className="chat-input-inner">
        <div className="chat-input-box">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            placeholder="输入问题…（Enter 发送，Shift+Enter 换行）"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={disabled}
          />
          <div className="chat-input-actions">
            <label
              className="search-toggle"
              title="开启后，当本地文档无法回答时自动搜索网络"
            >
              <input
                type="checkbox"
                checked={useSearch}
                onChange={(e) => setUseSearch(e.target.checked)}
              />
              <span className={`toggle-track ${useSearch ? 'on' : ''}`}>
                <span className="toggle-thumb" />
              </span>
              启用网络搜索
            </label>

            <button
              className="send-btn"
              onClick={submit}
              disabled={disabled || !text.trim()}
            >
              {disabled ? <Spinner size={13} /> : null}
              {disabled ? '生成中…' : '发送'}
            </button>
          </div>
        </div>
        <div className="chat-hint">DocMind 可能出错，请核实重要信息</div>
      </div>
    </div>
  );
}
