import pandas as pd
import os
import json
from datetime import datetime
import shutil
from get_date_run import getInitialDate
from auxiliar import *

# Variáveis 
column_index = 3


def process_file(file_path, operacao):
    # 2. Carregar o arquivo CSV em um DataFrame com especificação do separador
    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')  # Especificando o separador e encoding
        print(f"--- [DEBUG] Lendo arquivo: {os.path.basename(file_path)}")
        print(f"--- [DEBUG] Colunas identificadas: {df.columns.tolist()}")
        print(f"--- [DEBUG] Primeiras linhas:\n{df.head(2).to_string()}")
    except Exception as e:
        print(f"# Erro ao ler o arquivo {file_path}: {e}")
        return None

    # Remover espaços extras nos nomes das colunas
    df.columns = df.columns.str.strip()

    # Verificar e imprimir as primeiras linhas do DataFrame para depuração
    print(f"\n- Primeiras linhas do arquivo {file_path}:\n", df.head())

    # Verificar e imprimir as colunas do DataFrame para depuração
    print(f"\n- Colunas no arquivo {file_path}:\n", df.columns.tolist())

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
        print(f"O arquivo {file_path} não contém as seguintes colunas necessárias: {missing_columns}")
        return None

    # Selecionar apenas as colunas necessárias
    df = df[required_columns]

    # 4. Renomear a coluna 'cod_turno_tur' para 'id'
    df.rename(columns={'cod_turno_tur': 'id'}, inplace=True)
    
    # 4. Renomear a coluna 'cod_turno_tur' para 'id'
    df.rename(columns={'num_contrato': 'contrato'}, inplace=True)

    # 5. Criar a nova coluna 'data' a partir da coluna 'dta_inicio'
    df['data'] = pd.to_datetime(df['dta_inicio'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')

    # 6. Adicionar a coluna 'operacao'
    df['operacao'] = operacao

    # 7. Ordenar o DataFrame pela ordem especificada
    df = df[[
        'des_equipe',
        'parceiros',
        'Coordenador',
        'Supervisor',
        'placa',
        'dta_inicio',
        'Dta_inicio de deslocamento primeiro serv',
        'Dta_inicio do inicio do reparo primeiro serv',
        'id',
        'contrato',
        'data',
        'operacao'
    ]]

    # Salvar o DataFrame processado no mesmo arquivo CSV
    try:
        df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"- Arquivo processado e salvo no mesmo local: {file_path}")
    except Exception as e:
        print(f"# Erro ao salvar o arquivo {file_path}: {e}")

def find_and_process_files(path_temp, operacao):
    for filename in os.listdir(path_temp):
        if filename.startswith(f"consulta turno {operacao}"):
            file_path = os.path.join(path_temp, filename)
            process_file(file_path, operacao)
            
def process_pontomais_files(path_temp):
    # Lista para armazenar os dataframes
    dfs = []

    # Percorrer os arquivos no diretório
    for filename in os.listdir(path_temp):
        if "Pontomais" in filename and filename.endswith('.xlsx'):
            file_path = os.path.join(path_temp, filename)
            
            # Ler o arquivo Excel, ignorando as 3 primeiras linhas
            df = pd.read_excel(file_path, skiprows=3)
            
            # Filtrar a coluna Data e remover os valores indesejados
            df = df[~df['Data'].isin(['TOTAIS', 'Resumo', 'Colaborador', 'Data'])]
            
            # Filtrar a coluna especificada
            if column_index == 3:
                df = df[df.iloc[:, column_index - 1].notna()]
            elif column_index == 2:
                df = df[df.iloc[:, column_index].notna()]
            else:
                raise ValueError("O índice da coluna deve ser 2 ou 3.")

            # Adicionar o dataframe à lista
            dfs.append(df)

    # Concatenar todos os dataframes em um só
    final_df = pd.concat(dfs)

    # Salvar o dataframe final em um arquivo Excel
    final_df.to_excel(os.path.join(path_temp, "Pontomais_final.xlsx"), index=False)
    
    # Ler o arquivo final
    final_df = pd.read_excel(pontomais_df, header=0)

    # Verifica se a coluna '1ª Entrada' existe; se não, cria a coluna com valores nulos
    if '1ª Entrada' not in final_df.columns:
        final_df['1ª Entrada'] = None
        
    # Manter apenas as colunas desejadas
    final_df = final_df[['Data', 'Nome', '1ª Entrada']]

    # Salvar o dataframe final com as colunas desejadas
    final_df.to_excel(pontomais_df, index=False)

def process_consulta_turno_files(path_temp, pontomais_df, operacao):
    # Iterar sobre os arquivos no diretório
    for filename in os.listdir(path_temp):
        if filename.startswith(f"consulta turno {operacao}") and filename.endswith(".csv"):
            # Ler o arquivo "consulta turno"
            file_path = os.path.join(path_temp, filename)
            consulta_turno_df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')

            # Função para extrair o primeiro nome da coluna 'parceiros'
            def extrair_primeiro_nome(parceiros):
                return parceiros.split(' - ')[0] if isinstance(parceiros, str) else None
            
            # Aplicar a função para extrair o primeiro nome em cada linha da coluna 'parceiros'
            consulta_turno_df['primeiro_nome'] = consulta_turno_df['parceiros'].apply(extrair_primeiro_nome)
            
            # Encontrar o menor horário de ponto batido por um membro da equipe
            df_parceiros = loc_menor_entrada_pontomais()
            
            # Juntar DataFrames
            consulta_turno_df = consulta_turno_df.merge(
                df_parceiros[['parceiro_1', 'menor_tempo']],
                how='left',
                left_on='primeiro_nome',
                right_on='parceiro_1'
            )
            
            # Renomear a coluna 'menor_tempo' para 'hora_pontomais'
            consulta_turno_df.rename(columns={'menor_tempo': 'hora_pontomais'}, inplace=True)
            
            # Remover a coluna 'parceiro_1'
            consulta_turno_df.drop(columns=['parceiro_1'], inplace=True)

            # Criar a coluna 'date_hour_pontomais' que é a concatenação das colunas 'Data' e 'hora_pontomais'
            consulta_turno_df['date_hour_pontomais'] = consulta_turno_df['data'].astype(str) + ' ' + consulta_turno_df['hora_pontomais'].astype(str)

            # Salvar o arquivo "consulta turno" com as novas colunas, sobrescrevendo o conteúdo original
            consulta_turno_df.to_csv(file_path, sep=';', index=False, encoding='utf-8-sig')
            print(f"- Arquivo processado e salvo: {file_path}\n")

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
    # Função para encontrar a data do evento correspondente à placa no arquivo de notificações
    def find_event_date(plate):
        with open(notifications_file, 'r', encoding='utf-8') as json_file:
            notifications_data = json.load(json_file)
        
        for notification in notifications_data:
            vehicle = notification.get('vehicle', {})
            if vehicle.get('licensePlate') == plate:
                event_date = notification.get('eventDate')
                if event_date:
                    try:
                        # Remove milissegundos se houver (corta tudo depois do ponto)
                        if "." in event_date:
                            event_date = event_date.split(".")[0]

                        # Converter a data para o formato dd/mm/yyyy hh:mm
                        event_date = datetime.strptime(event_date, "%Y-%m-%dT%H:%M:%S")
                        return event_date.strftime("%d/%m/%Y %H:%M")
                    except ValueError:
                        print(f"Erro ao converter a data para a placa {plate}. Data original: {event_date}")
        return None

    # Ler o arquivo "consulta turno" correspondente à operação
    consulta_turno_file = f"consulta turno {operacao}.csv"
    consulta_turno_path = os.path.join(path_temp, consulta_turno_file)
    consulta_turno_df = pd.read_csv(consulta_turno_path, sep=';', encoding='utf-8-sig')

    # Verificar se a coluna 'hour_km_run_pontomais' existe, se não, criar com valores vazios
    if 'hour_km_run_pontomais' not in consulta_turno_df.columns:
        consulta_turno_df['hour_km_run_pontomais'] = None

    # Iterar sobre as linhas do DataFrame "consulta turno"
    for index, row in consulta_turno_df.iterrows():
        plate = row['placa']
        # Verificar se a coluna 'hour_km_run_pontomais' está vazia ou tem valor "0"
        if pd.isna(row['hour_km_run_pontomais']) or row['hour_km_run_pontomais'] == "0":
            event_date = find_event_date(plate)
            if event_date:
                consulta_turno_df.at[index, 'hour_km_run_pontomais'] = event_date

    # Salvar o arquivo "consulta turno" com as atualizações na coluna 'hour_km_run_pontomais'
    consulta_turno_df.to_csv(consulta_turno_path, sep=';', index=False, encoding='utf-8-sig')
    print(f"\n- Arquivo 'consulta turno {operacao}' processado e salvo com as atualizações na coluna 'hour_km_run_pontomais'.")
        
    # Fazer uma cópia do arquivo, renomear e mover para a pasta final
    data_objeto = datetime.strptime(getInitialDate(), "%Y-%m-%dT%H:%M:%S")
    current_date = data_objeto.strftime("%Y_%m_%d")

    new_file_name = f"{operacao}{current_date}_df_final.csv"
    new_file_path = os.path.join(path_final, new_file_name)

    os.makedirs(path_final, exist_ok=True)
    
    shutil.copy2(consulta_turno_path, new_file_path)
    print(f"- Arquivo copiado, renomeado e movido para: {new_file_path}")
    return new_file_path
    
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
    df = pd.DataFrame(df)
    return df
    
def loc_menor_entrada_pontomais():

    # Função para encontrar a primeira entrada correspondente ao primeiro nome na coluna 'Nome' do arquivo "Pontomais_final.xlsx"
    def encontrar_primeira_entrada(nome):
        if isinstance(nome, str):
            match = df_pontomais_final[df_pontomais_final['Nome'] == nome]['1ª Entrada']
            return match.iloc[0] if not match.empty else None
        return None

    df_pontomais_final = criar_dataframe(path_temp, 'Pontomais_final', '.xlsx')
    df_consulta_turno = criar_dataframe(path_temp, 'consulta turno', '.csv')

    # Verifica se a coluna '1ª Entrada' existe; se não, cria a coluna com valores nulos
    if '1ª Entrada' not in df_pontomais_final.columns:
        df_pontomais_final['1ª Entrada'] = None

    # Verifica se a coluna '1ª Entrada' existe; se não, cria a coluna com valores nulos
    if '1ª Entrada' not in df_consulta_turno.columns:
        df_consulta_turno['1ª Entrada'] = None

    df_parceiros = df_consulta_turno['parceiros']
    df_parceiros = df_consulta_turno.reindex(columns=['parceiros'])

    df_parceiros = df_parceiros['parceiros'].str.split(' - ', expand=True)
    df_parceiros.columns = [f'parceiro_{i+1}' for i in range(df_parceiros.shape[1])]
        

    for col in df_parceiros.columns:
        # Nome da nova coluna para armazenar a hora do ponto
        hora_col = f"{col}_hora_ponto"

        # Aplicar a função e criar a nova coluna
        df_parceiros[hora_col] = df_parceiros[col].apply(encontrar_primeira_entrada)

    for col in df_parceiros.columns:
        if '_hora_ponto' in col:
            # Converter valores para tipo datetime.time
            df_parceiros[col] = pd.to_datetime(df_parceiros[col], format='%H:%M', errors='coerce').dt.time

    # Garantir que todas as colunas de horário tenham valores válidos para comparação
    colunas_horario = [col for col in df_parceiros.columns if '_hora_ponto' in col]
    for col in colunas_horario:
        # Substituir apenas valores nulos ou NaT por "23:59:59"
        df_parceiros[col] = df_parceiros[col].apply(
            lambda x: x if pd.notnull(x) else datetime.strptime("23:59:59", "%H:%M:%S").time()
        )

    # Criar uma nova coluna com o menor registro de tempo
    df_parceiros['menor_tempo'] = df_parceiros[colunas_horario].apply(
        lambda row: min(row), axis=1
    )
    
    # Substituir valores 23:59:59 por None na coluna menor_tempo
    df_parceiros['menor_tempo'] = df_parceiros['menor_tempo'].apply(
        lambda x: None if x == datetime.strptime("23:59:59", "%H:%M:%S").time() else x
    )

    df_parceiros.to_csv(os.path.join(path_temp,'menor-entrada-equipes.csv'), sep=';', index=False, encoding='utf-8-sig')
    
    return df_parceiros


