import requests
from bs4 import BeautifulSoup
import pymorphy2
morph = pymorphy2.MorphAnalyzer()


class Main:
    def __init__(self, url, word):
        self.url = url
        self.word = word

    # pymorphy2 везде, где возможно, пишет 'ё',
    # поэтому, в опр. случаях, на выходе необходимо заменить все 'ё' на 'е'
    def output_convert(self, word_input):
        if 'ё' in self.word:
            return word_input
        else:
            while 'ё' in word_input:
                word_input = word_input.replace('ё', 'е')
            return word_input

    def spaces_check(self, word_form, word_form_capital, paragraph):
        word_forms = [word_form, word_form_capital]
        check_par = paragraph + ' '
        for x in word_forms:
            while x in check_par:
                index = check_par.find(x)
                if index != -1:
                    if check_par[index - 1].isalpha() is False or check_par[index - 1] == 'n' or \
                            index == 0:
                        if check_par != x:
                            if check_par[index + len(x)].isalpha() is False \
                                    or check_par[index + len(x)] == '.':
                                check_par = check_par.replace(x, '', 1)
                                return True
                            else:
                                check_par = check_par.replace(x, '', 1)
                        else:
                            check_par = check_par.replace(x, '', 1)
                            return True
                    else:
                        check_par = check_par.replace(x, '', 1)

    def main(self):
        # получаем весь текст с сайта
        # тег div выводит много мусора - есть ли смысл его искать?
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'lxml')
        # TODO: определиться с полным набором тегов html, где может находиться нужный текст
        paragraphs = soup.find_all('p') + soup.find_all('li')

        # перевод в читабельный вид, удаление лишних переносов и т.д.
        for i in range(len(paragraphs)):
            paragraphs[i] = paragraphs[i].text
            while '\n\n' in paragraphs[i]:
                paragraphs[i] = paragraphs[i].replace('\n\n', '')

        # ввод слова и подготовка к использованию pymorphy2
        word = self.word
        word1 = morph.parse(word)[0]
        res = morph.parse(word)[0]

        # ОЧЕНЬ костыльный метод преобразования глагола сов. вида в несов.. Pymorphy2, похоже, такой функционал не поддерживает
        # TODO: придумать что-нибудь для работы с видами глагола
        if "VERB" in res.tag or "INFN" in res.tag:
            word_form = word
            word_form_capital = word.capitalize()
            used_par = []
            for paragraph in paragraphs:
                if word_form in paragraph or word_form_capital in paragraph:
                    if Main.spaces_check(self, word_form, word_form_capital, paragraph) and paragraph not in used_par:
                        used_par.append(paragraph)
                        return paragraph
            if word[:1] == 'вы' or word[:1] == 'за' or word[:1] == 'на' or word[:2] == 'по':
                word = word[2:]
            if word[:3] == 'про' or word[:3] == 'рас':
                word = word[3:]
            if word[0] == 'с' or word[0] == 'у':
                word = word[1:]

        word1 = morph.parse(word)[0]
        res = morph.parse(word)[0]

        result = []

        # проверка на наличие всех форм существительного в параграфах
        if "NOUN" in res.tag:
            forms = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']
            numbers = ['sing', 'plur']

            used_par = []
            for paragraph in paragraphs:
                for form in forms:
                    for number in numbers:

                        word_form = Main.output_convert(self, word1.inflect({form, number}).word)
                        word_form_capital = Main.output_convert(self, word1.inflect({form, number}).word).capitalize()

                        if word_form in paragraph or word_form_capital in paragraph:
                            if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                    and paragraph not in used_par:
                                used_par.append(paragraph)
                                result.append(paragraph)

        # проверка на наличие всех форм глагола в параграфах
        used_par = []
        if "VERB" in res.tag or "INFN" in res.tag:
            persons = ['1per', '2per', '3per']
            tensions = ['pres', 'past']
            moods = ['indc', 'impr']
            numbers = ['sing', 'plur']
            genders = ['masc', 'femn', 'neut']

            for paragraph in paragraphs:
                for person in persons:
                    for tens in tensions:
                        for mood in moods:
                            for number in numbers:
                                for gender in genders:

                                    if tens == 'past':
                                        if number == 'plur':
                                            word_form = Main.output_convert(self, word1.inflect({tens, number}).word)
                                            word_form_capital = \
                                                Main.output_convert(self, word1.inflect({tens, number}).word)\
                                                    .capitalize()
                                        else:
                                            word_form = Main.output_convert(self, word1.inflect({tens, number, gender})
                                                                            .word)
                                            word_form_capital = \
                                                Main.output_convert(self, word1.inflect({tens, number, gender}).word)\
                                                    .capitalize()
                                    if tens == 'pres':
                                        if number == 'sing':
                                            word_form = Main.output_convert(self, word1.inflect({tens, number, gender})
                                                                            .word)
                                            word_form_capital = \
                                                Main.output_convert(self, word1.inflect({tens, number, gender}).word)\
                                                    .capitalize()
                                        else:
                                            word_form = Main.output_convert(self, word1.inflect({tens, number, person})
                                                                            .word)
                                            word_form_capital = \
                                                Main.output_convert(self, word1.inflect({tens, number, person}).word)\
                                                    .capitalize()

                                    if word_form in paragraph or word_form_capital in paragraph:
                                        if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                                and paragraph not in used_par:
                                            used_par.append(paragraph)
                                            result.append(paragraph)

        # TODO: необходимо реализовать поиск формы глагола будущего времени, что зависит от вида глагола

        # проверка на наличие всех форм количественного числительного в параграфах
        if "NUMR" in res.tag:
            forms = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']

            for paragraph in paragraphs:
                for form in forms:

                    word_form = Main.output_convert(self, word1.inflect({form}).word)
                    word_form_capital = Main.output_convert(self, word1.inflect({form}).word).capitalize()

                    if word_form in paragraph or word_form_capital in paragraph:
                        if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                and paragraph not in used_par:
                            used_par.append(paragraph)
                            result.append(paragraph)

        # проверка на наличие всех форм порядкового числительного в параграфах
        if "ADJF" in res.tag and "Anum" in res.tag:
            forms = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']
            genders = ['masc', 'femn', 'neut']
            numbers = ['sing', 'plur']

            for paragraph in paragraphs:
                for form in forms:
                    for gender in genders:
                        for number in numbers:

                            if number == 'plur':
                                word_form = Main.output_convert(self, word1.inflect({form, number}).word)
                                word_form_capital = Main.output_convert(self, word1.inflect({form, number}).word)\
                                    .capitalize()

                            else:
                                word_form = Main.output_convert(self, word1.inflect({form, gender, number}).word)
                                word_form_capital = Main.output_convert(self, word1.inflect({
                                    form, gender, number}).word).capitalize()

                            if word_form in paragraph or word_form_capital in paragraph:
                                if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                        and paragraph not in used_par:
                                    used_par.append(paragraph)
                                    result.append(paragraph)

        # проверка на наличие всех форм полного прилагательного в параграфах
        if "ADJF" in res.tag and "Anum" not in res.tag:
            # проверка сравнительынх степеней
            if "Qual" in res.tag:
                comps = ['COMP', 'Cmp2', 'V-ej']
                for paragraph in paragraphs:
                    for comp in comps:

                        word_form = Main.output_convert(self, word1.inflect({comp}).word)
                        word_form_capital = Main.output_convert(self, word1.inflect({comp}).word).capitalize()

                        if word_form in paragraph or word_form_capital in paragraph:
                            if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                    and paragraph not in used_par:
                                used_par.append(paragraph)
                                result.append(paragraph)
            # TODO: проверить работоспособнсть проверки сравнительных степеней

            genders = ['masc', 'femn', 'neut']
            numbers = ['sing', 'plur']
            forms = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']

            used_par = []
            for paragraph in paragraphs:
                for gender in genders:
                    for number in numbers:
                        for form in forms:

                            if number == 'plur':
                                word_form = Main.output_convert(self, word1.inflect({number, form}).word)
                                word_form_capital = Main.output_convert(self, word1.inflect({number, form}).word)\
                                    .capitalize()

                            else:
                                word_form = Main.output_convert(self, word1.inflect({gender, number, form}).word)
                                word_form_capital = Main.output_convert(self, word1.inflect({gender, number, form})
                                                                        .word).capitalize()

                            if word_form in paragraph or word_form_capital in paragraph:
                                if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                        and paragraph not in used_par:
                                    used_par.append(paragraph)
                                    result.append(paragraph)

        # проверка на наличие всех форм краткого прилагательного в параграфах
        if "ADJS" in res.tag:
            genders = ['masc', 'femn', 'neut']
            numbers = ['sing', 'plur']

            used_par = []
            for paragraph in paragraphs:
                for gender in genders:
                    for number in numbers:
                        check = False

                        if number == 'sing':
                            word_form = Main.output_convert(self, word1.inflect({number, gender}).word)
                            word_form_capital = Main.output_convert(self, word1.inflect({number, gender}).word)\
                                .capitalize()

                        else:
                            word_form = Main.output_convert(self, word1.inflect({number}).word)
                            word_form_capital = Main.output_convert(self, word1.inflect({number}).word).capitalize()

                        if word_form in paragraph or word_form_capital in paragraph:
                            if Main.spaces_check(self, word_form, word_form_capital, paragraph)\
                                    and paragraph not in used_par:
                                used_par.append(paragraph)
                                result.append(paragraph)

        # проверка на наличие всех форм полного причастия в параграфах
        if "PRTF" in res.tag:
            genders = ['masc', 'femn', 'neut']
            numbers = ['sing', 'plur']
            forms = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']

            used_par = []
            for paragraph in paragraphs:
                for gender in genders:
                    for number in numbers:
                        for form in forms:

                            if number == 'plur':
                                word_form = Main.output_convert(self, word1.inflect({form, number}).word)
                                word_form_capital = Main.output_convert(self, word1.inflect({form, number}).word)\
                                    .capitalize()

                            else:
                                word_form = Main.output_convert(self, word1.inflect({gender, number, form}).word)
                                word_form_capital = Main.output_convert(self, word1.inflect({gender, number, form})
                                                                        .word).capitalize()

                            if word_form in paragraph or word_form_capital in paragraph:
                                if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                        and paragraph not in used_par:
                                    used_par.append(paragraph)
                                    result.append(paragraph)

        # проверка на наличие всех форм краткого причастия в параграфах
        if "PRTS" in res.tag:
            genders = ['masc', 'femn', 'neut']
            numbers = ['sing', 'plur']

            used_par = []
            for paragraph in paragraphs:
                for gender in genders:
                    for number in numbers:

                        if number == 'plur':
                            word_form = Main.output_convert(self, word1.inflect({number}).word)
                            word_form_capital = Main.output_convert(self, word1.inflect({number}).word).capitalize()

                        else:
                            word_form = Main.output_convert(self, word1.inflect({gender, number}).word)
                            word_form_capital = Main.output_convert(self, word1.inflect({gender, number}).word)\
                                .capitalize()

                        if word_form in paragraph or word_form_capital in paragraph:
                            if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                    and paragraph not in used_par:
                                used_par.append(paragraph)
                                result.append(paragraph)

        # проверка на наличие всех форм деепричастия в параграфах
        if "GRND" in res.tag:

            for paragraph in paragraphs:
                word_form = word
                word_form_capital = word.capitalize()

                if word_form in paragraph or word_form_capital in paragraph:
                    if Main.spaces_check(self, word_form, word_form_capital, paragraph) and paragraph not in used_par:
                        used_par.append(paragraph)
                        result.append(paragraph)

        # проверка на наличие наречия в параграфах
        if "ADVB" in res.tag:

            for paragraph in paragraphs:
                word_form = word
                word_form_capital = word.capitalize()

                if word_form in paragraph or word_form_capital in paragraph:
                    if Main.spaces_check(self, word_form, word_form_capital, paragraph) and paragraph not in used_par:
                        used_par.append(paragraph)
                        result.append(paragraph)

        if "NPRO" in res.tag:

            forms = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']

            for paragraph in paragraphs:
                for form in forms:
                    word_form = Main.output_convert(self, word1.inflect({form}).word)
                    word_form_capital = Main.output_convert(self, word1.inflect({form}).word).capitalize()

                    if word_form in paragraph or word_form_capital in paragraph:
                        if Main.spaces_check(self, word_form, word_form_capital, paragraph) \
                                and paragraph not in used_par:
                            used_par.append(paragraph)
                            result.append(paragraph)

        if "PREP" in res.tag or "CONJ" in res.tag or "PRCL" in res.tag or "INTJ" in res.tag:

            for paragraph in paragraphs:
                word_form = word
                word_form_capital = word.capitalize()

                if word_form in paragraph or word_form_capital in paragraph:
                    if Main.spaces_check(self, word_form, word_form_capital, paragraph) and paragraph not in used_par:
                        used_par.append(paragraph)
                        result.append(paragraph)

        for elem in range(len(result)):
            if '\n' in result[elem]:
                result[elem] = result[elem].replace('\n', '')
            if '\xa0' in result[elem]:
                result[elem] = result[elem].replace('\xa0', ' ')

        return result

    def exact(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'lxml')
        # TODO: определиться с полным набором тегов html, где может находиться нужный текст
        paragraphs = soup.find_all('p') + soup.find_all('li')

        # перевод в читабельный вид, удаление лишних переносов и т.д.
        for i in range(len(paragraphs)):
            paragraphs[i] = paragraphs[i].text
            while '\n\n' in paragraphs[i]:
                paragraphs[i] = paragraphs[i].replace('\n\n', '')

        # ввод слова
        word = self.word

        # поиск совпадений по параграфам
        result = []
        used_par = []
        for paragraph in paragraphs:
            if word in paragraph and paragraph not in used_par:
                result.append(paragraph)
                used_par.append(paragraph)

        for elem in range(len(result)):
            if '\n' in result[elem]:
                result[elem] = result[elem].replace('\n', '')
            if '\xa0' in result[elem]:
                result[elem] = result[elem].replace('\xa0', ' ')

        # возвращение результата
        return result
