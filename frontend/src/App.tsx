import { Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import NewEntry from './pages/NewEntry'
import EntryDetail from './pages/EntryDetail'
import Patterns from './pages/Patterns'
import Recall from './pages/Recall'
import Analytics from './pages/Analytics'
import Revision from './pages/Revision'
import Recommendations from './pages/Recommendations'
import Plans from './pages/Plans'
import ReviewSession from './pages/ReviewSession'
import Graph from './pages/Graph'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewEntry />} />
          <Route path="/entry/:id" element={<EntryDetail />} />
          <Route path="/patterns" element={<Patterns />} />
          <Route path="/recall" element={<Recall />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/revision" element={<Revision />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/plans" element={<Plans />} />
          <Route path="/review" element={<ReviewSession />} />
          <Route path="/graph" element={<Graph />} />
        </Routes>
      </Layout>
    </QueryClientProvider>
  )
}

export default App
