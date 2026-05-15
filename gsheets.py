
import os
import json
import logging
logger = logging.getLogger(__name__)
from time import sleep
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from auxiliar import id_planilha_gsheet
import traceback
import time
from zoneinfo import ZoneInfo

dir_script = os.path.dirname(os.path.abspath(__file__))
dir_app = os.path.join(dir_script, 'app')

def _localizar_credenciais():
    """
    Localiza o chaveGoogle.json.
    - No GitHub Actions: grava o JSON da env GOOGLE_CREDENTIALS_JSON em app/chaveGoogle.json.
    - Localmente: busca em app/ ou na raiz do projeto.
    """
    caminho_app = os.path.join(dir_app, "chaveGoogle.json")

    # Modo CI: monta o arquivo a partir da secret
    credenciais_json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if credenciais_json_str:
        try:
            os.makedirs(dir_app, exist_ok=True)
            with open(caminho_app, 'w', encoding='utf-8') as f:
                json.dump(json.loads(credenciais_json_str), f)
            print("- Credenciais Google carregadas da variável de ambiente.")
            return caminho_app
        except Exception as e:
            print(f"# Erro ao gravar credenciais do Actions: {e}")

    # Modo local: busca o arquivo físico
    caminho_raiz = os.path.join(dir_script, "chaveGoogle.json")
    if os.path.exists(caminho_app):
        return caminho_app
    elif os.path.exists(caminho_raiz):
        return caminho_raiz
    return caminho_app  # Retorna padrão (erro aparecerá no try/except do __init__)

arq_credenciais_json = _localizar_credenciais()

