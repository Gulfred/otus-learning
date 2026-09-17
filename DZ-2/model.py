"""Модель телефонного справочника.

В этом модуле находятся данные, бизнес-логика и работа с JSON-файлом.
"""

import json
import os


class PhoneBookError(Exception):
    """Базовое исключение телефонного справочника."""


class ValidationError(PhoneBookError):
    """Ошибка проверки введённых данных."""


class ContactNotFoundError(PhoneBookError):
    """Контакт с указанным ID не найден."""


class FileReadError(PhoneBookError):
    """Не удалось прочитать справочник из файла."""


class FileWriteError(PhoneBookError):
    """Не удалось записать справочник в файл."""


class InvalidIdError(PhoneBookError):
    """ID должен быть положительным целым числом."""


class InvalidMenuChoiceError(PhoneBookError):
    """Пользователь выбрал отсутствующий пункт меню."""


class Contact:
    """Контакт телефонного справочника."""

    def __init__(self, contact_id, name, phone, comment=""):
        self.id = self._validate_id(contact_id)
        self.name = self.validate_name(name)
        self.phone = self.validate_phone(phone)
        self.comment = "" if comment is None else str(comment).strip()

    @staticmethod
    def _validate_id(contact_id):
        if isinstance(contact_id, bool):
            raise InvalidIdError("ID должен быть положительным числом.")

        try:
            contact_id = int(contact_id)
        except (TypeError, ValueError) as error:
            raise InvalidIdError("ID должен быть положительным числом.") from error

        if contact_id < 1:
            raise InvalidIdError("ID должен быть положительным числом.")
        return contact_id

    @staticmethod
    def validate_name(name):
        """Проверяет имя и возвращает его без лишних пробелов."""
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Имя контакта не может быть пустым.")
        return name.strip()

    @staticmethod
    def validate_phone(phone):
        """Проверяет номер телефона и возвращает нормализованную строку."""
        if phone is None or not str(phone).strip():
            raise ValidationError("Номер телефона не может быть пустым.")

        phone = str(phone).strip()
        if phone.count("+") > 1 or ("+" in phone and not phone.startswith("+")):
            raise ValidationError("Знак '+' может находиться только в начале номера.")

        if not all(character.isdigit() or character == "+" for character in phone):
            raise ValidationError("Номер телефона может содержать только цифры и '+'.")

        digits_count = sum(character.isdigit() for character in phone)
        if digits_count < 5:
            raise ValidationError("Номер телефона должен содержать минимум 5 цифр.")

        return phone

    @property
    def description(self):
        """Старое имя поля, оставленное для совместимости с заготовкой DZ-2."""
        return self.comment

    @description.setter
    def description(self, value):
        self.comment = "" if value is None else str(value).strip()

    def to_dict(self):
        """Преобразует объект контакта в словарь для JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data):
        """Создаёт контакт из словаря, прочитанного из JSON."""
        if not isinstance(data, dict):
            raise ValidationError("Данные контакта должны быть объектом JSON.")

        try:
            comment = data.get("comment", data.get("description", ""))
            return cls(data["id"], data["name"], data["phone"], comment)
        except KeyError as error:
            raise ValidationError(f"В данных контакта отсутствует поле: {error.args[0]}.") from error

    def __str__(self):
        comment = self.comment if self.comment else "нет"
        return (
            f"ID: {self.id}, Имя: {self.name}, "
            f"Телефон: {self.phone}, Комментарий: {comment}"
        )


class FileReader:
    """Читает данные телефонного справочника из JSON-файла."""

    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        """Возвращает данные файла или пустой справочник, если файла нет."""
        if not os.path.exists(self.file_path):
            return {"contacts": [], "next_id": 1}

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise FileReadError(f"Не удалось прочитать файл: {self.file_path}") from error

        if not isinstance(data, dict):
            raise FileReadError("Файл справочника должен содержать JSON-объект.")
        return data


class FileWriter:
    """Записывает данные телефонного справочника в JSON-файл."""

    def __init__(self, file_path):
        self.file_path = file_path

    def write(self, phone_book):
        """Сохраняет переданный объект PhoneBook в JSON."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump(phone_book.to_dict(), file, ensure_ascii=False, indent=2)
        except (OSError, TypeError) as error:
            raise FileWriteError(f"Не удалось записать файл: {self.file_path}") from error


