import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from PIL import ImageFile

# Разрешаем загрузку усеченных изображений
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Отключаем предупреждения TensorFlow
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Конфигурация
IMG_SIZE = 224
BATCH_SIZE = 16
LEARNING_RATE = 0.0001

class MicrofractureDetector:

    def __init__(self, img_size=IMG_SIZE):
        self.img_size = img_size
        self.model = None
        self.base_model = None
        self.history = None
        
    def create_data_generators(self, train_dir, val_dir, test_dir=None):

        # Простая аугментация
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=10,
            zoom_range=0.1,
            horizontal_flip=True
        )
        
        # Для валидации только нормализация
        val_test_datagen = ImageDataGenerator(rescale=1./255)
        
        try:
            train_generator = train_datagen.flow_from_directory(
                train_dir,
                target_size=(self.img_size, self.img_size),
                batch_size=BATCH_SIZE,
                class_mode='binary',
                classes=['no_fracture', 'fracture'],
                shuffle=True
            )
            
            validation_generator = val_test_datagen.flow_from_directory(
                val_dir,
                target_size=(self.img_size, self.img_size),
                batch_size=BATCH_SIZE,
                class_mode='binary',
                classes=['no_fracture', 'fracture'],
                shuffle=False
            )
            
            return train_generator, validation_generator
            
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return None, None, None
    
    def build_model(self):

        # Загружаем DenseNet121
        self.base_model = DenseNet121(
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size, self.img_size, 3)
        )
        
        # Замораживаем базовую модель
        self.base_model.trainable = False
        
        # Создаем модель
        inputs = keras.Input(shape=(self.img_size, self.img_size, 3))
        x = self.base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(1, activation='sigmoid')(x)
        
        self.model = keras.Model(inputs, outputs)
        
        return self.model
    
    def compile_model(self):

        self.model.compile(
            optimizer=Adam(learning_rate=LEARNING_RATE),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
    
    def train_model(self, train_generator, validation_generator, epochs=30):

        if train_generator.samples == 0 or validation_generator.samples == 0:
            print("Ошибка: нет данных")
            return None
        
        # Правильно вычисляем количество шагов
        steps_per_epoch = train_generator.samples // BATCH_SIZE
        validation_steps = validation_generator.samples // BATCH_SIZE
        
        # Если есть остаток, добавляем шаг
        if train_generator.samples % BATCH_SIZE != 0:
            steps_per_epoch += 1
        if validation_generator.samples % BATCH_SIZE != 0:
            validation_steps += 1
        
        print(f"\n=== ОБУЧЕНИЕ МОДЕЛИ ===")
        print(f"Тренировочных изображений: {train_generator.samples}")
        print(f"Валидационных изображений: {validation_generator.samples}")
        print(f"Размер батча: {BATCH_SIZE}")
        print(f"Шагов за эпоху: {steps_per_epoch}")
        print(f"Валидационных шагов: {validation_steps}")
        
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                verbose=1
            )
        ]
        
        try:
            history = self.model.fit(
                train_generator,
                steps_per_epoch=steps_per_epoch,
                epochs=epochs,
                validation_data=validation_generator,
                validation_steps=validation_steps,
                callbacks=callbacks,
                verbose=1
            )
            
            self.history = history.history
            return history
            
        except Exception as e:
            print(f"Ошибка при обучении: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    # Пути к данным
    TRAIN_DIR = r"C:\Users\lolka\.vscode\joj\bone-fracture-detection\data\raw\train"
    VAL_DIR = r"C:\Users\lolka\.vscode\joj\bone-fracture-detection\data\raw\val"

    # Создаем детектор
    detector = MicrofractureDetector()
    
    # Загружаем данные
    print("Загрузка данных...")
    train_gen, val_gen  = detector.create_data_generators(
        TRAIN_DIR, VAL_DIR
    )
    
    if train_gen is None or val_gen is None:
        print("Не удалось загрузить данные")
        return
    
    if train_gen.samples == 0 or val_gen.samples == 0:
        print("Нет изображений для обучения")
        return
    
    # Показываем распределение классов
    print(f"\nКлассы: {train_gen.class_indices}")
    
    # Создаем и компилируем модель
    print("\nСоздание модели DenseNet121...")
    detector.build_model()
    detector.compile_model()
    detector.model.summary()
    
    # Обучение
    history = detector.train_model(train_gen, val_gen, epochs=30)
    
    if history is None:
        print("Обучение не удалось")
        return

    # Сохраняем модель
    detector.model.save(r"C:\Users\lolka\.vscode\joj\bone-fracture-detection\models\best_model.keras")
    
if __name__ == "__main__":
    main()