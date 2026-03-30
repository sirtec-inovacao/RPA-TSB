import download_gpm as dg
import api_zuq as az
import data_analysis as da
from gsheets import Gsheets
from get_date_run import writeDate
from get_date_run import getInitialDate
from auxiliar import *
from download_gpm import Chrome
from download_pontomais import Pontomais

from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import os

def main():

    print(f'{t}\t\tINICIANDO EXECUCAO ROBO TSB{t}')

    chrome = Chrome()
    gsheets = Gsheets()
    ponto = Pontomais()

    hoje = datetime.now().strftime("%d/%m/%Y")
    hoje_obj = datetime.strptime(hoje, "%d/%m/%Y")

    # Loop para processar dia a dia, do dia seguinte ao da planilha até hoje
    while True:
        # Busca a data atual na planilha de controle
        data_planilha = getDate()
        
        # Se não conseguir buscar a data, para a execução com erro claro
        if data_planilha is None:
            print(f"{l}# ERRO: Falha ao obter a data da planilha. Verifique as credenciais e o ID da planilha.{l}")
            break

        # O dia a ser processado é o SEGUINTE ao que está na planilha
        data_planilha_obj = datetime.strptime(data_planilha, "%d/%m/%Y")
        data_execucao_obj = data_planilha_obj + timedelta(days=1)

        # Se o próximo dia a processar já passou de hoje, não há mais datas
        if data_execucao_obj > hoje_obj:
            print(f'{l}- Todas as datas foram processadas até hoje ({hoje})! Nenhuma data pendente.{l}')
            break

        data_execucao = data_execucao_obj.strftime("%d/%m/%Y")
        print(f'{t}>>> PROCESSANDO DIA: {data_execucao} (Planilha estava em: {data_planilha}) <<<{t}')

        # Avança a data na planilha ANTES de processar
        # writeDate soma +1 dia, então a planilha terá a data_execucao
        # Isso garante que getInitialDate() retorna a data correta nos módulos de download
        writeDate(data_planilha, data_planilha)
            
        # Remover arquivos antigos
        chrome.limpar_pasta_temp()
        chrome.limpar_downloads_inicial()
        
        # Fazer download dos arquivos do GPM
        chrome.baixar_consulta_turno("BA")
        chrome.baixar_consulta_turno("CE")
        sleep(5)
        
        # Fazer download dos arquivos do pontomais
        ponto.baixar_relatorios()
        
        # Fazer requisição e puxar os dados da API
        az.relatorio_zuq()

        # Processar arquivos para BA
        da.find_and_process_files(path_temp, 'BA')

        # Processar arquivos para CE
        da.find_and_process_files(path_temp, 'CE')

        da.process_pontomais_files(path_temp)

        # Fazer upload do arquivo consolidado do Pontomais para o Drive
        print(f"{l}- Fazendo upload do arquivo consolidado do Pontomais para o Drive...")
        gsheets.upload_para_drive(pontomais_df, "1KGzQdGQOpSi-CDJgmMakVe8zBwf9tzmM")
        
        # Chamar a função para processar os arquivos de consulta turno para BA
        da.process_consulta_turno_files(path_temp, pontomais_df, "BA")
        # Chamar a função para processar os arquivos de consulta turno para CE
        da.process_consulta_turno_files(path_temp, pontomais_df, "CE")

        # Processar os logs dos veículos para a operação BA
        arquivo_final_ba = da.process_vehicle_logs_by_operation(path_temp, "BA", notifications_file)
        if arquivo_final_ba and id_pasta_drive_final:
            sucesso_ba = gsheets.upload_para_drive(arquivo_final_ba, id_pasta_drive_final)
            if sucesso_ba:
                print(f"\nSUCESSO: Arquivo BA salvo no Drive ({os.path.basename(arquivo_final_ba)})")
            else:
                print(f"\nERRO: Falha ao salvar arquivo BA no Drive ({os.path.basename(arquivo_final_ba)})")

        # Processar os logs dos veículos para a operação CE
        arquivo_final_ce = da.process_vehicle_logs_by_operation(path_temp, "CE", notifications_file)
        if arquivo_final_ce and id_pasta_drive_final:
            sucesso_ce = gsheets.upload_para_drive(arquivo_final_ce, id_pasta_drive_final)
            if sucesso_ce:
                print(f"\nSUCESSO: Arquivo CE salvo no Drive ({os.path.basename(arquivo_final_ce)})")
            else:
                print(f"\nERRO: Falha ao salvar arquivo CE no Drive ({os.path.basename(arquivo_final_ce)})")

        # A data já foi avançada no início da iteração, não precisa chamar writeDate novamente
        print(f'{l}- Dia {data_execucao} concluído com sucesso!{l}')

    # Atualiza planilha de robos (fora do loop, apenas uma vez ao final)                              
    gsheets.attsheets(id_planilha_att_gsheet, aba_att_gsheet)

def getDate():
    data_raw = getInitialDate()
    if not data_raw:
        return None
    data_objeto = datetime.strptime(data_raw, "%Y-%m-%dT%H:%M:%S")
    return data_objeto.strftime("%d/%m/%Y")

main()