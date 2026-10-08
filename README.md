# Brasil em perspectiva

Dashboard público e exploratório para comparar indicadores econômicos, propostas
legislativas e votações parlamentares no Brasil. A comparação é descritiva: não
atribui resultados econômicos exclusivamente a um governo nem presume motivações
pessoais a partir do voto. O projeto não é um canal oficial de candidatura ou partido.

## O que o site apresenta

- Séries econômicas e sociais incorporadas ao projeto, com cobertura de 2003 a 2024.
- Exemplos de propostas e seus status legislativos, com links para fontes públicas.
- Votações nominais de Flávio Bolsonaro consultadas na API oficial do Senado.
- Dados mantidos por curadoria no repositório, com referências a fontes oficiais;
  a aplicação não aceita arquivos para inserir ou substituir indicadores, propostas
  ou votações.
- Relatório que relaciona o voto Sim/Não à direção expressamente descrita para a
  medida votada: por exemplo, Sim em um item que propõe reduzir a maioridade penal
  é classificado como favorável à redução. Abstenção, obstrução e ausência não são
  convertidas em posicionamento; descrições sem uma medida concreta ficam sem
  classificação.
- Exportação do comparativo de dois períodos como PNG vertical 1080 × 1920,
  preparado para um Story do Instagram. A imagem inclui os oito indicadores do
  painel, mostra N/D quando não há dados e mantém notas metodológicas. A fonte
  Roboto é instalada pelas dependências do projeto para preservar acentos,
  cedilha e hífens também em ambientes de hospedagem sem fontes do sistema. Um
  checkbox permite incluir atribuições resumidas das fontes dos dados na imagem.
- Formulário para sugerir melhorias. Com a integração configurada, cada envio
  cria uma issue pública neste repositório; o formulário avisa sobre a publicação
  e exige consentimento antes do envio. Não inclua dados pessoais ou privados.

Os dados econômicos incorporados são aproximados e arredondados para exploração,
não projeções oficiais. Programas de transferência de renda, séries e metodologias
podem diferir entre períodos. A consulta legislativa depende de serviço externo e
pode ficar temporariamente indisponível. Confira as fontes e as notas metodológicas
na página antes de reutilizar os dados.

## Executar localmente

Requer Python 3.11 ou superior. No PowerShell, a partir da pasta do projeto:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Se `py` não estiver disponível, instale Python 3.11+ e repita os comandos com
`python` no lugar de `py -3.11`. O uso de `python -m pip` evita depender do comando
`pip` estar registrado separadamente no `PATH`.

Abra o endereço local indicado pelo Streamlit (normalmente
`http://localhost:8501`).

## Publicar como site

Uma opção simples é o [Streamlit Community Cloud](https://share.streamlit.io/):

1. Publique estes arquivos em um repositório GitHub acessível ao serviço. Não envie
   `.venv`, credenciais, arquivos `.env` ou dados privados.
2. No Streamlit Community Cloud, conecte o repositório e selecione a branch e o
   arquivo principal `app.py`.
3. O serviço instalará as dependências listadas em `requirements.txt`.
4. Acesse o endereço público fornecido e teste os links das fontes e a consulta ao
   Senado após a publicação.

O site funciona sem segredos, mas o formulário de ideias depende de um token do
GitHub com permissão mínima para criar issues neste repositório:

- **Streamlit Community Cloud:** adicione `GITHUB_TOKEN` em **App settings >
  Secrets**.
- **Execução local:** crie `.streamlit/secrets.toml` (já ignorado pelo Git) e
  inclua `GITHUB_TOKEN = "seu-token"`; alternativamente, defina a variável de
  ambiente `GITHUB_TOKEN`.

Use um fine-grained personal access token limitado a este repositório e com
permissão **Issues: Read and write**. Nunca inclua o token no código ou em arquivos
versionados. Sem o token, o formulário permanece visível, mas não permite enviar.
Não há upload de dados na aplicação. Atualizações do catálogo devem ser feitas no
repositório, após conferência em fontes oficiais, mantendo os links de origem e as
notas metodológicas junto aos dados.

## Testes

Com o ambiente virtual ativado:

```powershell
python -m unittest discover -s tests -v
```
