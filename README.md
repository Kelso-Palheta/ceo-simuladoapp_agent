# 🏛️ SimuladoApp — Mesa Diretora & Assistente Executivo de IA

Sistema autônomo de inteligência executiva com **8 Diretores Especialistas** para o **SimuladoApp**, operando sob o modelo consultivo *Human-in-the-Loop* (Fábrica de Especificações, PRDs e Briefings).

---

## 👥 Composição do Conselho Executivo (8 Agentes)

| Diretor / Papel | Especialidade & Entregável Principal | Referências de Mentalidade |
| :--- | :--- | :--- |
| **👑 CEO & Estrategista Chefe** | Orquestração, Split 33/33/33, Sparring 1-a-1 e Síntese Executiva | Alex Hormozi, Eric Ries, David Sacks |
| **💻 CTO & Arquiteto Tech** | Mini-PRDs Técnicos, Django, MySQL (sem N+1), Celery e OpenCV | John Carmack, Martin Fowler, Kelsey Hightower |
| **🎓 CPO & Especialista Pedagógico** | UX/UI docente, alinhamento BNCC/SAEB e North Star (TTFV < 5min) | Salman Khan, Tony Fadell, Julie Zhuo |
| **💰 CFO & Controller Financeiro** | Unit Economics, conciliação quinzenal, DRE e proteção de liquidez | Warren Buffett, Ray Dalio, David Sacks |
| **🎧 Head de CS & Suporte** | Retenção, encantamento, redução de churn < 5% e régua no WhatsApp | Tony Hsieh, Nick Mehta |
| **⚖️ Consultor Jurídico & DPO** | Blindagem LGPD escolar (dados de menores), Termos SaaS e INPI | Brad Smith, Ann Cavoukian |
| **✍️ Head de Conteúdo & Copywriter** | Comunidade 'Devolve seus fins de semana' e roteiros de Reels/Shorts | GaryVee, Nicolas Cole, Ann Handley |
| **📈 Head de Growth & Performance** | Tráfego Meta Ads (CPL ≤ R$ 0,75, CAC ≤ R$ 15,00) e picos bimestrais | Sean Ellis, Russell Brunson, David Ogilvy |

---

## 🚀 Canais de Operação

### 1. 📱 Telegram Bot (`bot.py`)
* **Comandos Diretos:** `/ceo`, `/cto`, `/cfo`, `/growth`, `/conteudo`, `/cpo`, `/cs`, `/legal`
* **Voz & Áudio:** Transcrição instantânea com Groq Whisper Large v3
* **Documentos:** Envio de `.pdf`, `.docx`, `.txt` para análise do conselho
* **Exportação & Lembretes:** `/pdf <demanda>`, `/lembrete <texto>`, `/tarefas`, `/historico`

### 2. 🖥️ Dashboard Web Interativo (`dashboard.py`)
* **Mesa Redonda:** Despacho geral ou seleção direta de especialistas
* **Entrada Multimodal:** Gravação de voz, upload de áudios e anexo de documentos
* **Exportações:** Download em `.md`, PDF formatado e sincronização com **Notion**
* **Editor de Diretrizes:** Personalização de preços, metas e regras direto no painel
* **Quadro Kanban de Tarefas:** Sincronizado em tempo real com o Telegram

### 3. 💻 Terminal Interativo CLI (`session.py`)
* TUI estilizada com Rich Markdown, painéis e suporte a menções `@cto`, `@cfo`, etc.

---

## 🔒 Governança & Regras de Negócio Inegociáveis

* **Split Societário:** 33,33% Sócio 1 / 33,33% Sócio 2 / 33,33% Caixa PJ.
* **Modelo Comercial:** Gratuito 15 correções/mês, Assinatura R$ 4,99/mês e Pacotes P/M/G.
* **North Star Metric:** Time-to-First-Value (TTFV) < 5 minutos.
* **Performance do Scanner:** OpenCV < 1s por gabarito com precisão > 98%.
