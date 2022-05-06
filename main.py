import sys
import os, shutil
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtGui import QPixmap
from main_prog import Main
import requests
import sqlite3
from lxml import html


# проверка на наличие одинакового запроса в истории поиска
def history_check(site, text, search_type):
    con = sqlite3.connect('ParsingTool.sqlite')
    cur = con.cursor()
    check = cur.execute("""SELECT result FROM search_history
                                        WHERE site = ? AND request = ? AND search = ?""",
                        (site, text, search_type)).fetchall()
    cur.close()
    return check


class MainWindow(QMainWindow):
    def __init__(self):
        # инициализация интерфейса главного окна. Сразу применяются настройки шрифта и темы.
        super().__init__()
        uic.loadUi('main_UI.ui', self)

        self.save_but.hide()
        self.show_pics.hide()

        self.con = sqlite3.connect("ParsingTool.sqlite")
        self.cur = self.con.cursor()

        con = sqlite3.connect('ParsingTool.sqlite')
        cur = con.cursor()
        a = cur.execute('''SELECT font_size FROM settings''').fetchall()
        a = a[0][0]
        app.setStyleSheet("QLabel, QTextEdit, QLineEdit, QStatusBar{font-size: " + str(a) + "pt;}")

        a = cur.execute('''SELECT theme FROM settings''').fetchall()
        a = a[0][0]
        if a == 'Темная':
            self.setStyleSheet("background-color: lightGray")
        else:
            self.setStyleSheet("")

        self.search_forms.clicked.connect(self.search)
        self.search_exact.clicked.connect(self.search)
        self.save_but.clicked.connect(self.save)

        self.hist_but.clicked.connect(self.opendialog)
        self.interface_but.clicked.connect(self.opendialog1)
        self.show_pics.clicked.connect(self.opendialog2)

        self.check_pics.setChecked(True)
        self.check_pics.stateChanged.connect(self.pic_activate)

        cur.close()

    def pic_activate(self):
        if self.check_pics.isChecked() is True:
            self.show_pics.setEnabled(True)
        if self.check_pics.isChecked() is False:
            self.show_pics.setEnabled(False)

    # открытие окна с историей поиска
    def opendialog(self):
        dialog = History(self)
        dialog.show()

    # открытие окна с настройками
    def opendialog1(self):
        dialog = Settings(self)
        dialog.show()

    # открытие окна с изображениями
    def opendialog2(self):
        dialog = Pictures(self)
        dialog.show()

    # функция для вызова ошибки в статусбаре
    # принимает в себя текст ошибки
    def error_message(self, message):
        self.statusBar().showMessage(message)
        self.save_but.hide()
        self.show_pics.hide()
        self.result_UI.setText('')
        self.statusBar().show()

    def pics(self):
        # работа с изображениями
        global pics
        global pic_count
        con = sqlite3.connect('ParsingTool.sqlite')
        cur = con.cursor()
        check = cur.execute("""SELECT pics FROM search_history WHERE site = ?""",
                            (self.site,)).fetchall()
        # если изображения уже скачаны
        if self.check_pics.isChecked() is True:
            try:
                if check[0][0] is not None:
                    pics = str(check[0])[2:-3].split(' ')
                    pic_count = len(pics)
            except IndexError:
                pass
            # если не скачаны
            else:
                url = self.site
                page = requests.get(url)
                tree = html.fromstring(page.content)
                zxc = []
                # в список 'zxc' получаем ссылки на все изображения формата jpg
                for x in tree.cssselect('img'):
                    if 'jpg' in x.attrib['src'] or 'JPG' in x.attrib['src']:
                        zxc.append(x.attrib['src'])
                # преобразуем ссылки в нужный вид, сохраняем пути к изображениям в список pics
                for pic_link in zxc:
                    pic_link = 'https:' + pic_link
                    try:
                        with open('pics/' + pic_link.split('/')[-1], 'wb') as f:
                            f.write(requests.get(pic_link).content)
                        pics.append('pics/' + pic_link.split('/')[-1])
                        pic_count += 1
                    except OSError:
                        pass

                # добавляем найденные изображения в историю поиска
                to_add = ''
                for i in range(pic_count):
                    to_add += pics[i] + ' '
                to_add = to_add[:-1]
                cur.execute("""UPDATE search_history SET pics = ? WHERE site = ? AND request = ?
                                                        AND search = ?""",
                            (to_add, self.site, self.word_line.text(), self.search_type))
                con.commit()
                con.close()

    # функция поиска
    def search(self):
        global pic_count
        global pics
        if self.sender().text() == 'Поиск по формам слова':
            self.search_type = 'forms'
        else:
            self.search_type = 'exact'
        a = ''
        current = ''
        self.sites = self.url_line.text().split(' ')
        pic_count = 0
        pics = []
        for self.site in self.sites:
            con = sqlite3.connect('ParsingTool.sqlite')
            cur = con.cursor()
            # обработка неверного ввода
            error = False
            try:
                if requests.get(self.site).status_code != 200:
                    self.error_message('Ошибка в адресе сайта')
                    check = history_check(self.site, self.word_line.text(), self.search_type)
                    if len(check) == 0:
                        cur.execute("""INSERT INTO search_history (site, request, result, search, success)
                                                                    VALUES(?, ?, ?, ?, ?)""",
                                    (self.site, self.word_line.text(), 'неверный адрес', self.search_type, '0'))
                        con.commit()
                    error = True
            except requests.exceptions.MissingSchema or requests.exceptions.InvalidURL:
                self.error_message('Ошибка в адресе сайта')
                check = history_check(self.site, self.word_line.text(), self.search_type)
                if len(check) == 0:
                    cur.execute("""INSERT INTO search_history (site, request, result, search, success)
                                                                VALUES(?, ?, ?, ?, ?)""",
                                (self.site, self.word_line.text(), 'неверный адрес', self.search_type, '0'))
                    con.commit()
                error = True
            if self.site == '' or self.word_line.text() == '':
                self.error_message('Введите адрес и ключевое слово')
                error = True
            # получили верный ввод
            if error is False:
                self.statusBar().hide()
                check = history_check(self.site, self.word_line.text(), self.search_type)
                # одинаковый запрос уже есть в БД? тогда возьмем результаты оттуда
                if len(check) != 0:
                    result = check[0][0]
                # если нет, то выполним поиск через алгоритм
                else:
                    if self.search_type == 'forms':
                        result = Main(self.site, self.word_line.text()).main()
                    else:
                        result = Main(self.site, self.word_line.text()).exact()
                # если ничего не нашли
                if len(result) == 0:
                    self.statusBar().showMessage('Ничего не найдено!')
                    self.statusBar().show()
                    self.result_UI.setText('')
                    cur.execute("""INSERT INTO search_history (site, request, result, search, success)
                                            VALUES(?, ?, ?, ?, ?)""",
                                (self.site, self.word_line.text(), 'ничего не найдено', self.search_type, '0'))
                    con.commit()
                # если нашли
                else:
                    # ссылка на сайт (на случай ввода нескольких адресов)
                    a += '---------------------------------- \n ' + \
                         self.site + ' \n----------------------------------\n '
                    # записываем весь результат поиска в переменные, добавляем в историю поиска
                    for par in result:
                        a += par
                        current += par
                    check = history_check(self.site, self.word_line.text(), self.search_type)
                    if len(check) == 0:
                        cur.execute("""INSERT INTO search_history (site, request, result, search, success)
                        VALUES(?, ?, ?, ?, ?)""", (self.site, self.word_line.text(), current, self.search_type, '1'))
                        con.commit()
                    current = ''
                # выводим результат в главное окно
                self.result_UI.setText(a)
                self.save_but.show()
                self.show_pics.show()

                self.pics()

    def save(self):
        # функция сохранения результата в txt
        try:
            name = QFileDialog.getSaveFileName(self, 'Save File',
                                               ('saved_results/' + self.url_line.text() + ' - '
                                                + self.word_line.text() + '.txt'), '.txt')
            file = open(name[0], 'w', encoding="utf-8")
            text = self.result_UI.toPlainText()
            file.write(text)
            file.close()
        except UnicodeEncodeError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Не удалось декодировать символ в тексте. Файл не был сохранен.")
            msg.setWindowTitle("Ошибка!")
            msg.exec_()
            file.write('Ошибка!')
            file.close()
        except FileNotFoundError:
            pass


