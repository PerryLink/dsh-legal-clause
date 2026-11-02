import { mkdir, realpath } from 'node:fs/promises'
import path from 'node:path'

/** Error raised when an export path would leave the directory the caller owns. */
export type LegalErrorCode = 'E_LEGAL_PATH_INVALID' | 'E_LEGAL_PATH_NOT_ALLOWED'
const LEGAL_HUMAN: Record<LegalErrorCode, { text: string; next: string }> = {
  E_LEGAL_PATH_INVALID: {
    text: '导出文件名里有不允许的字符',
    next: '把合同编号改成只用字母、数字、点和短横线，例如 CONTRACT-001',
  },
  E_LEGAL_PATH_NOT_ALLOWED: {
    text: '导出路径跑到了允许目录之外',
    next: '只填文件名，不要带 / 或 ../',
  },
}
/** `human sentence（E_CODE）｜Next: one action` — the only text shown to end users. */
export function legalErrorMessage(code: LegalErrorCode) {
  const h = LEGAL_HUMAN[code]
  return `${h.text}（${code}）｜下一步：${h.next}`
}
export class LegalError extends Error {
  readonly code: LegalErrorCode
  constructor(code: LegalErrorCode) {
    super(legalErrorMessage(code))
    this.name = 'LegalError'
    this.code = code
  }
}

/** A single export filename component: no separators, no whitespace, max 120 chars. */
export const SAFE_EXPORT_FILENAME = /^[A-Za-z0-9._-]{1,120}$/

/**
 * Resolve a caller-supplied export filename inside a base directory.
 *
 * 1. the filename must be one safe component (`[A-Za-z0-9._-]{1,120}`);
 * 2. the resolved path must stay below `resolve(baseDir) + sep`;
 * 3. the directory is created with `mkdir -p` and the path is re-anchored on
 *    `realpath(baseDir)` so a symlinked directory cannot redirect the write
 *    outside the canonical base.
 */
export async function safeExportPath(baseDir: string, filename: string): Promise<string> {
  if (!SAFE_EXPORT_FILENAME.test(filename)) {
    throw new LegalError('E_LEGAL_PATH_INVALID')
  }
  const base = path.resolve(baseDir)
  const candidate = path.resolve(base, filename)
  if (!candidate.startsWith(base + path.sep)) {
    throw new LegalError('E_LEGAL_PATH_NOT_ALLOWED')
  }
  await mkdir(base, { recursive: true })
  const realBase = await realpath(base)
  const realCandidate = path.resolve(realBase, filename)
  if (!realCandidate.startsWith(realBase + path.sep)) {
    throw new LegalError('E_LEGAL_PATH_NOT_ALLOWED')
  }
  return realCandidate
}
