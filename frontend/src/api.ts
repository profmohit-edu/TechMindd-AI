import axios from 'axios'
import type { Job, JobResult, Plugin, Provider, Workflow } from './types'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000', timeout: 30000 })
export const endpoints = {
  jobs: () => api.get<Job[]>('/jobs').then(r => r.data),
  job: (id:string) => api.get<Job>(`/jobs/${id}`).then(r => r.data),
  result: (id:string) => api.get<JobResult>(`/jobs/${id}/result`).then(r => r.data),
  generate: (body:{topic:string;workflow:string;provider?:string}) => api.post<{job_id:string;status:string}>('/generate', body).then(r => r.data),
  retry: (id:string) => api.post<{job_id:string;status:string}>(`/jobs/${id}/retry`).then(r => r.data),
  workflows: () => api.get<Workflow[]>('/workflows').then(r => r.data),
  plugins: () => api.get<Plugin[]>('/plugins').then(r => r.data),
  providers: () => api.get<Provider[]>('/providers').then(r => r.data),
  uploadKnowledge: (file:File) => { const data=new FormData(); data.append('file',file); return api.post('/knowledge/upload',data).then(r=>r.data) },
  reindex: () => api.post('/knowledge/reindex').then(r=>r.data),
}
export function errorMessage(error:unknown) { return axios.isAxiosError(error) ? String(error.response?.data?.detail || error.message) : 'Something went wrong' }
