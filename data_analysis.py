import pandas as pd
import os
import json
from datetime import datetime
import shutil
from auxiliar import *

# Variáveis 
column_index = 3


def process_file(file_path, operacao):
    # 2. Carregar o arquivo CSV
    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
    except Exception as e:
        print(f"# Erro ao ler o arquivo {file_path}: {e}")
        return None

    # Remover espaços extras nos nomes das colunas
    df.columns = df.columns.str.strip()

    # 3. Verificar se as colunas necessárias estão presentes
    required_columns = [
        'cod_turno_tur',
        'des_equipe',
        'parceiros',
        'Coordenador',
        'Supervisor',
        'placa',
        'dta_inicio',
        'num_contrato',
        'Dta_inicio de deslocamento primeiro serv',
        'Dta_inicio do inicio do reparo primeiro serv'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"# Colunas ausentes em {os.path.basename(file_path)}: {missing_columns}")
        return None

    df = df[required_columns]
    df.rename(columns={'cod_turno_tur': 'id', 'num_contrato': 'contrato'}, inplace=True)
    df.columns = df.columns.str.strip()

    # 5. Criar coluna 'data' a partir de dta_inicio
    coluna_selecionada = 'dta_inicio'
    if coluna_selecionada not in df.columns or df[coluna_selecionada].dropna().empty:
        print(f"# AVISO: Coluna '{coluna_selecionada}' vazia em {os.path.basename(file_path)}.")

    df['data'] = pd.to_datetime(df[coluna_selecionada], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    df['operacao'] = operacao

    # 7. Reordenar colunas
    df = df[[
        'des_equipe', 'parceiros', 'Coordenador', 'Supervisor', 'placa',
        'dta_inicio', 'Dta_inicio de deslocamento primeiro serv',
        'Dta_inicio do inicio do reparo primeiro serv',
        'id', 'contrato', 'data', 'operacao'
    ]]

    # Salvar o DataFrame processado
    try:
        df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"- GPM {operacao} processado: {len(df)} registros.")
    except Exception as e:
        print(f"# Erro ao salvar o arquivo {file_path}: {e}")

def find_and_process_files(path_temp, operacao):
    for filename in os.listdir(path_temp):
        if filename.startswith(f"consulta turno {operacao}"):
            file_path = os.path.join(path_temp, filename)
            process_file(file_path, operacao)
            
def process_pontomais_files(path_temp):
    """
    Lê o arquivo Pontomais_final.csv (já consolidado pelo main.py a partir do parquet do Drive)
    e garante que a coluna '1ª Entrada' existe para o cruzamento com GPM.
    """
    caminho_consolidado = os.path.join(path_temp, "Pontomais_final.csv")
    
    # Verifica se o arquivo consolidado já foi gerado pelo main.py
    if not os.path.exists(caminho_consolidado):
        # Fallback: tenta ler CSVs yyyy-mm diretamente na pasta temp
        print("# AVISO: Pontomais_final.csv não encontrado. Tentando montar a partir de CSVs...")
        dfs = []
        for filename in sorted(os.listdir(path_temp)):
            if filename.endswith('.csv') and len(filename) == 11:  # Padrão yyyy-mm.csv
                file_path = os.path.join(path_temp, filename)
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig', dtype=str)
                    dfs.append(df)
                    print(f"- Lido: {filename}")
                except Exception as e:
                    print(f"# Erro ao ler {filename}: {e}")
        
        if not dfs:
            print("# ERRO CRÍTICO: Nenhum arquivo de ponto encontrado.")
            return
        
        final_df = pd.concat(dfs, ignore_index=True)
        final_df.to_csv(caminho_consolidado, index=False, sep=';', encoding='utf-8-sig')
        print(f"- Pontomais_final.csv gerado com {len(final_df)} linhas.")
    else:
        print(f"- Pontomais_final.csv já existe ({caminho_consolidado}). Usando arquivo existente.")
        final_df = pd.read_csv(caminho_consolidado, dtype=str, sep=';', encoding='utf-8-sig')

    # Garante que a coluna '1ª Entrada' existe (necessária para o cruzamento com GPM)
    if '1ª Entrada' not in final_df.columns:
        print("# AVISO: Coluna '1ª Entrada' não encontrada. Criando coluna vazia.")
        final_df['1ª Entrada'] = None
        final_df.to_csv(caminho_consolidado, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"- process_pontomais_files concluído. Total de linhas: {len(final_df)}")

