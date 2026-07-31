# Implementações Futuras

## Contexto

Este documento registra um ponto importante do projeto: o algoritmo atual é simples e eficiente para a fase inicial, mas ainda possui limitações em casos de escrita não literal, como erros de digitação ou variações de palavras.

## Exemplo de limitação

Um exemplo claro é a palavra "acabate", usada de forma intencional para simular uma variação que o sistema poderia interpretar de maneira incorreta. Para o computador, "abacate" e "acabate" são palavras diferentes, porque a comparação é feita de forma direta e não entende o contexto de typo ou de brincadeira.

## O que isso significa

- O algoritmo pode errar em alguns cenários.
- Esse comportamento é aceitável para a versão atual.
- O objetivo atual não é alcançar perfeição, mas sim manter uma solução simples e funcional.

## Evolução futura

Em uma próxima etapa, esse tipo de situação pode ser tratado com uma biblioteca específica de Python para correção de palavras, como o SymSpellPy.

### Objetivo da melhoria

A ideia é usar a biblioteca para reconhecer e corrigir variações comuns de escrita, como:

- "acabate" → "abacate"
- erros leves de digitação
- pequenas diferenças ortográficas

### Benefício esperado

Com essa melhoria, o sistema ficará mais robusto para textos reais, sem perder a simplicidade da abordagem atual.

## Observação final

Essa melhoria deve ser vista como uma evolução incremental do projeto, e não como uma exigência da versão atual. O foco inicial é manter o comportamento "bom o suficiente" enquanto o modelo cresce.
