import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Dashboard from './pages/Dashboard'
import Strategies from './pages/Strategies'
import Journal from './pages/Journal'
import MT5Connect from './pages/MT5Connect'

function App() {
  return (
    <div className="min-h-screen bg-dashboard-bg">
      <Navbar />
      <main className="container mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/connect" element={<MT5Connect />} />
        </Routes>
      </main>
    </div>
  )
}

export default App