def process_consulta_turno_files(path_temp, pontomais_df, operacao):
    # Iterar sobre os arquivos no diretório
    for filename in os.listdir(path_temp):
        if filename.startswith(f"consulta turno {operacao}") and filename.endswith(".csv"):
            # Ler o arquivo "consulta turno"
            file_path = os.path.join(path_temp, filename)
            consulta_turno_df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')

            # Extrai primeiro nome (vetorizado, sem apply)
            consulta_turno_df['primeiro_nome'] = (
                consulta_turno_df['parceiros']
                .astype(str)
                .str.split(' - ')
                .str[0]
                .str.strip()
                .str.upper()
            )

            # Encontrar o menor horário de ponto batido por um membro da equipe
            # (cruzamento por Nome + Data — sem bias do histórico inteiro)
            df_parceiros_resumo = loc_menor_entrada_pontomais()

            # Juntar DataFrames pelo ID do turno
            consulta_turno_df = consulta_turno_df.merge(
                df_parceiros_resumo[['id', 'menor_tempo']],
                on='id',
                how='left'
            )

            # Renomear a coluna 'menor_tempo' para 'hora_pontomais'
            consulta_turno_df.rename(columns={'menor_tempo': 'hora_pontomais'}, inplace=True)

            # Criar a coluna 'date_hour_pontomais' (vetorizado: None onde não há hora)
            tem_hora = consulta_turno_df['hora_pontomais'].notna()
            consulta_turno_df['date_hour_pontomais'] = (
                consulta_turno_df['data'].astype(str).str.strip()
                + ' '
                + consulta_turno_df['hora_pontomais'].astype(str)
            ).where(tem_hora, other=None)

            # Salvar o arquivo "consulta turno" enriquecido
            consulta_turno_df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
            print(f"- Consulta turno {operacao} enriquecido com hora_pontomais: {len(consulta_turno_df)} registros.")

def load_vehicle_records(file_path):
    # Carregar os registros de veículos do arquivo JSON
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data

def find_initial_mileage_and_hour(vehicle_records, plate):
    initial_mileage = None
    initial_hour = None
    for record in vehicle_records:
        if record['Plate'] == plate:
            initial_mileage = float(record['Mileage'])
            initial_hour = datetime.strptime(record['Date'], "%Y-%m-%dT%H:%M:%S")
            break
    return initial_mileage, initial_hour

def find_hour_km_run(vehicle_records, plate, initial_mileage, initial_hour):
    for record in vehicle_records:
        if record['Plate'] == plate:
            mileage = float(record['Mileage'])
            hour = datetime.strptime(record['Date'], "%Y-%m-%dT%H:%M:%S")
            if mileage - initial_mileage >= 2:
                return hour.strftime("%d/%m/%Y %H:%M")
    return None

