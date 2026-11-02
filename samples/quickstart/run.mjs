#!/usr/bin/env node
/**
 * dsh-legal-clause quickstart — runs the built plugin tools over the bundled
 * synthetic NDA. The golden file `expected/result.json` is the stdout of
 * `node samples/quickstart/run.mjs --json`, so it is a real run, not hand-written.
 *
 *   node samples/quickstart/run.mjs            # human-readable summary
 *   node samples/quickstart/run.mjs --json     # the golden result on stdout
 *   node samples/quickstart/run.mjs --check    # recompute and diff against the golden file
 */
import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createTools } from '../../lib/plugin/tools.js'

const here = path.dirname(fileURLToPath(import.meta.url))
const inputDir = path.join(here, 'input')
const expectedPath = path.join(here, 'expected', 'result.json')
const mode = process.argv.includes('--check') ? 'check' : process.argv.includes('--json') ? 'json' : 'summary'

class Table {
  map = new Map()
  get(key) { return this.map.get(key) }
  entries() { return this.map.entries() }
  get size() { return this.map.size }
  async put(key, value) { this.map.set(key, value) }
}

async function run() {
  const contractText = await readFile(path.join(inputDir, 'synthetic-nda-2026.txt'), 'utf8')
  const workDir = await mkdtemp(path.join(os.tmpdir(), 'dsh-legal-clause-quickstart-'))
  try {
    const tools = createTools({ contracts: new Table(), baseDir: path.join(workDir, 'store') })
    const byName = Object.fromEntries(tools.map((tool) => [tool.name, tool]))
    const call = { callId: 'quickstart' }

    const tree = await byName['legal.clause_tree'].execute(
      { contract_text: contractText, contract_id: 'NDA-2026-001' }, call,
    )
    const playbook = await byName['legal.playbook_check'].execute({ contract_id: 'NDA-2026-001' }, call)
    const integrity = await byName['legal.clause_integrity'].execute({ text: contractText }, call)
    const coverage = await byName['legal.coverage_check'].execute({ text: contractText }, call)
    const exported = await byName['legal.export_tree'].execute({ contract_id: 'NDA-2026-001' }, call)
    const exportedJson = JSON.parse(await readFile(exported.path, 'utf8'))

    return {
      sample: 'samples/quickstart/input/synthetic-nda-2026.txt',
      contract_id: tree.contract_id,
      clauses: tree.clauses,
      unresolved: tree.unresolved,
      present_keys: playbook.present,
      missing_keys: playbook.missing,
      coverage: playbook.coverage,
      coverage_pct: coverage.coverage_pct,
      integrity_issue_codes: integrity.issues.map((issue) => issue.code),
      export_file: path.basename(exported.path),
      export_clauses: exportedJson.clauses.length,
      export_has_clause_key: JSON.stringify(exportedJson).includes('clause_key'),
    }
  } finally {
    await rm(workDir, { recursive: true, force: true })
  }
}

const result = await run()

if (mode === 'json') {
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
} else if (mode === 'check') {
  const expected = JSON.parse(await readFile(expectedPath, 'utf8'))
  assert.deepEqual(result, expected)
  console.log('dsh-legal-clause quickstart - synthetic NDA (not a real contract)')
  console.log(`contract ${result.contract_id}: ${result.clauses} clauses, ${result.unresolved} unresolved`)
  console.log(`12-key playbook: ${result.present_keys.length} present, ${result.missing_keys.length} missing (${result.missing_keys.join(', ')})`)
  console.log(`clause-number issues: ${result.integrity_issue_codes.length}`)
  console.log(`export ${result.export_file}: ${result.export_clauses} clauses, clause_key=${result.export_has_clause_key}`)
  console.log(`golden samples/quickstart/expected/result.json matches`)
  console.log('quickstart ok')
} else {
  console.log('dsh-legal-clause quickstart - synthetic NDA (not a real contract)')
  console.log(`contract ${result.contract_id}: ${result.clauses} clauses, ${result.unresolved} unresolved`)
  console.log(`12-key playbook: ${result.present_keys.length} present, ${result.missing_keys.length} missing (${result.missing_keys.join(', ')})`)
  console.log(`clause-number issues: ${result.integrity_issue_codes.length}`)
  console.log(`export ${result.export_file}: ${result.export_clauses} clauses, clause_key=${result.export_has_clause_key}`)
  console.log('run with --check to compare against expected/result.json')
}
