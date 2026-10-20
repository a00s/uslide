# Proposta futura: tampa dos reservatórios com troca de CO2

## Objetivo

Reduzir a evaporação da gota nos dois reservatórios e permitir troca gasosa com uma atmosfera de CO2. Esta é uma proposta de módulo futuro, ainda sem STL/3MF porque as dimensões dos poços do modelo original não correspondem com segurança às dimensões do protótipo físico mostrado nas fotos.

## Conceito

Usar uma pequena tampa independente em cada reservatório:

1. Um aro rígido externo (PC ou PETG) apoia no topo do colar TPU e limita o deslocamento da tampa.
2. A tampa tem um rebaixo para prender uma membrana hidrofóbica permeável a gases, com área útil voltada para uma pequena câmara de ar acima do líquido.
3. O perímetro da tampa fecha por pressão leve contra o colar, sem atravessar nem obstruir o canal em U.
4. A câmara interna reduz a área de líquido exposta. A membrana permite troca gasosa; não se deve presumir que ela impeça a passagem de vapor de água.
5. A incubação em atmosfera umidificada com CO2 continua necessária para limitar a evaporação. Uma membrana aberta ao ar ambiente não garante balanço de CO2 nem retenção de água.

## Montagem sugerida para o protótipo

- Imprimir o corpo/aro rígido em PC ou PETG, conforme temperatura de aquecimento e compatibilidade com os líquidos de limpeza usados.
- Usar um disco de membrana hidrofóbica comercial apropriada para cultura celular e para o solvente/esterilização pretendidos. Dimensionar o rebaixo e o método de retenção a partir da ficha do produto escolhido.
- Não imprimir a membrana em TPU: a permeabilidade a CO2 e vapor depende da formulação, espessura e processo; não é conhecida para a peça atual.
- Testar primeiro perda de massa/volume e vazamento com água ou meio sem células, comparando sem tampa, tampa fechada e tampa com membrana em condição umidificada.

## Medidas necessárias antes de modelar

- Diâmetro externo, diâmetro interno e altura do colar de cada reservatório impresso.
- Diâmetro útil de abertura acima do líquido e espaço livre até o objetivo do microscópio.
- Material e espessura da membrana, diâmetro do disco e método de fixação recomendado pelo fabricante.
- Temperatura máxima da placa e se a tampa ficará instalada durante o aquecimento (a recomendação inicial é instalar depois de aquecer/resfriar).

## Limitações

A membrana permite troca gasosa, mas também pode permitir transporte de vapor. O controle confiável de evaporação requer ensaio no ambiente real de incubação. O módulo não faz parte do 3MF atual e não deve ser tratado como esterilizável, estéril ou validado para cultura celular sem validação própria.
