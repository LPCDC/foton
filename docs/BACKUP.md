# BACKUP.md — o que protege o acervo, e o que ainda não protege

> Item #9 da lista de infra do dono: *"backup restaurável testado — não apenas
> 'backup existe'"*. Este documento existe porque a frase estava certa: havia cópia
> diária e **nenhuma nunca tinha sido restaurada**. Backup que nunca foi restaurado não
> é backup — é a esperança de que um dia vá funcionar.
>
> Data: 2026-08-30.

## O que existe hoje

`/usr/local/bin/foton-backup` (criado por `infra/instalar-foton.sh`), disparado por um
timer do systemd, uma vez por dia:

```
sqlite3 /var/lib/foton/foton.db ".backup /var/lib/foton/backup/foton-$(date +%u).db"
  || cp /var/lib/foton/foton.db /var/lib/foton/backup/foton-$(date +%u).db
```

`date +%u` é o dia da semana (1–7): são **7 cópias rotativas**, uma por dia, sobrescritas
a cada semana.

## A prova de restauração (novo)

`infra/restaurar-teste.sh` pega a cópia mais recente, restaura numa pasta temporária e
verifica — **sem tocar no banco de produção**:

1. a idade do backup (avisa se o timer parou: > 48 h reprova);
2. `PRAGMA integrity_check` — o SQLite conferindo a si mesmo, o único veredito que vale
   sobre corrupção;
3. cada tabela que importa é legível e quantas linhas tem;
4. **a maior foto abre**: confere que o BLOB começa com a assinatura de JPEG (`FFD8FF`).
   Contar linhas não prova que a foto veio inteira — um BLOB truncado conta igual;
5. compara com o banco vivo; backup com **mais** fotos que produção é alarme (alguém
   apagou dados?).

Sai `0` se o backup presta, `1` se não presta.

```bash
ssh ubuntu@152.67.46.113 'bash -s' < infra/restaurar-teste.sh
```

**Validado nos dois sentidos (2026-08-30)** — um teste que só passa nunca provou nada:

| cenário | resultado |
|---|---|
| backup íntegro (5 fotos) | `BACKUP RESTAURAVEL`, saída **0** |
| backup com 5 000 bytes corrompidos de propósito | `BACKUP NAO CONFIAVEL`, saída **1**, `integrity_check` acusou schema malformado |

## O que o backup atual NÃO protege — em ordem de gravidade

### 1. Perder a máquina (o buraco grande) — `RESOLVIDO (2026-08-31, ADR-0031)`

As cópias locais moram em `/var/lib/foton/backup`, **no mesmo disco da mesma VM** que o
banco. Isso protege contra apagar por engano e contra corrupção do arquivo — mas sozinho
**não protegia contra perder a VM** — falha de disco, instância encerrada pela Oracle (é
Always Free: pode ser recuperada por inatividade), conta suspensa.

> **Era o único risco irreversível do sistema.** Agora não é mais: `infra/backup-externo.sh`
> rodou em produção (Cloud Shell, com o dono logado) e provou funcionando —
> **`foton-2026-08-31.db` (54 MB) enviado e confirmado no bucket `foton-backup`
> (Cloudflare R2)**. Timer diário instalado (`foton-backup-externo.timer`, roda depois
> do backup local), credenciais gravadas só na VM (`/root/.config/rclone`, modo 600),
> retenção de 30 dias lá fora. Detalhe completo em `docs/DECISIONS.md` ADR-0031.
> **54 MB** também resolve o `UNKNOWN` de tamanho do banco que este documento tinha.

### 2. Corrupção silenciosa vence a rotação — `RESOLVIDO FORA, ABERTO DENTRO`

A rotação é por dia da semana: 7 dias. Se o banco corromper e ninguém notar em uma
semana, **todas as cópias já foram sobrescritas pela versão corrompida**. Correção
barata: rodar `restaurar-teste.sh` pelo timer, e não gravar por cima quando ele reprovar.

### 3. O `cp` de emergência não é seguro — `ABERTO`

Se o `sqlite3` não estiver instalado, o script cai para `cp`. Copiar um SQLite **em uso,
em modo WAL**, com `cp` pode gerar arquivo inconsistente — e o pior tipo de inconsistente:
o que parece ter funcionado. O `.backup` do próprio SQLite existe justamente para isso.
Correção: falhar ruidosamente em vez de usar `cp`.

### 4. Ninguém era avisado — `RESOLVIDO PELA METADE`

Agora existe a prova, mas ela é **manual**. Enquanto não estiver no timer com aviso, ainda
depende de alguém lembrar.

## Ordem recomendada

1. ~~**Cópia para fora da VM**~~ — **feito** (2026-08-31): risco virou "perco um dia",
   não mais "perco tudo".
2. `restaurar-teste.sh` no timer diário, com o backup recusando sobrescrever quando reprovar.
3. Tirar o `cp` de emergência.
4. (novo) Rodar `restaurar-teste.sh` puxando a cópia **do R2** de volta, não só a local —
   prova de restauração completa a partir da nuvem ainda não existe.

**Medido (2026-08-31):** tamanho real do banco em produção = **54 MB** (era `UNKNOWN`).

`UNKNOWN — REQUIRES EXPERIMENT`: quanto tempo leva uma restauração completa **a partir
do R2** em produção (aqui, num banco sintético local, foi instantâneo — não é a mesma
coisa que puxar de volta da nuvem).
