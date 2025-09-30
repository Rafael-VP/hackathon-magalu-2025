# PyQt System Blocker

Este projeto foi desenvolvido para o **Hackathon Magalu 2025**. É uma aplicação de desktop focada em produtividade, construída em Python com a biblioteca PyQt6. A ferramenta foi projetada para ajudar os usuários a manter o foco, evitando distrações digitais através de um timer, bloqueio de sites/aplicativos e análise do histórico de uso. Ademais, o sistema da Magalu Cloud foi utilizado de uma maneira criativa, pensada na produtividade, permitindo os usuários a sincronizarem seus dados, exortando a cooperação e atenção para tarefas importantes.

## Funcionalidades

* **Autenticação de Usuário:** Sistema de login e registro conectado a um servidor, permitindo uma experiência personalizada.
* **Timer Circular de Foco:** Uma interface de timer visual para gerenciar sessões de foco.
* **Bloqueador de Sites e Aplicativos:**
    * **Sites:** Interface aprimorada para adicionar e remover URLs de uma lista de bloqueio, que funciona através da edição do arquivo `hosts` do sistema.
    * **Aplicativos (Windows):** Permite ao usuário listar arquivos executáveis (`.exe`) para bloqueá-los durante o período de foco.
* **Histórico de Foco com Gráfico:** A aplicação salva a duração de cada sessão de foco e exibe um gráfico visual do tempo focado nos últimos dias.
* **Interface Simples:** Um design com tema escuro e componentes personalizados, incluindo uma barra de título própria para uma experiência de uso agradável.

## Como Funciona

A aplicação possui uma arquitetura cliente-servidor para autenticação. A lógica principal (`main.py`) controla a interface (`gui.py`) e as funcionalidades de bloqueio.

* **Bloqueio de Sites:** Adiciona entradas ao arquivo `hosts` do sistema para redirecionar o acesso a URLs listadas para `127.0.0.1`.
* **Bloqueio de Aplicativos (Windows):** Manipula o Registro do Windows para interceptar e impedir a execução de aplicativos especificados. **Isso exige que o programa seja executado com privilégios de administrador.**
* **Histórico de Sessões:** Salva os dados de tempo de foco em um arquivo `blocker_history.json` local, na pasta de dados do aplicativo do usuário.

## Pré-requisitos

* Python 3
* Bibliotecas Python: `PyQt6`, `requests`

## Como Executar

1.  Clone ou faça o download deste repositório.
2.  Instale as dependências necessárias:
    ```bash
    pip install PyQt6 requests
    ```
3.  Navegue até o diretório do projeto.
4.  Execute o script `main.py`. Lembre-se de **executar como administrador** no Windows para que as funcionalidades de bloqueio funcionem corretamente.
    ```bash
    python main.py
    ```
5.  A janela de login aparecerá. Crie um novo usuário ou entre com uma conta existente.

## Como Usar

### Utilizando o Timer
1.  Na aba **Timer**, defina o tempo desejado (horas, minutos e segundos).
2.  Clique em **Start** para iniciar a contagem regressiva.
3.  Clique em **Reset** para parar e reiniciar o timer. A duração da sessão será salva no seu histórico.

### Bloqueando Sites e Aplicativos
1.  Vá para a aba **Lista**.
2.  **Para bloquear sites:**
    * Digite a URL (ex: `youtube.com`) no campo de texto superior.
    * Clique em **Adicionar**. O domínio será extraído e adicionado à lista.
    * Para remover, selecione um ou mais sites na lista e clique em **Remover Selecionado**.
    * DICA: para garantir um uso correto, é interessante adicionar variações de URLs, como "www.instagram.com" e "instagram.com"
3.  **Para bloquear aplicativos:**
    * Na caixa de texto inferior, insira o nome dos executáveis (ex: `chrome.exe`, `discord.exe`), um por linha.
    * DICA: você pode clicar no aplicativo com o botão direito, e "ir ao local do arquivo", para garantir o nome correto do executável do app.
4.  Para ativar os bloqueios, marque a caixa **Enable Blockers**.
5.  Clique em **Apply Blocking Changes** para que as regras entrem em vigor.

### Verificando o Histórico
1.  Clique na aba **History**.
2.  Um gráfico será exibido mostrando a quantidade total de segundos em foco para cada um dos últimos 7 dias.
