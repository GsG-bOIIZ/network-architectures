#!/usr/bin/env python3
import sys, os, json, hashlib, random, base64
from cryptography.fernet import Fernet

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QDialog,
    QLabel, QLineEdit, QComboBox, QListWidget, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, QAbstractItemView,
    QButtonGroup, QRadioButton, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

# =====================================================================
# Функции хэширования пароля
# =====================================================================
def hash_password(password, salt="some_salt"):
    return hashlib.sha256((salt+password).encode()).hexdigest()

def check_password(input_password, stored_hash, salt="some_salt"):
    return hash_password(input_password, salt) == stored_hash

# =====================================================================
# Менеджер данных: шифрование/расшифровка, загрузка/сохранение
# =====================================================================

# Ключ шифрования (32 url-safe base64 байт, можно сгенерировать через Fernet.generate_key())
ENCRYPTION_KEY = b'k_Nm-GI6e-d9U8i8JSGpWn9VZNU3ZQq2gVJXZ32XZxg='

class DataManager:
    def __init__(self, filename="data.enc"):
        self.filename = filename
        self.key = ENCRYPTION_KEY
        self.fernet = Fernet(self.key)
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            # Если файла нет – создаём структуру по умолчанию с паролем "admin"
            default_password = "admin"
            hashed = hash_password(default_password)
            data = {"password": hashed, "tests": []}
            self.save_data(data)
            return data
        else:
            with open(self.filename, "rb") as f:
                encrypted_data = f.read()
            try:
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
            except Exception as e:
                print("Ошибка расшифровки данных:", e)
                return {"password": "", "tests": []}

    def save_data(self, data):
        data_json = json.dumps(data, ensure_ascii=False).encode()
        encrypted_data = self.fernet.encrypt(data_json)
        with open(self.filename, "wb") as f:
            f.write(encrypted_data)
        self.data = data

# Глобальный экземпляр DataManager
data_manager = DataManager()

# =====================================================================
# Диалог ввода пароля для режима редактирования
# =====================================================================
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("Вход в режим редактирования")
        layout = QVBoxLayout()
        self.label = QLabel("Введите пароль:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.ok_button = QPushButton("ОК")
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #D9D9D9;
                color: black;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #AEAEAE;
            }
        """)
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

# =====================================================================
# Диалог смены пароля
# =====================================================================
class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super(ChangePasswordDialog, self).__init__(parent)
        self.setWindowTitle("Сменить пароль")
        layout = QVBoxLayout()
        self.current_label = QLabel("Текущий пароль:")
        self.current_edit = QLineEdit()
        self.current_edit.setEchoMode(QLineEdit.Password)
        self.new_label = QLabel("Новый пароль:")
        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.Password)
        self.confirm_label = QLabel("Подтвердите новый пароль:")
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.ok_button = QPushButton("Сменить пароль")
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
        # Обновляем пароль
        data_manager.data["password"] = hash_password(new)
        data_manager.save_data(data_manager.data)
        QMessageBox.information(self, "Успех", "Пароль успешно изменён!")
        self.accept()

# =====================================================================
# Диалог выбора теста (темы)
# =====================================================================
class TestSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super(TestSelectionDialog, self).__init__(parent)
        self.setWindowTitle("Выбор теста")
        layout = QVBoxLayout()
        self.test_list = QListWidget()
        self.load_tests()
        self.select_button = QPushButton("Выбрать")
        self.select_button.clicked.connect(self.select_test)
        layout.addWidget(self.test_list)
        layout.addWidget(self.select_button)
        self.setLayout(layout)
        self.selected_test = None
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #D9D9D9;
                color: black;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #AEAEAE;
            }
        """)


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

