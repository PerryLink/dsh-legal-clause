# 故障排查 — dsh-legal-clause

每条按「症状 / 原因 / 动作」写。报错原文都是 `<一句人话>（E_XXX）｜下一步：<动作>`，
把 `E_XXX` 和这句话一起发到 issue 即可定位；不要把客户合同贴进 issue。

## 1. 合同文本是空的（E_CLAUSE_EMPTY）

- **症状**：`合同文本是空的，没有任何条款可以拆（E_CLAUSE_EMPTY）｜下一步：粘贴或选择一份带“1.”“2.”编号的纯文本合同`
- **原因**：`contract_text` 传了空字符串，或选中的文件是 0 字节 / 只有空白。
- **动作**：先确认 `.txt` 文件里有正文；把合同正文直接粘进工具参数，或换一份文件再跑 `legal.clause_tree`。

## 2. 找不到条款编号（E_CLAUSE_TREE_INVALID）

- **症状**：`这段文本里找不到“1.”这种条款编号（E_CLAUSE_TREE_INVALID）｜下一步：把每个条款改成单独一行、以“1.”开头再试`
- **原因**：PDF/Word 转出来的文本把编号丢了，或条款用的是「第一条」这类没有阿拉伯数字的写法。
- **动作**：在 Word/记事本里把每个条款改成单独一行、以 `1.`、`2.` 开头；扫描件请先做 OCR，再重跑。

## 3. 导出文件名被拒绝（E_LEGAL_PATH_INVALID）

- **症状**：`导出文件名里有不允许的字符（E_LEGAL_PATH_INVALID）｜下一步：把合同编号改成只用字母、数字、点和短横线，例如 CONTRACT-001`
- **原因**：合同编号里有 `/`、`..`、空格或中文，导出时会写到允许目录之外。
- **动作**：给 `legal.clause_tree` 传一个纯 ASCII 的 `contract_id`（如 `NDA-2026-001`），再调用 `legal.export_tree`。

## 还不行

```sh
node samples/quickstart/run.mjs --check   # 自带样例必须通过
node --test test/*.test.mjs               # 25 项测试
```

仍失败时请在 <https://github.com/PerryLink/dsh-legal-clause/issues> 附上：包版本、最小合成输入、完整报错那一行。
