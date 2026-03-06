import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterOrgPage from './pages/RegisterOrgPage'
import DashboardPage from './pages/DashboardPage'
import RegionsPage from './pages/RegionsPage'
import RegionDetailPage from './pages/RegionDetailPage'
import AlertsPage from './pages/AlertsPage'
import ReadingsPage from './pages/ReadingsPage'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterOrgPage />} />

        {/* Protected routes wrapped in Layout */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/regions" element={<RegionsPage />} />
          <Route path="/regions/:id" element={<RegionDetailPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/readings" element={<ReadingsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