# =====================================================================
# Окно проведения теста с навигацией и прикреплёнными изображениями
# =====================================================================
class TestWindow(QDialog):
    def __init__(self, test_data, parent=None):
        super(TestWindow, self).__init__(parent)
        self.setWindowTitle(f"Тест: {test_data.get('topic','')}")
        self.setMinimumSize(800, 600)
        self.test_data = test_data
        self.questions = test_data.get("questions", [])
        self.total_questions = len(self.questions)
        # Для каждого вопроса генерируем постоянное случайное распределение индексов ответов
        self.question_order = []
        for q in self.questions:
            order = list(range(len(q.get("answers", []))))
            random.shuffle(order)
            self.question_order.append(order)
        # Инициализируем список ответов (None для неотвеченных)
        self.user_answers = [None] * self.total_questions
        self.current_index = 0

        self.layout = QVBoxLayout()
        # Верхняя панель навигации
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Предыдущий")
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #D9D9D9;
                color: black;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #AEAEAE;
            }
        """)
        self.prev_button.clicked.connect(self.go_prev)
        self.nav_combo = QComboBox()
        self.nav_combo.addItems([f"Вопрос {i+1}" for i in range(self.total_questions)])
        self.nav_combo.currentIndexChanged.connect(self.on_nav_change)
        self.next_button = QPushButton("Следующий")
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #D9D9D9;
                color: black;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #AEAEAE;
            }
        """)
        self.next_button.clicked.connect(self.go_next)
        self.finish_button = QPushButton("Завершить тест")
        self.finish_button.setStyleSheet("""
            QPushButton {
                background-color: #D9D9D9;
                color: black;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #AEAEAE;
            }
        """)
        self.finish_button.clicked.connect(self.finish_test_clicked)
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.nav_combo)
        self.nav_layout.addWidget(self.next_button)
        self.nav_layout.addWidget(self.finish_button)
        self.layout.addLayout(self.nav_layout)

        # Блок для вопроса и изображения вопроса
        self.question_image_label = QLabel()
        self.layout.addWidget(self.question_image_label)
        self.question_label = QLabel()
        self.layout.addWidget(self.question_label)

        # Область для вариантов ответов
        self.answers_widget = QWidget()
        self.answers_layout = QVBoxLayout()
        self.answers_widget.setLayout(self.answers_layout)
        self.layout.addWidget(self.answers_widget)

        self.setLayout(self.layout)
        self.current_answer_widgets = []  # хранит виджеты текущего вопроса
        self.show_question()

    def save_current_answer(self):
        """Сохраняет ответ текущего вопроса в self.user_answers."""
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
        """Восстанавливает ранее сохранённый ответ (если есть) для текущего вопроса."""
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
            # Показываем изображение вопроса (если есть)
            if question.get("image"):
                data = base64.b64decode(question["image"])
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                self.question_image_label.setPixmap(pixmap.scaledToWidth(300, Qt.SmoothTransformation))
            else:
                self.question_image_label.clear()
            self.question_label.setText(f"Вопрос {self.current_index+1}: {question.get('question','')}")
            # Очистка области вариантов ответов
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
                    container_layout.setContentsMargins(0, 0, 0, 0)
                    rb = QRadioButton(answer.get("text", ""))
                    rb.original_index = orig_idx  # сохраняем оригинальный индекс
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
                    self.answers_layout.addWidget(container)
                    self.current_answer_widgets.append(rb)
            elif question.get("type") == "multiple":
                for orig_idx in order:
                    answer = answers[orig_idx]
                    container = QWidget()
                    container_layout = QHBoxLayout()
                    container_layout.setContentsMargins(0, 0, 0, 0)
                    cb = QCheckBox(answer.get("text", ""))
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
                    self.answers_layout.addWidget(container)
                    self.current_answer_widgets.append(cb)
            # Восстанавливаем ранее сохранённый ответ (если есть)
            self.restore_answer()
            # Обновляем состояние кнопок навигации
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
        for i, question in enumerate(self.questions):
            if question.get("type") == "single":
                correct_idx = None
                answers = question.get("answers", [])
                for idx, ans in enumerate(answers):
                    if ans.get("correct", False):
                        correct_idx = idx
                        break
                user_ans = self.user_answers[i]
                q_score = 1 if user_ans == correct_idx else 0
            elif question.get("type") == "multiple":
                answers = question.get("answers", [])
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
            total_score += q_score
        percent = (total_score / self.total_questions) * 100 if self.total_questions else 0
        QMessageBox.information(self, "Результаты", 
            f"Ваш суммарный балл: {total_score:.2f} из {self.total_questions}\n"
            f"Успешность: {percent:.0f}%")
        self.accept()

# =====================================================================
# Диалог добавления нового теста (темы)
# =====================================================================
class AddTestDialog(QDialog):
    def __init__(self, parent=None):
        super(AddTestDialog, self).__init__(parent)
        self.setWindowTitle("Добавить тест")
        layout = QVBoxLayout()
        self.label = QLabel("Название теста:")
        self.topic_edit = QLineEdit()
        self.ok_button = QPushButton("Добавить")
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

