# COBOL AI Engine v2.6.0 - Release Notes

**Data de Lançamento**: 2025-09-10

Esta versão do COBOL AI Engine introduz a integração com o provedor LuzIA real, um sistema de prompts customizáveis e a capacidade de gerar documentação em formato PDF. Além disso, foram corrigidos vários bugs e melhorada a estabilidade geral do sistema.

## Novas Funcionalidades

- **Integração com LuzIA Real**: Agora é possível utilizar o provedor LuzIA real para análise de programas COBOL, com autenticação OAuth2 e controle de tokens.
- **Sistema de Prompts Customizáveis**: O novo sistema de prompts permite ao usuário customizar as perguntas de análise através do arquivo `config/prompts.yaml`.
- **Geração de PDF**: A documentação gerada em Markdown agora pode ser convertida para PDF utilizando a flag `--pdf`.

## Melhorias

- **Controle de Tokens**: O sistema de controle de tokens foi aprimorado para incluir limites por hora e por dia, evitando o uso excessivo de recursos.
- **Sistema de Fallback**: O sistema de fallback foi melhorado para garantir que a análise seja concluída mesmo que o provedor primário falhe.
- **Documentação**: Foram criados manuais de usuário e de configuração detalhados para facilitar o uso e a configuração do sistema.

## Correções

- Corrigidos vários erros de importação e inicialização de provedores que impediam a execução do sistema.
- Corrigidos erros no gerador de documentação que impediam a criação dos arquivos de saída.
- Estabilizada a execução do sistema com diferentes configurações de provedores.

## Arquivos Inclusos no Pacote

- Código fonte completo do COBOL AI Engine v2.6.0.
- Documentação completa, incluindo manuais de usuário e de configuração.
- Exemplos de arquivos de entrada (fontes e copybooks).
- Arquivos de configuração de exemplo.
- Evidências de teste, incluindo os arquivos de saída gerados.


