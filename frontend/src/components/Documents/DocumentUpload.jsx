import { useState, useRef } from 'react';
import { uploadDocument } from '../../api/client';

const ALLOWED = ['.pdf', '.txt', '.md'];

export default function DocumentUpload({ onSuccess }) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [toast, setToast] = useState(null); // { type: 'success'|'error', text }
  const inputRef = useRef(null);

  function showToast(type, text) {
    setToast({ type, text });
    setTimeout(() => setToast(null), 4000);
  }

  async function handleFile(file) {
    if (!file) return;
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      showToast('error', `不支持的文件格式：${ext}，仅支持 .pdf、.txt、.md`);
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      const result = await uploadDocument(file, setProgress);
      showToast('success', `${result.filename} 上传成功（${result.chunk_count} 个分块）`);
      onSuccess?.();
    } catch (err) {
      showToast('error', err.message);
    } finally {
      setUploading(false);
      setProgress(0);
      if (inputRef.current) inputRef.current.value = '';
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  function onInputChange(e) {
    handleFile(e.target.files?.[0]);
  }

  return (
    <div>
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
        onClick={() => !uploading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          className="upload-input"
          accept=".pdf,.txt,.md"
          onChange={onInputChange}
        />
        <div className="upload-icon">⬆</div>
        <div className="upload-text">
          {uploading ? '上传中…' : '点击选择文件或拖拽到此处'}
        </div>
        <div className="upload-hint">支持 .pdf、.txt、.md，最大 20MB</div>

        {uploading && (
          <div className="upload-progress">
            <div className="upload-progress-bar" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>

      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.type === 'success' ? '✓' : '✕'} {toast.text}
        </div>
      )}
    </div>
  );
}
