from datetime import datetime, timedelta
import os
import time
import zipfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from time import sleep
from get_date_run import getInitialDate
import shutil
from auxiliar import *

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # TensorFlow logs: erros apenas

class Chrome:
    def __init__(self):
        """Construtor que configura todas as opções do Chrome."""
        self.options = webdriver.ChromeOptions()

        if 'GITHUB_ACTIONS' in os.environ:
            self.options.add_argument('--headless=new')
            self.options.add_argument('--lang=pt-BR')
        
        # User-Agent Spoofing: Simula um navegador Windows real para evitar bloqueios de robô
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.options.add_argument(f"user-agent={user_agent}")
        
        # self.options.add_argument('--headless') # janela oculta
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--force-device-scale-factor=0.67') # Zoom
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-features=InsecureDownloadWarnings")
        
        # Define as preferências do Chrome
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "download.default_directory": os.path.abspath(path_downloads),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "intl.accept_languages": "pt-BR,pt"
        }
        self.options.add_experimental_option('prefs', prefs)
        
        # Oculta logs desnecessários e remove flags de automação
        self.options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)

        self.navegador = None
        self.janela_web_atual = None

    def _navegar(self, destino):      
        if not self.navegador:
            self.navegador = webdriver.Chrome(options=self.options)
            
            # Remove flag de automação via JS
            self.navegador.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            if 'GITHUB_ACTIONS' in os.environ:
                self.navegador.execute_cdp_cmd("Page.setDownloadBehavior", {
                    "behavior": "allow",
                    "downloadPath": os.path.abspath(path_downloads)
                })
            
            self.janela_web_atual = self.navegador.current_window_handle
            
        print(f"- Acessando página web: {destino}")
        self.navegador.get(destino)  

    def _fechar_chrome(self):
        if self.navegador:
            self.navegador.quit()
            self.navegador = None

    def _send_Keys(self, X_PATH, key):
        # Espera o campo estar visível e pronto para receber texto
        elemento = WebDriverWait(self.navegador, 360).until(EC.visibility_of_element_located((By.XPATH, X_PATH)))
        elemento.clear() # LIMPA O CAMPO ANTES DE DIGITAR
        elemento.send_keys(key)
        sleep(0.3)

    def _click(self, X_PATH):
        # Espera o botão estar clicável e rola a tela se necessário
        button = WebDriverWait(self.navegador, 360).until(EC.element_to_be_clickable((By.XPATH, X_PATH)))
        self.navegador.execute_script("arguments[0].scrollIntoView(true);", button)
        sleep(0.5)
        button.click() 

    def _logar_gpm(self, login, senha):
        '''Faz o login no GPM usando os localizadores específicos.'''
        try:
            # 1. Preenche o campo de login por ID
            WebDriverWait(self.navegador, 60).until(EC.visibility_of_element_located((By.ID, "idLogin")))
            self.navegador.find_element(by=By.ID, value="idLogin").send_keys(login)
            sleep(0.3)

            # 2. Preenche o campo de senha por ID
            WebDriverWait(self.navegador, 60).until(EC.visibility_of_element_located((By.ID, "idSenha")))
            self.navegador.find_element(by=By.ID, value="idSenha").send_keys(senha)
            sleep(0.3)

            # 3. Clica no botão de entrar por XPATH
            xpath_entrar = '//input[contains(@value, "ntrar")]'
            WebDriverWait(self.navegador, 60).until(EC.element_to_be_clickable((By.XPATH, xpath_entrar)))
            self.navegador.find_element(by=By.XPATH, value=xpath_entrar).click()
            
            print('- GPM logado com sucesso')
            sleep(5)
            
        except Exception as e:
            print(f'# Erro ao fazer login no GPM: {e}')
            
    def descompactar_e_renomear(self, path_downloads, operacao, tipo_relatorio): #######
        if not os.path.exists(path_temp):
            os.makedirs(path_temp)
        
        files = os.listdir(path_downloads)
        for file in files:
            if file.endswith(".zip") and "consulta" in file.lower():  # evita zip genéricos como o RevoUninstaller
                zip_path = os.path.join(path_downloads, file)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(path_downloads)
                    extracted_files = zip_ref.namelist()
                    print(f"- Arquivo {zip_path} descompactado")

                    for extracted_file in extracted_files:
                        if not extracted_file.endswith(".csv"):
                            continue  # ignora arquivos que não são CSV

                        original_file_path = os.path.join(path_downloads, extracted_file)
                        new_file_name = f"{tipo_relatorio} {operacao}.csv"
                        new_file_path = os.path.join(path_temp, new_file_name)

                        # Se já existir o destino, remove
                        if os.path.exists(new_file_path):
                            os.remove(new_file_path)

                        shutil.move(original_file_path, new_file_path)
                        print(f"- Arquivo renomeado e movido para {new_file_path}")

    def limpar_arquivos_zip(self, diretorio):
        arquivos = os.listdir(diretorio)
        for arquivo in arquivos:
            if arquivo.endswith(".zip"):
                caminho_arquivo = os.path.join(diretorio, arquivo)
                os.remove(caminho_arquivo)
                print(f"- Arquivo {arquivo} removido com sucesso!")

    def getDate(self):
        data_objeto = datetime.strptime(getInitialDate(), "%Y-%m-%dT%H:%M:%S")
        return data_objeto.strftime("%d/%m/%Y")

    def _processar_download(self, consulta_url, login_gpm, senha_gpm, operacao):

        login_url = f'https://sirtec{operacao.lower()}.gpm.srv.br/index.php'

        self._navegar(login_url)
        self._logar_gpm(login_gpm, senha_gpm)
        self._navegar(consulta_url)
        
        # DIGITAÇÃO HUMANA: Evita bloqueios de locale e aciona gatilhos do GPM
        data_str = self.getDate()
        print(f"- Simulando digitação humana das datas: {data_str}")
        
        def digitar_humanizado(element_id, texto):
            el = self.navegador.find_element(By.ID, element_id)
            el.click()
            el.clear()
            sleep(0.5)
            for char in texto:
                el.send_keys(char)
                sleep(0.1) # Delay entre caracteres
            sleep(0.5)
            el.send_keys(Keys.TAB) # Sai do campo para acionar eventos

        try:
            from selenium.webdriver.common.keys import Keys
            digitar_humanizado("data_inicial", data_str)
            digitar_humanizado("data_final", data_str)
        except Exception as e:
            print(f"# Erro na digitação humana, tentando fallback JS: {e}")
            self.navegador.execute_script(f"document.getElementById('data_inicial').value = '{data_str}';")
            self.navegador.execute_script(f"document.getElementById('data_final').value = '{data_str}';")

        self._click('/html/body/form[5]/div/input')
        
        print("- Aguardando processamento do GPM (vão de loading)...")
        # Aguarda o overlay de "Processing..." sumir
        try:
            WebDriverWait(self.navegador, 20).until(
                EC.invisibility_of_element_located((By.ID, "tab_resultados_processing"))
            )
            print("- Processamento concluído!")
        except:
            print("- Timeout aguardando overlay de processamento.")

        # Tenta selecionar "Ver Todos" no Datatables para garantir que todos os dados estejam no DOM
        print("- Tentando expandir visualização para 'Todos' os registros...")
        try:
            self.navegador.execute_script("if($.fn.DataTable.isDataTable('#tab_resultados')) { $('#tab_resultados').DataTable().page.len(-1).draw(); }")
            sleep(5)
        except:
            pass

        # INSPEÇÃO VISUAL DA TABELA (DIAGNÓSTICO): Verifica se os dados existem na tela
        print("- [DIAGNÓSTICO] Inspecionando dados na tabela visível do navegador...")
        tabela_com_dados = False
        try:
            linha_dados = self.navegador.find_element(By.XPATH, '//*[@id="tab_resultados"]/tbody/tr[1]')
            texto_linha = linha_dados.text.strip()
            if texto_linha and len(texto_linha) > 10:
                print(f"- [DEBUG VISUAL] Dados encontrados na 1ª linha da tela: {texto_linha[:150]}...")
                tabela_com_dados = True
            else:
                print("- [DEBUG VISUAL] Alerta: Tabela visível parece vazia.")
        except Exception as e:
            print(f"- [DEBUG VISUAL] Erro ao ler tabela: {e}")

        # TENTATIVA DE EXPORTAÇÃO DINÂMICA
        print("- Localizando botão de exportação CSV via classe...")
        exportou_sucesso = False
        try:
            btn_csv = self.navegador.find_element(By.CLASS_NAME, "buttons-csv")
            btn_csv.click()
            print("- Clique no botão .buttons-csv realizado.")
            exportou_sucesso = True
            sleep(15)
        except:
            print("- Botão .buttons-csv não encontrado. Tentando clique por índice antigo...")
            try:
                self._click('//*[@id="tab_resultados_wrapper"]/div[1]/button[4]')
                exportou_sucesso = True
                sleep(15)
            except:
                print("- Falha em todos os métodos de clique de exportação.")

        # PLANO DE CONTINGÊNCIA: SCRAPING DIRETO DA TELA (Caso o export do site falhe no GitHub)
        if tabela_com_dados:
            print("- [BACKUP] Iniciando scraping direto da tela via JS para garantir dados...")
            try:
                # Script JS para extrair os dados da tabela em formato CSV
                script_scraper = """
                var csv = [];
                var rows = document.querySelectorAll("#tab_resultados tr");
                for (var i = 0; i < rows.length; i++) {
                    var row = [], cols = rows[i].querySelectorAll("td, th");
                    for (var j = 0; j < cols.length; j++) 
                        row.push(cols[j].innerText.replace(/;/g, ",")); // Troca ; por , interno
                    csv.push(row.join(";"));
                }
                return csv.join("\\n");
                """
                csv_data = self.navegador.execute_script(script_scraper)
                
                # Salva o resultado do scraping como um arquivo CSV de backup
                backup_filename = f"SCRAPED_BACKUP_{operacao}.csv"
                backup_path = os.path.join(path_downloads, backup_filename)
                with open(backup_path, "w", encoding="utf-8-sig") as f:
                    f.write(csv_data)
                print(f"- [BACKUP] Scraping concluído e salvo em: {backup_filename}")
            except Exception as e:
                print(f"- [BACKUP] Falha no scraping manual: {e}")

        self._fechar_chrome()
        
        # ORGANIZAÇÃO DE ARQUIVOS
        self._organizar_arquivos_v5(operacao)
        print(f'- Processo de download do consulta turno finalizado para operação {operacao}')

    def _organizar_arquivos_v5(self, operacao):
        # código de descompactação e renomeação
        files = os.listdir(path_downloads)
        zip_files = [f for f in files if f.endswith('.zip')]
        
        if zip_files:
            for zip_name in zip_files:
                zip_path = os.path.join(path_downloads, zip_name)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(path_downloads)
                
                print(f"- Arquivo {zip_path} descompactado")
                
                extracted_files = [f for f in os.listdir(path_downloads) if f.endswith('.csv') and 'SCRAPED' not in f]
                for ext_file in extracted_files:
                    old_path = os.path.join(path_downloads, ext_file)
                    new_filename = f"consulta turno {operacao}.csv"
                    new_path = os.path.join(path_temp, new_filename)
                    shutil.move(old_path, new_path)
                    print(f"- Arquivo renomeado e movido para {new_path}")
                
                os.remove(zip_path)
                print(f"- Arquivo {zip_name} removido com sucesso!")
        
        # Caso especial: Se não veio ZIP ou se o CSV veio vazio, usamos o BACKUP de scraping
        backup_file = f"SCRAPED_BACKUP_{operacao}.csv"
        backup_path = os.path.join(path_downloads, backup_file)
        if os.path.exists(backup_path):
            new_path = os.path.join(path_temp, f"consulta turno {operacao}.csv")
            # Só usa o scraping se o original não existir ou estiver quase vazio
            if not os.path.exists(new_path) or os.path.getsize(new_path) < 500:
                shutil.move(backup_path, new_path)
                print(f"- [ROBUSTEZ] Usando dados capturados via SCRAPING direto da tela para '{operacao}'.")
            else:
                if os.path.exists(backup_path): os.remove(backup_path)


##### outros ###             
    def limpar_pasta_temp(self):
        if os.path.exists(path_temp):
            for temp_file in os.listdir(path_temp):
                temp_file_path = os.path.join(path_temp, temp_file)
                try:
                    if os.path.isfile(temp_file_path) or os.path.islink(temp_file_path):
                        os.unlink(temp_file_path)
                    elif os.path.isdir(temp_file_path):
                        shutil.rmtree(temp_file_path)
                except Exception as e:
                    print(f"# Falha ao deletar {temp_file_path}. Razão: {e}\n")
