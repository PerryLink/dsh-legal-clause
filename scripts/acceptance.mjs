import{mkdtemp,rm,readFile}from'node:fs/promises';import{mkdirSync,writeFileSync}from'node:fs';import os from'node:os';import path from'node:path';import{createHash}from'node:crypto';import{createTools}from'../lib/plugin/tools.js'
class T{map=new Map();get(k){return this.map.get(k)};entries(){return this.map.entries()};get size(){return this.map.size};async put(k,v){this.map.set(k,v)}}
const titles=['Confidentiality','Limitation of Liability','Indemnity','Termination','Assignment','Governing Law','Dispute Resolution','Payment','Price Adjustment','Intellectual Property','Warranty','Data Protection'];const d=await mkdtemp(path.join(os.tmpdir(),'clause-acc-')),root=process.cwd(),run=`sku10-${Date.now()}`,ev=path.join(root,'evidence',run);mkdirSync(ev,{recursive:true});let trees=0,mapped=0,unres=0,exports=0
try{const ts=createTools({contracts:new T(),baseDir:path.join(d,'s')});const b=Object.fromEntries(ts.map(t=>[t.name,t]));for(let i=0;i<20;i++){const text=titles.map((t,j)=>`${j+1}. ${t}\n${t} clause body.`).join('\n');const r=await b['legal.clause_tree'].execute({contract_text:text},{callId:'a'});trees++;mapped+=r.clauses-r.unresolved;unres+=r.unresolved;const x=await b['legal.export_tree'].execute({contract_id:r.contract_id},{callId:'a'});if((await readFile(x.path,'utf8')).includes('clause_key'))exports++}}finally{await rm(d,{recursive:true,force:true})}
const pbTools=createTools({contracts:new T(),playbooks:new T(),baseDir:'/tmp/legal-pb'});const pb=Object.fromEntries(pbTools.map(t=>[t.name,t]));const pbTree=await pb['legal.clause_tree'].execute({contract_text:'1. CONFIDENTIALITY\nSecret.\n2. GOVERNING LAW\nDelaware.',contract_id:'pb1'},{callId:'a'});await pb['legal.playbook_register'].execute({version:'v2',keys:['confidentiality','governing_law']},{callId:'a'});const pbCheck=await pb['legal.playbook_check'].execute({contract_id:pbTree.contract_id,version:'v2'},{callId:'a'});const ms=[{i:'SKU-10-A01',m:'合同条款树（20）',t:'20/20',a:trees,p:trees===20},{i:'SKU-10-A02',m:'条款映射',t:'240',a:mapped,p:mapped===240},{i:'SKU-10-A03',m:'未映射',t:'0',a:unres,p:unres===0},{i:'SKU-10-A04',m:'JSON 导出',t:'20',a:exports,p:exports===20},{i:'SKU-10-A05',m:'自定义 playbook v2',t:'1/1',a:pbCheck.coverage===1?1:0,p:pbCheck.coverage===1}];const r={run_id:run,scope:'SKU-10-S1',status:'partial',counted:false,note:'synthetic contracts; user-approved public/synthetic; 0 real contracts',metrics:ms,pass:ms.every(x=>x.p)};const s=JSON.stringify(r,null,2)+'\n';writeFileSync(path.join(ev,'result.json'),s);const h=createHash('sha256').update(s).digest('hex');writeFileSync('ACCEPTANCE.csv','req_id,metric,threshold,actual,script,evidence_sha256,pass\n'+ms.map(x=>`${x.i},${x.m},${x.t},${x.a},scripts/acceptance.mjs,${h},${x.p}`).join('\n')+'\n');if(!r.pass){console.error(JSON.stringify(r));process.exit(1)};console.log('acceptance ok')


// Normalize the public-only acceptance schema: source + counted=false.
{
  const fs = await import('node:fs')
  const file = 'ACCEPTANCE.csv'
  const lines = fs.readFileSync(file, 'utf8').trim().split('\n')
  if (!lines[0].includes('source,counted')) {
    lines[0] += ',source,counted'
    for (let i = 1; i < lines.length; i += 1) lines[i] += ',public/synthetic,false'
    fs.writeFileSync(file, lines.join('\n') + '\n')
  }
}
