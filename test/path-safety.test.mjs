import test from 'node:test'
import assert from 'node:assert/strict'
import { access, mkdir, mkdtemp, readFile, realpath, rm, symlink, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { LegalError, safeExportPath } from '../lib/core/safe-path.js'
import { createTools } from '../lib/plugin/tools.js'

class T { map = new Map(); get(k) { return this.map.get(k) }; entries() { return this.map.entries() }; get size() { return this.map.size }; async put(k, v) { this.map.set(k, v) } }

const temp = () => mkdtemp(path.join(os.tmpdir(), 'dsh-legal-path-'))
const code = (expected) => (error) => {
  assert.ok(error instanceof LegalError)
  assert.equal(error.code, expected)
  return true
}

test('a normal export filename resolves inside the base directory and is writable', async () => {
  const dir = await temp()
  try {
    const file = await safeExportPath(dir, 'contract_abc123.json')
    assert.equal(file, path.join(await realpath(dir), 'contract_abc123.json'))
    await writeFile(file, '{"ok":true}')
    assert.equal(await readFile(file, 'utf8'), '{"ok":true}')
  } finally { await rm(dir, { recursive: true, force: true }) }
})

test('parent traversal is rejected with E_LEGAL_PATH_INVALID', async () => {
  const dir = await temp()
  try {
    await assert.rejects(() => safeExportPath(dir, '../evil.json'), code('E_LEGAL_PATH_INVALID'))
  } finally { await rm(dir, { recursive: true, force: true }) }
})

test('a separator in the filename is rejected with E_LEGAL_PATH_INVALID', async () => {
  const dir = await temp()
  try {
    await assert.rejects(() => safeExportPath(dir, 'a/b.json'), code('E_LEGAL_PATH_INVALID'))
  } finally { await rm(dir, { recursive: true, force: true }) }
})

test('an overlong filename is rejected with E_LEGAL_PATH_INVALID', async () => {
  const dir = await temp()
  try {
    await assert.rejects(() => safeExportPath(dir, `${'a'.repeat(121)}.json`), code('E_LEGAL_PATH_INVALID'))
  } finally { await rm(dir, { recursive: true, force: true }) }
})

test('a dot-only filename is rejected by the resolved-prefix check', async () => {
  const dir = await temp()
  try {
    await assert.rejects(() => safeExportPath(dir, '..'), code('E_LEGAL_PATH_NOT_ALLOWED'))
    await assert.rejects(() => safeExportPath(dir, '.'), code('E_LEGAL_PATH_NOT_ALLOWED'))
  } finally { await rm(dir, { recursive: true, force: true }) }
})

test('a symlinked export directory is re-anchored on its realpath', async () => {
  const dir = await temp()
  try {
    const real = path.join(dir, 'real')
    const link = path.join(dir, 'link')
    await mkdir(real)
    await symlink(real, link, 'dir')
    const file = await safeExportPath(link, 'ok.json')
    assert.ok(file.startsWith((await realpath(real)) + path.sep), file)
  } finally { await rm(dir, { recursive: true, force: true }) }
})

test('the export tool refuses a traversal contract id', async () => {
  const dir = await temp()
  try {
    const baseDir = path.join(dir, 'store')
    const by = Object.fromEntries(createTools({ contracts: new T(), baseDir }).map((tool) => [tool.name, tool]))
    const exec = { callId: 'path' }
    await by['legal.clause_tree'].execute({ contract_text: '1. Confidentiality\nSecret.', contract_id: '../evil' }, exec)
    await assert.rejects(() => by['legal.export_tree'].execute({ contract_id: '../evil' }, exec), code('E_LEGAL_PATH_INVALID'))
    await assert.rejects(() => access(path.join(baseDir, 'evil.json')))
  } finally { await rm(dir, { recursive: true, force: true }) }
})
