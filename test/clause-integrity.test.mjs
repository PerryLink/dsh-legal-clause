import test from 'node:test'
import assert from 'node:assert/strict'
import { createTools } from '../lib/plugin/tools.js'

class T { map = new Map(); get(k){return this.map.get(k)}; entries(){return this.map.entries()}; get size(){return this.map.size}; async put(k,v){this.map.set(k,v)} }
const tools = Object.fromEntries(createTools({ contracts: new T(), baseDir: '/tmp/clause-integrity' }).map((t) => [t.name, t]))
const exec = { callId: 'integrity' }

test('duplicate and missing clause numbers are reported', async () => {
  const r = await tools['legal.clause_integrity'].execute({ text: '1. Confidentiality\nKeep it confidential.\n3. Termination\nEither party may terminate.\n3. Governing law\nGoverned by law.' }, exec)
  assert.equal(r.clauses, 3)
  assert.ok(r.issues.some((i) => i.code === 'E_CLAUSE_NUMBER_DUPLICATE' && i.clause_no === '3'))
  assert.ok(r.issues.some((i) => i.code === 'E_CLAUSE_NUMBER_GAP' && i.clause_no === '2'))
})

test('out-of-order numbering is reported once', async () => {
  const r = await tools['legal.clause_integrity'].execute({ text: '1. A\n3. B\n2. C' }, exec)
  const order = r.issues.filter((i) => i.code === 'E_CLAUSE_NUMBER_ORDER')
  assert.equal(order.length, 1)
  assert.equal(order[0].clause_no, '2')
})

test('a clean 1..3 tree has no issues', async () => {
  const r = await tools['legal.clause_integrity'].execute({ text: '1. A\n2. B\n3. C' }, exec)
  assert.equal(r.clauses, 3)
  assert.equal(r.issues.length, 0)
})
