"""Представление телефонного справочника.

Модуль отвечает только за меню, ввод и вывод информации пользователю.
"""


class View:
    """Консольное представление программы."""

    def show_welcome(self):
        print("\nТЕЛЕФОННЫЙ СПРАВОЧНИК")

    def show_start_menu(self):
        print("\n1. Открыть или создать справочник")
        print("8. Выход")

    def show_main_menu(self):
        print("\n2. Сохранить справочник")
        print("3. Показать все контакты")
        print("4. Создать контакт")
        print("5. Найти контакт")
        print("6. Изменить контакт")
        print("7. Удалить контакт")
        print("8. Выход")

    def get_menu_choice(self):
        return input("Выберите пункт меню: ").strip()

    def show_search_menu(self):
        print("\nПараметры поиска:")
        print("1. По всем полям")
        print("2. По имени")
        print("3. По телефону")
        print("4. По комментарию")

    def get_search_query(self):
        return input("Введите поисковый запрос: ").strip()

    def get_new_contact_data(self):
        name = input("Введите имя: ").strip()
        phone = input("Введите телефон: ").strip()
        comment = input("Введите комментарий (необязательно): ").strip()
        return name, phone, comment

    def get_contact_id(self, action):
        return input(f"Введите ID контакта для действия «{action}»: ").strip()

    def get_update_data(self, contact):
        print("\nТекущие данные контакта:")
        print(contact)
        print("\nОставьте поле пустым, чтобы не изменять его.")

        name = input(f"Имя [{contact.name}]: ").strip()
        phone = input(f"Телефон [{contact.phone}]: ").strip()
        comment = input(f"Комментарий [{contact.comment}]: ").strip()

        return {
            "name": name if name else None,
            "phone": phone if phone else None,
            "comment": comment if comment else None,
        }

    def ask_save_changes(self):
        """Возвращает yes, no или cancel."""
        while True:
            answer = input(
                "Есть несохранённые изменения. Сохранить? (д/н/о): "
            ).strip().lower()
            if answer in {"д", "да", "y", "yes"}:
                return "yes"
            if answer in {"н", "нет", "n", "no"}:
                return "no"
            if answer in {"о", "отмена", "c", "cancel"}:
                return "cancel"
            print("Введите «д», «н» или «о».")

    def show_contacts(self, contacts):
        if not contacts:
            print("\nСправочник пуст или контакты не найдены.")
            return

        print("\nСписок контактов:")
        for contact in contacts:
            print(contact)

    def show_search_results(self, contacts):
        if not contacts:
            print("\nКонтакты не найдены.")
            return

        print(f"\nНайдено контактов: {len(contacts)}")
        self.show_contacts(contacts)

    def show_message(self, message):
        print(f"\n{message}")

    def show_error(self, error):
        print(f"\nОшибка: {error}")
