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

class BrowserGPM:
    def __init__(self, headless=None):
        """
        Construtor que configura todas as opções do Firefox.
        :param headless: Se True, roda sem janela. Se None, decide com base no ambiente.
        """
        if headless is None:
            headless = 'GITHUB_ACTIONS' in os.environ

        self.options = webdriver.FirefoxOptions()

        if headless:
            self.options.add_argument('--headless')
        else:
            print("- [MODO VISÍVEL] Abrindo navegador com interface...")
        
        # User-Agent Spoofing: Simula um navegador Windows real
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        self.options.set_preference("general.useragent.override", user_agent)
        
        # Regionalização e Idioma
        self.options.set_preference("intl.accept_languages", "pt-BR, pt")
        self.options.set_preference("javascript.enabled", True)

        # Configurações de Download (Firefox é diferente do Chrome)
        self.options.set_preference("browser.download.folderList", 2) # 2 = pasta customizada
        self.options.set_preference("browser.download.dir", os.path.abspath(path_downloads))
        self.options.set_preference("browser.download.useDownloadDir", True)
        self.options.set_preference("browser.download.viewableInternally.enabledTypes", "")
        self.options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip,application/octet-stream,application/csv,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.options.set_preference("pdfjs.disabled", True) # Evita abrir PDF no navegador

        self.navegador = None
        self.janela_web_atual = None

    def _navegar(self, destino):
        if not self.navegador:
            self.navegador = webdriver.Firefox(options=self.options)
            self.navegador.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.janela_web_atual = self.navegador.current_window_handle
            
        print(f"- Acessando página web: {destino}")
        self.navegador.get(destino)
        sleep(2)

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

    def baixar_consulta_turno(self, operacao):
        """Método chamado pelo main.py para iniciar o processo por operação."""
        print(f"----------------------------------------------------------------------")
        print(f"- Iniciando download do consulta turno para operação {operacao}")
        
        if operacao == 'BA':
            consulta_url = 'https://sirtecba.gpm.srv.br/#GR412'
            login_gpm = os.getenv('LOGIN_GPM_BA') or os.getenv('LOGIN_GPM')
            senha_gpm = os.getenv('PASSWORD_GPM_BA') or os.getenv('SENHA_GPM_BA') or os.getenv('SENHA_GPM')
        elif operacao == 'CE':
            consulta_url = 'https://sirtecce.gpm.srv.br/#GR412'
            login_gpm = os.getenv('LOGIN_GPM_CE') or os.getenv('LOGIN_GPM')
            senha_gpm = os.getenv('PASSWORD_GPM_CE') or os.getenv('SENHA_GPM_CE') or os.getenv('SENHA_GPM')
        else:
            print(f"# Operação {operacao} não reconhecida.")
            return

        if not login_gpm or not senha_gpm:
            print(f"# ERRO: Credenciais de login GPM não encontradas para {operacao}. Verifique os Secrets/Ambiente.")
            return

        self._processar_download(consulta_url, login_gpm, senha_gpm, operacao)

    def _processar_download(self, consulta_url, login_gpm, senha_gpm, operacao):
        login_url = f'https://sirtec{operacao.lower()}.gpm.srv.br/index.php'

        self._navegar(login_url)
        self._logar_gpm(login_gpm, senha_gpm)
        
        print(f"- Navegando para a consulta via hash: {consulta_url}")
        self.navegador.execute_script(f"window.location.hash = '#GR412';")
        
        # AGUARDA O CARREGAMENTO DOS FILTROS (Novo Layout)
        print("- Localizando frame da consulta...")
        def switch_to_correct_frame():
            self.navegador.switch_to.default_content()
            if self.navegador.find_elements(By.XPATH, "//input[contains(@placeholder,'Data Inicial')]"):
                return True
            iframes = self.navegador.find_elements(By.TAG_NAME, "iframe")
            for frame in iframes:
                try:
                    self.navegador.switch_to.frame(frame)
                    if self.navegador.find_elements(By.XPATH, "//input[contains(@placeholder,'Data Inicial')]"):
                        return True
                except: pass
                self.navegador.switch_to.default_content()
            return False

        if not switch_to_correct_frame():
            sleep(5)
            if not switch_to_correct_frame():
                print(f"# ERRO: Página de consulta ou iframe não encontrado.")
                return
        
        # PREENCHIMENTO DE DATAS (NOVO LAYOUT FLATPICKR)
        data_str = self.getDate() # DD/MM/YYYY
        # ISO para flatpickr (mais confiável via JS)
        try:
            data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except:
            data_iso = data_str

        print(f"- Definindo datas: {data_str} (ISO: {data_iso})")
        
        def set_date_via_typing(placeholder_part, value, iso_val):
            try:
                # Seletor mais amplo para placeholder (ignora case)
                xpath = f"//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{placeholder_part.lower()}')]"
                el = WebDriverWait(self.navegador, 15).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                # Remove readonly
                self.navegador.execute_script("arguments[0].removeAttribute('readonly');", el)
                
                # Tenta via Flatpickr API primeiro (é o mais garantido no Falconer)
                success_js = self.navegador.execute_script(f"""
                    var el = arguments[0];
                    if (el._flatpickr) {{
                        el._flatpickr.setDate('{iso_val}', true);
                        return true;
                    }}
                    return false;
                """, el)
                
                if not success_js:
                    el.click()
                    el.clear()
                    el.send_keys(value)
                    el.send_keys("\t") 
                    self.navegador.execute_script("arguments[0].dispatchEvent(new Event('change')); arguments[0].dispatchEvent(new Event('blur'));", el)
                return True
            except:
                return False

        r1 = set_date_via_typing('Inicial', data_str, data_iso)
        r2 = set_date_via_typing('Final', data_str, data_iso)
        
        if not (r1 and r2):
            print("⚠️ Aviso: Falha parcial na aplicação de datas. Verificando fallbacks...")
            # Fallback 2: JS Direto via classe flatpickr-input
            js_fallback = f"""
                var inputs = document.querySelectorAll('.flatpickr-input');
                if (inputs.length >= 2) {{
                    if(inputs[0]._flatpickr) inputs[0]._flatpickr.setDate('{data_iso}', true);
                    if(inputs[1]._flatpickr) inputs[1]._flatpickr.setDate('{data_iso}', true);
                }}
            """
            self.navegador.execute_script(js_fallback)

        # CLIQUE NO BOTÃO PESQUISAR
        print("- Clicando em Pesquisar...")
        try:
            # Tenta clicar no botão azul "Pesquisar"
            btn_pesquisar = WebDriverWait(self.navegador, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Pesquisar')]"))
            )
            btn_pesquisar.click()
        except:
            print("- Falha no botão Pesquisar principal, tentando 'buscar' via ID ou JS...")
            try:
                self.navegador.execute_script("document.getElementById('buscar').click();")
            except:
                self._click("//button[contains(@class,'btn-primary')]")
        
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

        # TENTATIVA DE EXPORTAÇÃO (Botão Excel/CSV Padrão)
        print("- Localizando botão de exportação 'Excel/CSV Padrão'...")
        exportou_sucesso = False
        try:
            # O seletor XPath mais robusto para este botão verde
            btn_export = WebDriverWait(self.navegador, 40).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Excel/CSV Padrão')]"))
            )
            btn_export.click()
            print("- Clique no botão 'Excel/CSV Padrão' realizado.")
            exportou_sucesso = True
            sleep(20) # Tempo maior para o download do ZIP
        except Exception as e:
            print(f"- Botão principal falhou ({e}). Tentando alternativas...")
            try:
                self.navegador.execute_script("document.querySelector('button.btn-success').click();")
                exportou_sucesso = True
                sleep(20)
            except:
                print("- Falha em todos os métodos de exportação principal.")

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
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(path_downloads)
                    print(f"- Arquivo {zip_path} descompactado")
                    
                    # Procura por CSV, XLS ou XLSX extraídos
                    extracted_files = [f for f in os.listdir(path_downloads) if (f.endswith('.csv') or f.endswith('.xls') or f.endswith('.xlsx')) and 'SCRAPED' not in f]
                    for ext_file in extracted_files:
                        old_path = os.path.join(path_downloads, ext_file)
                        new_filename = f"consulta turno {operacao}.{'xls' if ext_file.endswith('.xls') else ('xlsx' if ext_file.endswith('.xlsx') else 'csv')}"
                        new_path = os.path.join(path_temp, new_filename)
                        
                        if os.path.exists(new_path): os.remove(new_path)
                        shutil.move(old_path, new_path)
                        print(f"- Arquivo extraído renomeado e movido para {new_path}")
                    
                    os.remove(zip_path)
                    print(f"- Arquivo ZIP {zip_name} removido.")
                except Exception as e:
                    print(f"# Erro ao processar ZIP {zip_name}: {e}")
        
        # Caso especial: Se não veio ZIP ou se o CSV veio vazio, usamos o BACKUP de scraping
        backup_file = f"SCRAPED_BACKUP_{operacao}.csv"
        backup_path = os.path.join(path_downloads, backup_file)
        if os.path.exists(backup_path):
            os.makedirs(path_temp, exist_ok=True)
            new_path = os.path.join(path_temp, f"consulta turno {operacao}.csv")
            # Só usa o scraping se o original não existir ou estiver quase vazio
            if not os.path.exists(new_path) or os.path.getsize(new_path) < 500:
                if os.path.exists(backup_path):
                    shutil.move(backup_path, new_path)
                    print(f"- [ROBUSTEZ] Usando dados capturados via SCRAPING direto da tela para '{operacao}'.")
            else:
                if os.path.exists(backup_path): os.remove(backup_path)


##### outros ###             
    def limpar_pasta_temp(self):
        # GARANTE QUE A PASTA TEMP EXISTE (Crucial para o GitHub Actions)
        if not os.path.exists(path_temp):
            os.makedirs(path_temp, exist_ok=True)
            print(f"- Pasta temp criada em: {path_temp}")

        for temp_file in os.listdir(path_temp):
            temp_file_path = os.path.join(path_temp, temp_file)
            try:
                if os.path.isfile(temp_file_path) or os.path.islink(temp_file_path):
                    os.unlink(temp_file_path)
                elif os.path.isdir(temp_file_path):
                    shutil.rmtree(temp_file_path)
            except Exception as e:
                print(f"# Falha ao deletar {temp_file_path}. Razão: {e}\n")

    def limpar_downloads_inicial(self):
        """Limpa arquivos CSV e ZIP da pasta de downloads antes de começar."""
        if os.path.exists(path_downloads):
            print(f"- Limpando arquivos residuais em: {path_downloads}")
            for f in os.listdir(path_downloads):
                if f.endswith('.csv') or f.endswith('.zip'):
                    try:
                        os.remove(os.path.join(path_downloads, f))
                    except:
                        pass

# Alias de compatibilidade para o main.py antigo
Chrome = BrowserGPM
