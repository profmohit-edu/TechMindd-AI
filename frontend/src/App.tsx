import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Generate from './pages/Generate'
import Jobs from './pages/Jobs'
import Packages from './pages/Packages'
import Knowledge from './pages/Knowledge'
import Plugins from './pages/Plugins'
import Providers from './pages/Providers'
import Settings from './pages/Settings'

export default function App(){return <Routes><Route element={<Layout/>}><Route index element={<Dashboard/>}/><Route path="generate" element={<Generate/>}/><Route path="jobs" element={<Jobs/>}/><Route path="packages" element={<Packages/>}/><Route path="knowledge" element={<Knowledge/>}/><Route path="plugins" element={<Plugins/>}/><Route path="providers" element={<Providers/>}/><Route path="settings" element={<Settings/>}/><Route path="*" element={<Navigate to="/"/>}/></Route></Routes>}
