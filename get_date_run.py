import os
import json
from datetime import datetime, timedelta
from auxiliar import *
from gsheets import Gsheets

def writeDate(initial_date, final_date_unused):
    """Atualiza a data na planilha de controle do Google Sheets para o próximo dia."""
    try:
        gsheets = Gsheets()
        print(f"- Atualizando planilha de controle via API ({celula_data_controle})...")
        planilha = gsheets.cliente_sheets.open_by_key(id_planilha_controle)
        aba = planilha.worksheet(nome_aba_controle)
        
        # Converte a data atual para objeto para somar 1 dia
        data_atual = datetime.strptime(initial_date, "%d/%m/%Y")
        proxima_data = data_atual + timedelta(days=1)
        hora_atual = datetime.now().strftime("%H:%M:%S")
        proxima_data_str = f"{proxima_data.strftime('%d/%m/%Y')} {hora_atual}"
        
        # Atualiza a célula correspondente
        aba.update_acell(celula_data_controle, proxima_data_str)
        print(f" Data de controle avançada para: {proxima_data_str}")
        return True
    except Exception as e:
        print(f"# Erro ao atualizar a data na planilha: {e}")
        return False

def _buscar_data_planilha():
    try:
        gsheets = Gsheets()
        print("- Consultando data de execução no Google Sheets...")
        planilha = gsheets.cliente_sheets.open_by_key(id_planilha_controle)
        aba = planilha.worksheet(nome_aba_controle)
        valor_celula = aba.acell(celula_data_controle).value
        
        if valor_celula:
            data_str = valor_celula.split(" ")[0]
            data_objeto = datetime.strptime(data_str, "%d/%m/%Y")
            
            return data_objeto
        else:
            print(f"# ALERTA: A célula de data ({celula_data_controle}) no Google Sheets está vazia.")
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
