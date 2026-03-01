import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Пути
MODEL_PATH = r"C:\Users\lolka\.vscode\joj\bone-fracture-detection\models\best_model.keras"
TEST_DIR = r"C:\Users\lolka\.vscode\joj\bone-fracture-detection\data\raw\test"

# Параметры
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# Загрузка данных
test_datagen = ImageDataGenerator(rescale=1./255)
test_gen = test_datagen.flow_from_directory(
    TEST_DIR,
    target_size=IMG_SIZE,
    color_mode='rgb',
    batch_size=BATCH_SIZE,
    class_mode='binary',
    shuffle=False
)

# Загрузка модели
model = load_model(MODEL_PATH)

# Предсказания
y_pred = model.predict(test_gen)
y_pred_classes = (y_pred > 0.5).astype(int)
y_true = test_gen.classes

# Отчёт
print("\n Classification Report:")
print(classification_report(y_true, y_pred_classes, target_names=list(test_gen.class_indices.keys())))

# Матрица ошибок
cm = confusion_matrix(y_true, y_pred_classes)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=list(test_gen.class_indices.keys()))
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix — Bone Fracture Detection")
plt.show()