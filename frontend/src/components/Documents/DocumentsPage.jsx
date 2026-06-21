import { useState } from 'react';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import './Documents.css';

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="docs-page">
      <div className="docs-header">
        <h2>文档管理</h2>
        <p>上传的文档将自动向量化并加入检索库，支持 .pdf、.txt、.md 格式</p>
      </div>
      <div className="docs-body">
        <DocumentUpload onSuccess={() => setRefreshKey((k) => k + 1)} />
        <DocumentList refreshKey={refreshKey} />
      </div>
    </div>
  );
}
