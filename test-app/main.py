#!/usr/bin/env python3
import sys, os, json, hashlib, random, base64, datetime
from collections import defaultdict
from cryptography.fernet import Fernet

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QDialog,
    QLabel, QLineEdit, QComboBox, QListWidget, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, QAbstractItemView,
    QButtonGroup, QRadioButton, QFileDialog, QTextEdit, QMenuBar, QAction,
    QTabWidget, QSplitter, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

# ===================== Универсальные стили =====================
label_style = """
    QLabel {
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 14pt;
        color: #2b2b2b;
        padding: 5px;
    }
"""

combobox_style = """
    QComboBox {
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12pt;
        padding: 5px;
        border: 1px solid #aeaeae;
        border-radius: 5px;
        background-color: #ffffff;
        color: #2b2b2b;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 1px solid #aeaeae;
    }
    QComboBox QAbstractItemView {
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 12pt;
        background-color: #ffffff;
        border: 1px solid #aeaeae;
        selection-background-color: #d9d9d9;
    }
"""

tablewidget_style = """
    QTableWidget {
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 11pt;
        color: #2b2b2b;
        background-color: #ffffff;
        gridline-color: #aeaeae;
        border: 1px solid #aeaeae;
    }
    QHeaderView::section {
        background-color: #f7f7f7;
        padding: 5px;
        border: 1px solid #aeaeae;
        font-size: 12pt;
        font-weight: bold;
    }
"""

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
            QMessageBox.warning(None, "Ошибка", f"Не удалось расшифровать файл:\n{e}")
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
        self.ok_button = QPushButton("ОК")
        self.ok_button.setStyleSheet("padding: 10px;")
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
            QMessageBox.warning(self, "Ошибка", "Неверный пароль!")

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super(ChangePasswordDialog, self).__init__(parent)
        self.setWindowTitle("Сменить пароль")
        layout = QVBoxLayout()
        self.current_label = QLabel("Текущий пароль:")
        self.current_label.setStyleSheet(label_style)
        self.current_edit = QLineEdit()
        self.current_edit.setEchoMode(QLineEdit.Password)
        self.new_label = QLabel("Новый пароль:")
        self.new_label.setStyleSheet(label_style)
        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.Password)
        self.confirm_label = QLabel("Подтвердите новый пароль:")
        self.confirm_label.setStyleSheet(label_style)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.ok_button = QPushButton("Сменить пароль")
        self.ok_button.setStyleSheet("padding: 10px;")
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
            QMessageBox.warning(self, "Ошибка", "Неверный текущий пароль!")
            return
        if new != confirm or not new:
            QMessageBox.warning(self, "Ошибка", "Новый пароль и подтверждение не совпадают или пусты!")
            return
        data_manager.data["password"] = hash_password(new)
        data_manager.save_data(data_manager.data)
        QMessageBox.information(self, "Успех", "Пароль успешно изменён!")
        self.accept()

class StudentLoginDialog(QDialog):
    def __init__(self, parent=None):
        super(StudentLoginDialog, self).__init__(parent)
        self.setWindowTitle("Вход студента")
        layout = QVBoxLayout()
        self.label = QLabel("Введите ваше имя:")
        self.label.setStyleSheet(label_style)
        self.name_edit = QLineEdit()
        self.ok_button = QPushButton("Начать тест")
        self.ok_button.setStyleSheet("padding: 10px;")
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
        self.test_list.setStyleSheet("""
            QListWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 12pt;
                padding: 5px;
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 5px;
            }
        """)
        self.load_tests()
        self.select_button = QPushButton("Выбрать")
        self.select_button.setStyleSheet("padding: 10px;")
        self.select_button.clicked.connect(self.select_test)
        layout.addWidget(self.test_list)
        layout.addWidget(self.select_button)
        self.setLayout(layout)
        self.selected_test = None

    def load_tests(self):
        self.test_list.clear()
        tests = data_manager.data.get("tests", [])
        for test in tests:
            self.test_list.addItem(test.get("topic", "Без темы"))

    def select_test(self):
        current_row = self.test_list.currentRow()
        if current_row >= 0:
            self.selected_test = data_manager.data["tests"][current_row]
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите тест!")

