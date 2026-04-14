# Backup, Restore e Continuidade Operacional

Este documento padroniza a contingencia operacional da aplicacao.

## 1. O que entra no backup

Os scripts da Sprint 4 empacotam:

- `.env`
- banco SQLite da instancia
- exportacoes em `data/exports/`
- manifesto do backup com metadados operacionais

## 2. O que fica fora do backup

Nao entram no pacote:

- `.venv`
- logs em `data/logs/`
- pid files em `data/run/`
- codigo da aplicacao clonado do Git

Motivo:

- virtualenv pode ser recriada com `make setup`
- logs e pid files sao artefatos operacionais descartaveis
- o codigo-fonte continua vindo do repositorio versionado

## 3. Onde os backups ficam

Padrao do projeto:

- `data/backups/`

Formato:

- `insightflow_backup_<timestamp>_<label>.tar.gz`

## 4. Comando de backup

Observacao:

- se `sqlite3` estiver disponivel, o script usa snapshot online do banco
- se `sqlite3` nao estiver disponivel, o script exige stack parada para copiar o arquivo SQLite com seguranca

### Local / WSL

```bash
scripts/backup.sh manual
```

Ou via Make:

```bash
make backup BACKUP_LABEL=manual
```

### EC2

```bash
cd ~/apps/agente-feedback-conversacional
scripts/backup.sh ec2-manual
```

## 5. Comando de restore

### Restore no projeto atual

Importante:

- pare a aplicacao antes
- use `--yes` para confirmar sobrescrita

```bash
scripts/restore.sh data/backups/insightflow_backup_20260414_130000_manual.tar.gz --yes
```

O restore atual:

- restaura `.env`
- restaura banco SQLite
- restaura exportacoes
- cria um snapshot de seguranca `pre_restore_*` antes de sobrescrever o ambiente atual
- roda `alembic upgrade head` se a virtualenv da instancia existir

### Restore em ambiente de teste

```bash
scripts/restore.sh data/backups/insightflow_backup_20260414_130000_manual.tar.gz --target-dir /tmp/insightflow-restore
```

## 6. Comando de validacao

Para validar um backup sem tocar na instancia atual:

```bash
scripts/backup_verify.sh data/backups/insightflow_backup_20260414_130000_manual.tar.gz
```

A validacao:

- executa restore em diretorio temporario
- confirma a presenca de `.env`
- confirma a restauracao do banco SQLite
- executa `pragma integrity_check` se `sqlite3` estiver disponivel

## 7. Frequencia recomendada

Para o estagio atual do produto:

- antes de mudancas sensiveis de configuracao
- antes de atualizar branch ou aplicar migration em EC2
- antes de demo importante
- ao final do dia quando houver coleta ou analise relevante

## 8. Procedimento de contingencia

Se a instancia falhar:

1. Pare a aplicacao
2. Identifique o ultimo backup valido em `data/backups/`
3. Rode `scripts/backup_verify.sh <arquivo>`
4. Rode `scripts/restore.sh <arquivo> --yes`
5. Suba a stack novamente
6. Valide:
   - `GET /health`
   - login do admin
   - lista de sessoes
   - detalhe de uma sessao
   - uma exportacao CSV ou PDF

## 9. Limite conhecido

O backup automatizado atual foi desenhado para as instancias SQLite do projeto.

Se a instancia usar banco externo no futuro:

- o script continua salvando `.env` e exportacoes
- o banco deve ser protegido por snapshot nativo do provedor
