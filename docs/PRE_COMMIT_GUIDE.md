# Pre-commit Hooks - Guia de Uso

Sistema de validação automática de código antes de commits para o projeto VOXY Agents.

## 🎯 Objetivo

Garantir que **nenhum código com problemas de qualidade** seja commitado, executando automaticamente:

- ✅ **Black** - Formatação de código
- ✅ **Ruff** - Linting e auto-fix
- ✅ **Mypy** - Type checking
- ✅ **General Checks** - Trailing whitespace, end of files, YAML syntax, etc.

---

## 📥 Instalação (Apenas uma vez)

```bash
cd /mnt/d/Projeto-Voxy/voxy/backend

# Instalar pre-commit hooks no repositório git
poetry run pre-commit install

# Output esperado:
# pre-commit installed at .git/hooks/pre-commit
# pre-commit installed at .git/hooks/pre-push
```

---

## 🚀 Uso Automático

**Os hooks executam automaticamente** ao fazer `git commit`:

```bash
# Stage seus arquivos
git add src/voxy_agents/api/fastapi_server.py

# Commitar (hooks executam automaticamente)
git commit -m "feat: Add new endpoint"

# Output:
# Black - Code Formatter...................................Passed ✅
# Ruff - Linter & Auto-fixer...............................Passed ✅
# Mypy - Type Checker......................................Passed ✅
# Trim Trailing Whitespace.................................Passed ✅
# ...
# [main abc1234] feat: Add new endpoint
```

---

## 🔧 Uso Manual

### Testar todos os arquivos

```bash
# Executar todos os hooks em todos os arquivos
poetry run pre-commit run --all-files

# Útil após:
# - Instalar pre-commit pela primeira vez
# - Modificar .pre-commit-config.yaml
# - Resolver problemas em múltiplos arquivos
```

### Testar um hook específico

```bash
# Apenas Black
poetry run pre-commit run black --all-files

# Apenas Ruff
poetry run pre-commit run ruff --all-files

# Apenas Mypy
poetry run pre-commit run mypy --all-files
```

### Testar apenas arquivos staged

```bash
# Executar hooks apenas nos arquivos prontos para commit
poetry run pre-commit run
```

---

## ⚠️ Quando os Hooks Falham

### Cenário 1: Auto-fix (Black/Ruff)

Se Black ou Ruff modificarem arquivos automaticamente:

```bash
git add src/voxy_agents/api/fastapi_server.py
git commit -m "feat: Add endpoint"

# Output:
# Black - Code Formatter...................................Failed ❌
# Files were modified by this hook.

# Solução: Re-adicionar arquivos modificados
git add src/voxy_agents/api/fastapi_server.py
git commit -m "feat: Add endpoint"  # Agora passa ✅
```

### Cenário 2: Erros de Type (Mypy)

Se Mypy encontrar erros de tipo:

```bash
# Output:
# Mypy - Type Checker......................................Failed ❌
# src/voxy_agents/api/fastapi_server.py:42: error: Name "status" is not defined

# Solução: Corrigir o erro manualmente
# 1. Editar o arquivo
# 2. Adicionar import faltante
# 3. Re-commitar
```

### Cenário 3: Erros de Linting (Ruff)

Se Ruff encontrar erros que não pode auto-fixar:

```bash
# Output:
# Ruff - Linter & Auto-fixer...............................Failed ❌
# src/voxy_agents/main.py:31:1: E402 Module level import not at top of file

# Solução: Verificar pyproject.toml
# - Este erro já está ignorado em per-file-ignores
# - Se não estiver, adicionar ao pyproject.toml ou corrigir código
```

---

## 🚨 Bypass (Emergências APENAS)

**NÃO RECOMENDADO!** Use apenas em emergências:

```bash
# Pular todos os hooks (não faça isso!)
git commit --no-verify -m "emergency fix"

# ⚠️ Consequências:
# - Código com problemas entra no repositório
# - Pode quebrar builds de CI/CD
# - Outros devs podem ter problemas
```

---

## 📋 Hooks Configurados

### 1. Black - Code Formatter

- **Ordem**: 1º (executa primeiro)
- **Ação**: Formata código automaticamente
- **Auto-fix**: ✅ Sim
- **Configuração**: `pyproject.toml` → `[tool.black]`
- **Exemplo**:
  ```python
  # Antes
  x=[1,2,3]

  # Depois (Black auto-formata)
  x = [1, 2, 3]
  ```

