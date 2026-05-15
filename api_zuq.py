import os
import requests
import json
from auxiliar import *

def baixar_zuq_periodo(data_inicio_obj, data_fim_obj):
    base_url = "https://app.zuq.com.br"
    data_endpoint = "/api/notification/list"

    start_date_str = data_inicio_obj.strftime("%Y-%m-%d")
    end_date_str = data_fim_obj.strftime("%Y-%m-%d")

    try:
        print(f'{l}- Iniciando integração com API ZUQ...')
        print(f'- Período: {start_date_str} até {end_date_str}')
        
        if not token_zuq:
            print('# ERRO: TOKEN_ZUQ não configurado. Verifique o arquivo .env.')
            with open(notifications_file, "w") as f:
                json.dump([], f)
            return
        
        headers = {"Authorization": f"{token_zuq}"}
        dados_agregados = []
        
        # Fatiamento de 30 em 30 dias para evitar Erro 400 em períodos longos
        from datetime import timedelta
        chunk_start = data_inicio_obj
        
        while chunk_start <= data_fim_obj:
            chunk_end = min(chunk_start + timedelta(days=30), data_fim_obj)
            c_start_str = chunk_start.strftime("%Y-%m-%d")
            c_end_str = chunk_end.strftime("%Y-%m-%d")
            
            print(f"  - Buscando fatia: {c_start_str} até {c_end_str}")
            page = 1
            while True:
                params = {
                    "start": c_start_str,
                    "end": c_end_str,
                    "page": page,
                    "size": 500,
                    "property": "ODOMETER"
                }
                data_response = requests.get(base_url + data_endpoint, headers=headers, params=params, timeout=30)
                data_response.raise_for_status()
                data = data_response.json()

                if not data:
                    break

                dados_agregados.extend(data)
                print(f"    - Página {page}: {len(data)} registros (total: {len(dados_agregados)})")
                
                # Se vier menos que o tamanho da página, é a última página desta fatia
                if len(data) < 500:
                    break
                page += 1
            
            chunk_start = chunk_end + timedelta(days=1)

        # Salva o resultado
        os.makedirs(os.path.dirname(notifications_file), exist_ok=True)
        with open(notifications_file, "w") as json_file:
            json.dump(dados_agregados, json_file, indent=4)
        print(f"✅ ZUQ: {len(dados_agregados)} registros salvos em: {notifications_file}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"# Erro na requisição ZUQ: {e}")
        return False

    except Exception as e:
        print(f"# Erro genérico na ZUQ: {e}")
        return False