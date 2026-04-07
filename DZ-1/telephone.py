import json
import os

contacts = []
next_id = 1
filename = "contacts.json"
changed = False
open_file = False

def validate_phone(phone):
    phone = str(phone)
    cleaned = ""
    for i in phone:
        if i.isdigit() or i == '+':
            cleaned += i
    if not cleaned or len(cleaned) < 5:
        print("Телефон должен содержать минимум 5 цифр")
        return None
    return cleaned


def create_contact(contact_id, name, phone, comment = ""):
    return {
        'id': contact_id,
        'name': name.strip(),
        'phone': validate_phone(phone),
        'comment': comment.strip()
    }


def load_from_file(save = None):
    global contacts, next_id, changed, open_file
    
    if not os.path.exists(filename):
        print(f"\nТелефонный справочник не создан.\n")
        return True

    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
        contacts = data.get('contacts', [])
        next_id = data.get('next_id', 1)
        changed = False
        open_file = True
        if not save:
            print('\nСправочник открыт\n')
        return True


def save_to_file():
    global changed
    sorted_contacts = sorted(contacts, key=lambda x: x['id'])
    
    data = {
        'contacts': sorted_contacts,
        'next_id': next_id
    }
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    changed = False
    load_from_file(True)
    print('\nСправочник сохранен\n')
    return True


def get_next_available_id():
    if not contacts:
        return 1
    
    existing_ids = [contact['id'] for contact in contacts]
    existing_ids.sort()
    
    for i in range(1, existing_ids[-1] + 1):
        if i not in existing_ids:
            return i
    
    return existing_ids[-1] + 1


def add_contact(name, phone, comment = ""):
    global contacts, next_id, changed
    
    contact_id = get_next_available_id()
    contact = create_contact(contact_id, name, phone, comment)
    contacts.append(contact)
    changed = True
    print('\nКонтакт добавлен')
    return True


def show_all_contacts():
    if not contacts:
        print("\nСправочник пуст")
        return

    print("\nСписок контактов:")
    for contact in contacts:
        print(f"ID: {contact['id']}, Имя: {contact['name']}, Телефон: {contact['phone']}, Комментарий: {contact['comment'] if contact['comment'] else 'нет'}")
    

def find_contacts(query, search_field = "all"):
    query = query.lower()
    results = []

    for contact in contacts:
        if search_field == "all":
            if (query in contact['name'].lower() or 
                query in contact['phone'] or 
                query in contact['comment'].lower()):
                results.append(contact)
        elif search_field == "name":
            if query in contact['name'].lower():
                results.append(contact)
        elif search_field == "phone":
            if query in contact['phone']:
                results.append(contact)
        elif search_field == "comment":
            if query in contact['comment'].lower():
                results.append(contact)

    return results

def get_contact_by_id(contact_id):
    for contact in contacts:
        if contact['id'] == contact_id:
            return contact
    return None

def update_contact(contact_id, name = None, phone = None, comment = None):
    global changed
    
    contact = get_contact_by_id(contact_id)
    if not contact:
        print(f"Контакт с ID {contact_id} не найден")
        return False

    if name is not None:
        contact['name'] = name.strip()
    if phone is not None:
        contact['phone'] = validate_phone(phone)
    if comment is not None:
        contact['comment'] = comment.strip()

    changed = True
    return True

def delete_contact(contact_id):
    global changed
    
    contact = get_contact_by_id(contact_id)
    if not contact:
        print(f"Контакт с ID {contact_id} не найден")
        return False

    contacts.remove(contact)
    changed = True
    print(f"Контакт '{contact['name']}' успешно удален")

    save_to_file()
    return True

def ask_to_save():
    if not changed:
        return True

    while True:
        answer = input("Есть несохраненные изменения. Сохранить? (д/н): ").lower().strip()
        if answer in ['д', 'да', 'y', 'yes']:
            return save_to_file()
        elif answer in ['н', 'нет', 'n', 'no']:
            return True
        else:
            print("Пожалуйста, введите 'д' или 'н'")

