import face_recognition
import cv2

# Загрузка изображения
image = cv2.imread("person.jpg")
rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Обнаружение лиц с HOG
face_locations = face_recognition.face_locations(rgb_image, model="hog")

# Отрисовка рамок
for top, right, bottom, left in face_locations:
    cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)

cv2.imshow("HOG Face Detection", image)
cv2.waitKey(0)