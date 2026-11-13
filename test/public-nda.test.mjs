import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { createTools } from '../lib/plugin/tools.js'

class T {
  map = new Map()
  get(key) { return this.map.get(key) }
  entries() { return this.map.entries() }
  get size() { return this.map.size }
  async put(key, value) { this.map.set(key, value) }
}

test('public MIT NDA clause tree', async () => {
  const text = readFileSync(path.resolve(process.cwd(), 'fixtures/public/mit/sample_nda.txt'), 'utf8')
  const tools = createTools({ contracts: new T(), baseDir: '/tmp/legal-clause-public' })
  const tree = tools.find((tool) => tool.name === 'legal_clause_tree')
  const result = await tree.execute({ contract_text: text, contract_id: 'public-nda' }, { callId: 'public-nda' })
  assert.ok(result.clauses >= 5)
})

test('public MIT NDA playbook check', async () => {
  const text = readFileSync(path.resolve(process.cwd(), 'fixtures/public/mit/sample_nda.txt'), 'utf8')
  const tools = createTools({ contracts: new T(), baseDir: '/tmp/legal-clause-public' })
  const by = Object.fromEntries(tools.map((tool) => [tool.name, tool]))
  const tree = await by['legal_clause_tree'].execute({ contract_text: text, contract_id: 'public-nda-2' }, { callId: 'nda' })
  const check = await by['legal_playbook_check'].execute({ contract_id: tree.contract_id }, { callId: 'nda' })
  assert.ok(check.present.includes('confidentiality'))
  assert.ok(check.present.includes('governing_law'))
  assert.ok(check.missing.length > 0)
})
