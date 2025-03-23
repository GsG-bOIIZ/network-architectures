#!/usr/bin/env python3
import sys, os, json, hashlib, random, base64, datetime
from collections import defaultdict
from cryptography.fernet import Fernet

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QDialog,
    QLabel, QLineEdit, QComboBox, QListWidget, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, QAbstractItemView,
    QButtonGroup, QRadioButton, QFileDialog, QTextEdit, QMenuBar, QAction,
    QTabWidget, QSplitter, QGridLayout, QSpacerItem, QSizePolicy, QScrollArea, QLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

# ===================== Глобальные стили =====================
GLOBAL_FONT_FAMILY = "Segoe UI"
BASE_FONT_SIZE = "14pt"
HEADER_FONT_SIZE = "20pt"

base_style = f"""
    font-family: "{GLOBAL_FONT_FAMILY}";
    font-size: {BASE_FONT_SIZE};
    color: #2b2b2b;
    background: #fff;
    border: solid;
"""

header_style = f"""
    font-family: "{GLOBAL_FONT_FAMILY}";
    font-size: {HEADER_FONT_SIZE};
    color: #2b2b2b;
    font-weight: bold;
"""

label_style = f"""
    QLabel {{
        {base_style}
        padding: 5px;
    }}
"""

combobox_style = f"""
    QComboBox {{
        {base_style}
        padding: 9px;
        border: 2px solid #000;
        border-radius: 5px;
        background-color: #ffffff;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 2px solid #000;
        background: #fff;
    }}
    QComboBox QAbstractItemView {{
        {base_style}
        background-color: #ffffff;
        border: 2px solid #000;
        selection-background-color: #d9d9d9;
    }}
"""

tablewidget_style = f"""
    QTableWidget {{
        {base_style}
        font-size: 12pt;
        background-color: #ffffff;
        gridline-color: #000;
        border: 2px solid #000;
        padding: 10px;
    }}
    QHeaderView::section {{
        {header_style}
        background-color: #f7f7f7;
        padding: 10px;
        border: 2px solid #000;
    }}
"""

button_style = f"""
    QPushButton {{
        {base_style}
        background-color: #fff;
        border: 2px solid;
        padding: 10px;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background-color: #aeaeae;
    }}
"""

button_not_enable = f"""
    QPushButton {{
        {base_style}
        border: 2px solid;
        padding: 10px;
        border-radius: 5px;
        background-color: #aeaeae;
    }}
"""

radiobutton_style = f"""
    QRadioButton {{
        {base_style}
        padding: 5px;
    }}
"""

checkbox_style = f"""
    QCheckBox {{
        {base_style}
        padding: 5px;
    }}
"""

lineedit_style = f"""
    QLineEdit {{
        {base_style}
        padding: 10px;
        border: 2px solid #000;
        border-radius: 5px;
        background-color: #ffffff;
    }}
"""

q_message_box = f"""
    QMessageBox {{
        background-color: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #A4D4F9, stop: 1 #005392
        );
        font-size: {BASE_FONT_SIZE};
    }}
    QMessageBox QLabel {{
        color: #000; /* Цвет текста */
        font-weight: bold;
        background: #fff;
    }}
    QMessageBox QPushButton {{
        background-color: #fff;
        font-size: 20px;
        color: #000000;
        border: 2px solid #000;
        padding: 10px;
        border-radius: 5px;
    }}
    QMessageBox QPushButton:hover {{
        background-color: #aeaeae; /* Цвет кнопки при наведении */
    }}
"""

filter_style = f"""
    {base_style}
    background-color: #fff;
    border: 2px solid;
    padding: 10px;
    border-radius: 5px;
"""

