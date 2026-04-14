# Operacao na EC2

Guia rapido para a instancia AWS EC2 do Insightflow.

## Subida manual

```bash
cd ~/apps/agente-feedback-conversacional
chmod +x 2.sh scripts/ec2_*.sh
scripts/ec2_bootstrap.sh
scripts/ec2_setup_app.sh
scripts/ec2_run_api.sh
scripts/ec2_run_admin.sh
scripts/ec2_status.sh
```

## Logs

```bash
scripts/ec2_logs.sh
scripts/ec2_logs.sh api
scripts/ec2_logs.sh admin
scripts/ec2_logs.sh nginx
```

## Sincronizar IP publico no .env

Quando o IP publico da EC2 mudar, atualize o `.env` com:

```bash
scripts/ec2_sync_public_ip.sh
```

Se quiser atualizar e reiniciar a aplicacao em seguida:

```bash
scripts/ec2_sync_public_ip.sh --restart
```

Os servicos `systemd` do projeto tambem executam essa sincronizacao automaticamente antes de subir API e admin.

## Transformar em servico permanente

```bash
scripts/ec2_install_systemd.sh
```

Depois disso, os servicos passam a ser controlados com:

```bash
sudo systemctl status insightflow-api --no-pager
sudo systemctl status insightflow-admin --no-pager
sudo journalctl -u insightflow-api -n 100 --no-pager
sudo journalctl -u insightflow-admin -n 100 --no-pager
```

## HTTPS

Importante:
- HTTPS confiavel com navegador exige dominio
- nao e recomendado tentar TLS valido apenas no IP publico

Quando o dominio ja estiver apontando para a EC2:

```bash
scripts/ec2_install_https.sh app.seudominio.com voce@seudominio.com
```

## Observacao

Hoje o admin esta publicado em:

- `/admin/`

E a API publica em:

- `/health`
- `/docs`
- `/api/`
- `/f/`
