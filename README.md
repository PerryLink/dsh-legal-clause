# dsh-legal-clause

Legal clause tree, 12-key playbook mapping and unresolved report for DeepSeek Harness.

> **Status: alpha / public-synthetic / partial / not counted / not GA.** No customer evidence, customer data, or production-readiness claim. All acceptance rows are `counted=false`.

## Install

```sh
dsh plugin --profile <profile> add dsh-legal-clause
dsh --profile <profile> --dump-config | grep dsh-legal-clause
```

Requires DSH `>=0.2.1-rc.3 <0.3.0` and Node `>=24.9 <25`.

<details>
<summary>中文摘要</summary>

合同条款树、playbook 映射与未解决报告。 安装：`dsh plugin --profile <profile> add dsh-legal-clause`。公开/合成、alpha、非 GA。

</details>

## Tools

| Tool | What it does | Risk |
|---|---|---|
| `legal.playbook` | Load the default 12-key playbook | R0 |
| `legal.clause_tree` | Build a clause tree from legal text | R1 local write |
| `legal.playbook_register` | Register versioned custom playbook keys | R1 local write |
| `legal.playbook_check` | Compare a stored tree with a playbook and report missing/extra keys | R0 |
| `legal.export_tree` | Export the clause tree as JSON | R1 local write |

## Input / output

**Input:** contract text and a playbook (default 12-key or a registered version). **Output:** a clause tree, playbook coverage/unresolved report, and JSON export. This is a review aid, not legal advice.

## Configuration

| Env | Default | Meaning |
|---|---|---|
| `DSH_CLAUSE_HOME` | `$DSH_HOME/storages/dsh-legal-clause` | local domain and exports |

## Limits / non-claims

- No redline/diff/apply, no contract rewriting, no e-signature, and no Client surface.
- No legal conclusion or enforceability opinion; outputs are structural checks.
- MIT NDA sample only; no customer contract.
- No customer evidence, customer data, or production-readiness claim; all fixtures are public/synthetic.

## Public sample

MIT NDA sample and a public clause-tree test; `ACCEPTANCE.csv` lists 5 public checks.

## Development

```sh
pnpm install --frozen-lockfile
pnpm build && pnpm lint && pnpm typecheck && pnpm test && pnpm gate:sku10
```

## License

Apache-2.0. See `LICENSE`, `NOTICE`, `THIRD-PARTY-NOTICES`.
