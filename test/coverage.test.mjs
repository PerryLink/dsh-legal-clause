import test from 'node:test'
import assert from 'node:assert/strict'
import { createTools } from '../lib/plugin/tools.js'

class T { map = new Map(); get(k){return this.map.get(k)}; entries(){return this.map.entries()}; get size(){return this.map.size}; async put(k,v){this.map.set(k,v)} }
const tools = Object.fromEntries(createTools({ contracts: new T(), baseDir: '/tmp/clause-coverage' }).map((t) => [t.name, t]))
const exec = { callId: 'cov' }

const twoClauses = '1. Confidentiality\nKeep it confidential.\n2. Governing law\nDelaware law applies.'
const full = [
  ['Confidentiality', 'confidential'], ['Limitation of liability', 'liability cap'], ['Indemnity', 'indemnify'],
  ['Termination', 'terminate'], ['Assignment', 'assignment'], ['Governing law', 'governing law'],
  ['Dispute resolution', 'arbitration'], ['Payment', 'invoice payment'], ['Price adjustment', 'price adjustment'],
  ['Intellectual property', 'intellectual property'], ['Warranty', 'warranty'], ['Data protection', 'data protection'],
].map(([title, body], i) => `${i + 1}. ${title}\n${body}.`).join('\n')

test('a two-clause contract reports the ten missing keys', async () => {
  const r = await tools['legal_coverage_check'].execute({ text: twoClauses }, exec)
  assert.equal(r.clauses, 2)
  assert.equal(r.mapped_keys.length, 2)
  assert.equal(r.missing_keys.length, 10)
  assert.ok(Math.abs(r.coverage_pct - 16.67) < 0.01)
})

test('a full playbook contract reaches full coverage', async () => {
  const r = await tools['legal_coverage_check'].execute({ text: full }, exec)
  assert.equal(r.clauses, 12)
  assert.deepEqual(r.missing_keys, [])
  assert.equal(r.coverage_pct, 100)
})

test('coverage is a ratio over the twelve playbook keys', async () => {
  const r = await tools['legal_coverage_check'].execute({ text: twoClauses }, exec)
  assert.equal(r.mapped_keys.length + r.missing_keys.length, 12)
})
