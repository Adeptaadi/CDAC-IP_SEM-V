import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/shell/AppShell';
import { SimulatePage } from './pages/SimulatePage';
import { InvestigatePage } from './pages/InvestigatePage';
import { HistoryPage } from './pages/HistoryPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { SystemPage } from './pages/SystemPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/simulate" replace />} />
          <Route path="/simulate" element={<SimulatePage />} />
          <Route path="/investigate" element={<InvestigatePage />} />
          <Route path="/investigate/:id" element={<InvestigatePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/system" element={<SystemPage />} />
          <Route path="*" element={<Navigate to="/simulate" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
