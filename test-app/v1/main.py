#!/usr/bin/env python3
import sys, os, json, hashlib, random
from cryptography.fernet import Fernet

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QDialog,
    QLabel, QLineEdit, QComboBox, QListWidget, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, QAbstractItemView,
    QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt

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
# Окно проведения теста
# =====================================================================
class TestWindow(QDialog):
    def __init__(self, test_data, parent=None):
        super(TestWindow, self).__init__(parent)
        self.setWindowTitle(f"Тест: {test_data.get('topic','')}")
        self.test_data = test_data
        self.questions = test_data.get("questions", [])
        self.current_index = 0
        self.user_answers = []  # Список для хранения ответов пользователя
        self.layout = QVBoxLayout()
        self.question_label = QLabel()
        self.layout.addWidget(self.question_label)
        self.answers_widget = QWidget()
        self.answers_layout = QVBoxLayout()
        self.answers_widget.setLayout(self.answers_layout)
        self.layout.addWidget(self.answers_widget)
        self.next_button = QPushButton("Далее")
        self.next_button.clicked.connect(self.next_question)
        self.layout.addWidget(self.next_button)
        self.setLayout(self.layout)
        self.show_question()

    def show_question(self):
        if self.current_index < len(self.questions):
            question = self.questions[self.current_index]
            self.question_label.setText(f"Вопрос {self.current_index+1}: {question.get('question','')}")
            # Очистка предыдущих виджетов с вариантами ответов
            for i in reversed(range(self.answers_layout.count())):
                widget_to_remove = self.answers_layout.itemAt(i).widget()
                if widget_to_remove:
                    widget_to_remove.setParent(None)
            self.current_answer_widgets = []

            answers = question.get("answers", [])
            indices = list(range(len(answers)))
            random.shuffle(indices)

            if question.get("type") == "single":
                # Для одиночного выбора – используем радио-кнопки
                self.button_group = QButtonGroup(self)
                
                for orig_idx in indices:
                    answer = answers[orig_idx]
                    rb = QRadioButton(answer.get("text", ""))
                    rb.original_index = orig_idx  # сохраняем оригинальный индекс
                    rb.correct = answer.get("correct", False)
                    self.button_group.addButton(rb)
                    self.answers_layout.addWidget(rb)
                    self.current_answer_widgets.append(rb)
            elif question.get("type") == "multiple":
                # Для множественного выбора – используем чекбоксы
                for orig_idx in indices:
                    answer = answers[orig_idx]
                    cb = QCheckBox(answer.get("text", ""))
                    cb.original_index = orig_idx  # сохраняем оригинальный индекс
                    cb.correct = answer.get("correct", False)
                    cb.penalty = float(answer.get("penalty", 0))
                    self.answers_layout.addWidget(cb)
                    self.current_answer_widgets.append(cb)
        else:
            self.finish_test()

    def next_question(self):
        # Сохраняем ответ пользователя для текущего вопроса
        if self.current_index < len(self.questions):
            question = self.questions[self.current_index]
            if question.get("type") == "single":
                selected_id = self.button_group.checkedId()
                self.user_answers.append(selected_id)
            elif question.get("type") == "multiple":
                selected = []
                for idx, cb in enumerate(self.current_answer_widgets):
                    if cb.isChecked():
                        selected.append(idx)
                self.user_answers.append(selected)
            self.current_index += 1
            self.show_question()

    def finish_test(self):
        # Подсчёт результатов теста
        score = 0
        total = len(self.questions)
        for i, question in enumerate(self.questions):
            correct_answers = [idx for idx, ans in enumerate(question.get("answers", [])) if ans.get("correct")]
            user_ans = self.user_answers[i] if i < len(self.user_answers) else None
            if question.get("type") == "single":
                if user_ans is not None and user_ans in correct_answers:
                    score += 1
            elif question.get("type") == "multiple":
                if set(user_ans) == set(correct_answers):
                    score += 1

        percent = (score/total)*100 if total else 0
        QMessageBox.information(self, "Результаты", 
                                f"Ваш результат: {score} из {total}\n" 
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
# Диалог добавления/редактирования вопроса
# =====================================================================
class AddQuestionDialog(QDialog):
    def __init__(self, question_data=None, parent=None):
        super(AddQuestionDialog, self).__init__(parent)
        self.setWindowTitle("Добавить вопрос" if question_data is None else "Редактировать вопрос")
        self.question_data = question_data
        layout = QVBoxLayout()

        # Поле для текста вопроса
        self.question_label = QLabel("Текст вопроса:")
        self.question_edit = QLineEdit()
        layout.addWidget(self.question_label)
        layout.addWidget(self.question_edit)

        # Выбор типа вопроса
        self.type_label = QLabel("Тип вопроса:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Один правильный", "Несколько правильных"])
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combo)

        # Таблица для вариантов ответов
        self.answers_table = QTableWidget()
        self.answers_table.setColumnCount(2)
        self.answers_table.setHorizontalHeaderLabels(["Ответ", "Правильный"])
        self.answers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.answers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.answers_table)

        # Кнопки добавления/удаления строк таблицы
        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("Добавить ответ")
        self.add_row_btn.clicked.connect(self.add_row)
        self.remove_row_btn = QPushButton("Удалить выбранный ответ")
        self.remove_row_btn.clicked.connect(self.remove_row)
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.remove_row_btn)
        layout.addLayout(btn_layout)

        # Кнопки сохранения и отмены
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_question)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)
        if question_data:
            self.load_question_data()

    def load_question_data(self):
        self.question_edit.setText(self.question_data.get("question", ""))
        qtype = self.question_data.get("type", "single")
        if qtype == "single":
            self.type_combo.setCurrentIndex(0)
        else:
            self.type_combo.setCurrentIndex(1)
        answers = self.question_data.get("answers", [])
        self.answers_table.setRowCount(0)
        for ans in answers:
            self.add_row(ans.get("text", ""), ans.get("correct", False))

    def add_row(self, text="", correct=False):
        row = self.answers_table.rowCount()
        self.answers_table.insertRow(row)
        item = QTableWidgetItem(text)
        self.answers_table.setItem(row, 0, item)
        # Чекбокс для отметки правильного ответа
        checkbox = QCheckBox()
        checkbox.setChecked(correct)
        self.answers_table.setCellWidget(row, 1, checkbox)

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
                if answer_text:
                    answers.append({"text": answer_text, "correct": correct})
        if len(answers) < 2:
            QMessageBox.warning(self, "Ошибка", "Должно быть минимум два ответа!")
            return
        # Для вопроса с одним правильным ответом – ровно один ответ должен быть отмечен как правильный
        if qtype == "single":
            correct_count = sum(1 for ans in answers if ans["correct"])
            if correct_count != 1:
                QMessageBox.warning(self, "Ошибка", "Для вопроса с одним правильным ответом должен быть ровно один правильный вариант!")
                return
        self.question_result = {"question": question_text, "type": qtype, "answers": answers}
        self.accept()