class Gsheets:
    def __init__(self):
        # Atributos inicializados como None para evitar AttributeError caso a autenticação falhe
        self.credenciais = None
        self.cliente = None
        self.cliente_sheets = None
        self.servico_drive = None
        self.planilhaGSheet = None
        self._cache_aba = {}

        self.escopo = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://spreadsheets.google.com/feeds"
        ]

        try:
            self.credenciais = Credentials.from_service_account_file(arq_credenciais_json, scopes=self.escopo)
            self.cliente = gspread.authorize(self.credenciais)

            self.creds_planilha = ServiceAccountCredentials.from_json_keyfile_name(arq_credenciais_json, scopes=self.escopo)
            self.client_planilha = gspread.authorize(self.creds_planilha)

            self.cliente_sheets = self.cliente
            self.servico_drive = build('drive', 'v3', credentials=self.credenciais)
            self.planilhaGSheet = self.cliente.open_by_key(id_planilha_gsheet)
            self.horario_inicio_execucao = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo('America/Sao_Paulo'))

        except Exception as e:
            logger.error(f'[AVISO] Falha ao conectar com o Google Sheets/Drive: {e}')

    def attsheets(self, planilha_id, aba_nome):
        """Atualiza a célula B1 da aba com a data/hora atual."""
        while True:
            try:
                planilha = self.cliente.open_by_key(planilha_id)
                aba = planilha.worksheet(aba_nome)
                data_hora_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
                aba.update_cell(1, 2, data_hora_atual)
                return
            except APIError as e:
                if '429' in str(e):
                    logger.error("[AVISO] Erro 429: Limite de requisicoes excedido. Aguardando 60s...")
                    sleep(60)

    def acessos(self, texto_local='', nome_aba=None):
        """
        Busca login e senha de uma planilha de acessos.
        Retorna (login, senha) ou (None, None) se não encontrado.
        Fallback: variáveis de ambiente LOGIN_GPM / SENHA_GPM.
        """
        # Fallback imediato se o cliente não está disponível
        if not self.cliente:
            return os.environ.get('LOGIN_GPM'), os.environ.get('SENHA_GPM')

        try:
            planilha = self.cliente.open_by_key("1odD_fRayhYp9wAkG6M76vU5blF2IAjGo4WjuMY3XelU")
            aba = planilha.worksheet(nome_aba)
            valores = aba.get_all_values()

            if not valores:
                return os.environ.get('LOGIN_GPM'), os.environ.get('SENHA_GPM')

            df = pd.DataFrame(valores[1:], columns=valores[0])

            linha = df[df['Parametro_de_busca'] == texto_local]
            if linha.empty:
                print(f"# Credencial '{texto_local}' nao encontrada na planilha. Usando variaveis de ambiente.")
                return os.environ.get('LOGIN_GPM'), os.environ.get('SENHA_GPM')

            login = str(linha.iloc[0]['Login'])
            senha = str(linha.iloc[0]['Senha'])
            return login, senha

        except Exception as e:
            print(f"# Erro ao buscar acessos na planilha: {e}. Usando variaveis de ambiente.")
            return os.environ.get('LOGIN_GPM'), os.environ.get('SENHA_GPM')

    def upload_para_drive(self, caminho_arquivo, id_pasta_drive):
        """
        Faz o upload de um arquivo para uma pasta no Google Drive.
        Se já existir arquivo com o mesmo nome: substitui. Caso contrário: cria novo.
        """
        if not self.servico_drive:
            print('# Conexao com Drive nao disponivel. Upload cancelado.')
            return False

        try:
            nome_arquivo = os.path.basename(caminho_arquivo)

            query = f"name='{nome_arquivo}' and '{id_pasta_drive}' in parents and trashed=false"
            response = self.servico_drive.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = response.get('files', [])
            mimetype = 'text/csv' if nome_arquivo.endswith('.csv') else None
            midia = MediaFileUpload(caminho_arquivo, mimetype=mimetype, resumable=True)

            if files:
                file_id = files[0].get('id')
                print(f'- Atualizando arquivo existente "{nome_arquivo}" no Drive...')
                self.servico_drive.files().update(
                    fileId=file_id,
                    media_body=midia,
                    supportsAllDrives=True
                ).execute()
                print(f'[OK] Arquivo "{nome_arquivo}" atualizado com sucesso!')
                return True
            else:
                print(f'- Criando novo arquivo "{nome_arquivo}" no Drive...')
                metadados_arquivo = {
                    'name': nome_arquivo,
                    'parents': [id_pasta_drive]
                }
                arquivo = self.servico_drive.files().create(
                    body=metadados_arquivo,
                    media_body=midia,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                print(f'[OK] Upload do novo arquivo "{nome_arquivo}" concluido! ID: {arquivo.get("id")}')
                return True

        except Exception as e:
            print(f'# Erro durante o upload para o Google Drive: {e}')
            traceback.print_exc()
            return False

    def selecionar_meses_drive(self, folder_id, data_inicio_obj=None, data_fim_obj=None):
        """
        Lista os arquivos yyyy-mm na pasta do Drive e seleciona todos os meses que
        estejam dentro do intervalo [data_inicio_obj, data_fim_obj].
        Se as datas não forem informadas, mantém o comportamento de pegar os 2 últimos.
        """
        import re

        if not self.servico_drive:
            print('# Conexao com Drive nao disponivel. Usando meses padrao (atual + anterior).')
            hoje = datetime.now()
            mes_atual = hoje.strftime("%Y-%m")
            mes_anterior = f"{hoje.year}-{hoje.month - 1:02d}" if hoje.month > 1 else f"{hoje.year - 1}-12"
            return [mes_anterior, mes_atual]

        try:
            query = f"'{folder_id}' in parents and trashed=false"
            response = self.servico_drive.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            padrao = re.compile(r'^\d{4}-\d{2}$')
            nomes_disponiveis = sorted([
                f['name'].replace('.csv', '').replace('.xlsx', '').replace('.xls', '')
                for f in response.get('files', [])
                if padrao.match(f['name'].replace('.csv', '').replace('.xlsx', '').replace('.xls', ''))
            ], reverse=True)

            if not nomes_disponiveis:
                print('# AVISO: Nenhum arquivo yyyy-mm encontrado na pasta do Drive.')
                return []

            # Se temos datas, filtramos o range. Caso contrário, pegamos os 2 últimos.
            if data_inicio_obj and data_fim_obj:
                # Gerar lista de todos os meses no range YYYY-MM
                inicio_str = data_inicio_obj.strftime("%Y-%m")
                fim_str = data_fim_obj.strftime("%Y-%m")
                
                selecionados = [m for m in nomes_disponiveis if inicio_str <= m <= fim_str]
                
                # O usuário mencionou que deveria pegar 2025-12 se começar em 2026-01
                # Vamos garantir que pegamos pelo menos o mês anterior ao início para cobrir viradas de turno
                mes_anterior_inicio = (data_inicio_obj - timedelta(days=15)).strftime("%Y-%m")
                if mes_anterior_inicio in nomes_disponiveis and mes_anterior_inicio not in selecionados:
                    selecionados.append(mes_anterior_inicio)
                
                if not selecionados:
                    selecionados = nomes_disponiveis[:2]
            else:
                mes_atual = datetime.now().strftime("%Y-%m")
                if mes_atual in nomes_disponiveis:
                    idx = nomes_disponiveis.index(mes_atual)
                    selecionados = nomes_disponiveis[idx:idx+2]
                else:
                    selecionados = nomes_disponiveis[:2]

            selecionados = sorted(list(set(selecionados))) # Garante únicos e ordem cronológica
            print(f"- Meses identificados no range: {selecionados}")
            return selecionados

        except Exception as e:
            print(f'# Erro ao listar arquivos do Drive: {e}')
            return []

    def download_arquivos_pasta_drive(self, folder_id, nomes_esperados, path_destino):
        """
        Baixa os arquivos de uma pasta do Google Drive cujos nomes contenham
        os valores da lista nomes_esperados.
        """
        import io
        from googleapiclient.http import MediaIoBaseDownload

        if not self.servico_drive:
            print('# Conexao com Drive nao disponivel.')
            return []

        print(f'- Procurando arquivos {nomes_esperados} no Google Drive (ID: {folder_id})...')

        try:
            query = f"'{folder_id}' in parents and trashed=false"
            response = self.servico_drive.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = response.get('files', [])
            arquivos_baixados = []
            os.makedirs(path_destino, exist_ok=True)

            for file in files:
                nome_arquivo = file.get('name')
                for esperado in nomes_esperados:
                    if esperado in nome_arquivo:
                        caminho_salvar = os.path.join(path_destino, nome_arquivo)
                        print(f"- Baixando arquivo encontrado: {nome_arquivo}...")
                        request = self.servico_drive.files().get_media(fileId=file.get('id'))
                        fh = io.FileIO(caminho_salvar, 'wb')
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            _, done = downloader.next_chunk()
                        print(f"[OK] Download concluido: {nome_arquivo}")
                        arquivos_baixados.append(caminho_salvar)
                        break

            return arquivos_baixados

        except Exception as e:
            print(f'# Erro ao baixar arquivos do Google Drive: {e}')
            traceback.print_exc()
            return []
