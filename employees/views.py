from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db import connection
from .models import Message
import json


def homepage(request):
    if request.method == 'POST':
        text = request.POST.get("text", "")
        language = request.POST.get("language", "ua")
        platform = request.POST.get("platform", "Unknown")
        if language == "ua":
            transliterated_text = transliterate_ua_text(text)
        elif language == "ru":
            transliterated_text = transliterate_ru_text(text)
        else:
            transliterated_text = text

        Message.objects.create(
            id_chat=None,
            platform=platform,
            lang=language,
            message=transliterated_text
        )

        return JsonResponse({'transliterated_text': transliterated_text})
    return render(request, 'homepage.html')


def transliterate_ua_text(input_text):
    # Translation table for faster replacements
    translation_table = str.maketrans({
        "q": "й", "w": "ц", "e": "у", "r": "к", "t": "е", "y": "н", "u": "г", "i": "ш", "o": "щ", "p": "з",
        "[": "х", "]": "ї", "a": "ф", "s": "і", "d": "в", "f": "а", "g": "п", "h": "р", "j": "о", "k": "л",
        "l": "д", ";": "ж", "'": "є", "\\": "ґ", "z": "я", "x": "ч", "c": "с", "v": "м", "b": "и", "n": "т",
        "m": "ь", ",": "б", ".": "ю", "Q": "Й", "W": "Ц", "E": "У", "R": "К", "T": "Е", "Y": "Н", "U": "Г",
        "I": "Ш", "O": "Щ", "P": "З", "{": "Х", "}": "Ї", "A": "Ф", "S": "І", "D": "В", "F": "А", "G": "П",
        "H": "Р", "J": "О", "K": "Л", "L": "Д", ":": "Ж", "\"": "Є", "|": "Ґ", "Z": "Я", "X": "Ч", "C": "С",
        "V": "М", "B": "И", "N": "Т", "M": "Ь", "<": "Б", ">": "Ю", "@": "\"", "#": "№", "$": ";", "^": ":",
        "?": ",", "/": "."
    })

    return input_text.translate(translation_table)


def transliterate_ru_text(input_text):
    # Create a translation table
    translation_table = str.maketrans({
        "q": "й", "w": "ц", "e": "у", "r": "к", "t": "е", "y": "н", "u": "г", "i": "ш", "o": "щ", "p": "з",
        "[": "х", "]": "ъ", "a": "ф", "s": "ы", "d": "в", "f": "а", "g": "п", "h": "р", "j": "о", "k": "л",
        "l": "д", ";": "ж", "'": "э", "z": "я", "x": "ч", "c": "с", "v": "м", "b": "и", "n": "т", "m": "ь",
        ",": "б", ".": "ю", "Q": "Й", "W": "Ц", "E": "У", "R": "К", "T": "Е", "Y": "Н", "U": "Г", "I": "Ш",
        "O": "Щ", "P": "З", "{": "Х", "}": "Ъ", "A": "Ф", "S": "Ы", "D": "В", "F": "А", "G": "П", "H": "Р",
        "J": "О", "K": "Л", "L": "Д", ":": "Ж", "\"": "Э", "Z": "Я", "X": "Ч", "C": "С", "V": "М", "B": "И",
        "N": "Т", "M": "Ь", "<": "Б", ">": "Ю", "@": "\"", "#": "№", "$": ";", "^": ":", "?": ",", "/": "."
    })

    # Use translate to transform the input text
    return input_text.translate(translation_table)

def employee_list(request):
    # Connect to the database and execute the query
    with connection.cursor() as cursor:
        query = """
            SELECT e.first_name, e.last_name, e.salary
            FROM employees e
            WHERE e.salary > 10000;
        """
        cursor.execute(query)
        results = cursor.fetchall()  # Fetch all results as a list of tuples

    employees = [{'first_name': row[0], 'last_name': row[1], 'salary': row[2]} for row in results]

    # Pass the results to the template
    return render(request, 'employees/employee_list.html', {'employees': employees})
