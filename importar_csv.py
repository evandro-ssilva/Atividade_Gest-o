import sqlite3
import pandas as pd
import numpy as np

# Este script lê os primeiros 50 registos do ficheiro CSV.
print("A ler os primeiros 50 registos do CSV...")
df = pd.read_csv('suicidios_2010_a_2019.csv', low_memory=False, nrows=50)

# Calcula a idade dos registos, tratando os erros de data.
print("A calcular a idade a partir das datas de nascimento e óbito...")
df['DTOBITO'] = pd.to_datetime(df['DTOBITO'], errors='coerce')
df['DTNASC'] = pd.to_datetime(df['DTNASC'], errors='coerce')
df['idade'] = np.floor((df['DTOBITO'] - df['DTNASC']).dt.days / 365.25)

# Banco de dados SQLite para armazenar os dados processados.
print("A ligar à base de dados...")
conn = sqlite3.connect('base_suicidios.db')
cursor = conn.cursor()

print("A criar as tabelas e views na base de dados...")
cursor.executescript('''
    DROP TABLE IF EXISTS Suicidios;
    DROP TABLE IF EXISTS Estados;
    DROP TABLE IF EXISTS Estado_civil;
    DROP TABLE IF EXISTS Escolaridade;
    DROP TABLE IF EXISTS Causas;
    DROP VIEW IF EXISTS vw_idade_sexo_estado;
    DROP VIEW IF EXISTS vw_total_suicidios_estado;
    DROP VIEW IF EXISTS vw_top10_estados_casos;
    DROP VIEW IF EXISTS vw_casos_escolaridade;
    DROP VIEW IF EXISTS vw_casos_estado_civil;
    DROP VIEW IF EXISTS vw_media_idade_estado;
    DROP VIEW IF EXISTS vw_relatorio_completo_casos;

    CREATE TABLE Estados (id_estado INTEGER PRIMARY KEY, sigla_estado TEXT);
    CREATE TABLE Estado_civil (id_estado_civil INTEGER PRIMARY KEY, estciv TEXT);
    CREATE TABLE Escolaridade (id_escolaridade INTEGER PRIMARY KEY, esc TEXT);
    CREATE TABLE Causas (id_causa INTEGER PRIMARY KEY, causabas TEXT, causabas_o TEXT);

    CREATE TABLE Suicidios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ano INTEGER,
        idade INTEGER,
        sexo TEXT,
        estado_id INTEGER,
        estado_civil_id INTEGER,
        escolaridade_id INTEGER,
        causa_id INTEGER,
        FOREIGN KEY (estado_id) REFERENCES Estados(id_estado),
        FOREIGN KEY (estado_civil_id) REFERENCES Estado_civil(id_estado_civil),
        FOREIGN KEY (escolaridade_id) REFERENCES Escolaridade(id_escolaridade),
        FOREIGN KEY (causa_id) REFERENCES Causas(id_causa)
    );
''')

print("A processar e a inserir dados nas dimensões...")
estados_unicos = df['estado'].dropna().unique()
df_estados = pd.DataFrame({'sigla_estado': estados_unicos})
df_estados['id_estado'] = range(1, len(df_estados) + 1)
df_estados.to_sql('Estados', conn, if_exists='append', index=False)

estciv_unicos = df['ESTCIV'].fillna('Não Informado').unique()
df_estciv = pd.DataFrame({'estciv': estciv_unicos})
df_estciv['id_estado_civil'] = range(1, len(df_estciv) + 1)
df_estciv.to_sql('Estado_civil', conn, if_exists='append', index=False)

esc_unicos = df['ESC'].fillna('Não Informada').unique()
df_esc = pd.DataFrame({'esc': esc_unicos})
df_esc['id_escolaridade'] = range(1, len(df_esc) + 1)
df_esc.to_sql('Escolaridade', conn, if_exists='append', index=False)