class ZoomableLabel(QLabel):
    def __init__(self, pixmap, parent=None):
        super(ZoomableLabel, self).__init__(parent)
        self.originalPixmap = pixmap
        self.zoomFactor = 1.0
        self.setPixmap(self.originalPixmap)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self.flag = True
    
    def mousePressEvent(self, event):
        # Увеличиваем изображение при каждом нажатии на 10%
        if self.flag:
            self.flag = False
            self.zoomFactor *= 2.0
            new_width = int(self.originalPixmap.width() * self.zoomFactor)
            new_height = int(self.originalPixmap.height() * self.zoomFactor)
            self.setPixmap(self.originalPixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.flag = True
            self.zoomFactor *= 0.5
            new_width = int(self.originalPixmap.width() * self.zoomFactor)
            new_height = int(self.originalPixmap.height() * self.zoomFactor)
            self.setPixmap(self.originalPixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.originalPixmap = None  # Хранит оригинальное изображение

    def mousePressEvent(self, event):
        if self.originalPixmap:
            self.open_enlarged_image()

    def open_enlarged_image(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Просмотр изображения")
        dialog.setWindowState(Qt.WindowMaximized)  # Открываем окно в максимизированном режиме
        layout = QVBoxLayout(dialog)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Контейнер с выравниванием по центру
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # Используем ZoomableLabel, который позволяет увеличивать изображение при нажатии
        zoom_label = ZoomableLabel(self.originalPixmap)
        container_layout.addWidget(zoom_label)
        
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        
        dialog.exec_()


# ===================== Функции хэширования пароля =====================
def hash_password(password, salt="some_salt"):
    return hashlib.sha256((salt+password).encode()).hexdigest()

def check_password(input_password, stored_hash, salt="some_salt"):
    return hash_password(input_password, salt) == stored_hash

# ===================== Менеджер данных =====================
ENCRYPTION_KEY = b'k_Nm-GI6e-d9U8i8JSGpWn9VZNU3ZQq2gVJXZ32XZxg='

class DataManager:
    def __init__(self, filename="data.enc"):
        self.filename = filename
        self.key = ENCRYPTION_KEY
        self.fernet = Fernet(self.key)
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            default_password = "admin"
            hashed = hash_password(default_password)
            data = {"password": hashed, "tests": [], "results_path": os.path.abspath("results"), "theme": "light"}
            self.save_data(data)
            if not os.path.exists(data["results_path"]):
                os.makedirs(data["results_path"])
            return data
        else:
            with open(self.filename, "rb") as f:
                encrypted_data = f.read()
            try:
                decrypted_data = self.fernet.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
                if "results_path" not in data:
                    data["results_path"] = os.path.abspath("results")
                if "theme" not in data:
                    data["theme"] = "light"
                if not os.path.exists(data["results_path"]):
                    os.makedirs(data["results_path"])
                return data
            except Exception as e:
                print("Ошибка расшифровки данных:", e)
                return {"password": "", "tests": [], "results_path": os.path.abspath("results"), "theme": "light"}

    def save_data(self, data):
        data_json = json.dumps(data, ensure_ascii=False).encode()
        encrypted_data = self.fernet.encrypt(data_json)
        with open(self.filename, "wb") as f:
            f.write(encrypted_data)
        self.data = data

data_manager = DataManager()

# ===================== Менеджер результатов тестов =====================
class ResultManager:
    def __init__(self, results_path):
        self.results_path = results_path
        self.key = ENCRYPTION_KEY
        self.fernet = Fernet(self.key)
        
    def save_result(self, result_data):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = os.path.join(self.results_path, f"TEST-{timestamp}.enc")
        data_json = json.dumps(result_data, ensure_ascii=False, indent=2).encode()
        encrypted_data = self.fernet.encrypt(data_json)
        with open(filename, "wb") as f:
            f.write(encrypted_data)
    
    def load_result(self, filepath):
        with open(filepath, "rb") as f:
            encrypted_data = f.read()
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Не удалось расшифровать файл:\n{e} </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()
            return None

# ===================== Диалоги =====================
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("Вход в режим редактирования")
        layout = QVBoxLayout()
        self.label = QLabel("Введите пароль:")
        self.label.setStyleSheet(label_style)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet(lineedit_style)
        self.ok_button = QPushButton("ОК")
        self.ok_button.setStyleSheet(button_style)
        self.ok_button.clicked.connect(self.check_password)
        layout.addWidget(self.label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)
        self.accepted = False

    def check_password(self):
        input_password = self.password_edit.text()
        stored_hash = data_manager.data.get("password", "")
        if check_password(input_password, stored_hash):
            self.accepted = True
            self.accept()
        else:
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Неверный пароль! </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super(ChangePasswordDialog, self).__init__(parent)
        self.setWindowTitle("Сменить пароль")
        layout = QVBoxLayout()
        self.current_label = QLabel("Текущий пароль:")
        self.current_label.setStyleSheet(label_style)
        self.current_edit = QLineEdit()
        self.current_edit.setEchoMode(QLineEdit.Password)
        self.current_edit.setStyleSheet(lineedit_style)
        self.new_label = QLabel("Новый пароль:")
        self.new_label.setStyleSheet(label_style)
        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.Password)
        self.new_edit.setStyleSheet(lineedit_style)
        self.confirm_label = QLabel("Подтвердите новый пароль:")
        self.confirm_label.setStyleSheet(label_style)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setStyleSheet(lineedit_style)
        self.ok_button = QPushButton("Сменить пароль")
        self.ok_button.setStyleSheet(button_style)
        self.ok_button.clicked.connect(self.change_password)
        layout.addWidget(self.current_label)
        layout.addWidget(self.current_edit)
        layout.addWidget(self.new_label)
        layout.addWidget(self.new_edit)
        layout.addWidget(self.confirm_label)
        layout.addWidget(self.confirm_edit)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def change_password(self):
        current = self.current_edit.text()
        new = self.new_edit.text()
        confirm = self.confirm_edit.text()
        stored_hash = data_manager.data.get("password", "")
        if not check_password(current, stored_hash):
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Неверный текущий пароль! </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()
            return
        if new != confirm or not new:
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Новый пароль и подтверждение не совпадают или пусты! </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()
            return
        data_manager.data["password"] = hash_password(new)
        data_manager.save_data(data_manager.data)
        msg_box = QMessageBox()
        msg_box.setStyleSheet(q_message_box)
        msg_box.setWindowTitle("Успех")
        msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Пароль успешно изменён! </p> ")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
        msg_box.exec_()
        self.accept()

class StudentLoginDialog(QDialog):
    def __init__(self, parent=None):
        super(StudentLoginDialog, self).__init__(parent)
        self.setWindowTitle("Вход студента")
        layout = QVBoxLayout()
        self.label = QLabel("Введите ваше имя:")
        self.label.setStyleSheet(label_style)
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(lineedit_style)
        self.ok_button = QPushButton("Начать тест")
        self.ok_button.setStyleSheet(button_style)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.label)
        layout.addWidget(self.name_edit)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)
    
    def get_name(self):
        return self.name_edit.text().strip()

class TestSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super(TestSelectionDialog, self).__init__(parent)
        self.setWindowTitle("Выбор теста")
        layout = QVBoxLayout()
        self.test_list = QListWidget()
        self.test_list.setStyleSheet(f"""
            QListWidget {{
                {base_style}
                padding: 5px;
                background-color: #fff;
                border: 2px solid #000;
                border-radius: 5px;
            }}
        """)
        self.load_tests()
        self.select_button = QPushButton("Выбрать")
        self.select_button.setStyleSheet(button_style)
        self.select_button.clicked.connect(self.select_test)
        layout.addWidget(self.test_list)
        layout.addWidget(self.select_button)
        self.setLayout(layout)
        self.selected_test = None

    def load_tests(self):
        self.test_list.clear()
        self.test_list.addItem("Итоговый тест")
        tests = data_manager.data.get("tests", [])
        for test in tests:
            self.test_list.addItem(test.get("topic", "Без темы"))

    def select_test(self):
        current_row = self.test_list.currentRow()
        if current_row >= 0:
            if current_row == 0:
                # Формируем итоговый тест: для каждого теста берем 3 случайных вопроса (или все, если вопросов меньше 3)
                final_questions = []
                for test in data_manager.data.get("tests", []):
                    questions = test.get("questions", [])
                    if len(questions) <= 3:
                        final_questions.extend(questions)
                    else:
                        final_questions.extend(random.sample(questions, 3))
                # Перемешиваем итоговые вопросы
                random.shuffle(final_questions)
                self.selected_test = {"topic": "Итоговый тест", "questions": final_questions}
            else:
                # Индексы смещены: первый пункт – Итоговый тест, остальные соответствуют данным
                self.selected_test = data_manager.data["tests"][current_row - 1]
            self.accept()
        else:
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Выберите тест! </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()

