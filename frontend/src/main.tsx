import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import App from './App'
import './index.css'

const queryClient = new QueryClient({ defaultOptions:{ queries:{ staleTime:5000, retry:1 }, mutations:{ retry:0 } } })
createRoot(document.getElementById('root')!).render(
  <StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><App/><Toaster richColors position="top-right"/></BrowserRouter></QueryClientProvider></StrictMode>,
)
