import os
import numpy as np
import visualkeras
from tensorflow import keras  
MODEL_PATH = r'D:\vkladki\best_model.keras'
print("Файл существует:", os.path.exists(MODEL_PATH))
model = keras.models.load_model(MODEL_PATH, compile=False)
model.summary()


test_image = np.random.random((1, 224, 224, 3)).astype(np.float32)  
prediction = model.predict(test_image)
print("Предсказание:", prediction)  