# ===================== Окно проведения теста =====================
class TestWindow(QDialog):
    def __init__(self, test_data, student_name, parent=None):
        super(TestWindow, self).__init__(parent)
        self.test_data = test_data  # Добавляем сохранение данных теста
        self.setWindowTitle(f"Тест: {test_data.get('topic','')}")
        self.setMinimumSize(1280, 720)
        # Получаем список вопросов и перемешиваем его
        self.questions = test_data.get("questions", [])
        random.shuffle(self.questions)
        self.total_questions = len(self.questions)
        self.question_order = []
        for q in self.questions:
            order = list(range(len(q.get("answers", []))))
            random.shuffle(order)
            self.question_order.append(order)
        self.user_answers = [None] * self.total_questions
        self.current_index = 0
        self.student_name = student_name

        self.layout = QVBoxLayout()
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Предыдущий")
        self.prev_button.setStyleSheet(button_style)
        self.prev_button.clicked.connect(self.go_prev)
        self.nav_combo = QComboBox()
        self.nav_combo.setStyleSheet(combobox_style)
        self.nav_combo.addItems([f"Вопрос {i+1}" for i in range(self.total_questions)])
        self.nav_combo.currentIndexChanged.connect(self.on_nav_change)
        self.next_button = QPushButton("Следующий")
        self.next_button.setStyleSheet(button_style)
        self.next_button.clicked.connect(self.go_next)
        self.finish_button = QPushButton("Завершить тест")
        self.finish_button.setStyleSheet(button_style)
        self.finish_button.clicked.connect(self.finish_test_clicked)
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.nav_combo)
        self.nav_layout.addWidget(self.next_button)
        self.nav_layout.addWidget(self.finish_button)
        self.layout.addLayout(self.nav_layout)

        # Используем кликабельную метку для изображения вопроса
        self.question_image_label = ClickableLabel()
        self.question_image_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.question_image_label)
        self.question_label = QLabel()
        self.question_label.setStyleSheet(f"""
            QLabel {{
                {header_style}
                padding: 10px;
                border: 2px solid #aeaeae;
                border-radius: 8px;
                background-color: #f7f7f7;
            }}
        """)
        self.layout.addWidget(self.question_label)

        self.answers_widget = QWidget()
        self.answers_layout = QVBoxLayout()
        self.answers_widget.setLayout(self.answers_layout)
        self.layout.addWidget(self.answers_widget)

        self.setLayout(self.layout)
        self.current_answer_widgets = []
        self.show_question()

    def save_current_answer(self):
        if self.total_questions == 0:
            return
        question = self.questions[self.current_index]
        if question.get("type") == "single":
            selected = None
            for rb in self.current_answer_widgets:
                if rb.isChecked():
                    selected = rb.original_index
                    break
            self.user_answers[self.current_index] = selected
        elif question.get("type") == "multiple":
            total = len(question.get("answers", []))
            selection = [False] * total
            for cb in self.current_answer_widgets:
                if cb.isChecked():
                    selection[cb.original_index] = True
            self.user_answers[self.current_index] = selection

    def restore_answer(self):
        ans = self.user_answers[self.current_index]
        if ans is None:
            return
        question = self.questions[self.current_index]
        if question.get("type") == "single":
            for rb in self.current_answer_widgets:
                if rb.original_index == ans:
                    rb.setChecked(True)
        elif question.get("type") == "multiple":
            for cb in self.current_answer_widgets:
                if ans[cb.original_index]:
                    cb.setChecked(True)

    def show_question(self):
        if self.current_index < self.total_questions:
            question = self.questions[self.current_index]
            order = self.question_order[self.current_index]
            if question.get("image"):
                data = base64.b64decode(question["image"])
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                # Отображаем уменьшенную версию для вопроса
                self.question_image_label.setPixmap(pixmap.scaledToWidth(300, Qt.SmoothTransformation))
                # Сохраняем оригинальное изображение для увеличенного просмотра
                self.question_image_label.originalPixmap = pixmap
            else:
                self.question_image_label.clear()
                self.question_image_label.originalPixmap = None  # Обязательно сбрасываем originalPixmap
            self.question_label.setText(f"Вопрос {self.current_index+1}: {question.get('question','')}")
            # Очистка старых виджетов ответов
            for i in reversed(range(self.answers_layout.count())):
                widget = self.answers_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            self.current_answer_widgets = []
            answers = question.get("answers", [])
            if question.get("type") == "single":
                self.button_group = QButtonGroup(self)
                for orig_idx in order:
                    answer = answers[orig_idx]
                    container = QWidget()
                    container_layout = QHBoxLayout()
                    container_layout.setContentsMargins(5, 5, 5, 5)
                    rb = QRadioButton(answer.get("text", ""))
                    rb.setStyleSheet(radiobutton_style)
                    rb.original_index = orig_idx
                    rb.correct = answer.get("correct", False)
                    self.button_group.addButton(rb)
                    container_layout.addWidget(rb)
                    if answer.get("image"):
                        data = base64.b64decode(answer["image"])
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        img_label = ClickableLabel()
                        img_label.setAlignment(Qt.AlignCenter)
                        # Отображаем уменьшенную версию для ответа
                        img_label.setPixmap(pixmap.scaledToWidth(100, Qt.SmoothTransformation))
                        img_label.originalPixmap = pixmap  # Сохраняем оригинал для увеличения
                        container_layout.addWidget(img_label)
                    else:
                        # Если изображения нет, убедимся, что originalPixmap сброшен
                        pass
                    container.setLayout(container_layout)
                    container.setStyleSheet(f"""
                        QWidget {{
                            border: 1px solid #d9d9d9;
                            border-radius: 5px;
                            margin-bottom: 5px;
                            background-color: #ffffff;
                        }}
                    """)
                    self.answers_layout.addWidget(container)
                    self.current_answer_widgets.append(rb)
            elif question.get("type") == "multiple":
                for orig_idx in order:
                    answer = answers[orig_idx]
                    container = QWidget()
                    container_layout = QHBoxLayout()
                    container_layout.setContentsMargins(5, 5, 5, 5)
                    cb = QCheckBox(answer.get("text", ""))
                    cb.setStyleSheet(checkbox_style)
                    cb.original_index = orig_idx
                    cb.correct = answer.get("correct", False)
                    cb.penalty = float(answer.get("penalty", 0))
                    container_layout.addWidget(cb)
                    if answer.get("image"):
                        data = base64.b64decode(answer["image"])
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        img_label = ClickableLabel()
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setPixmap(pixmap.scaledToWidth(100, Qt.SmoothTransformation))
                        img_label.originalPixmap = pixmap
                        container_layout.addWidget(img_label)
                    container.setLayout(container_layout)
                    container.setStyleSheet(f"""
                        QWidget {{
                            border: 1px solid #d9d9d9;
                            border-radius: 5px;
                            margin-bottom: 5px;
                            background-color: #ffffff;
                        }}
                    """)
                    self.answers_layout.addWidget(container)
                    self.current_answer_widgets.append(cb)
            self.restore_answer()
            self.update_nav_controls()
        else:
            self.finish_test()


    def update_nav_controls(self):
        self.nav_combo.blockSignals(True)
        self.nav_combo.setCurrentIndex(self.current_index)
        self.nav_combo.blockSignals(False)
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < self.total_questions - 1)
        if (self.current_index >= self.total_questions - 1):
            self.next_button.setStyleSheet(button_not_enable)
        else: 
            self.next_button.setStyleSheet(button_style)
        if (self.current_index == 0):
            self.prev_button.setStyleSheet(button_not_enable)
        else:
            self.prev_button.setStyleSheet(button_style)


    def on_nav_change(self, index):
        if index == self.current_index:
            return
        self.save_current_answer()
        self.current_index = index
        self.show_question()

    def go_prev(self):
        if self.current_index > 0:
            self.save_current_answer()
            self.current_index -= 1
            self.show_question()

    def go_next(self):
        if self.current_index < self.total_questions - 1:
            self.save_current_answer()
            self.current_index += 1
            self.show_question()

    def finish_test_clicked(self):
        self.save_current_answer()
        missing = []
        for i, question in enumerate(self.questions):
            ans = self.user_answers[i]
            if question.get("type") == "single":
                if ans is None:
                    missing.append(i+1)
            elif question.get("type") == "multiple":
                if ans is None or (isinstance(ans, list) and not any(ans)):
                    missing.append(i+1)
        if missing:
            msg = "Следующие вопросы не имеют ни одного ответа:<br><strong>" + ", ".join(map(str, missing)) + "</strong><br>Заполните их!"

            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)  # Применяем стили
            msg_box.setWindowTitle("Внимание")  # Устанавливаем заголовок окна
            msg_box.setText(f"""
                <p style='color: black; font-family: "Segoe UI", Arial, sans-serif; font-size: 14pt;'>
                    {msg}
                </p>
            """)

            ok_button = msg_box.addButton("ОК", QMessageBox.AcceptRole)
            ok_button.setStyleSheet(q_message_box)  # Применяем стили к кнопке

            msg_box.exec_()

            if msg_box.clickedButton() == ok_button:
                return
        self.finish_test()

    def finish_test(self):
        total_score = 0
        detailed_results = []
        for i, question in enumerate(self.questions):
            q_text = question.get("question", "")
            q_score = 0
            answers = question.get("answers", [])
            if question.get("type") == "single":
                correct_idx = None
                for idx, ans in enumerate(answers):
                    if ans.get("correct", False):
                        correct_idx = idx
                        break
                user_ans = self.user_answers[i]
                q_score = 1 if user_ans == correct_idx else 0
                correct_answer = answers[correct_idx]["text"] if correct_idx is not None and correct_idx < len(answers) else "Нет правильного ответа"
                detailed_results.append({
                    "question": q_text,
                    "correct_answer": correct_answer,
                    "user_answer": answers[user_ans]["text"] if user_ans is not None and user_ans < len(answers) else "Нет ответа",
                    "score": q_score
                })
            elif question.get("type") == "multiple":
                total_correct = sum(1 for ans in answers if ans.get("correct", False))
                correct_weight = 1/total_correct if total_correct else 0
                raw_score = 0
                user_selection = self.user_answers[i] if self.user_answers[i] is not None else [False]*len(answers)
                correct_selected = 0
                for idx, selected in enumerate(user_selection):
                    if selected:
                        if answers[idx].get("correct", False):
                            raw_score += correct_weight
                            correct_selected += 1
                        else:
                            raw_score -= float(answers[idx].get("penalty", 0))
                if correct_selected > 0 and raw_score < correct_weight:
                    raw_score = correct_weight
                q_score = max(0, min(raw_score, 1))
                correct_answer = ", ".join([ans["text"] for ans in answers if ans.get("correct", False)])
                detailed_results.append({
                    "question": q_text,
                    "correct_answer": correct_answer,
                    "user_answer": [answers[idx]["text"] for idx, selected in enumerate(user_selection) if selected],
                    "score": q_score
                })
            total_score += q_score
        percent = (total_score / self.total_questions) * 100 if self.total_questions else 0
        
        msg_box = QMessageBox()
        msg_box.setStyleSheet(q_message_box)  # Применяем стили
        msg_box.setWindowTitle("Результаты")  # Устанавливаем заголовок окна

        message_text = f"""
            <p style='color: black; font-family: "Segoe UI", Arial, sans-serif; font-size: 14pt;'>
                Ваш суммарный балл: <strong>{total_score:.2f}</strong> из <strong>{self.total_questions}</strong><br>
                Успешность: <strong>{percent:.0f}%</strong>
            </p>
        """
        msg_box.setText(message_text)  # Устанавливаем HTML-текст
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
        msg_box.exec_()
       
        result_data = {
            "student": self.student_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "test_topic": self.test_data.get("topic", ""),
            "results": detailed_results,
            "total_score": total_score,
            "total_questions": self.total_questions,
            "percent": percent
        }
        results_path = data_manager.data.get("results_path", os.path.abspath("results"))
        rm = ResultManager(results_path)
        rm.save_result(result_data)
        self.accept()

