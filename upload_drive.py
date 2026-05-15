"""
Script avulso: faz upload de todos os arquivos da pasta 'final/' para o Google Drive.
Use quando o processamento já rodou, mas o upload falhou.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auxiliar import path_final, id_pasta_drive_final
from gsheets import Gsheets

def main():
    gsheets = Gsheets()
    
    if not gsheets.servico_drive:
        print("# ERRO: Conexão com o Drive não estabelecida. Verifique o chaveGoogle.json e o .env.")
        return

    if not id_pasta_drive_final:
        print("# ERRO: ID_PASTA_DRIVE_FINAL não configurado no .env.")
        return

    if not os.path.exists(path_final):
        print(f"# Pasta 'final/' não encontrada em: {path_final}")
        return

    arquivos = sorted([
        os.path.join(path_final, f)
        for f in os.listdir(path_final)
        if f.endswith('_df_final.csv')
    ])

    if not arquivos:
        print("# Nenhum arquivo _df_final.csv encontrado na pasta final/.")
        return

    print(f"- {len(arquivos)} arquivo(s) encontrados para upload.\n")
    enviados = 0
    falhos = 0

    for arq in arquivos:
        nome = os.path.basename(arq)
        print(f"  -> Enviando: {nome}...")
        ok = gsheets.upload_para_drive(arq, id_pasta_drive_final)
        if ok:
            enviados += 1
            print(f"     [OK]")
        else:
            falhos += 1
            print(f"     # FALHA")

    print(f"\n--- Resultado: {enviados} enviados / {falhos} falhos ---")

if __name__ == "__main__":
    main()
