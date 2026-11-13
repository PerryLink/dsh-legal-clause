import test from 'node:test'
import assert from 'node:assert/strict'
import { createTools } from '../lib/plugin/tools.js'

class T {
  map = new Map()
  get(k) { return this.map.get(k) }
  entries() { return this.map.entries() }
  get size() { return this.map.size }
  async put(k, v) { this.map.set(k, v) }
}

// The model wire format only accepts names matching ^[a-zA-Z0-9_-]+$.
// A dotted name (the 0.1.x "legal.<tool>" style) is rejected by the provider
// with `Invalid 'tools[N].name'` and takes the whole tools array down with it,
// so the plugin registers but no request that carries the tools can succeed.
// See PerryLink/dsh-legal-clause#9.
const WIRE_NAME = /^[a-zA-Z0-9_-]+$/

test('every registered tool name is a valid model wire name', () => {
  const tools = createTools({ contracts: new T(), baseDir: '/tmp/legal-wire' })
  assert.equal(tools.length, 7)
  for (const tool of tools) {
    assert.match(tool.name, WIRE_NAME, `${tool.name} would be rejected by the provider`)
    assert.ok(!tool.name.includes('.'), `${tool.name} must not contain a dot`)
    assert.ok(tool.name.startsWith('legal_'), `${tool.name} must keep the legal_ namespace`)
  }
  const names = tools.map((t) => t.name)
  assert.equal(new Set(names).size, names.length, 'tool names must be unique')
})