def process_vehicle_logs_by_operation(path_temp, operacao, notifications_file):
    # Carrega as notificações UMA VEZ para otimizar
    notifications_data = []
    try:
        if os.path.exists(notifications_file):
            with open(notifications_file, 'r', encoding='utf-8') as json_file:
                notifications_data = json.load(json_file)
        else:
            print(f"# Aviso: Arquivo de notificações não encontrado: {notifications_file}")
    except Exception as e:
        print(f"# Erro ao carregar arquivo de notificações ({notifications_file}): {e}")

    # Pré-indexar as notificações por placa para otimizar a busca
    notificacoes_por_placa = {}
    for notification in notifications_data:
        vehicle = notification.get('vehicle', {})
        plate_n = vehicle.get('licensePlate')
        if plate_n:
            plate_n = plate_n.strip().upper().replace("-", "").replace(" ", "")
            if plate_n not in notificacoes_por_placa:
                notificacoes_por_placa[plate_n] = []
            notificacoes_por_placa[plate_n].append(notification)

    # Função para encontrar a data do evento correspondente à placa e ao DIA do serviço
    def find_event_date(plate, data_servico_str):
        if not isinstance(plate, str): return None
        plate_search = plate.strip().upper().replace("-", "").replace(" ", "")

        # Converter a data do serviço (DD/MM/YYYY) para objeto date para comparação
        try:
            data_servico = datetime.strptime(data_servico_str, "%d/%m/%Y").date()
        except Exception:
            data_servico = None

        candidatos = notificacoes_por_placa.get(plate_search, [])
        for notification in candidatos:
            event_date = notification.get('eventDate')
            if event_date:
                try:
                    if "." in event_date:
                        event_date = event_date.split(".")[0]
                    dt_obj = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S")

                    # Filtrar somente notificações do mesmo dia do serviço GPM
                    if data_servico and dt_obj.date() != data_servico:
                        continue

                    return dt_obj.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    print(f"# Erro ao converter data '{event_date}' para placa {plate}")
        return None

    # Ler o arquivo "consulta turno" correspondente à operação
    consulta_turno_file = f"consulta turno {operacao}.csv"
    consulta_turno_path = os.path.join(path_temp, consulta_turno_file)

    # Verificar se o arquivo existe (pode não existir se não houve turno no dia)
    if not os.path.exists(consulta_turno_path):
        print(f"# AVISO: Arquivo '{consulta_turno_file}' não encontrado. Sem turno para {operacao} neste dia.")
        return None

    consulta_turno_df = pd.read_csv(consulta_turno_path, sep=';', encoding='utf-8-sig')

    # Verificar se a coluna 'hour_km_run_pontomais' existe, se não, criar com valores vazios
    if 'hour_km_run_pontomais' not in consulta_turno_df.columns:
        consulta_turno_df['hour_km_run_pontomais'] = None

    # Iterar sobre as linhas do DataFrame "consulta turno"
    for index, row in consulta_turno_df.iterrows():
        plate = row['placa']
        data_servico_str = str(row.get('data', ''))
        # Verificar se a coluna 'hour_km_run_pontomais' está vazia ou tem valor "0"
        if pd.isna(row['hour_km_run_pontomais']) or row['hour_km_run_pontomais'] == "0":
            event_date = find_event_date(plate, data_servico_str)
            if event_date:
                consulta_turno_df.at[index, 'hour_km_run_pontomais'] = event_date

    # Salvar o arquivo "consulta turno" com as atualizações na coluna 'hour_km_run_pontomais'
    consulta_turno_df.to_csv(consulta_turno_path, sep=';', index=False, encoding='utf-8-sig')
    print(f"\n- GPM {operacao}: enriquecido com dados de telemetria ZUQ.")
        
    # Separa por dia e salva um arquivo por data
    os.makedirs(path_final, exist_ok=True)
    arquivos_gerados = []
    
    if 'data' not in consulta_turno_df.columns:
        print(f"# ERRO: Coluna 'data' não encontrada no arquivo de consulta turno {operacao}.")
        return None

    datas_unicas = consulta_turno_df['data'].dropna().unique()
    
    for data_str in sorted(datas_unicas):
        try:
            # Converte DD/MM/YYYY para YYYY_MM_DD para o nome do arquivo
            data_obj = datetime.strptime(data_str, "%d/%m/%Y")
            data_fmt = data_obj.strftime("%Y_%m_%d")
        except:
            continue
        
        df_dia = consulta_turno_df[consulta_turno_df['data'] == data_str]
        new_file_name = f"{operacao}{data_fmt}_df_final.csv"
        new_file_path = os.path.join(path_final, new_file_name)
        
        # Sobrescreve se já existir
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
        
        df_dia.to_csv(new_file_path, sep=';', index=False, encoding='utf-8-sig')
        arquivos_gerados.append(new_file_path)
    
    print(f"- {len(arquivos_gerados)} arquivos diarios gerados/atualizados na pasta final ({operacao}).")
    return arquivos_gerados if arquivos_gerados else None
    
def criar_dataframe(diretorio, comeca_com, termina_com):
    base_dados = []
    lista = [arquivo for arquivo in os.listdir(diretorio) if (arquivo.startswith(comeca_com) and arquivo.endswith(termina_com))]

    if not lista:
        print("Nenhum arquivo conforme especificado encontrado no diretório.")
        return pd.DataFrame()
        
    
    for arquivo in lista:
        try:
            if termina_com == '.xlsx':
                arq = pd.read_excel(os.path.join(diretorio, arquivo))
            elif termina_com == '.csv':
                arq = pd.read_csv(os.path.join(diretorio, arquivo), sep=';', encoding='utf-8-sig', low_memory=False)
            base_dados.append(arq)
            # print(f"- Arquivo processado: {arquivo}")
        except Exception as e:
            print(f"# Erro ao processar o arquivo {arquivo}: {e}")
            
    df = pd.concat(base_dados, ignore_index=True)
    df = df.drop_duplicates().reset_index(drop=True)
    return df
    