def print_menu():
    print("2. Сохранить/Создать справочник")
    print("3. Показать все контакты")
    print("4. Создать контакт")
    print("5. Найти контакт")
    print("6. Изменить контакт")
    print("7. Удалить контакт")
    print("8. Выход")

def print_menu_first():
    """Вывод меню"""
    print("1. Открыть справочник")
    print("8. Выход")

def get_contact_input():
    while True:
        name = input("Введите имя: ").strip()
        if name:
            break
        print("Имя не может быть пустым")

    while True:
        phone = input("Введите телефон: ").strip()
        if phone:
            if validate_phone(phone):
                break
            else:
                print(f"Ошибка в номере телефона: {phone}")
        else:
            print("Телефон не может быть пустым")

    comment = input("Введите комментарий (необязательно): ").strip()
    return name, phone, comment

def main():
    global contacts, next_id, filename, changed
    
    print("ТЕЛЕФОННЫЙ СПРАВОЧНИК")
    while True and not open_file:

        print('Первый запуск, откройте справочник')
        print_menu_first()

        choice = input("Выберите пункт меню: ").strip()
                
        if choice == '1':
            load_from_file()
            break

    while True and open_file:
        print_menu()
        
        choice = input("Выберите пункт меню (2-8): ").strip()

        if choice == '2':
            save_to_file()
            
        elif choice == '3':
            show_all_contacts()
            print()
            
        elif choice == '4':
            name, phone, comment = get_contact_input()
            add_contact(name, phone, comment)
            save_to_file()
            
        elif choice == '5':
            if not contacts:
                print("\nСправочник пуст\n")
                continue
            
            print("\nПараметры поиска:")
            print("1. По всем полям")
            print("2. По имени")
            print("3. По телефону")
            print("4. По комментарию")
            
            while True:
                search_choice = input("\nВыберите параметр (1-4): ").strip()
                if search_choice in ["1", "2", "3", "4"]:
                    break
                print("Неверный выбор, попробуйте снова")
            
            search_fields = {"1": "all", "2": "name", "3": "phone", "4": "comment"}
            search_field = search_fields.get(search_choice, "all")
            
            query = input("\nВведите поисковый запрос: ").strip()
            results = find_contacts(query, search_field)
            
            if results:
                print(f"\nНайдено контактов: {len(results)}")
                for contact in results:
                    print(f"ID: {contact['id']}, Имя: {contact['name']}, Телефон: {contact['phone']}")
                print('\n')
            else:
                print("\nКонтакты не найдены\n")
            
        elif choice == '6':
            if not contacts:
                print("\nСправочник пуст\n")
                continue
            
            show_all_contacts()
            contact_id = int(input("Введите ID контакта для изменения: "))
            contact = get_contact_by_id(contact_id)
            if not contact:
                print("Контакт не найден")
                continue
            
            print(f"Текущие данные контакта:")
            print(f"Имя: {contact['name']}")
            print(f"Телефон: {contact['phone']}")
            print(f"Комментарий: {contact['comment']}")
            
            print("\nВведите новые данные (оставьте пустым, чтобы не менять):")
            
            new_name = input(f"Имя [{contact['name']}]: ").strip()
            new_phone = input(f"Телефон [{contact['phone']}]: ").strip()
            new_comment = input(f"Комментарий [{contact['comment']}]: ").strip()
            
            update_contact(
                contact_id,
                name=new_name if new_name else None,
                phone=new_phone if new_phone else None,
                comment=new_comment if new_comment else None
            )
            print("Контакт успешно изменен")
            save_to_file()
            
        elif choice == '7':
            if not contacts:
                print("\nСправочник пуст\n")
                continue
            
            show_all_contacts()
            try:
                contact_id = int(input("Введите ID контакта для удаления: "))
                delete_contact(contact_id)
            except ValueError:
                print("ID должен быть числом")
        
        elif choice == '8':
            if ask_to_save():
                print("До свидания!")
                break
        
        else:
            print("Пожалуйста, выберите от 2 до 8")

if __name__ == "__main__":
    main()