# ===================== Окно проведения теста =====================
class TestWindow(QDialog):
    def __init__(self, test_data, student_name, parent=None):
        super(TestWindow, self).__init__(parent)
        self.setWindowTitle(f"Тест: {test_data.get('topic','')}")
        self.setMinimumSize(800, 600)
        self.test_data = test_data
        self.student_name = student_name
        self.questions = test_data.get("questions", [])
        self.total_questions = len(self.questions)
        self.question_order = []
        for q in self.questions:
            order = list(range(len(q.get("answers", []))))
            random.shuffle(order)
            self.question_order.append(order)
        self.user_answers = [None] * self.total_questions
        self.current_index = 0

        self.layout = QVBoxLayout()
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Предыдущий")
        self.prev_button.setStyleSheet("padding: 10px;")
        self.prev_button.clicked.connect(self.go_prev)
        self.nav_combo = QComboBox()
        self.nav_combo.setStyleSheet(combobox_style)
        self.nav_combo.addItems([f"Вопрос {i+1}" for i in range(self.total_questions)])
        self.nav_combo.currentIndexChanged.connect(self.on_nav_change)
        self.next_button = QPushButton("Следующий")
        self.next_button.setStyleSheet("padding: 10px;")
        self.next_button.clicked.connect(self.go_next)
        self.finish_button = QPushButton("Завершить тест")
        self.finish_button.setStyleSheet("padding: 10px;")
        self.finish_button.clicked.connect(self.finish_test_clicked)
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.nav_combo)
        self.nav_layout.addWidget(self.next_button)
        self.nav_layout.addWidget(self.finish_button)
        self.layout.addLayout(self.nav_layout)

        self.question_image_label = QLabel()
        self.layout.addWidget(self.question_image_label)
        self.question_label = QLabel()
        self.question_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                padding: 10px;
                border: 2px solid #aeaeae;
                border-radius: 8px;
                background-color: #f7f7f7;
            }
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
                self.question_image_label.setPixmap(pixmap.scaledToWidth(300, Qt.SmoothTransformation))
            else:
                self.question_image_label.clear()
            self.question_label.setText(f"Вопрос {self.current_index+1}: {question.get('question','')}")
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
                    rb.setStyleSheet("""
                        QRadioButton {
                            font-size: 12pt;
                            padding: 5px;
                        }
                    """)
                    rb.original_index = orig_idx
                    rb.correct = answer.get("correct", False)
                    self.button_group.addButton(rb)
                    container_layout.addWidget(rb)
                    if answer.get("image"):
                        data = base64.b64decode(answer["image"])
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        img_label = QLabel()
                        img_label.setPixmap(pixmap.scaledToWidth(100, Qt.SmoothTransformation))
                        container_layout.addWidget(img_label)
                    container.setLayout(container_layout)
                    container.setStyleSheet("""
                        QWidget {
                            border: 1px solid #d9d9d9;
                            border-radius: 5px;
                            margin-bottom: 5px;
                            background-color: #ffffff;
                        }
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
                    cb.setStyleSheet("""
                        QCheckBox {
                            font-size: 12pt;
                            padding: 5px;
                        }
                    """)
                    cb.original_index = orig_idx
                    cb.correct = answer.get("correct", False)
                    cb.penalty = float(answer.get("penalty", 0))
                    container_layout.addWidget(cb)
                    if answer.get("image"):
                        data = base64.b64decode(answer["image"])
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        img_label = QLabel()
                        img_label.setPixmap(pixmap.scaledToWidth(100, Qt.SmoothTransformation))
                        container_layout.addWidget(img_label)
                    container.setLayout(container_layout)
                    container.setStyleSheet("""
                        QWidget {
                            border: 1px solid #d9d9d9;
                            border-radius: 5px;
                            margin-bottom: 5px;
                            background-color: #ffffff;
                        }
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
            msg = "Следующие вопросы не имеют ни одного ответа:\n" + ", ".join(map(str, missing))
            msg += "\nЗаполните их!"
            reply = QMessageBox.question(self, "Внимание", msg, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
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
        QMessageBox.information(self, "Результаты", 
            f"Ваш суммарный балл: {total_score:.2f} из {self.total_questions}\n"
            f"Успешность: {percent:.0f}%")
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
        self.ok_button = QPushButton("Добавить")
        self.ok_button.setStyleSheet("padding: 10px;")
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
            QMessageBox.warning(self, "Ошибка", "Введите название теста!")

# ===================== Диалог добавления/редактирования вопроса =====================
class AddQuestionDialog(QDialog):
    def __init__(self, question_data=None, parent=None):
        super(AddQuestionDialog, self).__init__(parent)
        self.setWindowTitle("Добавить вопрос" if question_data is None else "Редактировать вопрос")
        self.setMinimumSize(700, 500)
        self.question_data = question_data
        self.question_image_data = None  
        layout = QVBoxLayout()

        self.question_label = QLabel("Текст вопроса:")
        self.question_label.setStyleSheet(label_style)
        self.question_edit = QLineEdit()
        layout.addWidget(self.question_label)
        layout.addWidget(self.question_edit)

        self.question_image_button = QPushButton("Прикрепить изображение")
        self.question_image_button.setStyleSheet("padding: 10px;")
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
        self.answers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.answers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.answers_table)

        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("Добавить ответ")
        self.add_row_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.add_row_btn.clicked.connect(lambda: self.add_row())
        self.remove_row_btn = QPushButton("Удалить выбранный ответ")
        self.remove_row_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.remove_row_btn.clicked.connect(self.remove_row)
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.remove_row_btn)
        layout.addLayout(btn_layout)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet("padding: 10px;")
        self.save_btn.clicked.connect(self.save_question)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setStyleSheet("padding: 10px;")
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
        image_button.setStyleSheet("padding: 8px; font-size: 10pt;")
        image_button.clicked.connect(lambda _, btn=image_button: self.choose_answer_image(btn))
        image_button.imageData = answer_image
        if answer_image:
            image_button.setText("Изменить изображение")
        self.answers_table.setCellWidget(row, 3, image_button)

    def remove_row(self):
        indices = self.answers_table.selectionModel().selectedRows()
        for index in sorted(indices, reverse=True):
            self.answers_table.removeRow(index.row())

    def save_question(self):
        question_text = self.question_edit.text().strip()
        if not question_text:
            QMessageBox.warning(self, "Ошибка", "Введите текст вопроса!")
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
            QMessageBox.warning(self, "Ошибка", "Должно быть минимум два ответа!")
            return
        if qtype == "single":
            correct_count = sum(1 for ans in answers if ans["correct"])
            if correct_count != 1:
                QMessageBox.warning(self, "Ошибка", "Для вопроса с одним правильным ответом должен быть ровно один правильный вариант!")
                return
        self.question_result = {
            "question": question_text,
            "type": qtype,
            "answers": answers,
            "image": self.question_image_data if self.question_image_data else ""
        }
        self.accept()

