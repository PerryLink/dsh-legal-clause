export type ClauseErrorCode='E_CLAUSE_EMPTY'|'E_CLAUSE_TREE_INVALID'|'E_CLAUSE_EXPORT_FAILED'|'E_CLAUSE_TREE_NOT_FOUND'|'E_PLAYBOOK_INVALID'|'E_PLAYBOOK_NOT_FOUND'
/** User-facing text for every error code: one plain sentence plus one next action. */
const CLAUSE_HUMAN:Record<ClauseErrorCode,{text:string;next:string}>={
 E_CLAUSE_EMPTY:{text:'合同文本是空的，没有任何条款可以拆',next:'粘贴或选择一份带“1.”“2.”编号的纯文本合同'},
 E_CLAUSE_TREE_INVALID:{text:'这段文本里找不到“1.”这种条款编号',next:'把每个条款改成单独一行、以“1.”开头再试'},
 E_CLAUSE_EXPORT_FAILED:{text:'条款树导出失败，没有写出 JSON 文件',next:'确认导出目录可写，或换一个合同编号'},
 E_CLAUSE_TREE_NOT_FOUND:{text:'找不到这个合同编号对应的条款树',next:'先用 legal_clause_tree 拆一次，再导出或检查'},
 E_PLAYBOOK_INVALID:{text:'自定义条款清单是空的，或者里面有重复的键',next:'给每个条款一个不重复的英文键名，至少保留一个'},
 E_PLAYBOOK_NOT_FOUND:{text:'找不到这个版本的自定义条款清单',next:'先用 legal_playbook_register 注册这个版本，再检查'},
}
/** `human sentence（E_CODE）｜Next: one action` — the only text shown to end users. */
export function clauseErrorMessage(code:ClauseErrorCode){const h=CLAUSE_HUMAN[code];return `${h.text}（${code}）｜下一步：${h.next}`}
export class ClauseError extends Error{readonly code:ClauseErrorCode;constructor(code:ClauseErrorCode){super(clauseErrorMessage(code));this.name='ClauseError';this.code=code}}
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
export function parseClauses(text:string){if(!text.trim())throw new ClauseError('E_CLAUSE_EMPTY');const lines=text.split(/\r?\n/);const starts:{no:string;title:string;body:string}[]=[];for(const line of lines){const m=/^\s*(\d+(?:\.\d+)*)[.)]?\s+(.+)$/.exec(line);if(m){starts.push({no:m[1]!,title:m[2]!.trim(),body:m[2]!});}else if(starts.length){starts[starts.length-1]!.body+=`\n${line}`}}if(!starts.length)throw new ClauseError('E_CLAUSE_TREE_INVALID');return starts.map(c=>{const scores=PLAYBOOK.map(p=>({key:p.key,score:(c.body.match(KEYWORDS[p.key])?2:0)+(KEYWORDS[p.key].test(c.title)?3:0)})).sort((a,b)=>b.score-a.score);const best=scores[0]!;const total=scores.reduce((s,x)=>s+x.score,0);return{clause_no:c.no,title:c.title,clause_key:best.score>0?best.key:'unresolved',confidence:best.score>0?Math.min(1,0.6+best.score/10):0,text_hash:Buffer.from(c.body).toString('base64').slice(0,16),unmapped:best.score===0}})}

export interface ClauseIntegrityIssue { code: string; clause_no: string; detail: string }
/** Above this top-level number the gap scan is not expanded (DoS guard). */
export const MAX_CLAUSE_NUMBER_SCAN = 5000
export function clauseIntegrity(clauses: { clause_no: string; title: string }[]): ClauseIntegrityIssue[] {
  const present = new Set<number>()
  let max = 0
  for (const c of clauses) {
    const major = Number(c.clause_no.split('.')[0])
    if (Number.isInteger(major) && major > 0) {
      present.add(major)
      if (major > max) max = major
    }
  }
  if (max > MAX_CLAUSE_NUMBER_SCAN) {
    return [{ code: 'E_CLAUSE_NUMBER_RANGE', clause_no: String(max), detail: `top-level clause number ${max} exceeds the ${MAX_CLAUSE_NUMBER_SCAN} scan limit; gaps are not expanded` }]
  }
  const issues: ClauseIntegrityIssue[] = []
  const seen = new Set<string>()
  for (const c of clauses) {
    if (seen.has(c.clause_no)) issues.push({ code: 'E_CLAUSE_NUMBER_DUPLICATE', clause_no: c.clause_no, detail: 'clause number appears more than once' })
    else seen.add(c.clause_no)
  }
  for (let n = 1; n <= max; n += 1) {
    if (!present.has(n)) issues.push({ code: 'E_CLAUSE_NUMBER_GAP', clause_no: String(n), detail: 'top-level clause number is missing' })
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
