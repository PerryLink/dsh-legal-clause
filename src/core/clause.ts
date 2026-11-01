export type ClauseErrorCode='E_CLAUSE_EMPTY'|'E_CLAUSE_TREE_INVALID'|'E_CLAUSE_EXPORT_FAILED'
export class ClauseError extends Error{readonly code:ClauseErrorCode;constructor(code:ClauseErrorCode,message:string){super(`${code}: ${message}`);this.name='ClauseError';this.code=code}}
export const PLAYBOOK=[
 {key:'confidentiality',category:'risk',title:'Confidentiality'},
 {key:'liability',category:'risk',title:'Limitation of Liability'},
 {key:'indemnity',category:'risk',title:'Indemnity'},
 {key:'termination',category:'control',title:'Termination'},
 {key:'assignment',category:'control',title:'Assignment'},
 {key:'governing_law',category:'control',title:'Governing Law'},
 {key:'dispute',category:'control',title:'Dispute Resolution'},
 {key:'payment',category:'commercial',title:'Payment'},
 {key:'price_adjustment',category:'commercial',title:'Price Adjustment'},
 {key:'ip',category:'commercial',title:'Intellectual Property'},
 {key:'warranty',category:'performance',title:'Warranty'},
 {key:'data_protection',category:'performance',title:'Data Protection'},
] as const
export type ClauseKey=typeof PLAYBOOK[number]['key']
const KEYWORDS:Record<ClauseKey,RegExp>={confidentiality:/confidential|保密/i,liability:/liability|责任限制|责任上限/i,indemnity:/indemn|赔偿|补偿/i,termination:/terminat|解除|终止/i,assignment:/assign|转让/i,governing_law:/governing law|适用法律|管辖/i,dispute:/dispute|arbitrat|诉讼|仲裁/i,payment:/payment|付款|账期/i,price_adjustment:/price adjustment|调价|价格调整/i,ip:/intellectual property|知识产权|著作权/i,warranty:/warrant|保证|质保/i,data_protection:/data protection|personal data|数据保护|个人信息/i}
export function parseClauses(text:string){if(!text.trim())throw new ClauseError('E_CLAUSE_EMPTY','empty contract');const lines=text.split(/\r?\n/);const starts:{no:string;title:string;body:string}[]=[];for(const line of lines){const m=/^\s*(\d+(?:\.\d+)*)[.)]?\s+(.+)$/.exec(line);if(m){starts.push({no:m[1]!,title:m[2]!.trim(),body:m[2]!});}else if(starts.length){starts[starts.length-1]!.body+=`\n${line}`}}if(!starts.length)throw new ClauseError('E_CLAUSE_TREE_INVALID','no numbered clauses');return starts.map(c=>{const scores=PLAYBOOK.map(p=>({key:p.key,score:(c.body.match(KEYWORDS[p.key])?2:0)+(KEYWORDS[p.key].test(c.title)?3:0)})).sort((a,b)=>b.score-a.score);const best=scores[0]!;const total=scores.reduce((s,x)=>s+x.score,0);return{clause_no:c.no,title:c.title,clause_key:best.score>0?best.key:'unresolved',confidence:best.score>0?Math.min(1,0.6+best.score/10):0,text_hash:Buffer.from(c.body).toString('base64').slice(0,16),unmapped:best.score===0}})}

export interface ClauseIntegrityIssue { code: string; clause_no: string; detail: string }
export function clauseIntegrity(clauses: { clause_no: string; title: string }[]): ClauseIntegrityIssue[] {
  const issues: ClauseIntegrityIssue[] = []
  const seen = new Set<string>()
  for (const c of clauses) {
    if (seen.has(c.clause_no)) issues.push({ code: 'E_CLAUSE_NUMBER_DUPLICATE', clause_no: c.clause_no, detail: 'clause number appears more than once' })
    else seen.add(c.clause_no)
  }
  const top = [...new Set(clauses.map((c) => Number(c.clause_no.split('.')[0])).filter((n) => Number.isInteger(n) && n > 0))].sort((a, b) => a - b)
  if (top.length) {
    for (let n = 1; n <= top[top.length - 1]!; n += 1) {
      if (!top.includes(n)) issues.push({ code: 'E_CLAUSE_NUMBER_GAP', clause_no: String(n), detail: 'top-level clause number is missing' })
    }
  }
  let previousMajor = 0
  for (const c of clauses) {
    const major = Number(c.clause_no.split('.')[0])
    if (Number.isInteger(major) && major < previousMajor) {
      issues.push({ code: 'E_CLAUSE_NUMBER_ORDER', clause_no: c.clause_no, detail: 'clause appears after a higher-numbered clause' })
    }
    if (Number.isInteger(major)) previousMajor = major
  }
  return issues
}
