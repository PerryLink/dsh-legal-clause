import path from'node:path';import type{Context}from'@deepseek-ai/cordis';import{createTools}from'./tools.js';import{openClause}from'./storage.js'
export const name='dsh-legal-clause';export const inject=['tools','storageDomain']
export async function apply(ctx:Context):Promise<void>{const baseDir=process.env.DSH_CLAUSE_HOME??path.join(process.env.DSH_HOME??process.cwd(),'storages','dsh-legal-clause');const contracts=await openClause(ctx);for(const t of createTools({contracts,baseDir}))ctx.tools.register(t)}
