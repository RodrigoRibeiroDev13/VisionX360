import cv2
import face_recognition
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis do arquivo .env
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ Erro: Verifique se o seu arquivo .env está configurado corretamente com SUPABASE_URL e SUPABASE_KEY.")
    exit()

supabase: Client = create_client(URL, KEY)

def cadastrar_usuario():
    print("--- 👤 CADASTRO DE NOVO USUÁRIO ---")
    nome = input("Digite o Nome completo: ").strip()
    cpf = input("Digite o CPF (somente números): ").strip()

    if not nome or not cpf:
        print("❌ Nome e CPF são obrigatórios!")
        return

    print("\n📸 Abrindo a câmera... Olhe para a webcam e aperte 'ESPAÇO' para tirar a foto (ou 'Q' para cancelar).")
    
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Erro ao acessar a câmera.")
            break

        cv2.imshow("Cadastro Facial - Aperte ESPACO para fotografar", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):  # Tecla ESPAÇO
            print("⏳ Processando imagem...")
            # Converte de BGR (OpenCV) para RGB (face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detecta os encodings do rosto
            encodings = face_recognition.face_encodings(rgb_frame)

            if len(encodings) == 0:
                print("⚠️ Nenhum rosto foi detectado! Tente novamente com boa iluminação.")
                continue
            elif len(encodings) > 1:
                print("⚠️ Mais de um rosto detectado! Garanta que apenas você esteja na câmera.")
                continue

            # Pega o primeiro rosto detectado e converte para lista
            encoding_lista = encodings[0].tolist()

            # Salva no Supabase
            try:
                data = {
                    "nome": nome,
                    "cpf": cpf,
                    "encoding": encoding_lista
                }
                res = supabase.table("usuarios").insert(data).execute()
                print(f"\n✅ Usuário '{nome}' cadastrado com sucesso no banco de dados!")
            except Exception as e:
                print(f"\n❌ Erro ao salvar no Supabase: {e}")

            break

        elif key == ord('q') or key == ord('Q'):
            print("Operação cancelada pelo usuário.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    cadastrar_usuario()