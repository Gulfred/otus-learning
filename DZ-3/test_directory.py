"""Тесты телефонного справочника из DZ-3."""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from controller import PhoneBookController
from model import (
    Contact,
    ContactNotFoundError,
    FileReadError,
    FileReader,
    FileWriteError,
    FileWriter,
    InvalidIdError,
    InvalidMenuChoiceError,
    PhoneBook,
    ValidationError,
)


class ContactTests(unittest.TestCase):
    """Тесты создания и проверки контакта."""

    def test_create_contact_and_to_dict(self):
        contact = Contact(1, "  Иван  ", "+79112223344", "  коллега  ")

        self.assertEqual(contact.id, 1)
        self.assertEqual(contact.name, "Иван")
        self.assertEqual(contact.phone, "+79112223344")
        self.assertEqual(contact.comment, "коллега")
        self.assertEqual(
            contact.to_dict(),
            {
                "id": 1,
                "name": "Иван",
                "phone": "+79112223344",
                "comment": "коллега",
            },
        )

    def test_create_contact_from_dict(self):
        data = {
            "id": 3,
            "name": "Пётр",
            "phone": "+79223334455",
            "comment": "друг",
        }

        contact = Contact.from_dict(data)

        self.assertEqual(str(contact), "ID: 3, Имя: Пётр, Телефон: +79223334455, Комментарий: друг")

    def test_create_contact_from_legacy_description(self):
        contact = Contact.from_dict(
            {
                "id": 1,
                "name": "Иван",
                "phone": "12345",
                "description": "старый формат",
            }
        )

        self.assertEqual(contact.comment, "старый формат")
        self.assertEqual(contact.description, "старый формат")

    def test_valid_names_with_subTest(self):
        names = ["Иван", "A", "  Пётр  ", "Анна-Мария"]

        for name in names:
            with self.subTest(name=name):
                contact = Contact(1, name, "12345")
                self.assertTrue(contact.name)

    def test_valid_phones_with_subTest(self):
        phones = ["12345", "+12345", "+79112223344", "89991234567"]

        for phone in phones:
            with self.subTest(phone=phone):
                self.assertEqual(Contact.validate_phone(phone), phone)

    def test_invalid_names_raise_validation_error(self):
        for name in ["", "   ", None, 123]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValidationError, "Имя"):
                    Contact(1, name, "12345")

    def test_invalid_phones_raise_validation_error(self):
        phones = ["", "   ", None, "1234", "12-ab", "123-45", "+12+345", "123+45"]

        for phone in phones:
            with self.subTest(phone=phone):
                with self.assertRaises(ValidationError):
                    Contact(1, "Иван", phone)

    def test_invalid_id_raises_invalid_id_error(self):
        for contact_id in [0, -1, "abc", True]:
            with self.subTest(contact_id=contact_id):
                with self.assertRaisesRegex(InvalidIdError, "ID"):
                    Contact(contact_id, "Иван", "12345")

    def test_from_dict_without_required_field_raises_validation_error(self):
        with self.assertRaisesRegex(ValidationError, "phone"):
            Contact.from_dict({"id": 1, "name": "Иван"})