# =====================================================================
# Окно редактирования тестов и вопросов
# =====================================================================
class EditWindow(QMainWindow):
    def __init__(self, parent=None):
        super(EditWindow, self).__init__(parent)
        self.setWindowTitle("Редактирование тестов")
        self.resize(800, 600)
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

        # Панель кнопок для редактирования
        btn_layout = QVBoxLayout()
        self.add_test_btn = QPushButton("Добавить тест")
        self.add_test_btn.clicked.connect(self.add_test)
        self.delete_test_btn = QPushButton("Удалить тест")
        self.delete_test_btn.clicked.connect(self.delete_test)
        self.add_question_btn = QPushButton("Добавить вопрос")
        self.add_question_btn.clicked.connect(self.add_question)
        self.delete_question_btn = QPushButton("Удалить вопрос")
        self.delete_question_btn.clicked.connect(self.delete_question)
        # self.edit_question_btn = QPushButton("Редактировать вопрос")
        # self.edit_question_btn.clicked.connect(self.edit_question)
        btn_layout.addWidget(self.add_test_btn)
        btn_layout.addWidget(self.delete_test_btn)
        btn_layout.addWidget(self.add_question_btn)
        btn_layout.addWidget(self.delete_question_btn)
        # btn_layout.addWidget(self.edit_question_btn)
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

# =====================================================================
# Главное окно – выбор режима
# =====================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Приложение для тестирования")
        self.resize(400, 200)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.test_button = QPushButton("Тестирование")
        self.test_button.clicked.connect(self.start_test)
        self.edit_button = QPushButton("Редактирование")
        self.edit_button.clicked.connect(self.start_edit)
        layout.addWidget(self.test_button)
        layout.addWidget(self.edit_button)

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
