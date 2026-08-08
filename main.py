import cv2
import face_recognition
import numpy as np
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis de ambiente
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ Erro: SUPABASE_URL e SUPABASE_KEY não configuradas no .env")
    exit()

supabase: Client = create_client(URL, KEY)

def carregar_usuarios():
    """Busca todos os usuários e seus vetores faciais no Supabase"""
    print("⏳ Carregando banco de dados de rostos do Supabase...")
    try:
        res = supabase.from_("usuarios").select("nome, cpf, encoding").execute()
        usuarios = res.data

        known_face_encodings = []
        known_face_names = []

        for user in usuarios:
            # O encoding vem como JSON/Lista e precisa ser convertido em array numpy
            encoding_data = user["encoding"]
            if isinstance(encoding_data, str):
                encoding_data = json.loads(encoding_data)

            known_face_encodings.append(np.array(encoding_data))
            known_face_names.append(f"{user['nome']} ({user['cpf']})")

        print(f"✅ {len(known_face_encodings)} rostos carregados com sucesso!")
        return known_face_encodings, known_face_names
    except Exception as e:
        print(f"❌ Erro ao buscar usuários no Supabase: {e}")
        return [], []

def rodar_reconhecimento():
    known_face_encodings, known_face_names = carregar_usuarios()

    if not known_face_encodings:
        print("⚠️ Nenhum usuário cadastrado. Rode o 'cadastrar.py' primeiro!")
        return

    print("\n🎥 Iniciando câmera para reconhecimento em tempo real...")
    print("Aperte 'Q' para encerrar.")

    cap = cv2.VideoCapture(0)

    # Variável para otimizar o processamento (processa quadro sim, quadro não)
    process_this_frame = True

    face_locations = []
    face_encodings = []
    face_names = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Falha ao capturar imagem da câmera.")
            break

        # Reduz o tamanho do frame para 1/4 para o processamento ficar leve e rápido
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Converte a imagem de BGR (OpenCV) para RGB (face_recognition)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        if process_this_frame:
            # Localiza os rostos e calcula seus encodings na imagem atual
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # Compara o rosto da câmera com os rostos conhecidos do banco
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                name = "Desconhecido"

                # Calcula a distância (quanto menor a distância, mais parecido)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]

                face_names.append(name)

        process_this_frame = not process_this_frame

        # Desenha os retângulos e nomes na imagem original
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Redimensiona os pontos de volta para a dimensão original (x4)
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Cor do retângulo: Verde se conhecido, Vermelho se desconhecido
            color = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)

            # Caixa do rosto
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Etiqueta com o nome abaixo do rosto
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        # Mostra o resultado na tela
        cv2.imshow("VISIONX360 - Reconhecimento Facial em Tempo Real", frame)

        # Sai ao pressionar 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    rodar_reconhecimento()
