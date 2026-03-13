from get_date_run import getInitialDate
from gsheets import Gsheets
from auxiliar import *

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime, timedelta
from time import sleep
import shutil
import os

# --- INICIALIZAÇÃO E DEFINIÇÃO DE DATAS ---
gsheets = Gsheets()

# --- DADOS DE LOGIN ---
operacao_login = {
    'BAR':      gsheets.pegar_celula_gsheets('B21'),
    'BJL':      gsheets.pegar_celula_gsheets('B22'),
    'FRS':      gsheets.pegar_celula_gsheets('B24'), 
    'PEL':      gsheets.pegar_celula_gsheets('B25'),  
    'POA':      gsheets.pegar_celula_gsheets('B26'),
    'RS':       gsheets.pegar_celula_gsheets('B27'),            
    # 'SP':       gsheets.pegar_celula_gsheets('B28'),
    # 'VTC':      gsheets.pegar_celula_gsheets('B29'),                                
}

operacao_senha = { 
    'BAR':      gsheets.pegar_celula_gsheets('C21'), 
    'BJL':      gsheets.pegar_celula_gsheets('C22'),            
    'FRS':      gsheets.pegar_celula_gsheets('C24'), 
    'PEL':      gsheets.pegar_celula_gsheets('C25'),
    'POA':      gsheets.pegar_celula_gsheets('C26'),            
    'RS':       gsheets.pegar_celula_gsheets('C27'),  
    'SP':       gsheets.pegar_celula_gsheets('C28'), 
    'VTC':      gsheets.pegar_celula_gsheets('C29'),      
}


# def pontomais():
  
#     data_in = getDate()
#     data_fi = getDate()

#     # --- BAIXAR RELATÓRIOS PONTOMAIS  ---
#     for operacao, login in operacao_login.items():
#         senha = operacao_senha[operacao]
        
#         print(f'{l}- Iniciando download no pontomais de {operacao}')
#         print(f'- Periodo: {data_in} - {data_fi}')

#         # Parametros do Selenium
#         options = Options()
#         options.add_experimental_option("excludeSwitches",["enable-automation"])
#         options.add_experimental_option('detach', True)
#         options.add_argument('--start-maximized')
#         options.add_argument('--force-device-scale-factor=0.67')
#         options.add_argument("--log-level=3")
#         options.add_experimental_option("excludeSwitches", ["enable-logging"]) # Silencia o "DevTools listening"        
#         options.add_argument("--disable-gpu")  # Evitar erros em alguns ambientes
#         options.add_argument("--window-size=1920,1080")  # Define resolução padrão
        
#         # MODO HEADLESS SE ESTIVER NO GITHUB
#         if os.environ.get("GITHUB_ACTIONS") == "true":
#             options.add_argument("--headless=new")
            
#         driver = webdriver.Chrome(options=options)

#         driver.get(web_pontomais)

#         while True:
#             try:
#                 print('- Realizando login')
#                 # Login
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "//*[@id='container-login']/div[1]/div/div[4]/div[1]/login-form/pm-form/form/div/div/div[1]/pm-input/div/div/pm-text/div/input"
#                 ))).send_keys(login)
#                 # Senha
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH,
#                     "//*[@id='container-login']/div[1]/div/div[4]/div[1]/login-form/pm-form/form/div/div/div[2]/pm-input/div/div/pm-password/div/input"
#                 ))).send_keys(senha)
#                 # Clicar no entrar
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "//*[contains(text(), 'Entrar')]"))).click()
#                 # Aguarda carregar
#                 WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.XPATH, 
#                     "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/app-header/header/dx-toolbar/div/div[1]/div/dxi-item/a/img[2]")))
#                 break
#             except Exception as e:
#                 print(f"# Erro ao fazer login no Pontomais: {e}")

#         # Carrega a pág de relatórios
#         driver.get(web_pontomais_relatorios)
#         driver.delete_all_cookies()
#         driver.add_cookie({'name': 'NPS_3b815910_last_seen', 'value': 'true'})
#         driver.add_cookie({'name': 'NPS_1ded1401_surveyed', 'value': 'true'})
#         driver.refresh()
        
#         print('- Baixando arquivo de ponto')
#         while True:
#             try: 
#                 print(1)
#                 # Adiciona data do filtro
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/dx-drawer/div/div[2]/dx-scroll-view/div[1]/div/div[1]/div[2]/div[1]/app-container/reports/div/div[1]/div/pm-card/div/div[2]/pm-form/form/div[2]/div/div[3]/pm-input/div/div/pm-date-range/div/input"))).clear()
                
