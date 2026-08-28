# Roteiro do encontro com a Patrícia — testar as câmeras

> Leve o celular com o painel logado (`patricia@vargas.com`). Use o evento real
> dela (`8UY6`) só se ela topar misturar teste com produção; senão, crie um
> evento novo "Teste Câmera" e apague no fim.

1. **Fotografe o menu de rede das duas câmeras** (R8, T6s e a terceira, se
   existir mesmo um R6/R6 II). Procure "Transferência FTP" ou "FTP" no menu de
   Wi-Fi/Rede. **Não aceite "acho que tem"** — a R8 não tem, confirmado.

2. **Anote os modelos exatos** (corpo e versão). Isso decide o caminho de cada
   uma: só quem tem FTP no menu usa `/camera/config`; as outras vão por
   Camera Connect → celular → app.

3. Abra o painel, **crie o evento na hora, com ela operando** — cronometre.
   É o critério 5 do piloto: ela sozinha, sem você no ombro.

4. Mostre o QR e use **"testar foto"** no admin com uma foto que ela acabou de
   tirar — valida detecção de rosto em segundos, sem gastar crédito de evento.

5. **2 pessoas fazem selfie** no celular delas (não no seu). Confira: consentimento
   marcado, rosto reconhecido, entrada na galeria "minhas fotos".

6. **Rajada de 20 fotos**, cada câmera separadamente. Para cada uma, anote:
   - hora do disparo → hora que apareceu no celular do convidado (cronômetro)
   - quantas chegaram vs. quantas foram disparadas

7. **Teste o caminho do FTP direto**, se alguma câmera tiver: fotografe **antes**
   de abrir o evento — a foto tem que entrar sozinha quando o evento abrir
   (fila de pendentes, corrigido nesta semana). Sem isso, é bug novo.

8. **Olhe a faixa do painel** durante a rajada — o texto deve mudar
   ("X fotos a caminho" → "foto recebida agora"). Se ficar preso ou mentir,
   anote o que a tela dizia e o que estava realmente acontecendo.

9. **Confira uma foto ruim de propósito**: rosto de lado, contraluz, ou muito
   longe. Veja se o app avisa direito ("nenhum rosto detectado") em vez de
   travar ou dar erro genérico.

10. **No fim**, olhe `/admin/saude` com a senha do admin: alertas, disco,
    fila do FTP zerada. Se sobrar algo na fila, é sinal de foto perdida —
    investigar antes de fechar o dia.

## Preencher depois, em `docs/BENCHMARKS.md`

- Câmera / modelo / caminho usado (FTP ou celular)
- Fotos disparadas × fotos recebidas × perdidas
- P50 e P95 do disparo até aparecer no celular
- Quantas selfies reconheceram corretamente
- Qualquer erro, tela travada ou coisa que ela não entendeu sozinha

Isso é o material bruto para o **go/no-go** do piloto em `docs/PILOTO-1.md`.
