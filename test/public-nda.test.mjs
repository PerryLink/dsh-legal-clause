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
  const tree = tools.find((tool) => tool.name === 'legal.clause_tree')
  const result = await tree.execute({ contract_text: text, contract_id: 'public-nda' }, { callId: 'public-nda' })
  assert.ok(result.clauses >= 5)
})
