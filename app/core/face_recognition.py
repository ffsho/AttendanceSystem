import face_recognition
import cv2
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
from .definitions import FACES_IMG_DIR
from .database import DatabaseManager



class FaceRecognizer:
    def __init__(self, db: DatabaseManager):
        """
        Инициализация системы распознавания лиц
        
        :param db: Объект DatabaseManager для работы с базой данных
        """
        self.db = db
        self.known_face_encodings = []
        self.known_face_info = []  # (user_id, full_name)
        self.last_detected_user = None
        self.last_detection = False
        self.frame_skip = 1  # Оптимизация: обработка каждого 3-го кадра
        self.frame_counter = 0
        self.load_known_faces()

    def load_known_faces(self):
        """Загрузка данных о лицах из базы и файловой системы"""
        self.known_face_encodings.clear()
        self.known_face_info.clear()

        try:
            # Получаем пользователей через метод DatabaseManager
            users = self.db.get_all_users()
            for user in users:
                user_id = user[0]
                lastname = user[1]
                firstname = user[2]
                patronymic = user[3] or ""
                full_name = f"{lastname} {firstname} {patronymic}".strip()

                # Загрузка всех изображений пользователя
                user_folder = FACES_IMG_DIR / str(user_id)
                if user_folder.exists():
                    for img_path in user_folder.glob("*.jpg"):
                        try:
                            image = face_recognition.load_image_file(str(img_path))
                            encodings = face_recognition.face_encodings(image)
                            if encodings:
                                self.known_face_encodings.append(encodings[0])
                                self.known_face_info.append((user_id, full_name))
                        except Exception as e:
                            print(f"Ошибка загрузки {img_path}: {str(e)}")
        except Exception as e:
            print(f"Ошибка загрузки пользователей: {str(e)}")


    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Обработка кадра для распознавания лиц"""
        self.frame_counter += 1
        self.last_detection = False
        if self.frame_counter % self.frame_skip != 0:
            return frame

        # Оптимизация: уменьшение разрешения
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Обнаружение лиц
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            # Поиск совпадений с порогом 0.5
            matches = face_recognition.compare_faces(
                self.known_face_encodings, 
                face_encoding,
                tolerance=0.5
            )
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                self.last_detection = True
                user_id, full_name = self.known_face_info[best_match_index]
                self._handle_recognized_user(user_id)
                frame = self._draw_face_box(frame, top, right, bottom, left, full_name)

        return frame

    def _handle_recognized_user(self, user_id: int):
        """Обработка распознанного пользователя"""
        if self.last_detected_user != user_id:
            # Проверяем, есть ли уже сегодняшняя запись
            if not self.db.has_attendance_today(user_id):
                try:
                    self.db.add_attendance_record(user_id)
                    self.last_detected_user = user_id
                except Exception as e:
                    print(f"Ошибка записи посещения: {str(e)}")

    def _draw_face_box(self, frame: np.ndarray, 
                      top: int, right: int, 
                      bottom: int, left: int,
                      full_name: str) -> np.ndarray:
        """Отрисовка рамки и подписи"""
        # Масштабирование координат (т.к. обрабатывали уменьшенный кадр)
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        # Рамка
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Подложка для текста
        cv2.rectangle(frame, 
                     (left, bottom - 40), 
                     (right, bottom), 
                     (0, 255, 0), 
                     cv2.FILLED)
        
        # Текст
        cv2.putText(frame, full_name, 
                   (left + 6, bottom - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, (255, 255, 255), 2)
        
        return frame
    
    def add_face_sample(self, user_id: int, face_image: np.ndarray, sample_num: int):
        """Добавление образца лица"""
        user_folder = FACES_IMG_DIR / str(user_id)
        user_folder.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(user_folder / f"sample_{sample_num}.jpg"), face_image)


    def register_new_user(self, user_id: int, num_samples: int = 5) -> bool:
        """
        Регистрация нового пользователя через веб-камеру
        
        :param user_id: ID пользователя из базы данных
        :param num_samples: Количество сохраняемых образцов
        """
        user_folder = FACES_IMG_DIR / str(user_id)
        user_folder.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return False

        samples_captured = 0
        while samples_captured < num_samples:
            ret, frame = cap.read()
            if not ret:
                continue

            # Обнаружение лиц
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                top, right, bottom, left = face_locations[0]
                
                # Сохранение образца
                face_img = frame[top:bottom, left:right]
                img_path = user_folder / f"sample_{samples_captured}.jpg"
                cv2.imwrite(str(img_path), face_img)
                samples_captured += 1

                # Визуальная обратная связь
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, f"Образцов: {samples_captured}/{num_samples}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.imshow("Регистрация лица", frame)
            if cv2.waitKey(1) == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        self.load_known_faces()  # Перезагружаем данные
        return True