# ===================== Диалог добавления теста =====================
class AddTestDialog(QDialog):
    def __init__(self, parent=None):
        super(AddTestDialog, self).__init__(parent)
        self.setWindowTitle("Добавить тест")
        layout = QVBoxLayout()
        self.label = QLabel("Название теста:")
        self.label.setStyleSheet(label_style)
        self.topic_edit = QLineEdit()
        self.topic_edit.setStyleSheet(lineedit_style)
        self.ok_button = QPushButton("Добавить")
        self.ok_button.setStyleSheet(button_style)
        self.ok_button.clicked.connect(self.add_test)
        layout.addWidget(self.label)
        layout.addWidget(self.topic_edit)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)
        self.topic = None

    def add_test(self):
        topic = self.topic_edit.text().strip()
        if topic:
            self.topic = topic
            self.accept()
        else:
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Введите название теста! </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()

# ===================== Диалог добавления/редактирования вопроса =====================
class AddQuestionDialog(QDialog):
    def __init__(self, question_data=None, parent=None):
        super(AddQuestionDialog, self).__init__(parent)
        self.setWindowTitle("Добавить вопрос" if question_data is None else "Редактировать вопрос")
        self.setMinimumSize(1200, 700)
        self.question_data = question_data
        self.question_image_data = None  
        layout = QVBoxLayout()

        self.question_label = QLabel("Текст вопроса:")
        self.question_label.setStyleSheet(label_style)
        self.question_edit = QLineEdit()
        self.question_edit.setStyleSheet(lineedit_style)
        layout.addWidget(self.question_label)
        layout.addWidget(self.question_edit)

        self.question_image_button = QPushButton("Прикрепить изображение")
        self.question_image_button.setStyleSheet(button_style)
        self.question_image_button.clicked.connect(self.choose_question_image)
        layout.addWidget(self.question_image_button)

        self.type_label = QLabel("Тип вопроса:")
        self.type_label.setStyleSheet(label_style)
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(combobox_style)
        self.type_combo.addItems(["Один правильный", "Несколько правильных"])
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combo)

        self.answers_table = QTableWidget()
        self.answers_table.setStyleSheet(tablewidget_style)
        self.answers_table.setColumnCount(4)
        self.answers_table.setHorizontalHeaderLabels(["Ответ", "Правильный", "Штраф", "Изображение"])
        self.answers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Растянуть первый столбец
        self.answers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Подогнать второй столбец по содержимому
        self.answers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Подогнать третий столбец по содержимому
        self.answers_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Подогнать четвертый столбец по содержимому
        self.answers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.answers_table)

        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("Добавить ответ")
        self.add_row_btn.setStyleSheet(button_style)
        self.add_row_btn.clicked.connect(lambda: self.add_row())
        self.remove_row_btn = QPushButton("Удалить выбранный ответ")
        self.remove_row_btn.setStyleSheet(button_style)
        self.remove_row_btn.clicked.connect(self.remove_row)
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.remove_row_btn)
        layout.addLayout(btn_layout)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet(button_style)
        self.save_btn.clicked.connect(self.save_question)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setStyleSheet(button_style)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)
        if question_data:
            self.load_question_data()

    def choose_question_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if filename:
            with open(filename, "rb") as f:
                data = f.read()
            self.question_image_data = base64.b64encode(data).decode("utf-8")
            self.question_image_button.setText("Изменить изображение")

    def choose_answer_image(self, btn):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if filename:
            with open(filename, "rb") as f:
                data = f.read()
            btn.imageData = base64.b64encode(data).decode("utf-8")
            btn.setText("Изменить изображение")

    def load_question_data(self):
        self.question_edit.setText(self.question_data.get("question", ""))
        if self.question_data.get("image"):
            self.question_image_data = self.question_data.get("image")
            self.question_image_button.setText("Изменить изображение")
        qtype = self.question_data.get("type", "single")
        self.type_combo.setCurrentIndex(0 if qtype=="single" else 1)
        answers = self.question_data.get("answers", [])
        self.answers_table.setRowCount(0)
        for ans in answers:
            self.add_row(ans.get("text", ""), ans.get("correct", False), ans.get("penalty", 0), ans.get("image", ""))

    def add_row(self, text="", correct=False, penalty=0, answer_image=""):
        row = self.answers_table.rowCount()
        self.answers_table.insertRow(row)
        item = QTableWidgetItem(text)
        self.answers_table.setItem(row, 0, item)
        checkbox = QCheckBox()
        checkbox.setChecked(correct)
        checkbox.setStyleSheet(checkbox_style)
        self.answers_table.setCellWidget(row, 1, checkbox)
        penalty_combo = QComboBox()
        penalty_combo.setStyleSheet(combobox_style)
        penalty_values = ["0", "0.2", "0.33", "0.4", "0.5", "0.6", "0.67", "0.8", "1"]
        penalty_combo.addItems(penalty_values)
        try:
            penalty_str = "{:.2f}".format(float(penalty)).rstrip("0").rstrip(".")
            if penalty_str == "":
                penalty_str = "0"
            index = penalty_values.index(penalty_str)
        except ValueError:
            index = 0
        penalty_combo.setCurrentIndex(index)
        self.answers_table.setCellWidget(row, 2, penalty_combo)
        image_button = QPushButton("Прикрепить изображение")
        image_button.setStyleSheet(button_style)
        image_button.clicked.connect(lambda _, btn=image_button: self.choose_answer_image(btn))
        image_button.imageData = answer_image
        if answer_image:
            image_button.setText("Изменить изображение")
        self.answers_table.setCellWidget(row, 3, image_button)
        for i in range(self.answers_table.rowCount()):
            self.answers_table.setRowHeight(i, 50)

    def remove_row(self):
        indices = self.answers_table.selectionModel().selectedRows()
        for index in sorted(indices, reverse=True):
            self.answers_table.removeRow(index.row())

    def save_question(self):
        question_text = self.question_edit.text().strip()
        if not question_text:
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Введите текст вопроса! </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()
            return
        qtype = "single" if self.type_combo.currentIndex() == 0 else "multiple"
        answers = []
        for row in range(self.answers_table.rowCount()):
            answer_item = self.answers_table.item(row, 0)
            if answer_item:
                answer_text = answer_item.text().strip()
                checkbox = self.answers_table.cellWidget(row, 1)
                correct = checkbox.isChecked() if checkbox else False
                penalty_combo = self.answers_table.cellWidget(row, 2)
                try:
                    penalty_val = float(penalty_combo.currentText())
                except Exception:
                    penalty_val = 0
                image_button = self.answers_table.cellWidget(row, 3)
                answer_image = image_button.imageData if hasattr(image_button, "imageData") else ""
                if answer_text:
                    answers.append({
                        "text": answer_text,
                        "correct": correct,
                        "penalty": penalty_val,
                        "image": answer_image
                    })
        if len(answers) < 2:
            msg_box = QMessageBox()
            msg_box.setStyleSheet(q_message_box)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Должно быть минимум два ответа! </p> ")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
            msg_box.exec_()
            return
        if qtype == "single":
            correct_count = sum(1 for ans in answers if ans["correct"])
            if correct_count != 1:
                msg_box = QMessageBox()
                msg_box.setStyleSheet(q_message_box)
                msg_box.setWindowTitle("Ошибка")
                msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'>Для вопроса с одним правильным ответом должен быть ровно один правильный вариант! </p> ")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
                msg_box.exec_()
                return
        self.question_result = {
            "question": question_text,
            "type": qtype,
            "answers": answers,
            "image": self.question_image_data if self.question_image_data else ""
        }
        self.accept()

