import random
import datetime
import inspect


class Generator(object):
    empty_value = None

    def __init__(self, required=True, null=False, empty_chance=0.1,
                 empty_value=None, pattern=None, coerce=None):
        self.required = required
        self.null = null
        self.empty_chance = empty_chance
        self.pattern = pattern
        self.coerce = coerce

        if empty_value is not None:
            self.empty_value = empty_value

    def __add__(self, other):
        return ComboGenerator([self, other])

    def __radd__(self, other):
        return ComboGenerator([other, self])

    def generate(self):
        if self.null:
            if random.random() < self.empty_chance:
                return None

        if not self.required:
            if random.random() < self.empty_chance:
                return self.empty_value

        result = self._get()
        if self.pattern:
            result = self.pattern.replace('<gen>', str(result))

        if self.coerce:
            result = self.coerce(result)

        return result

    def _get(self):
        raise NotImplementedError('Subclasses must define this method.')


class IntGenerator(Generator):
    empty_value = 0

    def __init__(self, min=0, max=9999, *args, **kwargs):
        self.min = min
        self.max = max
        super(IntGenerator, self).__init__(*args, **kwargs)

    def _get(self):
        return random.randint(self.min, self.max)


class StrGenerator(Generator):
    empty_value = ''

    def __init__(self, alphabet='0123456789abcdef', min_len=3, max_len=10,
                 *args, **kwargs):
        self.alphabet = alphabet
        self.min_len = min_len
        self.max_len = max_len
        super(StrGenerator, self).__init__(*args, **kwargs)

    def _get(self):
        n = random.randint(self.min_len, self.max_len)
        return ''.join([random.choice(self.alphabet) for _ in range(n)])


class WordsGenerator(Generator):
    empty_value = ''
    vowels = 'aeiouy'
    consonants = 'bcdfghjklmnpqrstvwxz'

    def __init__(self, amount=1, min_len=3, max_len=8, capital=False,
                 uppercase=False, *args, **kwargs):
        self.amount = amount
        self.min_len = min_len
        self.max_len = max_len
        self.capital = capital
        self.uppercase = uppercase
        super(WordsGenerator, self).__init__(*args, **kwargs)

    def _get_letter(self):
        vowels_ratio = 0
        if self.status == '':
            vowels_ratio = 0.4
        elif self.status == 'v':
            vowels_ratio = 0.2
        elif self.status == 'vv':
            vowels_ratio = -0.1
        elif self.status == 'c':
            vowels_ratio = 0.7
        elif self.status == 'cc':
            vowels_ratio = 1.1

        alf = None
        if random.random() < vowels_ratio:
            alf = self.vowels
            if 'c' in self.status:
                self.status = 'v'
            else:
                self.status += 'v'
        else:
            alf = self.consonants
            if 'v' in self.status:
                self.status = 'c'
            else:
                self.status += 'c'

        return random.choice(alf)

    def _get_word(self):
        self.status = ''
        word = ''
        n = random.randint(self.min_len, self.max_len)

        for i in range(n):
            word += self._get_letter()

        if self.capital:
            word = word.capitalize()
        if self.uppercase:
            word = word.upper()

        return word

    def _get(self):
        words = []
        for i in range(self.amount):
            words.append(self._get_word())
        return " ".join(words)


class TextGenerator(Generator):
    empty_value = ''
    spacers = ['is', 'in', 'of', 'are', 'a', 'an', 'the',
               'for', 'and', 'or', 'by', 'to']

    def __init__(self, min_len=30, max_len=150, uppercase=False,
                 *args, **kwargs):
        self.min_len = min_len
        self.max_len = max_len
        self.uppercase = uppercase
        self.words_gen = WordsGenerator(amount=1, min_len=4, max_len=8)
        super(TextGenerator, self).__init__(*args, **kwargs)

    def _get_sentence(self):
        spacer_time = random.randint(2, 4)
        words_amount = random.randint(4, 12)
        comma = False
        words = []

        for i in range(words_amount):
            words.append(self.words_gen.generate())
            spacer_time -= 1

            if spacer_time <= 0:
                words.append(random.choice(self.spacers))
                spacer_time = random.randint(2, 4)

            if comma is False and i >= 2 and i < words_amount - 2:
                if random.random() < 0.25:
                    words[-1] = words[-1] + ','
                    comma = True

        sentence = " ".join(words)
        if random.random() < 0.2:
            sentence += '!'
        else:
            sentence += '.'

        return sentence.capitalize()

    def _get(self):
        text = ''
        length = random.randint(self.min_len, self.max_len)

        while(len(text) <= length):
            text += self._get_sentence() + ' '

        text = text.strip()
        if len(text) > self.max_len:
            text = text[:self.max_len - 1].strip() + '.'

        if self.uppercase:
            text = text.upper()

        return text


class ChoiceGenerator(Generator):
    empty_value = ''

    def __init__(self, choices=[], amount=1, separator=' ', *args, **kwargs):
        self.choices = choices
        self.amount = amount
        self.separator = separator
        super(ChoiceGenerator, self).__init__(*args, **kwargs)

    def _get(self):
        if self.amount == 1:
            return random.choice(self.choices)
        else:
            return self.separator.join([random.choice(self.choices)
                                        for _ in range(self.amount)])


class DateGenerator(Generator):
    empty_value = None

    def __init__(self, min_date=datetime.datetime(1960, 01, 01),
                 max_date=datetime.datetime.now(), *args, **kwargs):
        self.min_date = min_date
        self.max_date = max_date
        super(DateGenerator, self).__init__(*args, **kwargs)

    def _get(self):
        delta = self.max_date - self.min_date
        seconds_delta = (delta.days * 25 * 60 * 60) + delta.seconds

        return self.min_date + \
            datetime.timedelta(seconds=random.randint(0, seconds_delta))


class ComboGenerator(Generator):
    empty_value = None

    def __init__(self, objects, *args, **kwargs):
        self.objects = objects
        super(ComboGenerator, self).__init__(*args, **kwargs)

    def __add__(self, other):
        self.objects.append(other)
        return self

    def __radd__(self, other):
        self.objects.insert(0, other)
        return self

    def _get(self):
        chunks = []
        for obj in self.objects:
            parents = inspect.getmro(type(obj))
            if any(parent == Generator for parent in parents):
                chunks.append(obj.generate())
            else:
                chunks.append(obj)

        if len(chunks):
            result = None
            try:
                result = chunks[0]
                for i in range(1, len(chunks)):
                    result += chunks[i]
            except:
                result = ''
                for chunk in chunks:
                    result += str(chunk)
            return result
        return None