class History(QMainWindow):
    def __init__(self, parent=None):
        # инициализация окна с историей поиска, отрисовка таблицы с данными
        super(History, self).__init__(parent)
        uic.loadUi('history.ui', self)

        con = sqlite3.connect('ParsingTool.sqlite')
        cur = con.cursor()
        result = cur.execute('''SELECT * FROM search_history''').fetchall()

        self.tableWidget.setRowCount(len(result))
        self.tableWidget.setColumnCount(7)

        self.tableWidget.setHorizontalHeaderLabels(["ID", "Адрес", "Запрос", "Результат", "Тип поиска",
                                                    "Изображения", "Успешность"])

        for i, row in enumerate(result):
            self.tableWidget.setRowCount(
                self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(row[j])))
        self.tableWidget.setRowCount(len(result))

        con.close()

        self.clear_but.clicked.connect(self.clear)

    def clear(self):
        # очистка истории поиска и удаление изображений
        con = sqlite3.connect('ParsingTool.sqlite')
        cur = con.cursor()
        cur.execute('''PRAGMA foreign_keys = OFF''')
        con.commit()
        cur.execute('''DELETE FROM search_history''')
        con.commit()
        cur.execute('''PRAGMA foreign_keys = ON''')
        con.commit()
        con.close()
        self.tableWidget.clear()
        folder = 'pics'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)