# ===================== Виджет редактирования тестов =====================
class TestEditingTab(QWidget):
    def __init__(self, parent=None):
        super(TestEditingTab, self).__init__(parent)
        layout = QVBoxLayout(self)
        splitter_main = QSplitter(Qt.Vertical)
        layout.addWidget(splitter_main)

        # Верхний сплиттер: список тестов и вопросов
        top_splitter = QSplitter(Qt.Horizontal)
        self.tests_list = QListWidget()
        self.tests_list.setStyleSheet(f"""
            QListWidget {{
                {base_style}
                padding: 5px;
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 5px;
            }}
        """)
        self.tests_list.itemClicked.connect(self.load_questions)
        top_splitter.addWidget(self.tests_list)
        self.questions_list = QListWidget()
        self.questions_list.setStyleSheet(f"""
            QListWidget {{
                {base_style}
                padding: 5px;
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 5px;
            }}
        """)
        top_splitter.addWidget(self.questions_list)
        splitter_main.addWidget(top_splitter)

        # Нижняя панель с кнопками
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addStretch()

        vbox_left = QVBoxLayout()
        self.add_test_btn = QPushButton("Добавить тест")
        self.add_test_btn.setStyleSheet(button_style)
        self.add_test_btn.clicked.connect(self.add_test)
        self.delete_test_btn = QPushButton("Удалить тест")
        self.delete_test_btn.setStyleSheet(button_style)
        self.delete_test_btn.clicked.connect(self.delete_test)
        vbox_left.addWidget(self.add_test_btn)
        vbox_left.addWidget(self.delete_test_btn)

        vbox_center = QVBoxLayout()
        self.add_question_btn = QPushButton("Добавить вопрос")
        self.add_question_btn.setStyleSheet(button_style)
        self.add_question_btn.clicked.connect(self.add_question)
        self.delete_question_btn = QPushButton("Удалить вопрос")
        self.delete_question_btn.setStyleSheet(button_style)
        self.delete_question_btn.clicked.connect(self.delete_question)
        self.edit_question_btn = QPushButton("Редактировать вопрос")
        self.edit_question_btn.setStyleSheet(button_style)
        self.edit_question_btn.clicked.connect(self.edit_question)
        vbox_center.addWidget(self.add_question_btn)
        vbox_center.addWidget(self.delete_question_btn)
        vbox_center.addWidget(self.edit_question_btn)

        vbox_right = QVBoxLayout()
        self.change_password_btn = QPushButton("Сменить пароль")
        self.change_password_btn.setStyleSheet(button_style)
        self.change_password_btn.clicked.connect(self.change_password)
        vbox_right.addWidget(self.change_password_btn)

        vbox_far_right = QVBoxLayout()
        self.set_results_path_btn = QPushButton("Изменить путь сохранения результатов")
        self.set_results_path_btn.setStyleSheet(button_style)
        self.set_results_path_btn.clicked.connect(self.set_results_path)
        vbox_far_right.addWidget(self.set_results_path_btn)

        buttons_layout.addLayout(vbox_left)
        buttons_layout.addSpacing(20)
        buttons_layout.addLayout(vbox_center)
        buttons_layout.addSpacing(20)
        buttons_layout.addLayout(vbox_right)
        buttons_layout.addSpacing(20)
        buttons_layout.addLayout(vbox_far_right)
        buttons_layout.addStretch()
        splitter_main.addWidget(buttons_widget)

        self.load_tests()

    def load_tests(self):
        self.tests_list.clear()
        tests = data_manager.data.get("tests", [])
        for test in tests:
            self.tests_list.addItem(test.get("topic", "Без темы"))
        self.questions_list.clear()

    def load_questions(self):
        current_row = self.tests_list.currentRow()
        if current_row >= 0:
            test = data_manager.data["tests"][current_row]
            self.questions_list.clear()
            for q in test.get("questions", []):
                self.questions_list.addItem(q.get("question", ""))
    
    def add_test(self):
        dialog = AddTestDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_test = {"topic": dialog.topic, "questions": []}
            data_manager.data["tests"].append(new_test)
            data_manager.save_data(data_manager.data)
            self.load_tests()

    def delete_test(self):
        current_row = self.tests_list.currentRow()
        if current_row >= 0:
            confirm = QMessageBox.question(self, "Подтверждение", "Удалить выбранный тест?")
            if confirm == QMessageBox.Yes:
                del data_manager.data["tests"][current_row]
                data_manager.save_data(data_manager.data)
                self.load_tests()

    def add_question(self):
        current_test_index = self.tests_list.currentRow()
        if current_test_index < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите тест!")
            return
        dialog = AddQuestionDialog(None, self)
        if dialog.exec_() == QDialog.Accepted:
            question = dialog.question_result
            data_manager.data["tests"][current_test_index].setdefault("questions", []).append(question)
            data_manager.save_data(data_manager.data)
            self.load_questions()

    def delete_question(self):
        current_test_index = self.tests_list.currentRow()
        current_question_index = self.questions_list.currentRow()
        if current_test_index < 0 or current_question_index < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите вопрос для удаления!")
            return
        confirm = QMessageBox.question(self, "Подтверждение", "Удалить выбранный вопрос?")
        if confirm == QMessageBox.Yes:
            del data_manager.data["tests"][current_test_index]["questions"][current_question_index]
            data_manager.save_data(data_manager.data)
            self.load_questions()

    def edit_question(self):
        current_test_index = self.tests_list.currentRow()
        current_question_index = self.questions_list.currentRow()
        if current_test_index < 0 or current_question_index < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите вопрос для редактирования!")
            return
        question_data = data_manager.data["tests"][current_test_index]["questions"][current_question_index]
        dialog = AddQuestionDialog(question_data, self)
        if dialog.exec_() == QDialog.Accepted:
            data_manager.data["tests"][current_test_index]["questions"][current_question_index] = dialog.question_result
            data_manager.save_data(data_manager.data)
            self.load_questions()

    def change_password(self):
        dialog = ChangePasswordDialog(self)
        dialog.exec_()

    def set_results_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию для сохранения результатов")
        if directory:
            data_manager.data["results_path"] = directory
            data_manager.save_data(data_manager.data)
            QMessageBox.information(self, "Успех", "Путь сохранения результатов изменён.")

