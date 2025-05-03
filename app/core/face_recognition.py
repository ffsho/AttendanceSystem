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
        self.known_face_encodings.clear()
        self.known_face_info.clear()
        users = self.db.get_all_users()
        for user in users:
            user_id = user[0]
            lastname = user[1]
            firstname = user[2]
            patronymic = user[3] or ""  # Обработка None
            full_name = f"{lastname} {firstname} {patronymic}".strip()
            full_name = " ".join(full_name.split())  # Удаление лишних пробелов
            user_folder = FACES_IMG_DIR / str(user_id)
            if user_folder.exists():
                for img_path in user_folder.glob("*.jpg"):
                    try:
                        image = face_recognition.load_image_file(str(img_path))
                        encodings = face_recognition.face_encodings(image)
                        if encodings:
                            self.known_face_encodings.append(encodings[0])
                            self.known_face_info.append((user_id, full_name))
                            print(f"Загружено: {full_name}")  # Логирование
                        else:
                            print(f"Не удалось извлечь кодировку из {img_path}")
                    except Exception as e:
                        print(f"Ошибка загрузки {img_path}: {e}")
        print(f"Всего загружено {len(self.known_face_encodings)} кодировок")


    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.frame_counter += 1
        self.last_detection = False
        
        # Пропускаем кадры для оптимизации
        # if self.frame_counter % 2 != 0:
        #     return frame

        if not self.known_face_encodings:
            return frame
        
        # Уменьшаем разрешение кадра
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Обнаружение лиц
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            
            if not self.known_face_encodings:
                return frame
            
            # Увеличиваем точность сравнения
            matches = face_recognition.compare_faces(
                self.known_face_encodings, 
                face_encoding,
                tolerance=0.4  # Уменьшаем порог
            )
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) == 0:
                continue

            best_match_index = np.argmin(face_distances)
            print(f"Совпадение: {matches[best_match_index]}, Индекс: {best_match_index}")  # Логирование
        
            if matches[best_match_index]:
                user_id, full_name = self.known_face_info[best_match_index]
                print(f"Распознан: {full_name} (ID: {user_id})")
            
            if matches[best_match_index]:
                user_id, full_name = self.known_face_info[best_match_index]
                print(f"Распознан: {full_name}")  # Логирование
                self._handle_recognized_user(user_id)
                frame = self._draw_face_box(frame, top, right, bottom, left, full_name)
            else:
                frame = self._draw_face_box(frame, top, right, bottom, left, "Неизвестный")
        
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
        # Масштабирование координат с проверкой границ
        scale_factor = 2
        left = max(0, left * scale_factor)
        right = min(frame.shape[1], right * scale_factor)  # Ограничение по ширине
        top = max(0, top * scale_factor)
        bottom = min(frame.shape[0], bottom * scale_factor)  # Ограничение по высоте
        
        # Обрезка длинных имен
        display_name = full_name[:20] + ".." if len(full_name) > 20 else full_name
        
        # Отрисовка рамки и текста
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.rectangle(frame, (left, bottom - 30), (right, bottom), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, display_name, (left + 5, bottom - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return frame


    def register_new_user(self, user_id: int, num_samples: int = 10) -> bool:
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