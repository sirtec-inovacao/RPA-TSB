import os
from download_gpm import BrowserGPM
from get_date_run import writeDate
from auxiliar import path_temp, path_downloads
import shutil
import time
from time import sleep

def test_gpm_single():
    print("=== INICIANDO TESTE UNITÁRIO GPM (REFERÊNCIA: COLETOR) ===")
    
    # Iniciamos com headless=True para o Actions conforme solicitado
    browser = BrowserGPM(headless=True)
    
    # FORÇAR DATA FIXA PARA TESTE (Solicitado pelo Usuário)
    browser.getDate = lambda: "05/03/2026" 
    print(f"- [MODO TESTE] Data forçada para: {browser.getDate()}")
    
    # 1. Limpeza inicial
    print("- Limpando ambiente de teste...")
    browser.limpar_pasta_temp()
    browser.limpar_downloads_inicial()
    
    try:
        # REFERÊNCIA DE LOGIN (Baseada em coletor_faturamento.py)
        # O GPM às vezes exige uma navegação direta para garantir o foco
        login_url = "https://sirtecba.gpm.srv.br/"
        browser._navegar(login_url)
        
        print("🔑 Realizando login (Padrão Coletor)...")
        login_gpm = os.getenv('LOGIN_GPM')
        senha_gpm = os.getenv('SENHA_GPM')
        
        # Uso de IDs diretos e esperas mais longas conforme ref
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        WebDriverWait(browser.navegador, 60).until(EC.presence_of_element_located((By.ID, "idLogin"))).send_keys(login_gpm)
        browser.navegador.find_element(By.ID, "idSenha").send_keys(senha_gpm)
        
        # XPATH do botão de login idêntico ao de sucesso do usuário
        btn_login_xpath = '//*[@id="logar"]/div/div/div/div/div/div/div[4]/div[2]/div[2]/div[1]/input'
        browser.navegador.find_element(By.XPATH, btn_login_xpath).click()
        
        print("⏳ Aguardando tela inicial após login...")
        WebDriverWait(browser.navegador, 60).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]')))
        print("✅ Login realizado com sucesso!")

        # NAVEGAÇÃO PARA CONSULTA TURNO (NOVO LAYOUT VIA PESQUISA)
        print("- Pesquisando por 'Consulta Turno' no menu Falconer...")
        try:
            # 1. Abre a barra de pesquisa
            search_input = WebDriverWait(browser.navegador, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.typeahead, input[placeholder*='Pesquisar']"))
            )
            search_input.click()
            search_input.clear()
            search_input.send_keys("Consulta Turno")
            sleep(2)
            
            # 2. Clica no item da lista de resultados
            # O sistema Falconer costuma ter uma div com classe 'tt-suggestion' ou similar
            item_menu = WebDriverWait(browser.navegador, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Consulta Turno')] | //div[contains(text(), 'Consulta Turno')]"))
            )
            item_menu.click()
            print("✅ Navegação via pesquisa concluída com sucesso.")
            sleep(5)
        except Exception as e:
            print(f"- Aviso: Falha na navegação via pesquisa ({e}). Tentando hash direto...")
            browser.navegador.execute_script("window.location.hash = '#GR412';")
            browser.navegador.refresh()
            sleep(5)
        
        print("⏳ Esperando carregamento dos filtros (Novo Layout)...")
        # Falconer usa iframes para módulos. Precisamos encontrar em qual frame os campos estão.
        def switch_to_filter_frame():
            browser.navegador.switch_to.default_content()
            if browser.navegador.find_elements(By.XPATH, "//input[contains(@placeholder, 'Data Inicial')]"):
                return True # Já estamos no contexto certo
            
            iframes = browser.navegador.find_elements(By.TAG_NAME, "iframe")
            print(f"- Analisando {len(iframes)} iframes em busca dos filtros...")
            for i, frame in enumerate(iframes):
                try:
                    browser.navegador.switch_to.frame(frame)
                    if browser.navegador.find_elements(By.XPATH, "//input[contains(@placeholder, 'Data Inicial')]") or \
                       browser.navegador.find_elements(By.CLASS_NAME, "flatpickr-input"):
                        print(f"✅ Filtros encontrados no iframe {i}.")
                        return True
                except:
                    pass
                browser.navegador.switch_to.default_content()
            return False

        if not switch_to_filter_frame():
            print("⚠️ Aviso: Não consegui localizar os filtros nos frames padrão. Tentando aguardar mais...")
            sleep(5)
            switch_to_filter_frame()
        
        # Preenchimento das datas (Removendo readonly + Flatpickr API)
        data_str = browser.getDate() # DD/MM/YYYY
        try:
            data_iso = time.strftime("%Y-%m-%d", time.strptime(data_str, "%d/%m/%Y"))
        except:
            data_iso = data_str
            
        print(f"- Definindo datas: {data_str} (ISO: {data_iso})")
        
        def set_date_test(placeholder_part, value, iso_val):
            try:
                xpath = f"//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{placeholder_part.lower()}')]"
                el = WebDriverWait(browser.navegador, 15).until(EC.presence_of_element_located((By.XPATH, xpath)))
                browser.navegador.execute_script("arguments[0].removeAttribute('readonly');", el)
                
                # Prioridade: Flatpickr API
                success = browser.navegador.execute_script(f"""
                    var el = arguments[0];
                    if (el._flatpickr) {{
                        el._flatpickr.setDate('{iso_val}', true);
                        return true;
                    }}
                    return false;
                """, el)
                
                if not success:
                    el.click()
                    el.clear()
                    el.send_keys(value)
                    el.send_keys("\t")
                    browser.navegador.execute_script("arguments[0].dispatchEvent(new Event('change'));", el)
                return True
            except:
                return False

        set_date_test('Inicial', data_str, data_iso)
        set_date_test('Final', data_str, data_iso)
        
        # Tirar screenshot dos filtros preenchidos
        browser.navegador.save_screenshot("debug_passo_1_filtros.png")
        
        print(f"➡️ Submetendo consulta (Botão Pesquisar)...")
        try:
            btn_pesquisar = WebDriverWait(browser.navegador, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Pesquisar')]"))
            )
            btn_pesquisar.click()
        except Exception as e:
            print(f"- Aviso: Falha ao clicar em 'Pesquisar' via XPATH: {e}. Tentando via ID 'buscar'...")
            browser.navegador.execute_script("document.getElementById('buscar').click();")
        
        sleep(5)
        browser.navegador.save_screenshot("debug_passo_2_apos_pesquisa.png")
        
        # Espera a tabela carregar (Padrão do ref)
        print("⏳ Aguardando resultados na tabela...")
        WebDriverWait(browser.navegador, 60).until(EC.presence_of_element_located((By.ID, "tab_resultados")))
        
        # GARANTIA: Espera o "Processing" do Datatables sumir
        try:
            WebDriverWait(browser.navegador, 10).until(EC.invisibility_of_element_located((By.ID, "tab_resultados_processing")))
        except: pass

        # Tenta selecionar "Ver Todos" no Datatables para garantir que todos os dados estejam no DOM
        print("- Expandindo visualização para 'Todos' os registros...")
        try:
            # Tenta via API do DataTable
            browser.navegador.execute_script("if($.fn.DataTable.isDataTable('#tab_resultados')) { $('#tab_resultados').DataTable().page.len(-1).draw(); }")
            sleep(4)
        except: pass
        
        # Conta linhas reais (tbody tr)
        rows_count = browser.navegador.execute_script("return $('#tab_resultados tbody tr').filter(function() { return $(this).text().trim() != ''; }).length;")
        # Se for 1 e o texto for "Nenhum registro encontrado" ou similar
        if rows_count == 1:
            first_row_text = browser.navegador.execute_script("return $('#tab_resultados tbody tr').text().toLowerCase();")
            if "nenhum" in first_row_text or "não encontrado" in first_row_text:
                rows_count = 0
        
        print(f"📊 Registros identificados na tabela: {rows_count}")

        print("✅ Resultados prontos para exportação!")

        # EXPORTAÇÃO (Agora via Excel conforme solicitado)
        # EXPORTAÇÃO (Botão Verde: Excel/CSV Padrão)
        print("💾 Clicando no botão 'Excel/CSV Padrão'...")
        try:
            btn_export = WebDriverWait(browser.navegador, 40).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Excel/CSV Padrão')]"))
            )
            btn_export.click()
        except Exception as e:
            print(f"- Aviso: Falha no botão principal, tentando seletor alternativo: {e}")
            browser.navegador.execute_script("document.querySelector('.btn-success').click();")
        
        # ORGANIZAÇÃO E RENOMEAÇÃO (Lógica idêntica ao download_gpm.py)
        import zipfile
        files = os.listdir(path_downloads)
        
        # 1. Trata ZIPs (O botão Padrão costuma baixar ZIP no novo layout)
        for f in files:
            if f.endswith('.zip') and 'consulta' in f.lower():
                zip_path = os.path.join(path_downloads, f)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(path_downloads)
                    print(f"- ZIP {f} descompactado com sucesso.")
                    os.remove(zip_path)
                except Exception as e:
                    print(f"# Erro ao descompactar ZIP: {e}")

        # 2. Busca o arquivo final (mais flexível com extensões)
        for f in os.listdir(path_downloads):
            if (f.endswith('.xls') or f.endswith('.xlsx') or f.endswith('.csv')) and 'SCRAPED' not in f:
                old_p = os.path.join(path_downloads, f)
                ext = f.split('.')[-1]
                new_p = os.path.join(path_temp, f"consulta turno BA.{ext}")
                
                if os.path.exists(new_p): os.remove(new_p)
                shutil.move(old_p, new_p)
                print(f"- Arquivo {f} movido para temp como consulta turno BA.{ext}")

        # 3. Verifica se o arquivo apareceu na pasta temp (qualquer extensão)
        arquivos_temp = [f for f in os.listdir(path_temp) if f.startswith("consulta turno BA")]
        if arquivos_temp:
            esperado = os.path.join(path_temp, arquivos_temp[0])
            print(f"✅ SUCESSO: Arquivo encontrado em {esperado}")
            
            # 4. Upload para o Google Drive
            from gsheets import Gsheets
            from auxiliar import id_pasta_drive_final
            if id_pasta_drive_final:
                print("- Iniciando upload para o Drive...")
                gs = Gsheets()
                gs.upload_para_drive(esperado, id_pasta_drive_final)
                print("✅ SUCESSO: Arquivo enviado para o Google Drive.")
        else:
            # Fallback debug: lista o que tem no downloads
            print("❌ FALHA: Arquivo Excel/CSV não foi encontrado após download.")
            print(f"- Conteúdo da pasta downloads: {os.listdir(path_downloads)}")
            print(f"- Conteúdo da pasta temp: {os.listdir(path_temp)}")

    except Exception as e:
        print(f"💥 ERRO DURANTE O TESTE: {e}")
        # Tira screenshot se der erro (Padrão do ref)
        if browser.navegador:
             browser.navegador.save_screenshot("erro_test_gpm.png")
             print("- Screenshot de erro salva (erro_test_gpm.png)")
    finally:
        if browser.navegador: browser.navegador.quit()
        print("=== FIM DO TESTE UNITÁRIO ===")

if __name__ == "__main__":
    test_gpm_single()
