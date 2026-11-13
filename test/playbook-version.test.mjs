import test from 'node:test'
import assert from 'node:assert/strict'
import { createTools } from '../lib/plugin/tools.js'
class T { map=new Map(); get(k){return this.map.get(k)}; entries(){return this.map.entries()}; get size(){return this.map.size}; async put(k,v){this.map.set(k,v)} }
test('custom playbook version drives coverage', async () => {
  const contracts = new T(), playbooks = new T()
  const tools = createTools({ contracts, playbooks, baseDir: '/tmp/legal-playbook' })
  const by = Object.fromEntries(tools.map((tool) => [tool.name, tool]))
  const tree = await by['legal_clause_tree'].execute({ contract_text: '1. CONFIDENTIALITY\nKeep it secret.\n2. GOVERNING LAW\nDelaware.', contract_id: 'c1' }, { callId: 'p' })
  await by['legal_playbook_register'].execute({ version: 'v2', keys: ['confidentiality', 'governing_law'] }, { callId: 'p' })
  const check = await by['legal_playbook_check'].execute({ contract_id: tree.contract_id, version: 'v2' }, { callId: 'p' })
  assert.equal(check.coverage, 1)
  assert.deepEqual(check.missing, [])
})