df_causas_unicas = df[['CAUSABAS', 'CAUSABAS_O']].dropna().drop_duplicates()
df_causas_unicas['id_causa'] = range(1, len(df_causas_unicas) + 1)
df_causas_unicas = df_causas_unicas.rename(columns={'CAUSABAS': 'causabas', 'CAUSABAS_O': 'causabas_o'})
df_causas_unicas.to_sql('Causas', conn, if_exists='append', index=False)

print("A mapear IDs e a inserir dados na tabela Suicidios...")
df['ESTCIV'] = df['ESTCIV'].fillna('Não Informado')
df['ESC'] = df['ESC'].fillna('Não Informada')

df_fato = df.merge(df_estados, left_on='estado', right_on='sigla_estado', how='left')
df_fato = df_fato.merge(df_estciv, left_on='ESTCIV', right_on='estciv', how='left')
df_fato = df_fato.merge(df_esc, left_on='ESC', right_on='esc', how='left')
df_fato = df_fato.merge(df_causas_unicas, left_on=['CAUSABAS', 'CAUSABAS_O'], right_on=['causabas', 'causabas_o'], how='left')

df_inserir = df_fato[['ano', 'idade', 'SEXO', 'id_estado', 'id_estado_civil', 'id_escolaridade', 'id_causa']].copy()
df_inserir.rename(columns={
    'SEXO': 'sexo',
    'id_estado': 'estado_id',
    'id_estado_civil': 'estado_civil_id',
    'id_escolaridade': 'escolaridade_id',
    'id_causa': 'causa_id'
}, inplace=True)

df_inserir.to_sql('Suicidios', conn, if_exists='append', index=False)

print("A criar views para consultas...")
cursor.executescript('''
    CREATE VIEW vw_idade_sexo_estado AS
    SELECT s.idade, s.sexo, e.sigla_estado AS estado FROM Suicidios s JOIN Estados e ON s.estado_id = e.id_estado;

    CREATE VIEW vw_total_suicidios_estado AS
    SELECT e.sigla_estado AS estado, COUNT(s.id) AS total_registros FROM Suicidios s JOIN Estados e ON s.estado_id = e.id_estado GROUP BY e.sigla_estado;

    CREATE VIEW vw_top10_estados_casos AS
    SELECT e.sigla_estado AS estado, COUNT(s.id) AS total_casos FROM Suicidios s JOIN Estados e ON s.estado_id = e.id_estado GROUP BY e.sigla_estado ORDER BY total_casos DESC LIMIT 10;

    CREATE VIEW vw_casos_escolaridade AS
    SELECT esc.esc AS nivel_escolaridade, COUNT(s.id) AS quantidade_casos FROM Suicidios s JOIN Escolaridade esc ON s.escolaridade_id = esc.id_escolaridade GROUP BY esc.esc;

    CREATE VIEW vw_casos_estado_civil AS
    SELECT ec.estciv AS estado_civil, COUNT(s.id) AS quantidade_registros FROM Suicidios s JOIN Estado_civil ec ON s.estado_civil_id = ec.id_estado_civil GROUP BY ec.estciv;

    CREATE VIEW vw_media_idade_estado AS
    SELECT e.sigla_estado AS estado, ROUND(AVG(s.idade), 2) AS media_idade FROM Suicidios s JOIN Estados e ON s.estado_id = e.id_estado GROUP BY e.sigla_estado;

    CREATE VIEW vw_relatorio_completo_casos AS
    SELECT e.sigla_estado AS estado, ec.estciv AS estado_civil, esc.esc AS escolaridade, c.causabas AS causas, COUNT(s.id) AS quantidade_casos 
    FROM Suicidios s 
    JOIN Estados e ON s.estado_id = e.id_estado 
    LEFT JOIN Estado_civil ec ON s.estado_civil_id = ec.id_estado_civil 
    LEFT JOIN Escolaridade esc ON s.escolaridade_id = esc.id_escolaridade 
    JOIN Causas c ON s.causa_id = c.id_causa 
    GROUP BY e.sigla_estado, ec.estciv, esc.esc, c.causabas;
''')

conn.commit()
conn.close()
print("Extração de dados concluída!")
print("Tabelas e views criadas com sucesso na base de dados SQLite (limitado a 50 registos).")