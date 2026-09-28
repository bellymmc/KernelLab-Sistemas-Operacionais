# KernelLab - Simulador de Gerenciamento de CPU, Memória e Dispositivos

Projeto desenvolvido para a disciplina **Sistemas Operacionais**, a partir do cenário da **MedControl Systems**. O objetivo é reproduzir decisões típicas de um sistema operacional e comparar políticas de escalonamento de CPU, substituição de páginas e controle de acesso a dispositivos.

## 1. Problema e objetivo

O servidor da MedControl executa simultaneamente monitoramento cardíaco, telemetria, relatórios, alarmes, backup e atualização de dados. O cenário apresenta atraso em alarmes, disputa de CPU, page faults, espera excessiva de processos, concorrência em dispositivos e risco de acesso indevido.

O KernelLab permite comparar algoritmos e observar como diferentes políticas alteram tempo de espera, retorno, resposta, trocas de contexto, page faults e justiça de acesso.

## 2. Arquitetura

```text
kernellab/
├── src/
│   ├── main.py          # interface de terminal, integração e exportação dos gráficos
│   ├── schedulers.py    # FCFS, SJF, Round Robin e Prioridade
│   ├── memory.py        # FIFO, LRU e Optimal
│   ├── devices.py       # matriz de acesso + mutex para dispositivo
│   └── metrics.py       # espera, retorno, resposta e comparações
├── data/
│   ├── processes.json   # processos configuráveis
│   └── pages.json       # sequência de páginas e número de frames
├── tests/               # testes unitários
├── docs/
│   ├── generated/       # gráficos gerados pela execução
│   ├── relatorio_kernellab.pdf
│   └── roteiro_pitch.md
├── requirements.txt
└── README.md
```

## 3. Algoritmos implementados

### CPU
- **FCFS** - não preemptivo, atende pela ordem de chegada.
- **SJF** - não preemptivo, escolhe o menor burst entre os processos prontos.
- **Round Robin** - preemptivo, quantum configurável; valor padrão = 3.
- **Prioridade** - não preemptivo; **menor número significa maior prioridade**.

> O enunciado não define se o algoritmo de prioridade deve ser preemptivo. O projeto adota **prioridade não preemptiva** e documenta essa decisão. Na recomendação final é sugerida uma evolução híbrida/preemptiva para alarmes críticos.

### Memória
- **FIFO** - remove a página que entrou há mais tempo.
- **LRU** - remove a página menos recentemente utilizada.
- **Optimal** - remove a página cujo próximo uso está mais distante; é usado como referência comparativa.

### Dispositivos e segurança
- Matriz de controle de acesso por processo/dispositivo.
- Operações: leitura (R), gravação (W), execução (X), uso (U) e acesso exclusivo (E).
- Demonstração de concorrência em disco com `threading.Lock` (mutex).

## 4. Instalação

Recomendado: Python 3.10 ou superior.

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## 5. Execução

Na pasta raiz do projeto:

```bash
python -m src.main
```

Para gerar os gráficos:

```bash
python -m src.main --export docs/generated
```

### Alterar o quantum sem mexer na lógica

```bash
python -m src.main --quantum 4
```

### Alterar a quantidade de frames

```bash
python -m src.main --frames 3
```

### Usar uma sequência de páginas alternativa

```bash
python -m src.main --pages "1,2,3,1,4,2,5"
```

### Usar outro conjunto de processos

Crie outro JSON seguindo o formato de `data/processes.json` e execute:

```bash
python -m src.main --processes caminho/novo_processos.json
```

## 6. Formato dos dados de entrada

Exemplo:

```json
{
  "pid": "P4",
  "function": "Emissão de alarme crítico",
  "arrival": 3,
  "burst": 2,
  "priority": 0,
  "memory_mb": 60,
  "devices": ["audio", "rede"]
}
```

Campos principais: identificador, função, chegada, burst de CPU, prioridade, memória e dispositivos.

## 7. Testes

Execute:

```bash
python -m unittest discover -s tests -v
```

Os testes verificam resultados conhecidos dos escalonadores, contagens de page hits/page faults, permissões de acesso e a exclusão mútua no disco.

## 8. Resultados principais com os dados do enunciado

| Algoritmo | Espera média | Retorno médio | Resposta média | Trocas de contexto |
|---|---:|---:|---:|---:|
| FCFS | 13,67 | 20,50 | 13,67 | 5 |
| SJF | 10,67 | 17,50 | 10,67 | 5 |
| Round Robin (q=3) | 18,00 | 24,83 | **5,33** | 13 |
| Prioridade | 10,67 | 17,50 | 10,67 | 5 |

Neste conjunto de dados, SJF e Prioridade produzem a mesma ordem depois de P1. O alarme P4 começa em `t=8` nesses dois algoritmos, em `t=9` no Round Robin e apenas em `t=21` no FCFS.

| Memória (4 frames) | Hits | Faults | Taxa de faults |
|---|---:|---:|---:|
| FIFO | 5 | 12 | 70,59% |
| LRU | 7 | 10 | 58,82% |
| Optimal | 10 | **7** | **41,18%** |

O Optimal é a referência com menor número de faltas; entre os algoritmos implementáveis sem conhecimento do futuro, o LRU se sai melhor que o FIFO para a sequência fornecida.

## 9. Análise de justiça e starvation

- **FCFS:** simples, mas sofre efeito comboio; P6 espera muito no cenário.
- **SJF:** reduz a espera média, porém jobs longos podem ser adiados se jobs curtos continuarem chegando.
- **Prioridade:** atende bem a criticidade, mas processos de baixa prioridade podem sofrer starvation; P5 é o principal candidato teórico.
- **Round Robin:** oferece a distribuição mais justa do tempo de CPU e a menor resposta média, ao custo de mais trocas de contexto.

## 10. Recomendação técnica

Para a MedControl, a melhor evolução é **não depender de um único algoritmo puro**. Recomenda-se uma política **preemptiva por classes de prioridade**, garantindo atendimento imediato ao processo de alarme crítico, combinada com **Round Robin entre processos da mesma classe** e **aging** para elevar gradualmente a prioridade de processos que esperam por muito tempo. Essa solução equilibra criticidade, justiça e responsividade.

No simulador exigido pelo trabalho, todos os quatro algoritmos são mantidos separadamente para permitir a comparação solicitada.

## 11. Limitações e melhorias

- A prioridade implementada é não preemptiva por decisão de projeto.
- Burst de CPU e tempos são determinísticos; um simulador futuro pode usar cargas aleatórias.
- O Optimal exige conhecimento do futuro e serve apenas como referência.
- O modelo de dispositivos simplifica latência e capacidade.
- Uma evolução pode incluir prioridade preemptiva, aging, múltiplas CPUs, filas multinível e interface web.

## 12. Links da entrega

- **GitHub:** `COLE_AQUI_O_LINK_PUBLICO_DO_REPOSITORIO`
- **Vídeo pitch:** `COLE_AQUI_O_LINK_DO_VIDEO`
