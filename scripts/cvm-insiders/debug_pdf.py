import pdfplumber
from pathlib import Path

# --- CONFIGURE O ARQUIVO E A PÁGINA PARA DEPURAR ---
PDF_TO_DEBUG = Path("data/downloads/001023IPE010420240104542207-66.pdf")
PAGE_TO_DEBUG = 4 # Vamos focar na primeira página que falhou
# ----------------------------------------------------

def advanced_debug_parser(pdf_path: Path, page_number: int):
    if not pdf_path.exists():
        print(f"ERRO: Arquivo não encontrado em {pdf_path}")
        return

    print(f"--- Iniciando depuração avançada do arquivo: {pdf_path.name}, Página: {page_number} ---")

    with pdfplumber.open(pdf_path) as pdf:
        if page_number > len(pdf.pages):
            print(f"ERRO: O PDF só tem {len(pdf.pages)} páginas. Não é possível analisar a página {page_number}.")
            return
            
        page = pdf.pages[page_number - 1]
        
        print("\n[PASSO 1: Procurando por marcadores 'X']")
        x_marks = [char for char in page.chars if char['text'] == 'X' and char.get('width', 0) > 1]
        if not x_marks:
            print("Nenhum marcador 'X' encontrado nesta página.")
        else:
            print(f"Encontrados {len(x_marks)} marcadores 'X'. Coordenadas:")
            for i, x in enumerate(x_marks):
                print(f"  - X nº{i+1}: x0={x['x0']:.2f}, top={x['top']:.2f}")

        print("\n[PASSO 2: Procurando por textos candidatos a 'Grupo']")
        group_candidates = ["Controlador", "Conselho de Administração", "Diretoria", "Conselho Fiscal", "Órgãos Técnicos ou Consultivos"]
        candidate_boxes = []
        for candidate in group_candidates:
            found_list = page.search(candidate, strategy="text", explicit_vertical=False)
            if found_list:
                box_info = found_list[0]
                candidate_boxes.append({"text": candidate, "box": box_info})
        
        if not candidate_boxes:
            print("Nenhum texto candidato ('Diretoria', etc.) foi encontrado na página.")
        else:
            print(f"Encontrados {len(candidate_boxes)} textos candidatos. Coordenadas:")
            for item in candidate_boxes:
                box = item['box']
                print(f"  - '{item['text']}': x0={box['x0']:.2f}, x1={box['x1']:.2f}, top={box['top']:.2f}")

        print("\n[PASSO 3: Verificando a lógica de alinhamento de colunas]")
        match_found = False
        for i, x in enumerate(x_marks):
            for item in candidate_boxes:
                box = item['box']
                is_aligned = "SIM" if box['x0'] <= x['x0'] <= box['x1'] else "NÃO"
                print(f"  - Verificando X nº{i+1} (x0={x['x0']:.2f}) com '{item['text']}' (x0={box['x0']:.2f}, x1={box['x1']:.2f})... Alinhado? --> {is_aligned}")
                if is_aligned == "SIM":
                    match_found = True

        if not match_found:
            print("\n[CONCLUSÃO]: A lógica de alinhamento horizontal falhou. Nenhum 'X' foi encontrado dentro da 'coluna' de um texto candidato.")
        else:
            print("\n[CONCLUSÃO]: A lógica de alinhamento encontrou uma correspondência.")

        # --- Geração da Imagem de Depuração Visual ---
        try:
            print("\n[PASSO 4: Gerando imagem de depuração visual...]")
            im = page.to_image(resolution=200)
            
            # Desenha retângulos vermelhos nos marcadores 'X'
            if x_marks:
                im.draw_rects(x_marks, stroke="red", stroke_width=2)
            
            # Desenha retângulos azuis nos textos candidatos
            if candidate_boxes:
                im.draw_rects([item['box'] for item in candidate_boxes], stroke="blue", stroke_width=2)

            debug_image_path = f"debug_entity_finder_P{page_number}.png"
            im.save(debug_image_path, format="PNG")
            print(f">>> Imagem de depuração salva como: {debug_image_path}")
            print(">>> Na imagem, os 'X' estão em VERMELHO e os grupos ('Diretoria', etc) em AZUL.")

        except Exception as e:
            print(f"ERRO ao gerar imagem de depuração: {e}")

if __name__ == "__main__":
    advanced_debug_parser(PDF_TO_DEBUG, PAGE_TO_DEBUG)