# ===================== Виджет просмотра результатов =====================
class ResultsViewingTab(QWidget):
    def __init__(self, parent=None):
        super(ResultsViewingTab, self).__init__(parent)
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Вкладка с индивидуальными результатами
        individual_tab = QWidget()
        individual_layout = QVBoxLayout(individual_tab)
        
        filter_layout = QHBoxLayout()
        self.topic_filter = QComboBox()
        self.topic_filter.setEditable(True)
        self.topic_filter.setStyleSheet(combobox_style)
        self.topic_filter.addItem("Все темы")
        self.name_filter = QComboBox()
        self.name_filter.setEditable(True)
        self.name_filter.setStyleSheet(combobox_style)
        self.name_filter.addItem("Все студенты")
        label_theme = QLabel("По теме:")
        label_theme.setStyleSheet(filter_style)
        label_name = QLabel("По имени:")
        label_name.setStyleSheet(filter_style)
        filter_layout.addWidget(label_theme)
        filter_layout.addWidget(self.topic_filter)
        filter_layout.addWidget(label_name)
        filter_layout.addWidget(self.name_filter)
        individual_layout.addLayout(filter_layout)
        
        splitter = QSplitter(Qt.Vertical)
        self.result_list = QListWidget()
        splitter.addWidget(self.result_list)
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setStyleSheet(f"{base_style} font-size: 10pt;")
        splitter.addWidget(self.result_view)
        individual_layout.addWidget(splitter)
        
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Открыть")
        open_btn.setStyleSheet(button_style)
        clear_btn = QPushButton("Очистить")
        clear_btn.setStyleSheet(button_style)
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(clear_btn)
        individual_layout.addLayout(btn_layout)
        
        self.tab_widget.addTab(individual_tab, "Индивидуальные результаты")
        
        # Вкладка со сводной информацией по темам
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        self.summary_table = QTableWidget()
        self.summary_table.setStyleSheet(tablewidget_style)
        self.summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.summary_table.setColumnCount(3)
        self.summary_table.setHorizontalHeaderLabels(["Тема теста", "Кол-во студентов", "Средний балл (%)"])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary_layout.addWidget(self.summary_table)
        self.tab_widget.addTab(summary_tab, "Сводка по темам")
        
        # Новая вкладка "Итоги студентов"
        students_tab = QWidget()
        students_layout = QVBoxLayout(students_tab)
        self.students_table = QTableWidget()
        self.students_table.setStyleSheet(tablewidget_style)
        self.students_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        students_layout.addWidget(self.students_table)
        self.tab_widget.addTab(students_tab, "Итоги студентов")
        
        self.load_results()
        self.result_mapping = {}
        self.topic_filter.currentTextChanged.connect(self.update_result_list)
        self.name_filter.currentTextChanged.connect(self.update_result_list)
        open_btn.clicked.connect(self.open_result)
        clear_btn.clicked.connect(lambda: self.result_view.clear())
    
    def load_results(self):
        results_path = data_manager.data.get("results_path", os.path.abspath("results"))
        if not os.path.exists(results_path):
            QMessageBox.warning(self, "Ошибка", "Директория с результатами не существует.")
            return
        files = [f for f in os.listdir(results_path) if f.startswith("TEST-") and f.endswith(".enc")]
        self.all_results = []
        rm = ResultManager(results_path)
        for f in files:
            filepath = os.path.join(results_path, f)
            res = rm.load_result(filepath)
            if res and "student" in res and "test_topic" in res and "timestamp" in res:
                res["_filename"] = f
                self.all_results.append(res)
        
        topics = set(res.get("test_topic", "") for res in self.all_results)
        names = set(res.get("student", "") for res in self.all_results)
        self.topic_filter.addItems(sorted(topics))
        self.name_filter.addItems(sorted(names))
        self.update_result_list()
        self.update_summary_table()
        self.update_students_summary_table()
    
    def update_result_list(self):
        self.result_list.clear()
        self.result_mapping = {}
        filtered = []
        topic_val = self.topic_filter.currentText()
        name_val = self.name_filter.currentText()
        for res in self.all_results:
            if (topic_val == "Все темы" or res.get("test_topic", "") == topic_val) and \
               (name_val == "Все студенты" or res.get("student", "") == name_val):
                filtered.append(res)
        groups = defaultdict(list)
        for res in filtered:
            key = (res.get("student", ""), res.get("test_topic", ""))
            groups[key].append(res)
        display_items = []
        for key, results in groups.items():
            try:
                results.sort(key=lambda r: datetime.datetime.fromisoformat(r.get("timestamp", "")))
            except:
                results.sort(key=lambda r: r.get("timestamp", ""))
            for i, res in enumerate(results, start=1):
                time_str = res.get("timestamp", "")
                try:
                    dt = datetime.datetime.fromisoformat(time_str)
                    time_str = dt.strftime("%Y.%m.%d %H:%M")
                except:
                    pass
                base_text = f'{res.get("student", "")} - {res.get("test_topic", "")}'
                display_text = f'{base_text} ({time_str})'
                display_items.append((display_text, res))
        display_items.sort(
            key=lambda x: datetime.datetime.fromisoformat(x[1].get("timestamp", "1970-01-01T00:00:00")),
            reverse=True
        )
        for display_text, res in display_items:
            self.result_list.addItem(display_text)
            self.result_mapping[display_text] = res
        if self.result_list.count() > 0:
            self.result_list.setCurrentRow(0)
            self.open_result()
        self.result_list.setStyleSheet(
            f"""{base_style}
                padding: 5px;
                border: 2px solid #000;
                border-radius: 5px;
            """
        )  
    
    def update_summary_table(self):
        topic_groups = defaultdict(list)
        for res in self.all_results:
            topic = res.get("test_topic", "Без темы")
            topic_groups[topic].append(res)
        self.summary_table.setRowCount(0)
        for topic, results in topic_groups.items():
            count = len(results)
            avg_percent = sum(r.get("percent", 0) for r in results) / count if count else 0
            row = self.summary_table.rowCount()
            self.summary_table.insertRow(row)
            self.summary_table.setItem(row, 0, QTableWidgetItem(topic))
            self.summary_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.summary_table.setItem(row, 2, QTableWidgetItem(f"{avg_percent:.1f}"))
        for row in range(self.summary_table.rowCount()):
            self.summary_table.setRowHeight(row, 50)    

    def update_students_summary_table(self):
        # Формируем словарь: студент -> {тема: список процентов}
        data = {}
        topics = set()
        for res in self.all_results:
            student = res.get("student", "")
            topic = res.get("test_topic", "Без темы")
            topics.add(topic)
            if student not in data:
                data[student] = {}
            if topic not in data[student]:
                data[student][topic] = []
            data[student][topic].append(res.get("percent", 0))
        topics = sorted(topics)
        students = sorted(data.keys())
        self.students_table.setColumnCount(len(topics))
        self.students_table.setRowCount(len(students))
        self.students_table.setHorizontalHeaderLabels(topics)
        self.students_table.setVerticalHeaderLabels(students)
        for i, student in enumerate(students):
            self.students_table.setRowHeight(i, 60)
            for j, topic in enumerate(topics):
                scores = data[student].get(topic, [])
                if scores:
                    avg = sum(scores) / len(scores)
                    text = f"{avg:.1f}%"
                else:
                    text = ""
                self.students_table.setItem(i, j, QTableWidgetItem(text))
    
    def format_result(self, result):
        try:
            dt = datetime.datetime.fromisoformat(result.get("timestamp", ""))
            time_str = dt.strftime("%Y.%m.%d %H:%M:%S")
        except Exception:
            time_str = result.get("timestamp", "")
        html = []
        html.append(f'<div style="font-size: 24px;"><strong>Тестируемый:</strong> {result.get("student", "")}</div>')
        html.append(f'<div style="font-size: 24px;"><strong>Время начала теста:</strong> {time_str}</div>')
        html.append(f'<div style="font-size: 24px;"><strong>Тест:</strong> {result.get("test_topic", "")}</div><br>')
        html.append('<div style="font-size: 24px;"><strong>Результаты:</strong></div>')
        for i, item in enumerate(result.get("results", []), 1):
            bg_color = "#ffcccc" if item.get("score", 0) < 1 else "transparent"
            html.append(f'<div style="background-color:{bg_color}; font-size: 24px;"><strong>Вопрос {i}:</strong> {item.get("question", "")}</div>')
            html.append(f'<div style="background-color:{bg_color}; font-size: 24px;"><strong>Правильный ответ:</strong> {item.get("correct_answer", "")}</div>')
            ua = item.get("user_answer", "")
            if isinstance(ua, list):
                ua = ", ".join(ua)
            html.append(f'<div style="background-color:{bg_color};font-size: 24px;"><strong>Ответ тестируемого:</strong> {ua}</div>')
            html.append(f'<div style="background-color:{bg_color};font-size: 24px;"><strong>Баллы:</strong> {item.get("score", 0)}</div><br>')
        html.append(f'<div style="font-size: 24px;"><strong>Итоговый балл:</strong> {result.get("total_score", 0)}</div>')
        html.append(f'<div style="font-size: 24px;"><strong>Всего вопросов:</strong> {result.get("total_questions", 0)}</div>')
        html.append(f'<div style="font-size: 24px;"><strong>Процент прохождения:</strong> {round(result.get("percent", 0), 2)}%</div>')
        return "".join(html)
    
    def open_result(self):
        selected_item = self.result_list.currentItem()
        if selected_item:
            key = selected_item.text()
            res = self.result_mapping.get(key)
            if res:
                formatted = self.format_result(res)
                self.result_view.setHtml(formatted)
                self.result_view.setStyleSheet(
                    f"""
                        {base_style}
                        padding: 5px;
                        border: 2px solid #000;
                        border-radius: 5px; 
                    """)
            else:
                QMessageBox.warning(self, "Ошибка", "Результат не найден.")
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите результат из списка.")


