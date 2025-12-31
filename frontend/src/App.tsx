import { Routes, Route } from 'react-router-dom'
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

function App() {
  return (
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
      </Routes>
    </Layout>
  )
}

export default App
