import{defineDomain,domainTable}from'@deepseek-ai/dsh-storage-domain';import type{Context}from'@deepseek-ai/cordis';import{z}from'zod'
const playbook=z.object({version:z.string(),keys:z.array(z.string()),created_at:z.string()})
const tree=z.object({contract_id:z.string(),clauses:z.array(z.object({clause_no:z.string(),title:z.string(),clause_key:z.string(),confidence:z.number(),text_hash:z.string(),unmapped:z.boolean()})),unresolved:z.number(),coverage:z.number(),created_at:z.string()})
export type PlaybookRecord=z.infer<typeof playbook>;
export type TreeRecord=z.infer<typeof tree>;export type Table<T>={get(k:string):T|undefined;entries():IterableIterator<[string,T]>;size:number;put(k:string,v:T):Promise<void>}
export const clauseSpec=defineDomain({name:'legal_clause',version:1,tables:{contracts:domainTable<string,TreeRecord>(tree),playbooks:domainTable<string,PlaybookRecord>(playbook)}})
export async function openClause(ctx:Context){const d=await ctx.storageDomain.open(clauseSpec);ctx.effect(()=>()=>d.close(),'dsh-legal-clause.domainClose');return{contracts:d.table('contracts') as Table<TreeRecord>,playbooks:d.table('playbooks') as Table<PlaybookRecord>}}
