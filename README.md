# Brasil em perspectiva

Dashboard público e exploratório para comparar indicadores econômicos, propostas
legislativas e votações parlamentares no Brasil. A comparação é descritiva: não
atribui resultados econômicos exclusivamente a um governo nem presume motivações
pessoais a partir do voto. O projeto não é um canal oficial de candidatura ou partido.

## O que o site apresenta

- Séries econômicas e sociais incorporadas ao projeto, com cobertura de 2003 a 2024.
- Exemplos de propostas e seus status legislativos, com links para fontes públicas.
- Votações nominais de Flávio Bolsonaro consultadas na API oficial do Senado, além
  de suporte opcional a CSV documentado na própria aplicação.
- Relatório que relaciona o voto Sim/Não à direção expressamente descrita para a
  medida votada: por exemplo, Sim em um item que propõe reduzir a maioridade penal
  é classificado como favorável à redução. Abstenção, obstrução e ausência não são
  convertidas em posicionamento; descrições sem uma medida concreta ficam sem
  classificação.

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

O site não precisa de segredos para iniciar. O limite de upload configurado é de
5 MB, com validação adicional de tamanho e linhas no código. Os CSVs enviados são
usados na sessão da aplicação e não são gravados pelo projeto em disco.

## Testes

Com o ambiente virtual ativado:

```powershell
python -m unittest discover -s tests -v
```
