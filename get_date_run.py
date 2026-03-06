import json
from datetime import datetime, timedelta
from auxiliar import *
from gsheets import Gsheets

# ID e informações da planilha onde a data fica armazenada
ID_PLANILHA_CONTROLE = '1lM8Q3NIUrDsdR8OD_6RG0wAddXvq1PpWczuOUeOyivE'
NOME_ABA = 'CONTROLE_GERAL_ROBOS'
CELULA_DATA = 'F16'

def writeDate(initial_date, final_date):
    print("\n----------------------------------------------------------------------")
    print("Modo SIMULAÇÃO ativo: A nova data NÃO será enviada para o Drive ainda.")
    print(f"Datas processadas - Inicio: {initial_date} | Fim: {final_date}")
    print("----------------------------------------------------------------------\n")
    pass

def _buscar_data_planilha():
    try:
        gsheets = Gsheets()
        print("- Consultando data de execução no Google Sheets...")
        planilha = gsheets.cliente_sheets.open_by_key(ID_PLANILHA_CONTROLE)
        aba = planilha.worksheet(NOME_ABA)
        valor_celula = aba.acell(CELULA_DATA).value
        
        if valor_celula:
            # valor_celula vem como "06/03/2026 04:06"
            # Extraímos apenas a data ("06/03/2026")
            data_str = valor_celula.split(" ")[0]
            # Convertermos para datetime para garantir que o formato está válido
            data_objeto = datetime.strptime(data_str, "%d/%m/%Y")
            return data_objeto
        else:
            print("# ALERTA: A célula de data (F16) no Google Sheets está vazia.")
            return None
    except Exception as e:
        print(f"# Erro ao buscar a data no Google Sheets: {e}")
        return None

def getInitialDate():
    data_objeto = _buscar_data_planilha()
    if data_objeto:
        # Formatar para o formato esperado pelo robô (Início do dia: 00:00:00)
        data_formatada = data_objeto.strftime("%Y-%m-%dT00:00:00")
        return data_formatada
    return None

def getFinalDate():
    data_objeto = _buscar_data_planilha()
    if data_objeto:
        # Formatar para o formato esperado pelo robô (Fim do dia: 23:59:59)
        final_do_dia = datetime(data_objeto.year, data_objeto.month, data_objeto.day, 23, 59, 59)
        data_formatada = final_do_dia.strftime("%Y-%m-%dT%H:%M:%S")
        return data_formatada
    return None
