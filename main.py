import sys
import os
import random
from tensorflow import keras
import numpy as np
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QFileDialog,
    QMessageBox, QListWidget, QTextEdit, QSplitter, QTabWidget,
    QScrollArea, QGridLayout, QLineEdit, QComboBox, QDateEdit,
    QGroupBox, QTextBrowser
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QPixmap, QFont, QIcon, QPainter, QColor
from PyQt6.QtCore import QSize

class PatientCard(QFrame):
    def __init__(self, patient_data, parent=None):
        super().__init__(parent)
        self.patient_data = patient_data
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            PatientCard {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 15px;
            }
            PatientCard:hover {
                border-color: #2c5aa0;
                background-color: #f8fafc;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        
        # Основная информация
        name_label = QLabel(f"👤 {self.patient_data['name']}")
        name_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c5aa0;")
        
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"🎂 {self.patient_data['age']} лет"))
        info_layout.addWidget(QLabel(f"📋 №{self.patient_data['id']}"))
        
        diagnosis_label = QLabel(f"📝 Диагноз: {self.patient_data['diagnosis']}")
        diagnosis_label.setStyleSheet("color: #666666; font-size: 12px;")
        
        status_label = QLabel(f"📍 {self.patient_data['status']}")
        status_color = "#dc2626" if self.patient_data['status'] == "Требуется анализ" else "#16a34a"
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        
        layout.addWidget(name_label)
        layout.addLayout(info_layout)
        layout.addWidget(diagnosis_label)
        layout.addWidget(status_label)
        
        # Кнопка выбора
        select_btn = QPushButton("Выбрать пациента")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c5aa0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1e3a8a;
            }
        """)
        select_btn.clicked.connect(self.select_patient)
        
        layout.addWidget(select_btn)
        
    def select_patient(self):
        if self.parent:
            self.parent.select_patient(self.patient_data)

class MedicalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("МедАнализ - Система анализа рентгеновских снимков")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QTabWidget::pane {
                border: 1px solid #c4c4c4;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e2e8f0;
                color: #333333;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #2c5aa0;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #93c5fd;
            }
        """)
        
        self.current_patient = None
        self.current_image_path = None
        self.analysis_timer = None

        self.model = keras.models.load_model(r'D:\vkladki\best_model.keras', compile=False)
        self.init_ui()
        self.load_sample_patients()
        
    def init_ui(self):
        # Центральный виджет с вкладками
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Вкладка 1: Список пациентов
        self.patients_tab = self.create_patients_tab()
        self.tab_widget.addTab(self.patients_tab, "👥 Список пациентов")
        
        # Вкладка 2: Анализ снимка
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "📋 Карточка пациента")

        
        # Вкладка 3: Результаты
        self.results_tab = self.create_results_tab()
        self.tab_widget.addTab(self.results_tab, "📊 Результаты анализа")
        
        # Изначально блокируем вкладки анализа и результатов
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(2, False)
        
    def create_patients_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Список пациентов")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c5aa0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)

        # делаем атрибутами
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск пациентов...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #e2e8f0; border-radius: 5px;")

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все статусы", "Требуется анализ", "Анализ завершен", "Новые снимки"])
        self.status_filter.setStyleSheet("padding: 8px; border: 1px solid #e2e8f0; border-radius: 5px;")

        # сигналы на обновление списка
        self.search_input.textChanged.connect(self.display_patients)
        self.status_filter.currentIndexChanged.connect(self.display_patients)

        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()

        scroll_area = QScrollArea()
        self.patients_container = QWidget()
        self.patients_grid = QGridLayout(self.patients_container)

        scroll_area.setWidget(self.patients_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")

        layout.addWidget(title)
        layout.addWidget(filter_frame)
        layout.addWidget(scroll_area)

        return tab

        
    def create_analysis_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Информация о выбранном пациенте
        self.patient_info_frame = QFrame()
        self.patient_info_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f4ff;
                border: 2px solid #2c5aa0;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        patient_info_layout = QHBoxLayout(self.patient_info_frame)
        
        self.patient_avatar = QLabel("👤")
        self.patient_avatar.setStyleSheet("font-size: 40px;")
        
        self.patient_details = QLabel("Пациент не выбран")
        self.patient_details.setStyleSheet("font-size: 14px; color: #333333;")
        
        patient_info_layout.addWidget(self.patient_avatar)
        patient_info_layout.addWidget(self.patient_details)
        patient_info_layout.addStretch()
        
        # Основная область анализа
        analysis_layout = QHBoxLayout()
        
        # Левая часть - загрузка снимков
        left_frame = QFrame()
        left_frame.setStyleSheet("QFrame { background-color: white; border-radius: 10px; }")
        left_layout = QVBoxLayout(left_frame)
        
        upload_title = QLabel("Рентгеновские снимки пациента")
        # можно оставить или поменять по желанию

        gallery_label = QLabel("История анализов:")
        gallery_label.setStyleSheet("font-weight: bold; color: #2c5aa0; margin-top: 10px;")

        
        # Область загрузки
        self.upload_area = QLabel()
        self.upload_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.upload_area.setMinimumHeight(300)
        self.upload_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #2c5aa0;
                border-radius: 10px;
                background-color: #f8fafc;
                color: #666666;
                font-size: 14px;
            }
        """)
        self.upload_area.setText("Снимок не загружен\n\nНажмите 'Загрузить снимок' или перетащите файл")
        
        # Кнопки загрузки
        upload_btn = QPushButton("📁 Загрузить снимок")
        upload_btn.clicked.connect(self.upload_image)
        upload_btn.setStyleSheet("padding: 12px; font-size: 14px;")
        
        # Галлерея существующих снимков
        gallery_label = QLabel("История снимков:")
        gallery_label.setStyleSheet("font-weight: bold; color: #2c5aa0; margin-top: 10px;")
        
        self.gallery_list = QListWidget()
        self.gallery_list.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 5px;")
        
        left_layout.addWidget(upload_title)
        left_layout.addWidget(self.upload_area)
        left_layout.addWidget(upload_btn)
        left_layout.addWidget(gallery_label)
        left_layout.addWidget(self.gallery_list)
        
        # Правая часть - информация и управление
        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background-color: white; border-radius: 10px; }")
        right_layout = QVBoxLayout(right_frame)
        
        info_title = QLabel("Информация для анализа")
        info_title.setStyleSheet("font-weight: bold; font-size: 18px; color: #2c5aa0;")
        
        # Поля ввода информации (убрали выбор типа исследования)
        info_group = QGroupBox("Данные исследования")
        info_group.setStyleSheet("QGroupBox { font-weight: bold; color: #2c5aa0; }")
        group_layout = QVBoxLayout(info_group)
        
        # Убрали QComboBox для выбора типа исследования
        
        self.study_date = QDateEdit()
        self.study_date.setDate(QDate.currentDate())
        self.study_date.setCalendarPopup(True)
        
        self.comments_input = QTextEdit()
        self.comments_input.setPlaceholderText("Дополнительные комментарии...")
        self.comments_input.setMaximumHeight(100)
        
        # Убрали "Тип исследования:" и self.study_type
        group_layout.addWidget(QLabel("Дата исследования:"))
        group_layout.addWidget(self.study_date)
        group_layout.addWidget(QLabel("Комментарии:"))
        group_layout.addWidget(self.comments_input)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        
        # Кнопка анализа
        self.analyze_btn = QPushButton("🔍 Начать анализ снимка")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setStyleSheet("padding: 15px; font-size: 16px; font-weight: bold;")
        self.analyze_btn.setEnabled(False)
        
        right_layout.addWidget(info_title)
        right_layout.addWidget(info_group)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.status_label)
        right_layout.addWidget(self.analyze_btn)
        right_layout.addStretch()
        
        analysis_layout.addWidget(left_frame)
        analysis_layout.addWidget(right_frame)
        analysis_layout.setStretchFactor(left_frame, 2)
        analysis_layout.setStretchFactor(right_frame, 1)
        
        layout.addWidget(self.patient_info_frame)
        layout.addLayout(analysis_layout)
        
        return tab
        
    def create_results_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title = QLabel("Результаты анализа")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c5aa0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        study_info_frame = QFrame()
        study_info_frame.setStyleSheet("QFrame { background-color: #f8fafc; border-radius: 8px; padding: 15px; }")
        study_info_layout = QVBoxLayout(study_info_frame)

        self.study_info_label = QLabel("Информация о исследовании не доступна")
        self.study_info_label.setStyleSheet("color: #666666;")
        study_info_layout.addWidget(self.study_info_label)

        results_layout = QHBoxLayout()

        # Левая часть - снимок
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)

        image_label = QLabel("Проанализированный снимок")
        image_label.setStyleSheet("font-weight: bold; color: #2c5aa0;")

        self.result_image = QLabel()
        self.result_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_image.setMinimumSize(400, 400)
        self.result_image.setStyleSheet("QLabel { background-color: white; border: 1px solid #e2e8f0; border-radius: 5px; }")
        self.result_image.setText("Снимок не загружен")

        left_layout.addWidget(image_label)
        left_layout.addWidget(self.result_image)

        # Правая часть - заключение
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        conclusion_label = QLabel("Медицинское заключение")
        conclusion_label.setStyleSheet("font-weight: bold; color: #2c5aa0;")

        # Карточка результата
        self.result_card = QFrame()
        self.result_card.setStyleSheet("""
            QFrame {
                background-color: #fef2f2;
                border: 2px solid #fecaca;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        result_layout = QHBoxLayout(self.result_card)

        self.result_icon = QLabel("⚠️")
        self.result_icon.setStyleSheet("font-size: 32px;")

        result_text_layout = QVBoxLayout()
        self.result_main_text = QLabel("Ожидание анализа...")
        self.result_main_text.setStyleSheet("font-weight: bold; font-size: 18px; color: #dc2626;")

        self.result_description = QLabel("Результаты анализа появятся здесь")
        self.result_description.setStyleSheet("color: #666666;")

        result_text_layout.addWidget(self.result_main_text)
        result_text_layout.addWidget(self.result_description)

        result_layout.addWidget(self.result_icon)
        result_layout.addLayout(result_text_layout)

        # Комментарии
        comments_label = QLabel("Комментарии к анализу:")
        comments_label.setStyleSheet("font-weight: bold; color: #2c5aa0; margin-top: 10px;")

        self.comments_text = QTextEdit()
        self.comments_text.setMinimumHeight(300)
        self.comments_text.setPlaceholderText("Введите комментарий медицинского работника...")
        self.comments_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
        """)

        # Кнопки
        actions_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Сохранить заключение")
        self.save_btn.setStyleSheet("padding: 10px;")
        self.save_btn.clicked.connect(self.save_report)

        self.new_analysis_btn = QPushButton("🔄 Выбрать другой снимок")
        self.new_analysis_btn.setStyleSheet("padding: 10px;")
        self.new_analysis_btn.clicked.connect(self.new_analysis)

        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.new_analysis_btn)

        right_layout.addWidget(conclusion_label)
        right_layout.addWidget(self.result_card)
        right_layout.addWidget(comments_label)
        right_layout.addWidget(self.comments_text)
        right_layout.addLayout(actions_layout)

        results_layout.addWidget(left_frame)
        results_layout.addWidget(right_frame)

        layout.addWidget(title)
        layout.addWidget(study_info_frame)
        layout.addLayout(results_layout)

        return tab

    
    def load_sample_patients(self):
        """Загружаем тестовых пациентов"""
        self.patients = [
            {
                'id': '001', 'name': 'Иванов Алексей Петрович', 'age': 45,
                'diagnosis': 'Подозрение на перелом лучевой кости', 'status': 'Требуется анализ'
            },
            {
                'id': '002', 'name': 'Петрова Мария Сергеевна', 'age': 62,
                'diagnosis': 'Контроль после эндопротезирования тазобедренного сустава', 'status': 'Анализ завершен'
            },
            {
                'id': '003', 'name': 'Сидоров Дмитрий Иванович', 'age': 28,
                'diagnosis': 'Спортивная травма коленного сустава', 'status': 'Требуется анализ'
            },
            {
                'id': '004', 'name': 'Козлова Анна Викторовна', 'age': 35,
                'diagnosis': 'Артроз голеностопного сустава', 'status': 'Новые снимки'
            },
            {
                'id': '005', 'name': 'Николаев Владимир Александрович', 'age': 71,
                'diagnosis': 'Остеопороз, компрессионный перелом', 'status': 'Анализ завершен'
            },
            {
                'id': '006', 'name': 'Федорова Екатерина Олеговна', 'age': 52,
                'diagnosis': 'Посттравматическая деформация плечевой кости', 'status': 'Требуется анализ'
            }
        ]
        
        self.display_patients()
    
    def display_patients(self):
        
        # очищаем layout
        for i in reversed(range(self.patients_grid.count())):
            item = self.patients_grid.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)

        # фильтрация
        search_text = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        status_selected = self.status_filter.currentText() if hasattr(self, "status_filter") else "Все статусы"

        filtered = []
        for p in self.patients:
            match_search = (search_text in p['name'].lower()) or (search_text in p['id'].lower())
            if search_text and not match_search:
                continue
            if status_selected != "Все статусы" and p['status'] != status_selected:
                continue
            filtered.append(p)

        row, col = 0, 0
        for patient in filtered:
            card = PatientCard(patient, self)
            self.patients_grid.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
    
    def select_patient(self, patient_data):
        
        self.current_patient = patient_data

        self.patient_details.setText(
            f"<b>{patient_data['name']}</b><br>"
            f"Возраст: {patient_data['age']} лет<br>"
            f"Диагноз: {patient_data['diagnosis']}<br>"
            f"Статус: {patient_data['status']}"
        )

        # сброс загруженного снимка
        self.current_image_path = None
        self.upload_area.clear()
        self.upload_area.setText(
            "Снимок не загружен\n\nНажмите 'Загрузить снимок' или перетащите файл"
        )
        self.analyze_btn.setEnabled(False)

        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setCurrentIndex(1)

        self.update_patient_gallery()

    
    def update_patient_gallery(self):
        """Обновляем галлерею снимков пациента"""
        self.gallery_list.clear()
        # Здесь можно добавить загрузку реальных снимков из базы данных
        sample_images = ["Рентген правой руки (12.01.2024)", "КТ левого колена (05.01.2024)"]
        for image in sample_images:
            self.gallery_list.addItem(image)
    
    def upload_image(self):
        """Загрузка нового снимка"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите рентгеновский снимок",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_path:
            self.current_image_path = file_path
            pixmap = QPixmap(file_path)
            
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                self.upload_area.setPixmap(scaled_pixmap)
                self.analyze_btn.setEnabled(True)
                
                # Добавляем в галлерею
                filename = os.path.basename(file_path)
                self.gallery_list.addItem(f"Новый снимок: {filename}")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")
    
    def start_analysis(self):
        """Начало анализа снимка"""
        if not self.current_image_path or not self.current_patient:
            return
            
        self.progress_bar.setVisible(True)
        self.analyze_btn.setEnabled(False)
        self.status_label.setText("Подготовка к анализу...")
        
        # Имитация процесса анализа
        self.progress_bar.setValue(0)
        
        if self.analysis_timer and self.analysis_timer.isActive():
            self.analysis_timer.stop()
            
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.update_progress)
        self.analysis_timer.start(150)
    
    def update_progress(self):
        """Обновление прогресса анализа"""
        current_value = self.progress_bar.value()
        
        # Обновляем статус
        if current_value < 25:
            self.status_label.setText("Загрузка изображения...")
            increment = random.randint(5, 10)
        elif current_value < 50:
            self.status_label.setText("Предварительная обработка...")
            increment = random.randint(3, 8)
        elif current_value < 75:
            self.status_label.setText("Анализ костной структуры...")
            increment = random.randint(2, 6)
        else:
            self.status_label.setText("Формирование заключения...")
            increment = random.randint(1, 4)
        
        new_value = current_value + increment
        
        if new_value >= 100:
            self.progress_bar.setValue(100)
            self.analysis_timer.stop()
            self.status_label.setText("Анализ завершен!")
            QTimer.singleShot(500, self.show_results)
        else:
            self.progress_bar.setValue(new_value)
    
    def show_results(self):
        self.tab_widget.setTabEnabled(2, True)
        self.tab_widget.setCurrentIndex(2)

        study_date = self.study_date.date().toString("dd.MM.yyyy")

        # без диагноза
        self.study_info_label.setText(
            f"<b>Пациент:</b> {self.current_patient['name']}<br>"
            f"<b>Дата:</b> {study_date}"
        )

        if self.current_image_path:
            pixmap = QPixmap(self.current_image_path)
            scaled_pixmap = pixmap.scaled(
                400, 400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.result_image.setPixmap(scaled_pixmap)

        self.generate_analysis_results()
        self.comments_text.setPlainText("")  # очищаем комментарии при новом результате

    
    def generate_analysis_results(self):
        if not self.current_image_path:
            return
        try:
            img = Image.open(self.current_image_path).resize((224, 224)).convert('RGB')
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = np.expand_dims(img_array, 0)
            pred = self.model.predict(img_array, verbose=0)[0][0]
            has_fracture = pred > 0.5
            confidence = int(pred * 100 if has_fracture else (1 - pred) * 100)
        except Exception as e:
            print(f"Ошибка предсказания: {e}")
            has_fracture = False
            confidence = 0

        if has_fracture:
            self.result_card.setStyleSheet("""
            QFrame {
                background-color: #fef2f2;
                border: 2px solid #fecaca;
                border-radius: 8px;
                padding: 15px;
                    }
                """)
            self.result_icon.setText("⚠️")
            self.result_main_text.setText("Обнаружен перелом")
            self.result_main_text.setStyleSheet("font-weight: bold; font-size: 18px; color: #dc2626;")
            self.result_description.setText("На снимке обнаружены признаки перелома")
        else:
            self.result_card.setStyleSheet("""
                QFrame {
                    background-color: #f0fdf4;
                    border: 2px solid #bbf7d0;
                    border-radius: 8px;
                    padding: 15px;
                }
            """)
            self.result_icon.setText("✅")
            self.result_main_text.setText("Переломов не обнаружено")
            self.result_main_text.setStyleSheet("font-weight: bold; font-size: 18px; color: #16a34a;")
            self.result_description.setText("Явных признаков перелома не выявлено")

        details = self.generate_detailed_report(confidence, has_fracture)
        self.comments_text.setPlainText(details)  # было self.details_text

    
    def generate_detailed_report(self, confidence, has_fracture):
        location = random.choice(['Правая рука', 'Левая рука', 'Правая нога', 'Левая нога'])
        if has_fracture:
            status = "ПЕРЕЛОМ ОБНАРУЖЕН"
        else:
            status = "ПЕРЕЛОМОВ НЕ ОБНАРУЖЕНО"
        return f"""ЛОКАЛИЗАЦИЯ: {location}
    СТАТУС: {status}
    УВЕРЕННОСТЬ АНАЛИЗА: {confidence}%"""

    
    def get_damage_description(self, damage_type):
        """Описание повреждения"""
        descriptions = {
            "перелом лучевой кости": "Линия перелома видна в средней трети диафиза, смещение фрагментов минимальное",
            "трещина большеберцовой кости": "Линейный дефект кортикального слоя без смещения отломков",
            "вывих плечевого сустава": "Нарушение конгруэнтности суставных поверхностей, головка плеча смещена",
            "остеофиты коленного сустава": "Краевые костные разрастания в области суставных поверхностей",
            "признаки остеопороза": "Снижение плотности костной ткани, истончение кортикального слоя",
            "артроз тазобедренного сустава": "Сужение суставной щели, субхондральный остеосклероз"
        }
        return descriptions.get(damage_type, "Обнаружены изменения костной структуры, требующие уточнения")
    
    def save_report(self):
        if self.current_patient:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить заключение",
                f"заключение_{self.current_patient['name']}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("МЕДИЦИНСКОЕ ЗАКЛЮЧЕНИЕ\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Пациент: {self.current_patient['name']}\n")
                        f.write(f"Результат: {self.result_main_text.text()}\n")
                        f.write(f"Описание: {self.result_description.text()}\n\n")
                        f.write("КОММЕНТАРИИ МЕДИЦИНСКОГО РАБОТНИКА:\n")
                        f.write(self.comments_text.toPlainText())
                    QMessageBox.information(self, "Успех", "Заключение успешно сохранено!")
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить заключение: {str(e)}")

    
    def new_analysis(self):
        self.tab_widget.setCurrentIndex(1)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
        self.analyze_btn.setEnabled(False)
        self.comments_input.clear()
        self.comments_text.clear() 
        self.current_image_path = None
        self.upload_area.clear()
        self.upload_area.setText(
            "Снимок не загружен\n\nНажмите 'Загрузить снимок' или перетащите файл"
        )



def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MedicalApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()