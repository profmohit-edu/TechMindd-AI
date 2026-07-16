import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { Boxes, BrainCircuit, BriefcaseBusiness, Database, Gauge, Menu, Moon, Plug, Settings, Sparkles, Sun, X } from 'lucide-react'

const links=[['/',Gauge,'Dashboard'],['/generate',Sparkles,'Generate'],['/jobs',BriefcaseBusiness,'Jobs'],['/packages',Boxes,'Packages'],['/knowledge',Database,'Knowledge Base'],['/plugins',Plug,'Plugins'],['/providers',BrainCircuit,'Providers'],['/settings',Settings,'Settings']] as const
export default function Layout(){
 const [open,setOpen]=useState(false); const [dark,setDark]=useState(()=>localStorage.theme!=='light')
 useEffect(()=>{document.documentElement.classList.toggle('dark',dark);localStorage.theme=dark?'dark':'light'},[dark])
 return <div className="min-h-screen text-slate-900 dark:text-slate-100">
  <aside className={`fixed inset-y-0 left-0 z-40 w-72 border-r border-slate-200 bg-white p-5 transition-transform dark:border-slate-800 dark:bg-slate-950 lg:translate-x-0 ${open?'translate-x-0':'-translate-x-full'}`}>
   <div className="mb-8 flex items-center justify-between"><div className="flex items-center gap-3"><div className="grid size-10 place-items-center rounded-xl bg-cyan-500 text-slate-950"><BrainCircuit/></div><div><b>TechMindd AI</b><p className="text-xs text-slate-500">Content operations</p></div></div><button className="lg:hidden" onClick={()=>setOpen(false)}><X/></button></div>
   <nav className="space-y-1">{links.map(([to,Icon,label])=><NavLink key={to} to={to} end={to==='/'} onClick={()=>setOpen(false)} className={({isActive})=>`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium ${isActive?'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400':'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900'}`}><Icon size={18}/>{label}</NavLink>)}</nav>
   <div className="absolute inset-x-5 bottom-5 rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-4"><p className="text-xs font-semibold text-cyan-600 dark:text-cyan-400">ENGINE STATUS</p><p className="mt-1 flex items-center gap-2 text-sm"><span className="size-2 rounded-full bg-emerald-500"/>Ready for production</p></div>
  </aside>
  {open&&<button aria-label="Close menu" className="fixed inset-0 z-30 bg-slate-950/50 lg:hidden" onClick={()=>setOpen(false)}/>}
  <div className="lg:pl-72"><header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200/80 bg-white/80 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80 sm:px-8"><button className="lg:hidden" onClick={()=>setOpen(true)}><Menu/></button><div className="hidden text-sm text-slate-500 sm:block">AI content command center</div><button className="rounded-xl border border-slate-200 p-2 dark:border-slate-700" onClick={()=>setDark(!dark)}>{dark?<Sun size={18}/>:<Moon size={18}/>}</button></header><main className="p-4 sm:p-8"><Outlet/></main></div>
 </div>
}
