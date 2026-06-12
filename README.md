Sobre o Projeto
Este projeto consiste em um script Python desenvolvido para automatizar a extração de dados da série histórica de 2010 a 2019, provenientes do DATASUS. 

O objetivo principal é processar um arquivo CSV bruto e estruturá-lo em um banco de dados relacional, facilitando consultas e análises futuras. Para fins de demonstração, o script está configurado para processar os 50 primeiros registros do dataset.

Tecnologias Utilizadas
* **Python:** Linguagem base para a automação do script.
* **Pandas:** Utilizado para a leitura, limpeza e manipulação do arquivo CSV.
* **SQLite (sqlite3):** Biblioteca nativa do Python utilizada para criar e gerenciar o banco de dados relacional local (`.db`), sem a necessidade de instalar servidores externos.

 Modelagem do Banco de Dados
Os dados foram organizados divididos nas seguintes tabelas:

* **Tabela do Fato:** `Suicidios` (Armazena os eventos principais usando IDs relacionais).
* **Tabelas de estados:** `Estados`, `Estado_civil`, `Escolaridade` e `Causas`.

Além disso, o script gera automaticamente **7 Views (Consultas)** prontas no banco de dados, entregando relatórios rápidos como:
1. Idade, sexo e estado da ocorrência.
2. Total de registros por estado.
3. Top 10 estados com mais casos.
4. Quantidade de casos por escolaridade.
5. Registros por estado civil.
6. Média de idade por estado.
7. Relatório completo (Estado, estado civil, escolaridade, causa e quantidade).

Como Executar

1. Certifique-se de ter o Python instalado na sua máquina.
2. Instale as bibliotecas necessárias executando o comando no terminal:
   ```bash
   pip install pandas numpy
