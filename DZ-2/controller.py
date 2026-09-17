"""Контроллер телефонного справочника.

Контроллер получает данные от View, передаёт их в Model и показывает результат.
"""

import os

from model import (
    FileReader,
    FileWriter,
    InvalidIdError,
    InvalidMenuChoiceError,
    PhoneBook,
    PhoneBookError,
)
from view import View


class PhoneBookController:
    """Управляет работой приложения и связывает Model с View."""

    def __init__(self, file_path, view=None):
        self.phone_book = PhoneBook()
        self.file_reader = FileReader(file_path)
        self.file_writer = FileWriter(file_path)
        self.view = view or View()
        self.is_open = False

    def _read_choice(self, allowed_choices):
        """Читает пункт меню и проверяет, что он существует."""
        choice = self.view.get_menu_choice()
        if choice not in allowed_choices:
            raise InvalidMenuChoiceError("Выбран несуществующий пункт меню.")
        return choice

    @staticmethod
    def _parse_id(value):
        """Преобразует введённый ID в положительное число."""
        try:
            contact_id = int(value)
        except (TypeError, ValueError) as error:
            raise InvalidIdError("ID должен быть целым положительным числом.") from error

        if contact_id < 1:
            raise InvalidIdError("ID должен быть целым положительным числом.")
        return contact_id

    def open_phone_book(self):
        """Открывает существующий справочник или создаёт пустой в памяти."""
        data = self.file_reader.read()
        self.phone_book.load_data(data)
        self.is_open = True
        self.view.show_message("Справочник открыт.")

    def save_phone_book(self):
        """Сохраняет справочник и сбрасывает признак изменений."""
        self.file_writer.write(self.phone_book)
        self.phone_book.mark_saved()
        self.view.show_message("Справочник сохранён.")

    def add_contact(self):
        name, phone, comment = self.view.get_new_contact_data()
        contact = self.phone_book.add_contact(name, phone, comment)
        self.view.show_message(f"Контакт «{contact.name}» добавлен.")

    def show_all_contacts(self):
        self.view.show_contacts(self.phone_book.get_all_contacts())

    def find_contacts(self):
        self.view.show_search_menu()
        search_choice = self._read_choice({"1", "2", "3", "4"})
        search_fields = {
            "1": "all",
            "2": "name",
            "3": "phone",
            "4": "comment",
        }
        query = self.view.get_search_query()
        contacts = self.phone_book.find_contacts(query, search_fields[search_choice])
        self.view.show_search_results(contacts)

    def update_contact(self):
        self.show_all_contacts()
        contact_id = self._parse_id(self.view.get_contact_id("изменения"))
        contact = self.phone_book.get_contact(contact_id)
        update_data = self.view.get_update_data(contact)
        self.phone_book.update_contact(contact_id, **update_data)
        self.view.show_message("Контакт изменён.")

    def delete_contact(self):
        self.show_all_contacts()
        contact_id = self._parse_id(self.view.get_contact_id("удаления"))
        contact = self.phone_book.delete_contact(contact_id)
        self.view.show_message(f"Контакт «{contact.name}» удалён.")

    def can_exit(self):
        """Проверяет несохранённые изменения перед выходом."""
        if not self.phone_book.changed:
            return True

        answer = self.view.ask_save_changes()
        if answer == "yes":
            self.save_phone_book()
            return True
        if answer == "no":
            return True
        return False

    def run(self):
        """Запускает главный цикл приложения."""
        self.view.show_welcome()

        while not self.is_open:
            self.view.show_start_menu()
            try:
                choice = self._read_choice({"1", "8"})
                if choice == "1":
                    self.open_phone_book()
                else:
                    self.view.show_message("До свидания!")
                    return
            except PhoneBookError as error:
                self.view.show_error(error)

        while self.is_open:
            self.view.show_main_menu()
            try:
                choice = self._read_choice({"2", "3", "4", "5", "6", "7", "8"})

                if choice == "2":
                    self.save_phone_book()
                elif choice == "3":
                    self.show_all_contacts()
                elif choice == "4":
                    self.add_contact()
                elif choice == "5":
                    self.find_contacts()
                elif choice == "6":
                    self.update_contact()
                elif choice == "7":
                    self.delete_contact()
                elif choice == "8" and self.can_exit():
                    self.view.show_message("До свидания!")
                    return
            except PhoneBookError as error:
                self.view.show_error(error)


def main():
    """Точка входа в программу."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.json")
    controller = PhoneBookController(file_path)
    controller.run()


if __name__ == "__main__":
    main()
