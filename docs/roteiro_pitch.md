# Roteiro do vídeo pitch - até 4 minutos

## 0:00-0:30 - Problema
"Este projeto é o KernelLab, criado para simular decisões de um sistema operacional no cenário da MedControl Systems. O servidor executa monitoramento cardíaco, telemetria, relatórios, alarmes, backup e atualizações ao mesmo tempo. Os principais problemas são atraso em alarmes, disputa de CPU, muitas faltas de página e concorrência no acesso a dispositivos."

## 0:30-1:20 - Escalonamento de CPU
Abra o terminal e execute `python -m src.main`.

"Eu implementei quatro algoritmos: FCFS, SJF, Round Robin com quantum 3 e Prioridade. Para cada um o programa mostra ordem de execução, Diagrama de Gantt, tempo de espera, retorno, resposta, médias e trocas de contexto."

Mostre rapidamente os Gantts em `docs/generated/`.

"No conjunto de dados do trabalho, SJF e Prioridade tiveram espera média de 10,67. O Round Robin teve a melhor resposta média, 5,33, mas aumentou as trocas de contexto para 13. O processo P4, que é o alarme crítico, começa em t=8 no SJF e na Prioridade, t=9 no Round Robin e só em t=21 no FCFS."

## 1:20-2:10 - Memória
"A segunda parte simula quatro frames com a sequência definida no enunciado. Foram implementados FIFO, LRU e Optimal. O programa mostra o estado dos frames a cada referência e informa hit ou fault."

Mostre a tabela no terminal e o gráfico `memoria_hits_faults.png`.

"O FIFO teve 12 faults, o LRU 10 e o Optimal 7. O Optimal é a referência porque conhece o futuro, enquanto o LRU apresentou o melhor resultado entre as políticas práticas avaliadas nesta sequência."

## 2:10-2:55 - Dispositivos e segurança
"Também foi criada uma matriz de controle de acesso para disco, rede, áudio e logs. As permissões incluem leitura, gravação, execução, uso e acesso exclusivo. A ideia é aplicar o menor privilégio: por exemplo, o P4 pode usar o áudio e a rede para disparar o alarme, enquanto P1 não pode usar o disco."

Mostre a parte `Simulação concorrente no disco com mutex` no terminal.

"P3, P5 e P6 disputam o disco. Eu usei um mutex com `threading.Lock`, então apenas um processo entra na seção crítica por vez. O resultado confirma máximo simultâneo igual a 1."

## 2:55-3:35 - Comparação e recomendação
"Comparando os escalonadores, FCFS é simples mas pode gerar efeito comboio. SJF reduz espera média, porém pode atrasar jobs longos. Prioridade favorece tarefas críticas, mas tem risco de starvation. Round Robin distribui melhor a CPU, porém gera mais trocas de contexto."

"Para a MedControl, minha recomendação é uma política híbrida: prioridade preemptiva para eventos críticos, Round Robin entre processos da mesma classe e aging para evitar starvation."

## 3:35-4:00 - Encerramento
"O projeto também possui testes unitários, dados configuráveis em JSON e parâmetros para alterar quantum, frames e sequência de páginas sem modificar a lógica. O README contém as instruções completas para reprodução do projeto."

Mostre `python -m unittest discover -s tests -v` finalizando com `OK`.