# =====================================================================
# Диалог добавления/редактирования вопроса с поддержкой изображений
# =====================================================================
class AddQuestionDialog(QDialog):
    def __init__(self, question_data=None, parent=None):
        super(AddQuestionDialog, self).__init__(parent)
        self.setWindowTitle("Добавить вопрос" if question_data is None else "Редактировать вопрос")
        self.setMinimumSize(700, 500)
        self.question_data = question_data
        self.question_image_data = None  # для хранения base64 изображения вопроса
        layout = QVBoxLayout()

        # Текст вопроса
        self.question_label = QLabel("Текст вопроса:")
        self.question_edit = QLineEdit()
        layout.addWidget(self.question_label)
        layout.addWidget(self.question_edit)

        # Кнопка для прикрепления изображения к вопросу
        self.question_image_button = QPushButton("Прикрепить изображение")
        self.question_image_button.clicked.connect(self.choose_question_image)
        layout.addWidget(self.question_image_button)

        # Выбор типа вопроса
        self.type_label = QLabel("Тип вопроса:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Один правильный", "Несколько правильных"])
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combo)

        # Таблица вариантов ответов (4 колонки: Ответ, Правильный, Штраф, Изображение)
        self.answers_table = QTableWidget()
        self.answers_table.setColumnCount(4)
        self.answers_table.setHorizontalHeaderLabels(["Ответ", "Правильный", "Штраф", "Изображение"])
        self.answers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.answers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.answers_table)

        # Кнопки добавления/удаления строк
        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("Добавить ответ")
        self.add_row_btn.clicked.connect(lambda: self.add_row())
        self.remove_row_btn = QPushButton("Удалить выбранный ответ")
        self.remove_row_btn.clicked.connect(self.remove_row)
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.remove_row_btn)
        layout.addLayout(btn_layout)

        # Кнопки сохранения/отмены
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_question)
        self.cancel_btn = QPushButton("Отмена")
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

# =====================================================================
# Окно редактирования тестов и вопросов
# =====================================================================
class EditWindow(QMainWindow):
    def __init__(self, parent=None):
        super(EditWindow, self).__init__(parent)
        self.setWindowTitle("Редактирование тестов")
        self.setMinimumSize(800, 600)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)

        # Список тестов (тем)
        self.tests_list = QListWidget()
        self.tests_list.itemClicked.connect(self.load_questions)
        layout.addWidget(self.tests_list)

        # Список вопросов выбранного теста
        self.questions_list = QListWidget()
        layout.addWidget(self.questions_list)

        # Панель кнопок редактирования
        btn_layout = QVBoxLayout()
        self.add_test_btn = QPushButton("Добавить тест")
        self.add_test_btn.clicked.connect(self.add_test)
        self.delete_test_btn = QPushButton("Удалить тест")
        self.delete_test_btn.clicked.connect(self.delete_test)
        self.add_question_btn = QPushButton("Добавить вопрос")
        self.add_question_btn.clicked.connect(self.add_question)
        self.delete_question_btn = QPushButton("Удалить вопрос")
        self.delete_question_btn.clicked.connect(self.delete_question)
        self.edit_question_btn = QPushButton("Редактировать вопрос")
        self.edit_question_btn.clicked.connect(self.edit_question)
        self.change_password_btn = QPushButton("Сменить пароль")
        self.change_password_btn.clicked.connect(self.change_password)
        btn_layout.addWidget(self.add_test_btn)
        btn_layout.addWidget(self.delete_test_btn)
        btn_layout.addWidget(self.add_question_btn)
        btn_layout.addWidget(self.delete_question_btn)
        btn_layout.addWidget(self.edit_question_btn)
        btn_layout.addWidget(self.change_password_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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

# =====================================================================
# Главное окно – выбор режима
# =====================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Приложение для тестирования")
        self.setMinimumSize(800, 600)

        self.setStyleSheet("""
            background: qradialgradient(
                cx: 0.5, cy: 0.5, radius: 0.5,
                fx: 0.5, fy: 0.5,
                stop: 0 #9695B2, stop: 1 #8684F0
            );
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Заголовок
        title_label = QLabel("Приложение для тестирования")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Кнопка "Тестирование"
        test_button = QPushButton("Тестирование")
        test_button.setFont(QFont("Arial", 14))
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #D9D9D9;
                color: black;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #AEAEAE;
            }
        """)
        test_button.clicked.connect(self.start_test)
        layout.addWidget(test_button)

        # Кнопка "Редактирование"
        edit_button = QPushButton("Редактирование")
        edit_button.setFont(QFont("Arial", 14))
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #D9D9D9;
                color: black;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #AEAEAE;
            }
        """)
        edit_button.clicked.connect(self.start_edit)
        layout.addWidget(edit_button)

    def start_test(self):
        dialog = TestSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            test_data = dialog.selected_test
            test_window = TestWindow(test_data, self)
            test_window.exec_()

    def start_edit(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted and login_dialog.accepted:
            self.edit_window = EditWindow(self)
            self.edit_window.show()

# =====================================================================
# Точка входа в приложение
# =====================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