def loc_menor_entrada_pontomais():
    """
    Versão corrigida e otimizada:

    CORREÇÃO DO BUG:
      Cruzamento agora usa Nome + Data, eliminando o viés do histórico inteiro.
      Antes, o lookup era só por nome → pegava o menor horário de qualquer dia
      no histórico, causando horas incorretas no arquivo final.

    OTIMIZAÇÕES:
      1. Lê apenas as 3 colunas necessárias do Excel (Data, Nome, 1ª Entrada)
         via usecols — reduz drasticamente o tempo de I/O para arquivos grandes.
      2. Usa format explícito nos pd.to_datetime, eliminando inferência lenta.
      3. Pipeline vetorizado (sem apply), complexidade O(n log n).
    """
    caminho_pontomais = os.path.join(path_temp, 'Pontomais_final.csv')
    df_pontomais = pd.read_csv(
        caminho_pontomais,
        usecols=['Data', 'Nome', '1ª Entrada'],  # lê só o necessário
        dtype=str,
        sep=';',
        encoding='utf-8-sig'
    )
    df_consulta = criar_dataframe(path_temp, 'consulta turno', '.csv')

    if '1ª Entrada' not in df_pontomais.columns:
        df_pontomais['1ª Entrada'] = None

    # ----- 1. Prepara o lookup do Pontomais (Nome + Data) -----
    df_pontomais['_nome_key'] = df_pontomais['Nome'].astype(str).str.strip().str.upper()

    # Data do Pontomais vem como YYYY-MM-DD → converte para DD/MM/YYYY
    # format explícito evita inferência e warnings de performance
    df_pontomais['_data_pm'] = pd.to_datetime(
        df_pontomais['Data'], format='%Y-%m-%d', errors='coerce'
    ).dt.strftime('%d/%m/%Y')

    # Converte '1ª Entrada' (HH:MM) para datetime para comparar numericamente
    df_pontomais['_entrada_dt'] = pd.to_datetime(
        df_pontomais['1ª Entrada'], format='%H:%M', errors='coerce'
    )

    # Lookup: menor entrada por Nome + Data (CORREÇÃO DO BUG)
    lookup = (
        df_pontomais
        .dropna(subset=['_entrada_dt'])
        .groupby(['_nome_key', '_data_pm'])['_entrada_dt']
        .min()
        .reset_index()
        .rename(columns={'_entrada_dt': '_menor_entrada'})
    )

    # ----- 2. Explode parceiros em 1 linha por parceiro + data -----
    df_parceiros = df_consulta[['id', 'parceiros', 'data']].copy()
    df_parceiros['_parceiro'] = df_parceiros['parceiros'].astype(str).str.split(' - ')
    df_parceiros = df_parceiros.explode('_parceiro')
    df_parceiros['_nome_key'] = df_parceiros['_parceiro'].str.strip().str.upper()
    df_parceiros['_data_pm']  = df_parceiros['data'].astype(str).str.strip()

    # ----- 3. Merge por Nome + Data -----
    df_merged = df_parceiros.merge(lookup, on=['_nome_key', '_data_pm'], how='left')

    # ----- 4. Menor entrada por ID de turno -----
    df_min = (
        df_merged
        .groupby('id')['_menor_entrada']
        .min()
        .reset_index()
    )

    # Converte de volta para HH:MM (string), None onde não encontrou ponto
    df_min['menor_tempo'] = df_min['_menor_entrada'].dt.strftime('%H:%M')
    df_min.loc[df_min['_menor_entrada'].isna(), 'menor_tempo'] = None

    resultado = df_min[['id', 'menor_tempo']]
    resultado.to_csv(
        os.path.join(path_temp, 'menor-entrada-equipes.csv'),
        sep=';', index=False, encoding='utf-8-sig'
    )

    print(f"- Cruzamento concluido: {len(resultado)} turnos processados, {resultado['menor_tempo'].notna().sum()} com ponto encontrado.")
    return resultado