# ===================== Главное окно режима редактирования (Администрирования) =====================
class AdminWindow(QMainWindow):
    def __init__(self, parent=None):
        super(AdminWindow, self).__init__(parent)
        self.setWindowTitle("Режим редактирования")
        self.setMinimumSize(1280, 720)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self.edit_tab = TestEditingTab(self)
        self.results_tab = ResultsViewingTab(self)
        
        self.tab_widget.addTab(self.edit_tab, "Редактирование тестов")
        self.tab_widget.addTab(self.results_tab, "Просмотр результатов")

        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                {base_style}
            }}
            QTabBar::tab {{
                background: #fff;
                color: #000;
                padding: 10px;
                border: 2px solid #000;
                border-radius: 5px;
                margin: 0px 2px;
            }}
            QTabBar::tab:selected {{
                background: #aeaeae;
                color: #000;
                border-radius: 5px;
            }}
            QTabBar::tab:hover {{
                background: #d0d0d0;
            }}
        """)

# ===================== Главное окно =====================
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Приложение для тестирования")
        self.setMinimumSize(1280, 720)
        self.create_menu()
        self.setStyleSheet("""
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #A4D4F9, stop: 1 #005392
            );
        """)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        title_label = QLabel("Приложение для тестирования")
        title_label.setFont(QFont(GLOBAL_FONT_FAMILY, 18))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(header_style)
        layout.addWidget(title_label)

        test_button = QPushButton("Тестирование")
        test_button.setFont(QFont(GLOBAL_FONT_FAMILY, 14))
        test_button.setStyleSheet(button_style)
        test_button.clicked.connect(self.start_test)
        layout.addWidget(test_button)

        edit_button = QPushButton("Редактирование")
        edit_button.setFont(QFont(GLOBAL_FONT_FAMILY, 14))
        edit_button.setStyleSheet(button_style)
        edit_button.clicked.connect(self.start_edit)
        layout.addWidget(edit_button)

    def create_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

    def start_test(self):
        login_dialog = StudentLoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted:
            student_name = login_dialog.get_name()
            if not student_name:
                msg_box = QMessageBox()
                msg_box.setStyleSheet(q_message_box)
                msg_box.setWindowTitle("Ошибка")
                msg_box.setText("<p style='background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 #A4D4F9, stop: 1 #005392);; color: black; font-family: \"Segoe UI\", Arial, sans-serif; font-size: 20pt;'> Введите имя! </p> ")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.button(QMessageBox.Ok).setStyleSheet(q_message_box)
                msg_box.exec_()
                return
            dialog = TestSelectionDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                test_data = dialog.selected_test
                test_window = TestWindow(test_data, student_name, self)
                test_window.exec_()

    def start_edit(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted and login_dialog.accepted:
            self.edit_window = AdminWindow(self)
            self.edit_window.show()

# ===================== Точка входа в приложение =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())