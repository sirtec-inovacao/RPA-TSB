import os
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback
import time
import io
from auxiliar import l

# Importa as variáveis de configuração globais do arquivo Auxiliar.py
# É esperado que este arquivo contenha o ID da planilha de acesso principal.
from auxiliar import id_planilha_gsheet

class Gsheets:
    """
    Classe padronizada para gerenciar a conexão e as interações com as APIs
    do Google Sheets e Google Drive.
    
    Esta classe foi projetada para ser reutilizável em diversos projetos de automação.
    Ela lida com a autenticação de forma unificada, funcionando tanto em ambientes
    locais (usando um arquivo 'chaveGoogle.json') quanto em ambientes de nuvem como
    o GitHub Actions (usando uma variável de ambiente).
    """
    def __init__(self):
        # Define os escopos de permissão necessários para a API.
        # 'spreadsheets' para planilhas e 'drive' para arquivos.
        self.escopo = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Inicializa as variáveis de conexão como None. Elas serão preenchidas na autenticação.
        self.cliente_sheets = None # Cliente para interagir com o Google Sheets (gspread)
        self.servico_drive = None  # Serviço para interagir com o Google Drive (google-api-client)
        self.planilhaGSheet = None # Armazena o objeto da planilha principal de acesso
        
        # Captura o horário de início da execução, já convertido para o fuso horário de São Paulo.
        self.horario_inicio_execucao = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo('America/Sao_Paulo'))
        
        try:
            # print('- Iniciando autenticação unificada com o Google...')
            # Tenta carregar as credenciais da variável de ambiente 'GOOGLE_CREDENTIALS_JSON'.
            credenciais_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            credenciais = None

            if credenciais_json_str:
                # Se a variável de ambiente existir, carrega as credenciais a partir dela.
                # print('- Carregando credenciais a partir da variável de ambiente.')
                credenciais_info = json.loads(credenciais_json_str)
                credenciais = Credentials.from_service_account_info(credenciais_info, scopes=self.escopo)
            else:
                # Se a variável não existir, assume um ambiente de desenvolvimento local
                # e tenta carregar a partir de um arquivo físico.
                # print('- Carregando credenciais do arquivo local "chaveGoogle.json".')
                credenciais = Credentials.from_service_account_file('chaveGoogle.json', scopes=self.escopo)

            # --- Conexão com Google Sheets (usando a biblioteca gspread) ---
            self.cliente_sheets = gspread.authorize(credenciais)
            # Abre a planilha principal de acessos, cujo ID é definido no arquivo Auxiliar.py
            self.planilhaGSheet = self.cliente_sheets.open_by_key(id_planilha_gsheet)
            # print('✅ Conexão com Google Sheets estabelecida.')

            # --- Conexão com Google Drive (usando a biblioteca google-api-python-client) ---
            # Esta biblioteca é mais robusta para manipulação de arquivos (uploads, permissões, etc).
            self.servico_drive = build('drive', 'v3', credentials=credenciais)
            # print('✅ Conexão com Google Drive estabelecida.')

        except Exception as e:
            # Se a autenticação falhar, lança um erro crítico.
            print(f'# Erro CRÍTICO na inicialização da conexão com o Google: {e}')
            raise

    def upload_para_drive(self, caminho_arquivo, id_pasta_drive):
        """
        Faz o upload de um arquivo para uma pasta no Google Drive.
        A lógica é:     - Se um arquivo com o mesmo nome já existir, ele será SOBRESCRITO. 
                        - Caso contrário, um novo arquivo será criado.
        Parâmetros:
            caminho_arquivo (str): O caminho local do arquivo a ser enviado.
            id_pasta_drive (str): O ID da pasta de destino no Google Drive.
        """
        if not self.servico_drive:
            print('# Conexão com Drive não disponível. Upload cancelado.')
            return False

        try:
            nome_arquivo = os.path.basename(caminho_arquivo)
                        
            # 1. Procura por um arquivo com o mesmo nome na pasta de destino.
            # A query busca por nome, na pasta especificada ('parents'), e que não esteja na lixeira.
            query = f"name='{nome_arquivo}' and '{id_pasta_drive}' in parents and trashed=false"
            response = self.servico_drive.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,         # Essencial para encontrar arquivos em Drives Compartilhados
                includeItemsFromAllDrives=True  # Garante a busca em todos os drives
            ).execute()
            
            files = response.get('files', [])
            
            # Define o tipo do arquivo (MIME type) para o upload. Ajuda o Google Drive a identificar o arquivo.
            mimetype = 'text/csv' if nome_arquivo.endswith('.csv') else None
            midia = MediaFileUpload(caminho_arquivo, mimetype=mimetype, resumable=True)

            if files:
                # 2. SE O ARQUIVO EXISTE: Usa o método update() para substituir seu conteúdo.
                file_id = files[0].get('id')
                print(f'- Atualizando arquivo existente "{nome_arquivo}" no Drive...')
                self.servico_drive.files().update(
                    fileId=file_id,
                    media_body=midia,
                    supportsAllDrives=True  # Necessário para editar arquivos em Drives Compartilhados
                ).execute()
                print(f'✅ Arquivo "{nome_arquivo}" atualizado com sucesso!')
                return True
            else:
                # 3. SE O ARQUIVO NÃO EXISTE: Usa o método create() para criar um novo.
                print(f'- Criando novo arquivo "{nome_arquivo}" no Drive...')
                metadados_arquivo = {
                    'name': nome_arquivo,
                    'parents': [id_pasta_drive]
                }
                arquivo = self.servico_drive.files().create(
                    body=metadados_arquivo,
                    media_body=midia,
                    fields='id',
                    supportsAllDrives=True # Necessário para criar arquivos em Drives Compartilhados
                ).execute()
                print(f'✅ Upload do novo arquivo "{nome_arquivo}" concluído com sucesso! ID: {arquivo.get("id")}')
                return True

        except Exception as e:
            print(f'# Erro durante o upload para o Google Drive: {e}')
            traceback.print_exc()
            return False

    def attsheets(self, planilha_id, aba_nome):
        """
        Atualiza uma planilha de status com informações sobre a execução do robô.
        Registra o horário de início, fim e a duração total da execução.
        
        Parâmetros:
            planilha_id (str): O ID da planilha de status a ser atualizada.
            aba_nome (str): O nome da aba específica onde os dados serão escritos.
        """
        try:
            print(f'{l}- Atualizando planilha de robôs no drive')
            print(f'- Acessando planilha de status (Aba: "{aba_nome}")...')
            planilha = self.cliente_sheets.open_by_key(planilha_id)
            aba = planilha.worksheet(aba_nome)

            # Captura a hora final, já convertida para o fuso de São Paulo.
            horario_fim_obj = datetime.now(ZoneInfo('UTC')).astimezone(ZoneInfo('America/Sao_Paulo'))
            horario_inicio_obj = self.horario_inicio_execucao
            
            # Calcula a duração total da execução.
            duracao = horario_fim_obj - horario_inicio_obj
            total_segundos = int(duracao.total_seconds())
            horas, minutos, segundos = total_segundos // 3600, (total_segundos % 3600) // 60, total_segundos % 60
            duracao_formatada = f"{horas:02}:{minutos:02}:{segundos:02}"
            
            # Atualiza as células específicas na planilha (A2, B2, C2).
            aba.update_cell(2, 1, horario_fim_obj.strftime('%d/%m/%Y %H:%M:%S'))
            aba.update_cell(2, 2, horario_inicio_obj.strftime('%d/%m/%Y %H:%M:%S'))
            aba.update_cell(2, 3, duracao_formatada)
            print('- Planilha de status atualizada com sucesso!')   
        except Exception as e:
            print(f'# Erro ao atualizar e registrar status na planilha: {e}\n')

    def pegar_celula_gsheets(self, celula):
        """
        Lê o valor de uma célula específica da planilha principal de logins.
        Assume que a aba de logins sempre se chamará 'access'.
        
        Parâmetro:
            celula (str): A célula a ser lida (ex: 'B4').
        """
        time.sleep(1)
        try:
            aba_planilha_GSheet = self.planilhaGSheet.worksheet('access')
            return aba_planilha_GSheet.acell(celula).value
        except Exception as e:
            print(f"# Erro ao ler a célula {celula} da aba 'access': {e}")
            return None

            ##TESTE AQUI

    def download_do_drive(self, nome_arquivo, id_pasta_drive, caminho_destino):
        """
        Busca um arquivo no Drive pelo nome dentro de uma pasta e o baixa localmente.
        
        Parâmetros:
            nome_arquivo (str): O nome exato do arquivo no Drive.
            id_pasta_drive (str): O ID da pasta onde o arquivo está localizado.
            caminho_destino (str): O caminho local completo onde o arquivo será salvo.
        """
        if not self.servico_drive:
            print('# Conexão com Drive não disponível. Download cancelado.')
            return False

        try:
            # 1. Procura pelo arquivo na pasta especificada
            query = f"name='{nome_arquivo}' and '{id_pasta_drive}' in parents and trashed=false"
            response = self.servico_drive.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            files = response.get('files', [])
            
            if not files:
                print(f"# Aviso: Arquivo '{nome_arquivo}' não encontrado na pasta do Drive ({id_pasta_drive}).")
                return False
            
            file_id = files[0].get('id')
            print(f"- Iniciando download do arquivo '{nome_arquivo}' (ID: {file_id})...")

            # 2. Executa o download por chunks para maior segurança com arquivos grandes
            request = self.servico_drive.files().get_media(fileId=file_id)
            with io.FileIO(caminho_destino, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    # print(f"Download {int(status.progress() * 100)}%.")

            print(f"✅ Download do arquivo '{nome_arquivo}' realizado com sucesso em: {caminho_destino}")
            return True

        except Exception as e:
            print(f'# Erro durante o download do Drive: {e}')
            # traceback.print_exc()
            return False