# PyQt System Blocker

Este projeto foi desenvolvido para o **Hackathon Magalu 2025**. É uma aplicação de desktop focada em produtividade, construída em Python com a biblioteca PyQt6. A ferramenta oferece um timer de foco e um bloqueador de aplicativos para ajudar o usuário a evitar distrações.

## Funcionalidades

* **Timer Circular:** Uma interface de timer visual e customizável para gerenciar sessões de foco.
* **Bloqueador de Aplicativos (Windows):** Permite ao usuário listar arquivos executáveis (`.exe`) para bloqueá-los durante o período de foco.
* **Interface Moderna:** Um design com tema escuro e componentes personalizados, incluindo uma barra de título própria.
* **Navegação por Abas:** Acesso fácil a todas as funcionalidades do aplicativo.

## Como Funciona

A aplicação é dividida em lógica (`main.py`) e interface (`gui.py`). A funcionalidade de bloqueio de aplicativos no Windows é realizada através da manipulação do Registro do Windows, exigindo que o programa seja executado com privilégios de administrador.

## Pré-requisitos

* Python 3
* PyQt6

## Como Executar

1.  Clone ou faça o download deste repositório.
2.  Navegue até o diretório do projeto.
3.  Execute o script `main.py` (lembre-se de executar como administrador no Windows se for usar o bloqueador).

### Utilizando o Timer
1.  Na aba "Timer", defina o tempo desejado.
2.  Clique em **Start** para iniciar a contagem.
3.  Clique em **Reset** para parar e reiniciar o timer.

### Bloqueando Aplicativos
1.  Vá para a aba "Lista".
3.  Insira o nome dos executáveis (ex: `chrome.exe`) ou dos sites (ex: `www.instagram.com`), na respectiva lista, um por linha.
4.  Marque a caixa "Enable Blockers".
5.  Clique em "Apply Blocking Changes" para aplicar as regras.