class PhoneBookTests(unittest.TestCase):
    """Тесты бизнес-логики телефонного справочника."""

    def setUp(self):
        self.phone_book = PhoneBook()

    def add_two_contacts(self):
        first = self.phone_book.add_contact(
            "Иван", "+79112223344", "коллега"
        )
        second = self.phone_book.add_contact(
            "Пётр", "+79223334455", "друг"
        )
        return first, second

    def test_add_contact_generates_ids(self):
        first, second = self.add_two_contacts()

        self.assertEqual(first.id, 1)
        self.assertEqual(second.id, 2)
        self.assertTrue(self.phone_book.changed)
        self.assertEqual(len(self.phone_book.get_all_contacts()), 2)

    def test_get_contact(self):
        first, _ = self.add_two_contacts()

        self.assertIs(self.phone_book.get_contact(first.id), first)

    def test_get_missing_contact_raises_contact_not_found_error(self):
        with self.assertRaisesRegex(ContactNotFoundError, "99"):
            self.phone_book.get_contact(99)

    def test_get_contact_with_invalid_id_raises_invalid_id_error(self):
        with self.assertRaises(InvalidIdError):
            self.phone_book.get_contact("не ID")

    def test_find_by_name_phone_comment_and_all_fields(self):
        self.add_two_contacts()

        cases = [
            ("иван", "name", ["Иван"]),
            ("+7922", "phone", ["Пётр"]),
            ("коллег", "comment", ["Иван"]),
            ("друг", "all", ["Пётр"]),
        ]

        for query, search_field, expected_names in cases:
            with self.subTest(query=query, search_field=search_field):
                result = self.phone_book.find_contacts(query, search_field)
                self.assertEqual([contact.name for contact in result], expected_names)

    def test_find_returns_empty_list_when_contacts_not_found(self):
        self.add_two_contacts()

        self.assertEqual(self.phone_book.find_contacts("несуществующий", "all"), [])

    def test_empty_query_and_unknown_search_field_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            self.phone_book.find_contacts("", "all")

        with self.assertRaises(ValidationError):
            self.phone_book.find_contacts("Иван", "unknown")

    def test_update_contact(self):
        first, _ = self.add_two_contacts()

        updated = self.phone_book.update_contact(
            first.id,
            name="Анна",
            phone="+79998887766",
            comment="новый комментарий",
        )

        self.assertIs(updated, first)
        self.assertEqual(first.name, "Анна")
        self.assertEqual(first.phone, "+79998887766")
        self.assertEqual(first.comment, "новый комментарий")
        self.assertTrue(self.phone_book.changed)

    def test_update_without_data_raises_validation_error(self):
        self.add_two_contacts()

        with self.assertRaises(ValidationError):
            self.phone_book.update_contact(1)

    def test_update_missing_contact_raises_contact_not_found_error(self):
        with self.assertRaises(ContactNotFoundError):
            self.phone_book.update_contact(99, name="Анна")

    def test_update_with_invalid_phone_raises_validation_error(self):
        self.add_two_contacts()

        with self.assertRaises(ValidationError):
            self.phone_book.update_contact(1, phone="12-ab")

    def test_delete_contact(self):
        first, second = self.add_two_contacts()

        deleted = self.phone_book.delete_contact(first.id)

        self.assertIs(deleted, first)
        self.assertEqual(self.phone_book.get_all_contacts(), [second])
        self.assertTrue(self.phone_book.changed)

    def test_delete_missing_contact_raises_contact_not_found_error(self):
        with self.assertRaises(ContactNotFoundError):
            self.phone_book.delete_contact(99)

    def test_to_dict_and_mark_saved(self):
        self.add_two_contacts()

        data = self.phone_book.to_dict()
        self.assertEqual(data["next_id"], 3)
        self.assertEqual(len(data["contacts"]), 2)

        self.phone_book.mark_saved()
        self.assertFalse(self.phone_book.changed)

    def test_load_data(self):
        self.phone_book.load_data(
            {
                "contacts": [
                    {
                        "id": 5,
                        "name": "Сергей",
                        "phone": "+79334445566",
                        "comment": "работа",
                    }
                ],
                "next_id": 6,
            }
        )

        self.assertEqual(self.phone_book.get_contact(5).name, "Сергей")
        self.assertEqual(self.phone_book.next_id, 6)
        self.assertFalse(self.phone_book.changed)

    def test_load_invalid_data_raises_file_read_error(self):
        invalid_data = [
            None,
            {"contacts": "not a list"},
            {
                "contacts": [
                    {"id": 1, "name": "Иван", "phone": "12345"},
                    {"id": 1, "name": "Пётр", "phone": "12345"},
                ]
            },
        ]

        for data in invalid_data:
            with self.subTest(data=data):
                with self.assertRaises(FileReadError):
                    self.phone_book.load_data(data)


