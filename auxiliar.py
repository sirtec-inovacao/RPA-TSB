import os

# --- 1. CONFIGURAÇÃO DE AMBIENTE ---
def _setup_environment():
    """Carrega variáveis de ambiente dependendo de onde o código está rodando."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("- Rodando em modo GitHub Actions. Usando variáveis de ambiente.")
    else:
        # print("- Rodando em modo Local. Carregando variáveis do arquivo .env.")
        try:
            from dotenv import load_dotenv
            if not load_dotenv():
                print("# ALERTA: Arquivo .env não encontrado. Vezrifique as configurações.")
        except ImportError:
            print("# ATENÇÃO: 'python-dotenv' não instalado (Execute 'pip install python-dotenv').")

_setup_environment()

# --- 2. URLs DE SISTEMAS ---
web_pontomais = "https://app2.pontomais.com.br/login"
web_pontomais_relatorios = "https://app2.pontomais.com.br/relatorios"

# --- 3. CAMINHOS E DIRETÓRIOS ---
# Pastas Base
path_script = os.path.dirname(os.path.abspath(__file__))
path_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
path_temp = os.path.join(path_script, "temp")
path_final = os.path.join(path_script, "final")

# Arquivos de Configuração
chave_json = os.path.join(path_script, "chaveGoogle.json")
config_json = os.path.join(path_script, "config.json")

# Arquivos Temporários / Processamento
records_file = os.path.join(path_temp, "records.json")
pontomais_df = os.path.join(path_temp, "Pontomais_final.xlsx")
notifications_file = os.path.join(path_temp, "notifications_report.json")

# --- 4. CREDENCIAIS E IDs (.ENV) ---
# Google Sheets
aba_att_gsheet = "Att_TSB" 
id_planilha_gsheet = os.environ.get("ID_PLANILHA_GSHEET")
id_planilha_att_gsheet = os.environ.get("ID_PLANILHA_ATT_GSHEET")
id_pasta_drive_final = os.environ.get("ID_PASTA_DRIVE_FINAL")

# Planilha de Controle de Data (Se vier vazio da Action, usa o hardcoded como fallback)
id_planilha_controle = os.environ.get("ID_PLANILHA_CONTROLE") 
if not id_planilha_controle: id_planilha_controle = "1lM8Q3NIUrDsdR8OD_6RG0wAddXvq1PpWczuOUeOyivE"

nome_aba_controle = os.environ.get("NOME_ABA_CONTROLE") or "CONTROLE_GERAL_ROBOS"
celula_data_controle = os.environ.get("CELULA_DATA_CONTROLE") or "F16"

# Sistemas Terceiros
token_zuq = os.environ.get("TOKEN_ZUQ")
login_gpm = os.environ.get("LOGIN_GPM")
senha_gpm = os.environ.get("SENHA_GPM")

l = '\n----------------------------------------------------------------------\n'
t = '\n=============================================================================================================\n'