#                 print(2)
#                 pyperclip.copy(f'{data_in}-{data_fi}')
                
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/dx-drawer/div/div[2]/dx-scroll-view/div[1]/div/div[1]/div[2]/div[1]/app-container/reports/div/div[1]/div/pm-card/div/div[2]/pm-form/form/div[2]/div/div[3]/pm-input/div/div/pm-date-range/div/input"
#                 ))).send_keys(Keys.CONTROL, 'v')

#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/dx-drawer/div/div[2]/dx-scroll-view/div[1]/div/div[1]/div[2]/div[1]/app-container/reports/div/div[1]/div/pm-card/div/div[2]/pm-form/form/div[2]/div/div[3]/pm-input/div/div/pm-date-range/div/input"
#                 ))).send_keys(Keys.CONTROL, 'a')

#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/dx-drawer/div/div[2]/dx-scroll-view/div[1]/div/div[1]/div[2]/div[1]/app-container/reports/div/div[1]/div/pm-card/div/div[2]/pm-form/form/div[2]/div/div[3]/pm-input/div/div/pm-date-range/div/input"
#                 ))).send_keys(Keys.CONTROL, 'v')

#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/dx-drawer/div/div[2]/dx-scroll-view/div[1]/div/div[1]/div[2]/div[1]/app-container/reports/div/div[1]/div/pm-card/div/div[2]/pm-form/form/div[2]/div/div[3]/pm-input/div/div/pm-date-range/div/input"
#                 ))).send_keys(Keys.ENTER)
                
#                 print(4)
#                 # Seleciona o tipo de relatório
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "//*[@id='undefined']/div/div/div[2]"))).click()
#                 # Seleciona o relatorio jornada espelho ponto
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "//*[contains(text(), 'Jornada')]"))).click()
#                 print(5)
#                 try: 
#                     # fechar popup de pesquisa de satisfação
#                     WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, 
#                         "//*[@id='wootric-close']"))).click()
#                 except:
#                     pass

#                 # Seleciona o layout do relatorio
#                 print(6)
#                 #if operacao:
#                 # Novo método criando o layout através das colunas (sem modelo de relatório)
#                 WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.XPATH,
#                     "//span[contains(.,' Colunas ')]"))).click()

#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "//span[contains(.,'Adicional noturno')]"))).click()

#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "//span[contains(.,' Nome ')]"))).click()
                    
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "//span[contains(.,' Motivo/Observação ')]"))).click()
                    
