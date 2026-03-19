import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { PromptsPage } from './pages/PromptsPage'
import { PromptEditorPage } from './pages/PromptEditorPage'
import { TaskBuilderPage } from './pages/TaskBuilderPage'
import { TaskExecutionPage } from './pages/TaskExecutionPage'
import { ConversationViewerPage } from './pages/ConversationViewerPage'
import { APIKeysPage } from './pages/APIKeysPage'
import { SearchPage } from './pages/SearchPage'
import { SettingsPage } from './pages/SettingsPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token')
  if (!token) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/prompts"
          element={
            <ProtectedRoute>
              <PromptsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/prompts/new"
          element={
            <ProtectedRoute>
              <PromptEditorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/prompts/:id"
          element={
            <ProtectedRoute>
              <PromptEditorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tasks"
          element={
            <ProtectedRoute>
              <TaskBuilderPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tasks/:id"
          element={
            <ProtectedRoute>
              <TaskBuilderPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/executions/:id"
          element={
            <ProtectedRoute>
              <TaskExecutionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/conversations/:id"
          element={
            <ProtectedRoute>
              <ConversationViewerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys"
          element={
            <ProtectedRoute>
              <APIKeysPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <SearchPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
