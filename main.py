import download_gpm as dg
import api_zuq as az
import data_analysis as da
from gsheets import Gsheets
from get_date_run import writeDate
from get_date_run import getInitialDate
from auxiliar import *
from download_gpm import Chrome

from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import os
import sys

def main():

    print(f'{t}\t\tINICIANDO EXECUCAO ROBO TSB{t}')

    print("- Inicializando Gsheets...")
    gsheets = Gsheets()
    
    # Validação da conexão do Google Sheets/Drive no início
    if gsheets.cliente is None or gsheets.servico_drive is None:
        sys.exit("# ERRO CRÍTICO: Falha na conexão ou autenticação com as APIs do Google (Gsheets/Drive). Interrompendo execução.")

    print("- Inicializando Chrome...")
    chrome = Chrome()
    print("- Obtendo datas do sistema...")

    hoje = datetime.now().strftime("%d/%m/%Y")
    hoje_obj = datetime.strptime(hoje, "%d/%m/%Y")

    # Loop removido. Trabalhando em Lote (Batch).
    # Busca a data atual no config.json
    data_planilha = getDate()
    
    if data_planilha is None:
        sys.exit("# ERRO CRÍTICO: Falha ao obter a data do config.json. Interrompendo execução.")

    data_planilha_obj = datetime.strptime(data_planilha, "%d/%m/%Y")
    hoje_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ontem_obj = hoje_obj - timedelta(days=1)

    if data_planilha_obj > ontem_obj:
        print(f'{l}- Todas as datas já foram processadas! Nenhuma pendente.{l}')
        return

    print(f'{t}>>> PROCESSANDO PERIODO: {data_planilha_obj.strftime("%d/%m/%Y")} até {ontem_obj.strftime("%d/%m/%Y")} <<<{t}')
    
    # Limpa as pastas de trabalho para garantir que não há arquivos de execuções anteriores
    import shutil as _shutil
    for _pasta in [path_downloads, path_temp]:
        if os.path.exists(_pasta):
            try:
                # Tenta remover tudo. Se falhar (ex: arquivo aberto), remove o que der.
                for filename in os.listdir(_pasta):
                    file_path = os.path.join(_pasta, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            _shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"  # Aviso: Não foi possível remover {filename} (pode estar aberto).")
            except Exception as e:
                print(f"  # Erro ao limpar {_pasta}: {e}")
        os.makedirs(_pasta, exist_ok=True)
    print(f"- Pastas de trabalho limpas: downloads e temp.")
    
    # --- 1. DOWNLOAD ZUQ (CONEXÃO DA TELEMETRIA) ---
    print(f"{l}- Fazendo download dos arquivos ZUQ")
    sucesso_zuq = az.baixar_zuq_periodo(data_planilha_obj, ontem_obj)
    if not sucesso_zuq:
        sys.exit("# ERRO CRÍTICO: Falha na conexão ou download da API ZUQ. Interrompendo execução.")

    # --- 2. DOWNLOAD DRIVE (PONTOMAIS CONSOLIDADO) ---
    id_pasta_pontos = "1fDcVXWg1YJ3xlAer0JmOD59XtryiWR1N"
    
    # Lista os arquivos da pasta do Drive no padrão yyyy-mm e decide quais baixar
    # Regra: se o mês atual existe, baixa ele + anterior. Se não existe, baixa os 2 últimos disponíveis.
    print(f"{l}- Consultando arquivos disponíveis na pasta do Drive...")
    meses_str = gsheets.selecionar_meses_drive(id_pasta_pontos, data_planilha_obj, ontem_obj)
    print(f"- Meses selecionados para download: {meses_str}")
    arquivos_drive = gsheets.download_arquivos_pasta_drive(id_pasta_pontos, meses_str, path_downloads)
    
    # Concatena arquivos se houver e salva no path_temp
    if arquivos_drive:
        dfs = []
        for arq in arquivos_drive:
            ext = os.path.splitext(arq)[1].lower()
            try:
                if ext == '.csv':
                    # Arquivos do Drive usam ; como separador
                    dfs.append(pd.read_csv(arq, sep=';', encoding='utf-8-sig', dtype=str))
                elif ext in ('.xlsx', '.xls'):
                    dfs.append(pd.read_excel(arq, dtype=str))
                else:
                    dfs.append(pd.read_csv(arq, encoding='utf-8-sig', dtype=str))
                print(f"  - Lido: {os.path.basename(arq)}")
            except Exception as e:
                print(f"# Erro ao ler arquivo {os.path.basename(arq)}: {e}")
        
        if dfs:
            df_consolidado = pd.concat(dfs, ignore_index=True)
            os.makedirs(path_temp, exist_ok=True)
            caminho_ponto_temp = os.path.join(path_temp, "Pontomais_final.xlsx")
            df_consolidado.to_excel(caminho_ponto_temp, index=False)
            print(f"- Pontomais consolidado: {len(df_consolidado)} linhas")
        else:
            sys.exit("# ERRO CRÍTICO: Nenhum arquivo do Drive pôde ser lido. Interrompendo execução.")
    else:
        sys.exit("# ERRO CRÍTICO: Nenhum arquivo do Drive foi encontrado para os meses informados. Interrompendo execução.")
    
    # --- 3. DOWNLOAD GPM ---
    print(f"{l}- Fazendo download dos arquivos GPM (BA e CE)")
    chrome.baixar_gpm_periodo("BA", data_planilha_obj, ontem_obj)
    chrome.baixar_gpm_periodo("CE", data_planilha_obj, ontem_obj)

    print(f"{l}- Etapa de DOWNLOADS em lote finalizada!{l}")
    
    # --- 4. PROCESSAMENTO DOS DADOS ---
    print(f"{l}- Iniciando processamento dos dados...")
    
    # Processa os arquivos GPM (BA e CE) enriquecendo com colunas auxiliares
    da.find_and_process_files(path_temp, 'BA')
    da.find_and_process_files(path_temp, 'CE')
    
    # Garante que o Pontomais_final.xlsx está pronto e tem a coluna '1ª Entrada'
    da.process_pontomais_files(path_temp)

    # Faz o cruzamento GPM x Pontomais para obter a hora do ponto de cada equipe
    da.process_consulta_turno_files(path_temp, caminho_ponto_temp, "BA")
    da.process_consulta_turno_files(path_temp, caminho_ponto_temp, "CE")

    # Enriquece com dados de telemetria da ZUQ e gera os arquivos finais
    arquivo_final_ba = da.process_vehicle_logs_by_operation(path_temp, "BA", notifications_file)
    arquivo_final_ce = da.process_vehicle_logs_by_operation(path_temp, "CE", notifications_file)
    
    # Faz upload dos arquivos finais para o Google Drive
    for operacao_label, arquivos_finais in [('BA', arquivo_final_ba), ('CE', arquivo_final_ce)]:
        if not arquivos_finais or not id_pasta_drive_final:
            continue
        
        # Suporta tanto lista (novo padrão diário) quanto string (compatibilidade)
        lista = arquivos_finais if isinstance(arquivos_finais, list) else [arquivos_finais]
        enviados = 0
        for arq in lista:
            if arq and os.path.exists(arq):
                ok = gsheets.upload_para_drive(arq, id_pasta_drive_final)
                if ok:
                    enviados += 1
        print(f"\n✅ {enviados}/{len(lista)} arquivo(s) de {operacao_label} enviados ao Drive.")

    # --- 5. ATUALIZAÇÃO DO CONFIG ---
    # Avança a data do config para o dia seguinte ao último processado (que foi "ontem")
    writeDate(ontem_obj.strftime("%d/%m/%Y"))
    print(f'{l}✅ Período concluído! config.json avançado para o próximo ciclo.{l}')
    
    # Atualiza planilha de robos (fora do loop, apenas uma vez ao final)                              
    gsheets.attsheets(id_planilha_att_gsheet, aba_att_gsheet)

def getDate():
    data_raw = getInitialDate()
    if not data_raw:
        return None
    data_objeto = datetime.strptime(data_raw, "%Y-%m-%dT%H:%M:%S")
    return data_objeto.strftime("%d/%m/%Y")

main()