import { AppProvider, useApp } from './context/AppContext';
import Sidebar from './components/Sidebar/Sidebar';
import ChatWindow from './components/Chat/ChatWindow';
import DocumentsPage from './components/Documents/DocumentsPage';

function AppInner() {
  const { state } = useApp();

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main">
        {state.currentView === 'chat' ? <ChatWindow /> : <DocumentsPage />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppInner />
    </AppProvider>
  );
}
