import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Documents from '@/pages/Documents'
import Chat from '@/pages/Chat'
import Graph from '@/pages/Graph'
import Search from '@/pages/Search'
import Settings from '@/pages/Settings'
import Analysis from '@/pages/Analysis'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="documents" element={<Documents />} />
          <Route path="chat" element={<Chat />} />
          <Route path="graph" element={<Graph />} />
          <Route path="search" element={<Search />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App