class PhoneBook:
    """Хранит контакты и выполняет операции над ними."""

    def __init__(self):
        self.contacts = []
        self.next_id = 1
        self.changed = False

    def load_data(self, data):
        """Загружает контакты из словаря, полученного от FileReader."""
        if not isinstance(data, dict):
            raise FileReadError("Данные справочника должны быть JSON-объектом.")

        contacts_data = data.get("contacts", [])
        if not isinstance(contacts_data, list):
            raise FileReadError("Поле contacts в JSON должно быть списком.")

        try:
            contacts = [Contact.from_dict(item) for item in contacts_data]
        except PhoneBookError as error:
            raise FileReadError("В JSON содержатся некорректные данные контакта.") from error

        ids = [contact.id for contact in contacts]
        if len(ids) != len(set(ids)):
            raise FileReadError("В JSON обнаружены повторяющиеся ID контактов.")

        file_next_id = data.get("next_id", 1)
        try:
            file_next_id = int(file_next_id)
        except (TypeError, ValueError) as error:
            raise FileReadError("Поле next_id в JSON должно быть числом.") from error

        maximum_id = max(ids, default=0)
        self.contacts = contacts
        self.next_id = max(file_next_id, maximum_id + 1, 1)
        self.changed = False

    def _get_next_available_id(self):
        """Возвращает первый свободный положительный ID."""
        existing_ids = {contact.id for contact in self.contacts}
        contact_id = 1
        while contact_id in existing_ids:
            contact_id += 1
        return contact_id

    def add_contact(self, name, phone, comment=""):
        """Проверяет и добавляет новый контакт."""
        contact_id = self._get_next_available_id()
        contact = Contact(contact_id, name, phone, comment)
        self.contacts.append(contact)
        self.next_id = max(self.next_id, contact_id + 1)
        self.changed = True
        return contact

    def get_all_contacts(self):
        """Возвращает контакты, отсортированные по ID."""
        return sorted(self.contacts, key=lambda contact: contact.id)

    def get_contact(self, contact_id):
        """Возвращает контакт по ID или вызывает ContactNotFoundError."""
        contact_id = Contact._validate_id(contact_id)
        for contact in self.contacts:
            if contact.id == contact_id:
                return contact
        raise ContactNotFoundError(f"Контакт с ID {contact_id} не найден.")

    def find_contacts(self, query, search_field="all"):
        """Ищет контакты по одному полю или по всем полям."""
        if not isinstance(query, str) or not query.strip():
            raise ValidationError("Поисковый запрос не может быть пустым.")

        valid_fields = {"all", "name", "phone", "comment"}
        if search_field not in valid_fields:
            raise ValidationError("Указано неизвестное поле для поиска.")

        query = query.strip().lower()
        found_contacts = []

        for contact in self.contacts:
            fields = {
                "name": contact.name.lower(),
                "phone": contact.phone.lower(),
                "comment": contact.comment.lower(),
            }

            if search_field == "all":
                is_found = any(query in value for value in fields.values())
            else:
                is_found = query in fields[search_field]

            if is_found:
                found_contacts.append(contact)

        return found_contacts

    def update_contact(self, contact_id, name=None, phone=None, comment=None):
        """Изменяет переданные поля существующего контакта."""
        if name is None and phone is None and comment is None:
            raise ValidationError("Укажите хотя бы одно поле для изменения.")

        contact = self.get_contact(contact_id)

        if name is not None:
            contact.name = Contact.validate_name(name)
        if phone is not None:
            contact.phone = Contact.validate_phone(phone)
        if comment is not None:
            contact.comment = str(comment).strip()

        self.changed = True
        return contact

    def delete_contact(self, contact_id):
        """Удаляет контакт по ID."""
        contact = self.get_contact(contact_id)
        self.contacts.remove(contact)
        self.changed = True
        return contact

    def mark_saved(self):
        """Помечает справочник как сохранённый."""
        self.changed = False

    def to_dict(self):
        """Возвращает данные справочника в формате contacts.json."""
        return {
            "contacts": [contact.to_dict() for contact in self.get_all_contacts()],
            "next_id": self.next_id,
        }