#                 # WebDriverWait(driver, 20).until(EC.presence_of_element_located(
#                 #     (By.XPATH, "//span[contains(.,' Totais da jornada ')]"))).click()
#                 # WebDriverWait(driver, 20).until(EC.presence_of_element_located(
#                 #     (By.XPATH, "//span[contains(.,' Total de H. extras ')]"))).click()
#                 sleep(3)
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, 
#                     "/html/body/ngb-modal-window/div/div/pm-modal-multi-select-modal/div[2]/div/div/div[2]/pm-button/button"
#                 ))).click()
#                 print(7)
#                 # Baixa o relatório em xls
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located(
#                     (By.XPATH, "//*[@id='relatorios-baixar']/pm-drop-down/a/div/pm-button/button"))).click()
#                 button = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
#                     (By.XPATH, "//*[contains(text(), 'XLS')]")))
#                 # Da Scroll até a posicao do botao
#                 button.location_once_scrolled_into_view
                
#                 button2 = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
#                     (By.XPATH, "//*[contains(text(), 'XLS')]")))
#                 # Da Scroll até a posicao do botao
#                 button2.location_once_scrolled_into_view
#                 # Clica no botão
#                 WebDriverWait(driver, 20).until(EC.presence_of_element_located(
#                     (By.XPATH, "//*[contains(text(), 'XLS')]"))).click()
#                 break
#             except:
#                 try:
#                     # fechar popup de pesquisa de satisfação
#                     WebDriverWait(driver, 5).until(EC.presence_of_element_located(
#                         (By.XPATH, "//*[@id='wootric-close']"))).click()
#                     driver.refresh()
#                     driver.get(web_pontomais_relatorios)
#                     sleep(1.5)
#                 except:
#                     print('# Erro ao baixar arquivo de pontos de ' + operacao)
#                     print('# Tentando novamente')
                    
            
#         # Aguarda realizar download
#         while True:
#             try:# Renomear e mover o arquivo baixado                
#                 download_path = os.path.expanduser("~/Downloads")
#                 files = os.listdir(download_path)

#                 latest_file = None
#                 latest_time = 0
#                 for file in files:
#                     if file.startswith("Pontomais_-_Jornada_") and file.endswith(".xlsx"):
#                         file_path = os.path.join(download_path, file)
#                         file_time = os.path.getctime(file_path)
#                         if file_time > latest_time:
#                             latest_time = file_time
#                             latest_file = file_path

#                 if latest_file:
#                     new_filename = (operacao + "_Pontomais_-_Jornada_.xlsx")
#                     new_filepath = os.path.join(download_path, new_filename)
#                     os.rename(latest_file, new_filepath)
#                     destination_path = os.path.join(path_temp, new_filename)
#                     shutil.move(new_filepath, destination_path)
#                     print('Arquivo ' + new_filename + ' movido para o Google Drive.')
#                     break
#             except:
#                 sleep(5)
#         sleep(5)
#         driver.quit()
    
        
# Chamando a função principal para iniciar o processo para ambas as operações
        
def getDate():
    data_objeto = datetime.strptime(getInitialDate(), "%Y-%m-%dT%H:%M:%S")
    return data_objeto.strftime("%d/%m/%Y")

class Pontomais:
    def __init__(self):
        """Construtor que configura todas as opções do Chrome."""
        self.options = webdriver.ChromeOptions()

        if os.environ.get("GITHUB_ACTIONS") == "true":
            self.options.add_argument("--headless=new")
            
        self.options.add_argument('--start-maximized')
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument('--force-device-scale-factor=0.67')
        self.options.add_argument("--log-level=3")
        
        # --- BLOCO DE TESTE: DESCOMENTAR SE O CHROME BLOQUEAR O DOWNLOAD LOCALMENTE ---
        #self.options.add_argument("--safebrowsing-disable-download-protection")
        #self.options.add_argument("--safebrowsing-disable-extension-blacklist")
        #self.options.add_argument("--disable-features=InsecureDownloadWarnings")
        #self.options.add_argument("--allow-insecure-localhost")
        #self.options.add_argument("--ignore-certificate-errors")
        #self.options.add_argument("--allow-running-insecure-content")
        #self.options.add_argument("--unsafely-treat-insecure-origin-as-secure=https://app2.pontomais.com.br")
        # ---------------------------------------------------------------------------

        # Agrupando os excludeSwitches
        self.options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        self.options.add_experimental_option('detach', True)

        self.download_dir = os.path.join(os.getcwd(), "temp_downloads")
        os.makedirs(self.download_dir, exist_ok=True)
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True, #True para produção
            #"safebrowsing.disable_download_protection": True,
            #"profile.default_content_setting_values.automatic_downloads": 1,
            #"profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
            #"download.extensions_to_open": "xlsx",
            "profile.default_content_settings.popups": 0
        }
        self.options.add_experimental_option("prefs", prefs)

        self.navegador = None
        self.janela_web_atual = None

    def _navegar(self, destino):      
        if not self.navegador:
            self.navegador = webdriver.Chrome(options=self.options)
            
            # Habilita download em modo headless (GitHub Actions)
            if os.environ.get("GITHUB_ACTIONS") == "true":
                self.navegador.execute_cdp_cmd("Page.setDownloadBehavior", {
                    "behavior": "allow",
                    "downloadPath": self.download_dir
                })
                
            self.janela_web_atual = self.navegador.current_window_handle
            
        print(f"- Acessando página web: {destino}")
        self.navegador.get(destino)  

    def _fechar_chrome(self):
        if self.navegador:
            self.navegador.quit()
            self.navegador = None

    def baixar_relatorios(self):
        data_in = getDate()
        data_fi = getDate()

        # --- BAIXAR RELATÓRIOS PONTOMAIS  ---
        for operacao, login in operacao_login.items():
            senha = operacao_senha[operacao]
            
            print(f'{l}- Iniciando download no pontomais de {operacao}')
            print(f'- Periodo: {data_in} - {data_fi}')

            self._navegar(web_pontomais)
            
            # ATENÇÃO: A partir daqui no seu código, você deve substituir 'driver' por 'self.navegador'
            while True:
                try:
                    print('- Realizando login')
                    # Login
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "//*[@id='container-login']/div[1]/div/div[4]/div[1]/login-form/pm-form/form/div/div/div[1]/pm-input/div/div/pm-text/div/input"
                    ))).send_keys(login)
                    # Senha
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH,
                        "//*[@id='container-login']/div[1]/div/div[4]/div[1]/login-form/pm-form/form/div/div/div[2]/pm-input/div/div/pm-password/div/input"
                    ))).send_keys(senha)
                    # Clicar no entrar
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "//*[contains(text(), 'Entrar')]"))).click()
                    # Aguarda carregar
                    WebDriverWait(self.navegador, 50).until(EC.presence_of_element_located((By.XPATH, 
                        "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/app-header/header/dx-toolbar/div/div[1]/div/dxi-item/a/img[2]")))
                    break
                except Exception as e:
                    print(f"# Erro ao fazer login no Pontomais: {e}")

            # Carrega a pág de relatórios
            self.navegador.get(web_pontomais_relatorios)
            # REMOVIDO: self.navegador.delete_all_cookies() - Isso causava erro de sessão no download
            self.navegador.add_cookie({'name': 'NPS_3b815910_last_seen', 'value': 'true'})
            self.navegador.add_cookie({'name': 'NPS_1ded1401_surveyed', 'value': 'true'})
            self.navegador.refresh()
            
            print('- Baixando arquivo de ponto')
            while True:
                try: 
                    # Adiciona data do filtro
                    campo_data = WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "/html/body/app-mfe-remote/app-side-nav-outer-toolbar/dx-drawer/div/div[2]/dx-scroll-view/div[1]/div/div[1]/div[2]/div[1]/app-container/reports/div/div[1]/div/pm-card/div/div[2]/pm-form/form/div[2]/div/div[3]/pm-input/div/div/pm-date-range/div/input")))
                    
                    campo_data.clear()
                    # Envia a data diretamente (sem pyperclip que não funciona em headless)
                    campo_data.send_keys(f'{data_in}-{data_fi}')
                    campo_data.send_keys(Keys.ENTER)
                    
                    # Seleciona o tipo de relatório
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "//*[@id='undefined']/div/div/div[2]"))).click()
                    # Seleciona o relatorio jornada espelho ponto
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "//*[contains(text(), 'Jornada')]"))).click()
                    try: 
                        # fechar popup de pesquisa de satisfação
                        WebDriverWait(self.navegador, 5).until(EC.presence_of_element_located((By.XPATH, 
                            "//*[@id='wootric-close']"))).click()
                    except:
                        pass

                    # Seleciona o layout do relatorio
                    #if operacao:
                    # Novo método criando o layout através das colunas (sem modelo de relatório)
                    WebDriverWait(self.navegador, 50).until(EC.presence_of_element_located((By.XPATH,
                        "//span[contains(.,' Colunas ')]"))).click()

                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "//span[contains(.,'Adicional noturno')]"))).click()

                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "//span[contains(.,' Nome ')]"))).click()
                        
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "//span[contains(.,' Motivo/Observação ')]"))).click()
                        
                    # WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located(
                    #     (By.XPATH, "//span[contains(.,' Totais da jornada ')]"))).click()
                    # WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located(
                    #     (By.XPATH, "//span[contains(.,' Total de H. extras ')]"))).click()
                    sleep(3)
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located((By.XPATH, 
                        "/html/body/ngb-modal-window/div/div/pm-modal-multi-select-modal/div[2]/div/div/div[2]/pm-button/button"
                    ))).click()
                    # Baixa o relatório em xls
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located(
                        (By.XPATH, "//*[@id='relatorios-baixar']/pm-drop-down/a/div/pm-button/button"))).click()
                    button = WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'XLS')]")))
                    # Da Scroll até a posicao do botao
                    button.location_once_scrolled_into_view
                    
                    button2 = WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'XLS')]")))
                    # Da Scroll até a posicao do botao
                    button2.location_once_scrolled_into_view
                    # Clica no botão
                    WebDriverWait(self.navegador, 20).until(EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'XLS')]"))).click()
                    break
                except:
                    try:
                        # fechar popup de pesquisa de satisfação
                        WebDriverWait(self.navegador, 5).until(EC.presence_of_element_located(
                            (By.XPATH, "//*[@id='wootric-close']"))).click()
                        self.navegador.refresh()
                        self.navegador.get(web_pontomais_relatorios)
                        sleep(1.5)
                    except:
                        print('# Erro ao baixar arquivo de pontos de ' + operacao)
                        print('# Tentando novamente')
                        
                
            # Aguarda realizar download
            timeout_counter = 0
            downloaded = False
            while timeout_counter < 60:
                try:
                    # Renomear e mover o arquivo baixado                
                    download_path = self.download_dir
                    files = os.listdir(download_path)
 
                    latest_file = None
                    latest_time = 0
                    for file in files:
                        if file.startswith("Pontomais_-_Jornada_") and file.endswith(".xlsx"):
                            file_path = os.path.join(download_path, file)
                            file_time = os.path.getctime(file_path)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = file_path
 
                    if latest_file:
                        new_filename = (operacao + "_Pontomais_-_Jornada_.xlsx")
                        new_filepath = os.path.join(download_path, new_filename)
                        os.rename(latest_file, new_filepath)
                        os.makedirs(path_temp, exist_ok=True)
                        destination_path = os.path.join(path_temp, new_filename)
                        shutil.move(new_filepath, destination_path)
                        print('Arquivo ' + new_filename + ' movido para a pasta temp.')
                        downloaded = True
                        break
                    
                    sleep(1)
                    timeout_counter += 1
                except Exception as e:
                    sleep(2)
                    timeout_counter += 2
                    
            if not downloaded:
                print(f"Timeout: o arquivo de {operacao} não foi encontrado após o download.")
            sleep(5)
            self._fechar_chrome()