### 2. Ruff - Linter & Auto-fixer

- **Ordem**: 2º (após Black)
- **Ação**: Verifica PEP 8, imports, unused variables, etc.
- **Auto-fix**: ✅ Parcial (alguns erros)
- **Configuração**: `pyproject.toml` → `[tool.ruff]`
- **Exemplo**:
  ```python
  # Ruff detecta
  import os  # F401: Unused import

  # Ruff auto-remove
  # (import removido)
  ```

### 3. Mypy - Type Checker

- **Ordem**: 3º (último dos principais)
- **Ação**: Verifica type hints e type safety
- **Auto-fix**: ❌ Não
- **Configuração**: `pyproject.toml` → `[tool.mypy]`
- **Exemplo**:
  ```python
  # Mypy detecta
  def foo(x: int) -> str:
      return x  # error: Incompatible return value type

  # Correção manual necessária
  def foo(x: int) -> str:
      return str(x)  # ✅
  ```

### 4. General Checks

- **Trailing whitespace**: Remove espaços no final das linhas
- **End of files**: Garante newline no final dos arquivos
- **YAML syntax**: Valida arquivos .yaml
- **Large files**: Bloqueia arquivos > 1MB
- **Merge conflicts**: Detecta marcadores de conflito
- **Debug statements**: Detecta `breakpoint()`, `pdb.set_trace()`

---

## 🔍 Troubleshooting

### Problema: "poetry: command not found"

```bash
# Solução: Ativar Poetry environment
cd /mnt/d/Projeto-Voxy/voxy/backend
poetry shell
```

### Problema: "pre-commit: command not found"

```bash
# Solução: Reinstalar pre-commit
poetry install
poetry run pre-commit install
```

### Problema: Hooks não executam ao commitar

```bash
# Verificar se hooks estão instalados
ls -la .git/hooks/pre-commit

# Se não existir, reinstalar
poetry run pre-commit install
```

### Problema: Mypy muito lento

```bash
# Mypy verifica todo src/ a cada commit
# Isso é necessário para validar imports corretamente

# Solução: Usar commits menores e mais frequentes
# Ou: Skip mypy em commits WIP
git commit --no-verify -m "WIP: partial implementation"
```

---

## 📊 Performance

Tempo médio de execução (projeto com 53 arquivos):

- **Black**: ~2s
- **Ruff**: ~3s
- **Mypy**: ~8s (verifica todo src/)
- **General Checks**: ~1s
- **Total**: ~14s

**Dica**: Use commits menores para validação mais rápida.

---

## 🔄 Atualizar Configuração

Se modificar `.pre-commit-config.yaml`:

```bash
# 1. Limpar cache
poetry run pre-commit clean

# 2. Reinstalar hooks
poetry run pre-commit install --install-hooks

# 3. Testar
poetry run pre-commit run --all-files
```

---

## 📝 Arquivos Relacionados

- `.pre-commit-config.yaml` - Configuração dos hooks
- `pyproject.toml` - Configuração de Black, Ruff, Mypy
- `.git/hooks/pre-commit` - Hook instalado pelo pre-commit
- `PRE_COMMIT_GUIDE.md` - Este guia (você está aqui!)

---

## 🎓 Boas Práticas

1. **✅ Sempre execute os hooks**: Não use `--no-verify` a menos que seja emergência
2. **✅ Commits pequenos**: Menos arquivos = validação mais rápida
3. **✅ Fix antes de commit**: Corrija erros antes de commitar, não depois
4. **✅ Teste localmente**: Use `pre-commit run --all-files` antes de push
5. **❌ Não ignore erros**: Se Mypy falhou, corrija o código, não ignore

---

## 🚀 CI/CD Integration (Futuro)

Os mesmos checks podem rodar no GitHub Actions:

```yaml
# .github/workflows/quality.yml
- name: Run pre-commit
  run: poetry run pre-commit run --all-files
```

Benefícios:
- Garante que todos os PRs passem nos checks
- Evita merge de código com problemas
- Feedback automático em PRs

---

## 📞 Suporte

Problemas com pre-commit hooks?

1. Verificar este guia primeiro
2. Executar `poetry run pre-commit run --all-files --verbose`
3. Verificar logs em `/home/stefanogysin/.cache/pre-commit/pre-commit.log`
4. Reportar issue com output completo

---

**Pre-commit hooks instalados com sucesso! 🎉**

Agora seu código será validado automaticamente antes de cada commit.