class FileReaderWriterTests(unittest.TestCase):
    """Тесты чтения и записи JSON-файла."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_path = os.path.join(self.temp_dir.name, "contacts.json")
        self.phone_book = PhoneBook()
        self.phone_book.add_contact("Иван", "+79112223344", "коллега")

    def test_write_and_read_file(self):
        FileWriter(self.file_path).write(self.phone_book)

        data = FileReader(self.file_path).read()
        loaded_book = PhoneBook()
        loaded_book.load_data(data)

        self.assertEqual(loaded_book.get_contact(1).name, "Иван")
        self.assertEqual(loaded_book.get_contact(1).comment, "коллега")

    def test_write_multiple_contacts(self):
        self.phone_book.add_contact("Пётр", "+79223334455", "друг")
        FileWriter(self.file_path).write(self.phone_book)

        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.assertEqual(len(data["contacts"]), 2)
        self.assertEqual(data["next_id"], 3)

    def test_read_empty_file_format(self):
        empty_book = PhoneBook()
        FileWriter(self.file_path).write(empty_book)

        data = FileReader(self.file_path).read()

        self.assertEqual(data, {"contacts": [], "next_id": 1})

    def test_read_missing_file_returns_empty_book(self):
        data = FileReader(self.file_path).read()

        self.assertEqual(data, {"contacts": [], "next_id": 1})

    def test_read_broken_json_raises_file_read_error(self):
        with open(self.file_path, "w", encoding="utf-8") as file:
            file.write("{ broken json")

        with self.assertRaisesRegex(FileReadError, "прочитать"):
            FileReader(self.file_path).read()

    def test_reader_os_error_raises_file_read_error(self):
        with patch("model.os.path.exists", return_value=True), patch(
            "builtins.open", side_effect=OSError
        ):
            with self.assertRaises(FileReadError):
                FileReader(self.file_path).read()

    def test_writer_os_error_raises_file_write_error(self):
        with patch("builtins.open", side_effect=OSError):
            with self.assertRaisesRegex(FileWriteError, "записать"):
                FileWriter(self.file_path).write(self.phone_book)


class ControllerTests(unittest.TestCase):
    """Тесты вспомогательных методов и операций контроллера."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_path = os.path.join(self.temp_dir.name, "contacts.json")
        self.view = Mock()
        self.controller = PhoneBookController(self.file_path, self.view)

    def test_parse_valid_id(self):
        self.assertEqual(self.controller._parse_id("15"), 15)

    def test_parse_invalid_ids(self):
        for value in ["abc", "0", "-1", None]:
            with self.subTest(value=value):
                with self.assertRaises(InvalidIdError):
                    self.controller._parse_id(value)

    def test_read_valid_menu_choice(self):
        self.view.get_menu_choice.return_value = "3"

        self.assertEqual(self.controller._read_choice({"2", "3"}), "3")

    def test_read_invalid_menu_choice_raises_exception(self):
        self.view.get_menu_choice.return_value = "9"

        with self.assertRaisesRegex(InvalidMenuChoiceError, "пункт меню"):
            self.controller._read_choice({"2", "3"})

    def test_open_and_save_phone_book(self):
        self.controller.open_phone_book()
        self.controller.phone_book.add_contact("Иван", "+79112223344", "тест")
        self.controller.save_phone_book()

        loaded_data = FileReader(self.file_path).read()
        self.assertEqual(loaded_data["contacts"][0]["name"], "Иван")
        self.assertFalse(self.controller.phone_book.changed)

    def test_add_contact_uses_view_and_model(self):
        self.view.get_new_contact_data.return_value = (
            "Иван",
            "+79112223344",
            "тест",
        )

        self.controller.add_contact()

        self.assertEqual(self.controller.phone_book.get_contact(1).name, "Иван")
        self.view.show_message.assert_called_once()

    def test_find_contacts_uses_selected_field(self):
        self.controller.phone_book.add_contact("Иван", "+79112223344", "тест")
        self.view.get_menu_choice.return_value = "2"
        self.view.get_search_query.return_value = "иван"

        self.controller.find_contacts()

        result = self.view.show_search_results.call_args.args[0]
        self.assertEqual([contact.name for contact in result], ["Иван"])

    def test_can_exit_without_changes(self):
        self.assertTrue(self.controller.can_exit())
        self.view.ask_save_changes.assert_not_called()

    def test_can_exit_with_cancel(self):
        self.controller.phone_book.add_contact("Иван", "+79112223344")
        self.view.ask_save_changes.return_value = "cancel"

        self.assertFalse(self.controller.can_exit())

    def test_run_opens_book_and_exits(self):
        self.view.get_menu_choice.side_effect = ["1", "8"]

        self.controller.run()

        self.assertTrue(self.controller.is_open)


if __name__ == "__main__":
    unittest.main()