# ===================== Окно редактирования тестов и управления результатами =====================
class EditWindow(QMainWindow):
    def __init__(self, parent=None):
        super(EditWindow, self).__init__(parent)
        self.setWindowTitle("Редактирование тестов")
        self.setMinimumSize(800, 600)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        # Используем QSplitter для разделения верхней части (список тестов и вопросов) и нижней панели кнопок
        main_layout = QVBoxLayout(main_widget)
        splitter_main = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter_main)
        # Верхняя часть: QSplitter с тестами и вопросами (слева и справа)
        top_splitter = QSplitter(Qt.Horizontal)
        self.tests_list = QListWidget()
        self.tests_list.setStyleSheet("""
            QListWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 12pt;
                padding: 5px;
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 5px;
            }
        """)
        self.tests_list.itemClicked.connect(self.load_questions)
        top_splitter.addWidget(self.tests_list)
        self.questions_list = QListWidget()
        self.questions_list.setStyleSheet("""
            QListWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 12pt;
                padding: 5px;
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 5px;
            }
        """)
        top_splitter.addWidget(self.questions_list)
        splitter_main.addWidget(top_splitter)
        # Нижняя часть: панель кнопок (центрирована)
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addStretch()
        # Слева: "Добавить тест" и "Удалить тест"
        vbox_left = QVBoxLayout()
        self.add_test_btn = QPushButton("Добавить тест")
        self.add_test_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.add_test_btn.clicked.connect(self.add_test)
        self.delete_test_btn = QPushButton("Удалить тест")
        self.delete_test_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.delete_test_btn.clicked.connect(self.delete_test)
        vbox_left.addWidget(self.add_test_btn)
        vbox_left.addWidget(self.delete_test_btn)
        # Центр: "Добавить вопрос", "Удалить вопрос", "Редактировать вопрос"
        vbox_center = QVBoxLayout()
        self.add_question_btn = QPushButton("Добавить вопрос")
        self.add_question_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.add_question_btn.clicked.connect(self.add_question)
        self.delete_question_btn = QPushButton("Удалить вопрос")
        self.delete_question_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.delete_question_btn.clicked.connect(self.delete_question)
        self.edit_question_btn = QPushButton("Редактировать вопрос")
        self.edit_question_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.edit_question_btn.clicked.connect(self.edit_question)
        vbox_center.addWidget(self.add_question_btn)
        vbox_center.addWidget(self.delete_question_btn)
        vbox_center.addWidget(self.edit_question_btn)
        # Справа: "Просмотр результатов"
        vbox_right = QVBoxLayout()
        self.view_results_btn = QPushButton("Просмотр результатов")
        self.view_results_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.view_results_btn.clicked.connect(self.view_results)
        vbox_right.addWidget(self.view_results_btn)
        # Еще правее: "Сменить пароль" и "Изменить путь сохранения результатов"
        vbox_far_right = QVBoxLayout()
        self.change_password_btn = QPushButton("Сменить пароль")
        self.change_password_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.change_password_btn.clicked.connect(self.change_password)
        self.set_results_path_btn = QPushButton("Изменить путь сохранения результатов")
        self.set_results_path_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.set_results_path_btn.clicked.connect(self.set_results_path)
        vbox_far_right.addWidget(self.change_password_btn)
        vbox_far_right.addWidget(self.set_results_path_btn)
        # Собираем панели кнопок по центру
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

    def view_results(self):
        results_path = data_manager.data.get("results_path", os.path.abspath("results"))
        if not os.path.exists(results_path):
            QMessageBox.warning(self, "Ошибка", "Директория с результатами не существует.")
            return
        files = [f for f in os.listdir(results_path) if f.startswith("TEST-") and f.endswith(".enc")]
        if not files:
            QMessageBox.information(self, "Информация", "Файлы с результатами не найдены.")
            return

        dialog = QDialog(self)
        # Используем стандартные кнопки окна (максимизация, закрытие)
        dialog.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMaximizeButtonHint)
        dialog.setWindowTitle("Просмотр результатов")
        dialog.setMinimumSize(800, 600)

        tab_widget = QTabWidget()

        # Вкладка 1: Индивидуальные результаты с QSplitter и фильтрами
        individual_tab = QWidget()
        individual_layout = QVBoxLayout()
        individual_tab.setLayout(individual_layout)

        filter_layout = QHBoxLayout()
        self.topic_filter = QComboBox()
        self.topic_filter.setEditable(True)
        self.topic_filter.setStyleSheet(combobox_style)
        self.topic_filter.addItem("Все темы")
        self.name_filter = QComboBox()
        self.name_filter.setEditable(True)
        self.name_filter.setStyleSheet(combobox_style)
        self.name_filter.addItem("Все студенты")
        filter_layout.addWidget(QLabel("По теме:"))
        filter_layout.addWidget(self.topic_filter)
        filter_layout.addWidget(QLabel("По имени:"))
        filter_layout.addWidget(self.name_filter)
        individual_layout.addLayout(filter_layout)

        splitter = QSplitter(Qt.Vertical)
        self.result_list = QListWidget()
        splitter.addWidget(self.result_list)
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setStyleSheet("font-size: 16pt;")
        splitter.addWidget(self.result_view)
        individual_layout.addWidget(splitter)

        # Панель кнопок для индивидуальных результатов
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Открыть")
        open_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("padding: 8px; font-size: 10pt;")
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(close_btn)
        individual_layout.addLayout(btn_layout)

        tab_widget.addTab(individual_tab, "Индивидуальные результаты")

        # Вкладка 2: Сводка по темам тестов
        summary_tab = QWidget()
        summary_layout = QVBoxLayout()
        summary_tab.setLayout(summary_layout)
        summary_table = QTableWidget()
        summary_table.setStyleSheet(tablewidget_style)
        summary_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        summary_table.setColumnCount(3)
        summary_table.setHorizontalHeaderLabels(["Тема теста", "Кол-во студентов", "Средний балл (%)"])
        summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary_layout.addWidget(summary_table)
        tab_widget.addTab(summary_tab, "Сводка по темам")

        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        dialog.setLayout(main_layout)

        rm = ResultManager(results_path)
        all_results = []
        for f in files:
            filepath = os.path.join(results_path, f)
            res = rm.load_result(filepath)
            if res:
                res["_filename"] = f
                all_results.append(res)

        topics = set(res.get("test_topic", "") for res in all_results)
        names = set(res.get("student", "") for res in all_results)
        self.topic_filter.addItems(sorted(topics))
        self.name_filter.addItems(sorted(names))

        def update_result_list():
            self.result_list.clear()
            self.result_mapping = {}
            filtered = []
            topic_val = self.topic_filter.currentText()
            name_val = self.name_filter.currentText()
            for res in all_results:
                if (topic_val == "Все темы" or res.get("test_topic", "") == topic_val) and \
                   (name_val == "Все студенты" or res.get("student", "") == name_val):
                    filtered.append(res)
            groups = defaultdict(list)
            for res in filtered:
                key = (res.get("student", ""), res.get("test_topic", ""))
                groups[key].append(res)
            display_items = []
            for key, results in groups.items():
                results.sort(key=lambda r: datetime.datetime.fromisoformat(r.get("timestamp", "1970-01-01T00:00:00")))
                for i, res in enumerate(results, start=1):
                    base_text = f'{res.get("student", "")} - {res.get("test_topic", "")}'
                    if i > 1:
                        display_text = f'{base_text} (Попытка {i})'
                    else:
                        display_text = base_text
                    display_items.append((display_text, res))
            display_items.sort(key=lambda x: datetime.datetime.fromisoformat(x[1].get("timestamp", "1970-01-01T00:00:00")))
            for display_text, res in display_items:
                self.result_list.addItem(display_text)
                self.result_mapping[display_text] = res

        self.topic_filter.currentTextChanged.connect(update_result_list)
        self.name_filter.currentTextChanged.connect(update_result_list)
        update_result_list()

        def format_result(result):
            try:
                dt = datetime.datetime.fromisoformat(result.get("timestamp", ""))
                time_str = dt.strftime("%Y.%m.%d %H:%M:%S")
            except Exception:
                time_str = result.get("timestamp", "")
            html = []
            html.append(f'<div><strong>Тестируемый:</strong> {result.get("student", "")}</div>')
            html.append(f'<div><strong>Время начала теста:</strong> {time_str}</div>')
            html.append(f'<div><strong>Тест:</strong> {result.get("test_topic", "")}</div><br>')
            html.append('<div><strong>Результаты:</strong></div>')
            for i, item in enumerate(result.get("results", []), 1):
                bg_color = "#ffcccc" if item.get("score", 0) < 1 else "transparent"
                html.append(f'<div style="background-color:{bg_color}; padding:5px; margin:5px 0;">')
                html.append(f'<div><strong>Вопрос {i}:</strong> {item.get("question", "")}</div>')
                html.append(f'<div><strong>Правильный ответ:</strong> {item.get("correct_answer", "")}</div>')
                ua = item.get("user_answer", "")
                if isinstance(ua, list):
                    ua = ", ".join(ua)
                html.append(f'<div><strong>Ответ тестируемого:</strong> {ua}</div>')
                html.append(f'<div><strong>Баллы:</strong> {item.get("score", 0)}</div>')
                html.append('</div>')
            html.append(f'<div><strong>Итоговый балл:</strong> {result.get("total_score", 0)}</div>')
            html.append(f'<div><strong>Всего вопросов:</strong> {result.get("total_questions", 0)}</div>')
            html.append(f'<div><strong>Процент прохождения:</strong> {result.get("percent", 0)}%</div>')
            return "<br>".join(html)

        def open_result():
            selected_item = self.result_list.currentItem()
            if selected_item:
                key = selected_item.text()
                res = self.result_mapping.get(key)
                if res:
                    formatted = format_result(res)
                    self.result_view.setHtml(formatted)
        open_btn.clicked.connect(open_result)
        close_btn.clicked.connect(dialog.accept)

        # Формируем сводку по темам
        topic_groups = defaultdict(list)
        for res in all_results:
            topic = res.get("test_topic", "Без темы")
            topic_groups[topic].append(res)
        summary_table.setRowCount(0)
        for topic, results in topic_groups.items():
            count = len(results)
            avg_percent = sum(r.get("percent", 0) for r in results) / count if count else 0
            row = summary_table.rowCount()
            summary_table.insertRow(row)
            summary_table.setItem(row, 0, QTableWidgetItem(topic))
            summary_table.setItem(row, 1, QTableWidgetItem(str(count)))
            summary_table.setItem(row, 2, QTableWidgetItem(f"{avg_percent:.1f}"))
        dialog.exec_()

