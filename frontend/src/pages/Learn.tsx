import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { BookOpenCheck, BrainCircuit, Database, LoaderCircle, Target } from 'lucide-react'
import { endpoints, errorMessage } from '../api'
import { PageHeader } from '../components/UI'

const samples = [
  {domain:'Artificial Intelligence',level:'beginner',objective:'Understand how a neural network learns',question:'Explain gradient descent and backpropagation, then give me a small practice checkpoint.'},
  {domain:'Engineering Applications',level:'intermediate',objective:'Plan a dependable predictive-maintenance workflow',question:'How should sensor data and anomaly detection be combined to identify equipment faults?'},
]

export default function Learn(){
 const [form,setForm]=useState(samples[0]); const learn=useMutation({mutationFn:endpoints.learn});
 const set=(key:string,value:string)=>setForm({...form,[key]:value});
 return <><PageHeader title="Technical Learning Assistant" description="Retrieve trusted technical context, then generate structured, source-grounded learning guidance."/>
 <div className="mb-5 flex flex-wrap gap-2">{samples.map((sample,index)=><button key={sample.domain} className="btn-secondary" onClick={()=>{setForm(sample);learn.reset()}}>Load scenario {index+1}: {sample.domain}</button>)}</div>
 <div className="grid gap-6 xl:grid-cols-[0.85fr_1.4fr]">
  <section className="panel p-6"><div className="mb-5 flex items-center gap-3"><Target className="text-cyan-500"/><div><h2 className="font-semibold">Learner objective</h2><p className="text-xs text-slate-500">This input controls retrieval and assistance.</p></div></div>
   <label className="mb-4 block text-sm font-medium">Technical domain<input className="input mt-1.5" value={form.domain} onChange={e=>set('domain',e.target.value)}/></label>
   <label className="mb-4 block text-sm font-medium">Learning level<select className="input mt-1.5" value={form.level} onChange={e=>set('level',e.target.value)}><option>beginner</option><option>intermediate</option><option>advanced</option></select></label>
   <label className="mb-4 block text-sm font-medium">Learning objective<textarea className="input mt-1.5 min-h-20" value={form.objective} onChange={e=>set('objective',e.target.value)}/></label>
   <label className="block text-sm font-medium">Technical question<textarea className="input mt-1.5 min-h-32" value={form.question} onChange={e=>set('question',e.target.value)}/></label>
   <button className="btn-primary mt-5 w-full" disabled={learn.isPending} onClick={()=>learn.mutate(form)}>{learn.isPending?<LoaderCircle className="animate-spin" size={18}/>:<BrainCircuit size={18}/>}Retrieve and explain</button>
   {learn.isError&&<p className="mt-4 rounded-xl bg-rose-500/10 p-3 text-sm text-rose-600">{errorMessage(learn.error)}</p>}
  </section>
  <section className="space-y-5">{!learn.data?<div className="panel grid min-h-96 place-items-center p-8 text-center"><div><BookOpenCheck className="mx-auto mb-4 text-cyan-500" size={44}/><h2 className="text-xl font-semibold">Grounded assistance appears here</h2><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">Retrieved evidence remains visibly separate from AI-generated explanation and practice guidance.</p></div></div>:<>
   <div className="panel border-l-4 border-l-violet-500 p-6"><p className="text-xs font-bold uppercase tracking-widest text-violet-500">AI-generated explanation · {learn.data.provider}</p><h2 className="mt-3 text-xl font-semibold">{learn.data.objective}</h2><p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">{learn.data.explanation}</p><div className="mt-4 flex flex-wrap gap-2">{learn.data.evidence_used.map(id=><span key={id} className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600">Grounded in source {id}</span>)}</div></div>
   <div className="grid gap-5 md:grid-cols-2"><ListCard title="Key concepts" items={learn.data.concepts}/><ListCard title="Learning steps" items={learn.data.steps} numbered/><ListCard title="Common misconceptions" items={learn.data.misconceptions}/><ListCard title="Practice checkpoints" items={learn.data.practice} numbered/></div>
   <div className="panel p-6"><h3 className="font-semibold">Worked example</h3><p className="mt-2 leading-7 text-slate-600 dark:text-slate-300">{learn.data.example}</p><h3 className="mt-5 font-semibold">Next learning</h3><ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-slate-600 dark:text-slate-300">{learn.data.next_learning.map(x=><li key={x}>{x}</li>)}</ul></div>
   <div className="panel p-6"><div className="mb-4 flex items-center gap-2"><Database className="text-emerald-500"/><div><h3 className="font-semibold">Retrieved source context</h3><p className="text-xs text-slate-500">Deterministic retrieval evidence — separate from generated guidance</p></div></div><div className="space-y-3">{learn.data.sources.map(source=><article key={source.id} className="rounded-xl border border-slate-200 p-4 dark:border-slate-700"><div className="flex flex-wrap justify-between gap-2 text-xs font-semibold"><span>SOURCE {source.id} · {source.filename} · page {source.page}</span><span className="text-emerald-600">relevance {source.relevance.toFixed(3)}</span></div><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{source.excerpt}</p></article>)}</div></div>
  </>}</section>
 </div></>
}

function ListCard({title,items,numbered=false}:{title:string;items:string[];numbered?:boolean}){const Tag=numbered?'ol':'ul';return <div className="panel p-5"><h3 className="font-semibold">{title}</h3><Tag className={`${numbered?'list-decimal':'list-disc'} mt-3 space-y-2 pl-5 text-sm leading-6 text-slate-600 dark:text-slate-300`}>{items.map(x=><li key={x}>{x}</li>)}</Tag></div>}
