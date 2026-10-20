# U-Slide DIY para K1C

Câmara em D deitado, sem ilha central, entre slide de microscopia e cobrevidro, com corpo TPU 85A,
presilhas PLA e tampas eSUN TPU-LW. Desenvolvido para microscópio normal.

## Arquivos atuais

- [Projeto Creality Print 3MF](FINAL_K1C/U-Slide_K1C_FINAL.3mf)
- [Instruções e parâmetros](FINAL_K1C/LEIA-ME.txt)
- [G-code experimental do corpo TPU](FINAL_K1C/U-Slide_TPU_POCOS_SEQUENCIAIS_EXPERIMENTAL.gcode)
- [Visual das presilhas](revisao/CLIPES_LATERAIS/clipes_u_preview.png)

Pratos: 01 corpo TPU; 02 duas presilhas PLA; 03 tampa esquerda; 04 tampa direita.
O G-code do corpo contém trajetos personalizados que não são reproduzidos
simplesmente refatiando o 3MF. As presilhas e tampas são fatiadas a partir do projeto.

[Comparação U anterior / câmara D atual](revisao/CAMARA_D/camara_D_preview.png)

A abertura passou de408 para982mm², incluindo a limpeza do fundo dos
dois poços, mantendo altura0,4mm. Paredes dos poços,
clipes e tampas foram preservados; G-code do corpo atualizado.

## Fontes e conferência

- `revisao/SELAGEM`: corpo e sapatos dos poços.
- `revisao/CLIPES_LATERAIS`: presilhas atuais com parede externa fechada.
- `revisao/TAMPAS`: tampas e relatório `conferencia_conjunto_atual.json`.
- `revisao/SEQUENCIAL`: geração dos trajetos personalizados do corpo.
- `BASE_ORIGINAL` e `HISTORICO`: referências e versões anteriores.

A conferência CAD das tampas não encontrou interseção com corpo ou presilhas.
A expansão do TPU-LW, o encaixe real, a vedação, a folga das objetivas e a troca
de CO2 precisam ser avaliados fisicamente. O trajeto sequencial experimental do
corpo não tem a folga lateral do cabeçote confirmada.
