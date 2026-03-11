import os
from download_gpm import BrowserGPM
from get_date_run import writeDate
from auxiliar import path_temp, path_downloads
import shutil

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

        # NAVEGAÇÃO PARA CONSULTA TURNO
        consulta_url = "https://sirtecba.gpm.srv.br/gpm/geral/consulta_turno.php"
        browser._navegar(consulta_url)
        
        print("⏳ Esperando carregamento dos filtros...")
        WebDriverWait(browser.navegador, 60).until(EC.presence_of_element_located((By.ID, "data_inicial")))
        
        # Preenchimento das datas via JS (Evita problemas com a máscara do campo)
        data_str = browser.getDate()
        print(f"- Definindo datas via JS: {data_str}")
        browser.navegador.execute_script(f"document.getElementById('data_inicial').value = '{data_str}';")
        browser.navegador.execute_script(f"document.getElementById('data_final').value = '{data_str}';")
        # Dispara o evento de mudança se necessário
        browser.navegador.execute_script("$('#data_inicial').trigger('change'); $('#data_final').trigger('change');")
        
        print(f"➡️ Submetendo consulta para: {data_str}")
        # Botão de submissão (Padrão do ref com espera e fallback)
        try:
            WebDriverWait(browser.navegador, 30).until(EC.element_to_be_clickable((By.ID, "submit"))).click()
        except:
            # Fallback para o XPATH alternativo se o ID falhar
            browser.navegador.find_element(By.XPATH, '/html/body/form[5]/div/input').click()
        
        # Espera a tabela carregar (Padrão do ref)
        print("⏳ Aguardando resultados na tabela...")
        WebDriverWait(browser.navegador, 60).until(EC.presence_of_element_located((By.ID, "tab_resultados")))
        
        # GARANTIA: Espera o "Processing" do Datatables sumir
        try:
            WebDriverWait(browser.navegador, 10).until(EC.invisibility_of_element_located((By.ID, "tab_resultados_processing")))
        except: pass

        # Tenta selecionar "Ver Todos" no Datatables para garantir que todos os dados estejam no DOM
        print("- Expandindo visualização para 'Todos' os registros (Garantia de exportação)...")
        try:
            browser.navegador.execute_script("if($.fn.DataTable.isDataTable('#tab_resultados')) { $('#tab_resultados').DataTable().page.len(-1).draw(); }")
            time.sleep(5)
            # DEBUG: Conta linhas
            rows_count = browser.navegador.execute_script("return $('#tab_resultados tbody tr').length;")
            print(f"📊 Linhas encontradas na tabela após expansão: {rows_count}")
        except: pass

        print("✅ Resultados prontos para exportação!")

        # EXPORTAÇÃO (Agora via Excel conforme solicitado)
        print("💾 Clicando no botão de exportação EXCEL...")
        try:
            # Espera o botão estar clicável (DataTables standard class)
            WebDriverWait(browser.navegador, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "buttons-excel"))).click()
        except:
            # Fallback para XPATH se necessário
            browser.navegador.find_element(By.XPATH, "//a[contains(@class, 'buttons-excel')]").click()
        
        import time
        import zipfile
        time.sleep(15) # Espera o download concluir

        # ORGANIZAÇÃO E RENOMEAÇÃO (Lógica interna do Robô)
        # 1. Tenta mover arquivo se ele não foi movido automaticamente
        for f in os.listdir(path_downloads):
            # Procura o arquivo .xls (Conforme imagem do usuário)
            if f.endswith('.xls') or f.endswith('.xlsx'):
                 # O usuário solicitou deixar a parte de extração comentada
                 # if f.endswith('.zip') and 'consulta' in f.lower():
                 #     with zipfile.ZipFile(os.path.join(path_downloads, f), 'r') as zip_ref:
                 #         zip_ref.extractall(path_downloads)
                 
                 old_p = os.path.join(path_downloads, f)
                 new_p = os.path.join(path_temp, "consulta turno BA.xls")
                 if os.path.exists(new_p): os.remove(new_p)
                 shutil.move(old_p, new_p)
                 print(f"- Arquivo {f} movido para temp.")

        # 3. Verifica se o arquivo apareceu na pasta temp
        esperado = os.path.join(path_temp, "consulta turno BA.xls")
        if os.path.exists(esperado):
            print(f"✅ SUCESSO: Arquivo Excel gerado em {esperado}")
            
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
            print("❌ FALHA: Arquivo Excel não foi encontrado após download.")
            print(f"- Conteúdo da pasta downloads: {os.listdir(path_downloads)}")

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
