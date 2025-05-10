import cv2
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
from insightface.app import FaceAnalysis
from .paths import FACES_IMG_DIR_ENTERPRISE, FACES_IMG_DIR_EDUCATIONAL
from .database import DatabaseManager
from ..settings.settings import SettingsManager


class FaceRecognizer:

    def __init__(self, db: DatabaseManager, settings_manager: SettingsManager):
        """
        Инициализация класса распознавания лиц с использованием InsightFace
        :param db: Объект DatabaseManager для работы с базой данных
        """
        self.settings_manager = SettingsManager()
        self.settings_manager.load_settings()

        # Конфигурация
        self.USE_GPU = False
        self.MODEL_NAME = "buffalo_s"
        self.DET_SIZE = (320, 320)
        self.REC_THRESHOLD = 0.5
        self.max_faces = int(self.settings_manager.get_setting('max_faces'))
        self.institution_type = self.settings_manager.get_setting('institution')
        self.FRAME_SKIP = 1
        
        self.db = db
        self.known_embeddings = []
        self.known_users = []
        self.last_detected_user = None
        self.frame_counter = 0
        
        # Инициализация модели
        self._init_model()
        self.load_known_faces()
        print("Создание объекта FaceRecognizer с макс. кол-вом лиц:", self.max_faces)


    def _init_model(self):
        """Инициализация модели InsightFace"""
        self.model = FaceAnalysis(
            name=self.MODEL_NAME,
            providers=['CUDAExecutionProvider'] if self.USE_GPU else ['CPUExecutionProvider'],
            allowed_modules=['detection', 'recognition']
        )
        self.model.prepare(
            ctx_id=0 if self.USE_GPU else -1,
            det_size=self.DET_SIZE
        )


    def load_known_faces(self):
        """Загрузка известных лиц из базы данных"""
        self.known_embeddings = []
        self.known_users = []

        users = self.db.get_all_users()
        print(f"Найдено пользователей в БД: {len(users)}")

        for user in users:
            user_id = user[0]
            
            if self.institution_type == 'Educational':
                user_folder = FACES_IMG_DIR_EDUCATIONAL / str(user_id)
            elif self.institution_type == 'Enterprise':
                user_folder = FACES_IMG_DIR_ENTERPRISE / str(user_id)

            if not user_folder.exists():
                print(f"Папка {user_folder} не существует!")
                continue

            # Загрузка всех изображений пользователя
            for img_path in user_folder.glob("*.jpg"):
                print(f"Обработка файла: {img_path}")
                try:
                    img = cv2.imread(str(img_path))

                    if img is None:
                        print(f"Ошибка чтения файла: {img_path}")
                        continue

                    faces = self.model.get(img)
                    if not faces:
                        print(f"Лица не найдены на изображении: {img_path}")
                        continue
                    
                    # Используем первое найденное лицо
                    embedding = faces[0].embedding
                    self.known_embeddings.append(embedding)
                    self.known_users.append({
                        'id': user_id,
                        'name': self._get_user_name(user),
                        'path': img_path
                    })

                except Exception as e:
                    print(f"Ошибка обработки {img_path}: {str(e)}")

        print(f"Итого загружено эмбеддингов: {len(self.known_embeddings)}")


    def _get_user_name(self, user):
        """
        Формирование имени пользователя
        """

        # user = (id, lastname, firstname, patronymic, ...)
        lastname = user[1] if user[1] is not None else ""
        firstname = user[2] if user[2] is not None else ""
        patronymic = user[3] if user[3] is not None else ""
        
        full_name = f"{lastname} {firstname} {patronymic}".strip()
        full_name = " ".join(full_name.split())  # Удаление двойных пробелов
        
        if not full_name:
            print(f"Внимание! Пустое имя для пользователя ID: {user[0]}")
            return "Неизвестный"
        
        return full_name


    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, list]:
        """
        Обработка кадра и распознавание лиц
        Возвращает:
            - Обработанный кадр с визуализацией
            - Список распознанных пользователей
        """

        self.frame_counter += 1
        processed_frame = frame.copy()
        recognized = []
        
        # Пропуск кадров для оптимизации
        # if self.frame_counter % (self.FRAME_SKIP + 1) != 0:
        #     return processed_frame, recognized
        
        # Детекция лиц
        faces = self.model.get(frame)
        
        for face in faces[:self.max_faces]:
            bbox = face.bbox.astype(int)
            similarity, user_id, user_name = self._recognize_face(face.embedding)
            
            # Отрисовка результатов
            color = (0, 255, 0) if similarity >= self.REC_THRESHOLD else (0, 0, 255)
            label = f"{user_name} ({similarity:.2f})" if similarity >= self.REC_THRESHOLD else "Неизвестный"
            
            cv2.rectangle(processed_frame, 
                         (bbox[0], bbox[1]), 
                         (bbox[2], bbox[3]), 
                         color, 2)

            cv2.putText(processed_frame, label,
                   (bbox[0], bbox[1]-10),
                   cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)
            
            if similarity >= self.REC_THRESHOLD:
                recognized.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'similarity': similarity,
                    'bbox': bbox
                })
                self._handle_recognized_user(user_id)
        
        return processed_frame, recognized


    def _recognize_face(self, embedding: np.ndarray) -> Tuple[float, int, str]:
        """Сравнение с эталонными образцами"""

        if not self.known_embeddings:
            return 0.0, -1, ""

        # Нормализация эмбеддингов
        embedding = embedding / np.linalg.norm(embedding)
        known_embeddings_norm = [e / np.linalg.norm(e) for e in self.known_embeddings]

        # Вычисление косинусной схожести
        similarities = np.dot(known_embeddings_norm, embedding)
        best_match_idx = np.argmax(similarities)
        max_similarity = similarities[best_match_idx]

        if max_similarity >= self.REC_THRESHOLD:

            user = self.known_users[best_match_idx]
            return max_similarity, user['id'], user['name']

        return max_similarity, -1, ""


    def _handle_recognized_user(self, user_id: int):
        """Обработка распознанного пользователя"""

        if self.last_detected_user != user_id:
            if not self.db.has_attendance_today(user_id):
                try:
                    self.db.add_attendance_record(user_id)
                    self.last_detected_user = user_id

                except Exception as e:
                    print(f"Ошибка записи посещения: {str(e)}")


    def register_new_user(self, user_id: int, num_samples: int = 10) -> bool:
        """
        Регистрация нового пользователя
        Возвращает:
            True - регистрация успешна
            False - ошибка регистрации
        """

        if self.institution_type == 'Educational':
            user_folder = FACES_IMG_DIR_EDUCATIONAL / str(user_id)
        elif self.institution_type == 'Enterprise':
            user_folder = FACES_IMG_DIR_ENTERPRISE / str(user_id)

        user_folder.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return False

        samples = 0
        while samples < num_samples:
            ret, frame = cap.read()
            if not ret:
                continue

            # Детекция лиц
            faces = self.model.get(frame)
            if faces:
                face = faces[0]
                bbox = face.bbox.astype(int)
                
                # Сохранение образца
                face_img = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                img_path = user_folder / f"sample_{samples}.jpg"
                cv2.imwrite(str(img_path), face_img)
                samples += 1
                
                # Визуальная обратная связь
                cv2.rectangle(frame, 
                             (bbox[0], bbox[1]), 
                             (bbox[2], bbox[3]), 
                             (0, 255, 0), 2)

                cv2.putText(frame, f"Собрано образцов: {samples}/{num_samples}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            cv2.imshow("Регистрация пользователя", frame)

            if cv2.waitKey(1) == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        self.load_known_faces()
        return samples >= num_samples