class Settings(QMainWindow):
    def __init__(self, parent=None):
        # инициализация интерфейса окна пользовательских настроек
        super(Settings, self).__init__(parent)
        uic.loadUi('UI_settings.ui', self)

        con = sqlite3.connect('ParsingTool.sqlite')
        cur = con.cursor()
        a = cur.execute('''SELECT font_size FROM settings''').fetchall()
        a = a[0][0]
        self.font_line.setText(str(a))

        a = cur.execute('''SELECT theme FROM settings''').fetchall()
        a = a[0][0]
        self.theme_line.setCurrentText(a)

        con.close()

        self.font_line.textChanged.connect(self.set_font_size)
        self.theme_line.currentTextChanged.connect(self.set_theme)

    def set_font_size(self):
        # изменение размера шрифта
        con = sqlite3.connect('ParsingTool.sqlite')
        cur = con.cursor()
        size = self.sender().text()
        try:
            if 40 > int(size) > 5:
                app.setStyleSheet("QLabel, QTextEdit, QLineEdit, QStatusBar{font-size: " + size + "pt;}")
                cur.execute('''UPDATE settings SET font_size = ?''', (self.sender().text(),))
        except ValueError:
            pass
        con.commit()
        con.close()

    def set_theme(self):
        # переключение темы
        con = sqlite3.connect('ParsingTool.sqlite')
        cur = con.cursor()
        theme = self.sender().currentText()
        cur.execute('''UPDATE settings SET theme = ?''', (theme,))
        con.commit()
        con.close()
        msg = QMessageBox()
        msg.setText("Для сохранения изменений перезапустите приложение.")
        msg.setWindowTitle("Переключение темы")
        msg.exec_()


class Pictures(QMainWindow):
    def __init__(self, parent=None):
        # инициализация окна для вывода изображений, отображение первых трех
        super(Pictures, self).__init__(parent)
        uic.loadUi('pics.ui', self)

        self.count = 0

        try:
            self.pixmap = QPixmap(pics[self.count])
            self.image = self.pic_1
            self.image.setPixmap(self.pixmap)
        except IndexError:
            self.pic_1.setText('Пусто')
        try:
            self.pixmap = QPixmap(pics[self.count + 1])
            self.image = self.pic_2
            self.image.setPixmap(self.pixmap)
        except IndexError:
            self.pic_2.setText('Пусто')
        try:
            self.pixmap = QPixmap(pics[self.count + 2])
            self.image = self.pic_3
            self.image.setPixmap(self.pixmap)
        except IndexError:
            self.pic_3.setText('Пусто')

        self.next_but.clicked.connect(self.next_prev)
        self.prev_but.clicked.connect(self.next_prev)

    def next_prev(self):
        # прокрутка ленты изображений назад-вперед
        if self.sender().text() == 'Далее --->':
            if self.count <= pic_count - 3:
                self.count += 3
        else:
            if self.count >= 3:
                self.count -= 3

        try:
            self.pixmap = QPixmap(pics[self.count])
            self.image = self.pic_1
            self.image.setPixmap(self.pixmap)
        except IndexError:
            self.pic_1.setText('Пусто')
        try:
            self.pixmap = QPixmap(pics[self.count + 1])
            self.image = self.pic_2
            self.image.setPixmap(self.pixmap)
        except IndexError:
            self.pic_2.setText('Пусто')
        try:
            self.pixmap = QPixmap(pics[self.count + 2])
            self.image = self.pic_3
            self.image.setPixmap(self.pixmap)
        except IndexError:
            self.pic_3.setText('Пусто')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