# ===================== Главное окно =====================
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Приложение для тестирования")
        self.setMinimumSize(800, 600)
        self.create_menu()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        title_label = QLabel("Приложение для тестирования")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(label_style)
        layout.addWidget(title_label)

        test_button = QPushButton("Тестирование")
        test_button.setFont(QFont("Segoe UI", 14))
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #d9d9d9;
                color: #2b2b2b;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #aeaeae;
            }
        """)
        test_button.clicked.connect(self.start_test)
        layout.addWidget(test_button)

        edit_button = QPushButton("Редактирование")
        edit_button.setFont(QFont("Segoe UI", 14))
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #d9d9d9;
                color: #2b2b2b;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #aeaeae;
            }
        """)
        edit_button.clicked.connect(self.start_edit)
        layout.addWidget(edit_button)

    def create_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        # Дополнительное меню можно добавить по необходимости

    def start_test(self):
        login_dialog = StudentLoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted:
            student_name = login_dialog.get_name()
            if not student_name:
                QMessageBox.warning(self, "Ошибка", "Введите имя!")
                return
            dialog = TestSelectionDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                test_data = dialog.selected_test
                test_window = TestWindow(test_data, student_name, self)
                test_window.exec_()

    def start_edit(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted and login_dialog.accepted:
            self.edit_window = EditWindow(self)
            self.edit_window.show()

# ===================== Точка входа в приложение =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
