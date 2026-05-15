import os
import json
from datetime import datetime, timedelta

def _get_config_path():
    dir_script = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir_script, "config.json")

def _buscar_data_config():
    try:
        with open(_get_config_path(), 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Ler apenas a initial_date como base para a execução daquele dia
            data_str = config.get("initial_date", "").split("T")[0]
            if data_str:
                return datetime.strptime(data_str, "%Y-%m-%d")
    except Exception as e:
        print(f"# Erro ao ler o config.json: {e}")
    return None

def writeDate(initial_date, final_date_unused=None):
    """Atualiza a data no arquivo local config.json para o próximo dia."""
    try:
        # initial_date geralmente vem de main.py no formato DD/MM/YYYY
        # Precisamos converter para objeto datetime e somar 1 dia
        data_atual = datetime.strptime(initial_date, "%d/%m/%Y")
        proxima_data = data_atual + timedelta(days=1)
        
        proxima_data_str = proxima_data.strftime("%Y-%m-%dT00:00:00")
        
        config_path = _get_config_path()
        
        # Tenta carregar o config existente para não apagar outras chaves acidentalmente
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # Atualizamos APENAS a data inicial, já que a final é calculada em tempo de execução
        config["initial_date"] = proxima_data_str
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
        print(f"- Arquivo config.json avançado para o dia: {proxima_data.strftime('%d/%m/%Y')}")
        return True
    except Exception as e:
        print(f"# Erro ao atualizar a data no config.json: {e}")
        return False

def getInitialDate():
    data_objeto = _buscar_data_config()
    if data_objeto:
        # Formatar para o formato esperado pelo robô (Início do dia: 00:00:00)
        return data_objeto.strftime("%Y-%m-%dT00:00:00")
    return None

def getFinalDate():
    data_objeto = _buscar_data_config()
    if data_objeto:
        # Formatar para o formato esperado pelo robô (Fim do dia: 23:59:59)
        final_do_dia = datetime(data_objeto.year, data_objeto.month, data_objeto.day, 23, 59, 59)
        return final_do_dia.strftime("%Y-%m-%dT%H:%M:%S")
    return None
