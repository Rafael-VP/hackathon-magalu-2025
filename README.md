# hourClass - Hackathon Magalu 2025

O **hourClass** é um aplicativo de desktop de produtividade desenvolvido em Python para o **Hackathon Magalu 2025**. Inspirado no conceito de uma ampulheta (`hourglass`), a ferramenta foi criada para ajudar você a manter o foco, eliminando distrações digitais com um sistema de bloqueio e um timer. De maneira inovadora, o sistema aproveita a **Magalu Cloud** para permitir sessões de foco em grupo, promovendo cooperação e responsabilidade compartilhada para tarefas importantes.

## Sobre o Nome
O nome `hourClass` é um trocadilho com "hourglass" (ampulheta). A ampulheta simboliza a gestão do tempo, que é a funcionalidade central do programa. O nome também sugere a ideia de "our class" (nossa aula), enfatizando o recurso de sincronização que permite a colaboração em grupo.

## Funcionalidades

* **Autenticação Segura:** Sistema de login e registro conectado a um servidor, oferecendo uma experiência de uso personalizada.
* **Timer Circular de Foco:** Uma interface de timer visual para gerenciar suas sessões de foco.
* **Bloqueador de Sites e Aplicativos:**
    * **Sites:** Gerencie sua lista de bloqueio de URLs diretamente na interface. O programa edita o arquivo `hosts` do sistema para redirecionar o tráfego e garantir que os sites não possam ser acessados durante a sessão.
    * **Aplicativos (Windows):** Bloqueie aplicativos listando seus arquivos executáveis (`.exe`). O programa manipula o Registro do Windows para impedir a execução.
* **Sessões Sincronizadas:** Um recurso único que permite a você e a um parceiro se conectarem a uma sala de foco virtual. O timer inicia simultaneamente para ambos os usuários, criando uma sessão de estudo ou trabalho colaborativa e sem distrações.
* **Histórico de Foco com Gráfico:** A aplicação salva a duração de cada sessão de foco e exibe um gráfico visual do seu tempo focado nos últimos dias.
* **Interface Simples e Intuitiva:** Um design de tema escuro com componentes personalizados para uma experiência de usuário agradável.

## Como Funciona

A arquitetura do hourClass é cliente-servidor para autenticação e sincronização. A lógica principal (`main.py`) controla a interface (`gui.py`) e as funcionalidades de bloqueio.

* **Bloqueio de Sites:** Adiciona entradas ao arquivo `hosts` do sistema para redirecionar o acesso a URLs listadas para `127.0.0.1`.
* **Bloqueio de Aplicativos (Windows):** Manipula o Registro do Windows para interceptar e impedir a execução de aplicativos especificados. **Isso exige que o programa seja executado com privilégios de administrador.**
* **Histórico de Sessões:** Salva os dados de tempo de foco em um arquivo `blocker_history.json` local, na pasta de dados do aplicativo do usuário.

## Pré-requisitos

* Python 3
* Bibliotecas Python: `PyQt6`, `requests`, `uuid`

## Como Executar

1.  Clone ou faça o download deste repositório.
2.  Instale as dependências necessárias:
3.  Navegue até o diretório do projeto.
4.  Execute o script `main.py`. Lembre-se de **executar como administrador** no Windows para que as funcionalidades de bloqueio de aplicativos e sites funcionem corretamente.
    ```bash
    python main.py
    ```
5.  A janela de login aparecerá. Crie um novo usuário ou entre com uma conta existente para começar.

## Como Usar

### 1. Utilizando o Timer
Na aba **Timer**, você pode usar o timer de duas maneiras:

* **Timer Autônomo:** Defina o tempo desejado (horas, minutos e segundos) e clique em **Start** para iniciar a contagem regressiva para si mesmo.
* **Sessão Sincronizada:** Na seção "Sessão Sincronizada", digite um nome de sala e clique em **Conectar à Sala**. Quando o parceiro se conectar, um de vocês pode definir a duração e clicar em **Start**. O timer começará simultaneamente para ambos.

Clique em **Reset** para parar e reiniciar o timer. A duração da sessão será salva em seu histórico.
Durante a sessão, o bloqueio de sites e aplicativos é ativado, com intuito de promover um tempo de foco para o(s) participante(s).

### 2. Bloqueando Sites e Aplicativos
Vá para a aba **Lista** para gerenciar suas distrações.

* **Para bloquear sites:** Digite as URLs (ex: `youtube.com`) na caixa de texto superior, uma por linha. Para garantir um uso correto, adicione variações de URLs, como `www.instagram.com` e `instagram.com`.
* **Para bloquear aplicativos:** Na caixa de texto inferior, insira o nome dos executáveis (ex: `chrome.exe`, `discord.exe`), um por linha.

Para ativar os bloqueios, marque a caixa **Enable Blockers** e clique em **Apply Blocking Changes**.

### 3. Verificando seu Histórico
Clique na aba **Estatísticas** para visualizar um gráfico do seu tempo de foco diário ao longo dos últimos 365 dias.

### 4. Verificando sua Posição
Clique na aba **Rank** para visualizar sua colocação em relação a outros usuários do aplicativo, com base no tempo de uso do app nos últimos 365 dias.
