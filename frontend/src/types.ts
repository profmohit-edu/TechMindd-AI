export type JobStatus = 'queued' | 'running' | 'completed' | 'failed'
export interface Job { job_id:string; topic:string; status:JobStatus; progress:number; current_stage:string; provider:string; workflow:string; error?:string|null; logs:string[] }
export interface Workflow { name:string; description:string; provider:string; plugins:string[]; validation:boolean; quality:boolean; reflection:boolean; parallel:boolean; output:string }
export interface Plugin { name:string; output_name:string; prompt_template:string; template:string }
export interface Provider { name:string; configured:boolean; priority:number|null; health:string }
export interface OutputFile { name:string; size:number; download_url:string }
export interface JobResult { job_id:string; package_metadata:Record<string, unknown>; output_files:OutputFile[]; download_urls:string[] }
export interface LearningSource { id:number; filename:string; page:number; chunk_id:number; relevance:number; excerpt:string }
export interface LearningResponse { domain:string; level:string; objective:string; question:string; explanation:string; concepts:string[]; steps:string[]; example:string; misconceptions:string[]; practice:string[]; next_learning:string[]; evidence_used:number[]; sources:LearningSource[]; provider:string }
