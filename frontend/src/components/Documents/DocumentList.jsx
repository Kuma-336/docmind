import { useState, useEffect, useCallback } from 'react';
import { listDocuments, deleteDocument } from '../../api/client';
import Spinner from '../common/Spinner';

const PAGE_SIZE = 10;

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export default function DocumentList({ refreshKey }) {
  const [data, setData] = useState({ total: 0, page: 1, page_size: PAGE_SIZE, items: [] });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const load = useCallback(async (p = page) => {
    setLoading(true);
    try {
      const res = await listDocuments(p, PAGE_SIZE);
      setData(res);
      setPage(p);
    } catch (err) {
      console.error('获取文档列表失败:', err);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { load(1); }, [refreshKey]);  // Re-load when upload succeeds

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  async function handleDelete(fileId, filename) {
    if (!window.confirm(`确定要删除《${filename}》吗？此操作不可恢复，向量数据也将一并删除。`)) return;
    setDeletingId(fileId);
    try {
      await deleteDocument(fileId);
      // After delete, stay on current page or go to previous if page is now empty
      const newTotal = data.total - 1;
      const newTotalPages = Math.max(1, Math.ceil(newTotal / PAGE_SIZE));
      load(Math.min(page, newTotalPages));
    } catch (err) {
      alert(`删除失败：${err.message}`);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <div className="docs-list-header">
        <span className="docs-list-title">已上传文档</span>
        <span className="docs-count">{data.total} 个</span>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
          <Spinner /> 加载中…
        </div>
      ) : data.items.length === 0 ? (
        <div className="docs-empty">
          <div className="docs-empty-icon">⊘</div>
          <p>暂无文档，上传后可在对话中检索</p>
        </div>
      ) : (
        <>
          <table className="docs-table">
            <thead>
              <tr>
                <th>文件名</th>
                <th>大小</th>
                <th>上传时间</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((doc) => (
                <tr key={doc.file_id}>
                  <td><div className="doc-name" title={doc.filename}>{doc.filename}</div></td>
                  <td>{formatSize(doc.size)}</td>
                  <td>{formatDate(doc.uploaded_at)}</td>
                  <td>
                    <button
                      className="btn-delete"
                      onClick={() => handleDelete(doc.file_id, doc.filename)}
                      disabled={deletingId === doc.file_id}
                    >
                      {deletingId === doc.file_id ? '删除中…' : '删除'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="pagination">
              <button className="page-btn" onClick={() => load(page - 1)} disabled={page <= 1}>
                ← 上一页
              </button>
              <span>{page} / {totalPages}</span>
              <button className="page-btn" onClick={() => load(page + 1)} disabled={page >= totalPages}>
                下一页 →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
