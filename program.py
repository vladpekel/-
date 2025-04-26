import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import requests
from datetime import datetime

SERVER_URL = "http://77.91.77.108:8001"
ATTRACTIONS = ["Скалодром", "Зиплайн", "Веревочный парк", "Батутный парк"]


def show_start_page():
    start_root.deiconify()


# ------------------ Клиентская часть ------------------ (изначально была, сейчас и новые функции есть)
def show_client_app():
    start_root.withdraw()
    client_root = tk.Toplevel()
    client_root.title("Extreme Park – Бронирование")
    client_root.geometry("400x500")

    def validate_phone(phone):
        return phone.isdigit() and 10 <= len(phone) <= 15

    def send_booking():
        name = entry_name.get().strip()
        phone = entry_phone.get().replace(' ', '')
        age = age_var.get()
        date_str = date_entry.get()
        selected = [ATTRACTIONS[i] for i in range(len(ATTRACTIONS)) if attr_vars[i].get()]

        errors = []
        if not name: errors.append("Укажите ФИО")
        if not validate_phone(phone): errors.append("Телефон: 10-15 цифр")
        try:
            age = int(age)
            if (age < 14 or age > 100): errors.append("Возраст должен быть ≥14 и ты не должен быть слишком старым")
        except ValueError:
            errors.append("Некорректный возраст")
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            errors.append("Дата должна быть ГГГГ-ММ-ДД, я поменял Дмитрий Дмитриевич")
        if not selected: errors.append("Выберите аттракционы")

        if errors:
            messagebox.showerror("Ошибки", "\n".join(errors))
            return

        data = {
            "name": name,
            "phone": phone,
            "age": age,
            "date": date_str,
            "attractions": selected
        }

        try:
            response = requests.post(f"{SERVER_URL}/book", json=data)
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Бронирование принято!")
                client_root.destroy()
                show_start_page()
            else:
                messagebox.showerror("Ошибка", f"Ошибка: {response.text}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")

    # GUI клиентской части
    tk.Label(client_root, text="ФИО клиента:").pack()
    entry_name = tk.Entry(client_root, width=40)
    entry_name.pack()

    tk.Label(client_root, text="Телефон:").pack()
    entry_phone = tk.Entry(client_root, width=40)
    entry_phone.pack()

    tk.Label(client_root, text="Возраст:").pack()
    age_var = tk.StringVar()
    entry_age = tk.Entry(client_root, textvariable=age_var, width=10)
    entry_age.pack()

    tk.Label(client_root, text="Дата посещения (ГГГГ-ММ-ДД):").pack()
    date_entry = tk.Entry(client_root, width=20)
    date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
    date_entry.pack()

    tk.Label(client_root, text="Выберите аттракционы:").pack()
    attr_vars = []
    for attr in ATTRACTIONS:
        var = tk.IntVar()
        attr_vars.append(var)
        tk.Checkbutton(client_root, text=attr, variable=var).pack(anchor="w")

    tk.Button(client_root, text="Забронировать", command=send_booking,
              bg="#2e8b57", fg="white").pack(pady=20)

    client_root.protocol("WM_DELETE_WINDOW", lambda: (client_root.destroy(), show_start_page()))


# ------------------ Админская часть ------------------
def show_admin_panel():
    start_root.withdraw()
    admin_root = tk.Toplevel()
    admin_root.title("Extreme Park – Админ панель")
    admin_root.geometry("1200x600")

    # переменные для хранения состояния сортировки
    sort_column = tk.StringVar(value="ID")
    sort_order = tk.BooleanVar(value=True)

    def treeview_sort_column(col, reverse):
        nonlocal sort_column, sort_order

        sort_column.set(col)
        sort_order.set(reverse)

        lst = [(tree.set(k, col), k) for k in tree.get_children('')]

        # Сначало число потом дата потом строка
        try:
            lst = [(int(a[0]), a[1]) for a in lst]
        except ValueError:
            try:
                lst = [(datetime.strptime(a[0], "%Y-%m-%d"), a[1]) for a in lst]
            except ValueError:
                lst = [(a[0].lower(), a[1]) for a in lst]

        lst.sort(reverse=reverse)

        # Перемещаем элементы в отсортированном порядке
        for index, (val, k) in enumerate(lst):
            tree.move(k, '', index)

        tree.heading(col, command=lambda: treeview_sort_column(col, not reverse))

        for c in tree["columns"]:
            tree.heading(c, text=c)
        tree.heading(col, text=f"{col} {'▼' if reverse else '▲'}")

    def get_bookings():
        try:
            response = requests.get(f"{SERVER_URL}/bookings")
            if response.status_code == 200:
                update_table(response.json())
            else:
                messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")

    def delete_booking():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите запись для удаления")
            return

        booking_id = tree.item(selected[0])['values'][0]
        if not messagebox.askyesno("Подтверждение", f"Удалить бронирование #{booking_id}?"):
            return

        try:
            response = requests.delete(f"{SERVER_URL}/bookings/{booking_id}")
            if response.status_code == 200:
                messagebox.showinfo("Успех", "Бронирование удалено!")
                get_bookings()
            else:
                messagebox.showerror("Ошибка", f"Ошибка сервера: {response.text}")
        except Exception as e:
            messagebox.showerror("Ошибка подключения", str(e))

    def clear_bookings():
        if messagebox.askyesno("Подтверждение", "Удалить ВСЕ бронирования?"):
            try:
                response = requests.delete(f"{SERVER_URL}/bookings")
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Все бронирования удалены!")
                    update_table([])
                else:
                    messagebox.showerror("Ошибка", f"Ошибка: {response.text}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")

    def edit_booking():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите запись для редактирования")
            return

        item = tree.item(selected[0])
        values = item['values']
        booking_id = values[0]

        edit_window = tk.Toplevel(admin_root)
        edit_window.title("Редактирование бронирования")
        edit_window.geometry("400x500")

        # Поля ввода
        tk.Label(edit_window, text="ФИО:").pack()
        name_entry = tk.Entry(edit_window)
        name_entry.insert(0, values[1])
        name_entry.pack()

        tk.Label(edit_window, text="Телефон:").pack()
        phone_entry = tk.Entry(edit_window)
        phone_entry.insert(0, values[2])
        phone_entry.pack()

        tk.Label(edit_window, text="Возраст:").pack()
        age_entry = tk.Entry(edit_window)
        age_entry.insert(0, values[3])
        age_entry.pack()

        tk.Label(edit_window, text="Дата (ГГГГ-ММ-ДД):").pack()
        date_entry = tk.Entry(edit_window)
        date_entry.insert(0, values[4])
        date_entry.pack()

        tk.Label(edit_window, text="Аттракционы:").pack()
        attr_vars = []
        for i, attr in enumerate(ATTRACTIONS):
            var = tk.IntVar(value=1 if attr in values[5] else 0)
            attr_vars.append(var)
            tk.Checkbutton(edit_window, text=attr, variable=var).pack(anchor="w")

        def save_changes():
            data = {
                "name": name_entry.get(),
                "phone": phone_entry.get(),
                "age": age_entry.get(),
                "date": date_entry.get(),
                "attractions": [ATTRACTIONS[i] for i in range(len(ATTRACTIONS)) if attr_vars[i].get()]
            }

            errors = []
            if not data['phone'].isdigit() or len(data['phone']) not in range(10, 16):
                errors.append("Телефон должен содержать 10-15 цифр")
            try:
                data['age'] = int(data['age'])
                if (data['age'] < 14 or data['age'] > 100): errors.append("Возраст должен быть ≥14 и ты не должен быть слишком старым")
            except ValueError:
                errors.append("Некорректный возраст")
            try:
                datetime.strptime(data['date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Дата должна быть ГГГГ-ММ-ДД")
            if not data['name']: errors.append("Укажите ФИО")
            if not data['attractions']: errors.append("Выберите аттракционы")

            if errors:
                messagebox.showerror("Ошибки", "\n".join(errors))
                return

            try:
                response = requests.put(
                    f"{SERVER_URL}/bookings/{booking_id}",
                    json=data
                )
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Изменения сохранены")
                    edit_window.destroy()
                    get_bookings()
                else:
                    messagebox.showerror("Ошибка", f"Ошибка сервера: {response.text}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")

        tk.Button(edit_window, text="Сохранить", command=save_changes, bg="#4CAF50", fg="white").pack(pady=20)

    def update_table(bookings):
        tree.delete(*tree.get_children())
        for booking in bookings:
            tree.insert("", "end", values=(
                booking['id'],
                booking['name'],
                booking['phone'],
                booking['age'],
                booking['date'],
                ", ".join(booking['attractions'])
            ))
        # Применяем последнюю активную сортировку
        if sort_column.get():
            treeview_sort_column(sort_column.get(), sort_order.get())

    def auto_refresh():
        try:
            get_bookings()
        finally:
            admin_root.after(10000, auto_refresh)

    # GUI админской части
    tree = ttk.Treeview(admin_root, columns=("ID", "ФИО", "Телефон", "Возраст", "Дата", "Аттракционы"), show="headings")

    for col in ("ID", "ФИО", "Телефон", "Возраст", "Дата", "Аттракционы"):
        tree.heading(col, text=col,
                     command=lambda c=col: treeview_sort_column(c, False))
        tree.column(col, width=100 if col == "ID" else 150, anchor='center' if col in ("ID", "Возраст") else 'w')

    tree.column("ID", width=50, anchor='center')
    tree.column("ФИО", width=150)
    tree.column("Телефон", width=120)
    tree.column("Возраст", width=60, anchor='center')
    tree.column("Дата", width=100)
    tree.column("Аттракционы", width=300)

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    btn_frame = tk.Frame(admin_root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Обновить", command=get_bookings,
              bg="#2196F3", fg="white").pack(side="left", padx=5)
    tk.Button(btn_frame, text="Редактировать", command=edit_booking,
              bg="#FF9800", fg="white").pack(side="left", padx=5)
    tk.Button(btn_frame, text="Удалить", command=delete_booking,
              bg="#e74c3c", fg="white").pack(side="left", padx=5)
    tk.Button(btn_frame, text="Очистить все", command=clear_bookings,
              bg="#F44336", fg="white").pack(side="left", padx=5)

    auto_refresh()
    admin_root.protocol("WM_DELETE_WINDOW", lambda: (admin_root.destroy(), show_start_page()))


# ------------------ Стартовая страница ------------------
def check_admin_password():
    password = simpledialog.askstring("Пароль админа", "Введите пароль:",
                                      show='*',
                                      parent=start_root)
    if not password:
        return

    try:
        response = requests.post(
            f"{SERVER_URL}/auth/admin",
            auth=('admin', password),
            timeout=5
        )

        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")

        if response.status_code == 200:
            messagebox.showinfo("Успех", "Авторизация прошла успешно!")
            show_admin_panel()
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            messagebox.showerror("Ошибка", f"{error_msg} (код {response.status_code})")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")
    except Exception as e:
        messagebox.showerror("Критическая ошибка", str(e))

# Создание основного окна
start_root = tk.Tk()
start_root.title("Extreme Park – Выбор роли")
start_root.geometry("400x350")
start_root.configure(bg="#f0f2f5")

style = ttk.Style()
style.configure("Primary.TButton", font=('Helvetica', 12), padding=10,
                foreground="#000000", background="#2e8b57")
style.configure("Secondary.TButton", font=('Helvetica', 12), padding=10,
                foreground="#000000", background="#4682b4")

main_frame = tk.Frame(start_root, bg="#f0f2f5")
main_frame.pack(expand=True, fill="both", padx=40, pady=40)

tk.Label(main_frame, text="🏞️ Extreme Park", font=("Helvetica", 20, "bold"),
         bg="#f0f2f5", fg="#2d3436").pack(pady=(0, 30))
tk.Label(main_frame, text="Выберите тип входа:", font=("Helvetica", 12),
         bg="#f0f2f5", fg="#636e72").pack()

btn_frame = tk.Frame(main_frame, bg="#f0f2f5")
btn_frame.pack(pady=20)

ttk.Button(btn_frame, text="  Клиент  ", style="Primary.TButton",
           command=show_client_app).pack(pady=10, ipadx=20)
ttk.Button(btn_frame, text="  Администратор  ", style="Secondary.TButton",
           command=check_admin_password).pack(pady=10, ipadx=20)

tk.Label(main_frame, text="© 2024 Extreme Park System",
         font=("Helvetica", 9), bg="#f0f2f5", fg="#636e72").pack(side="bottom", pady=10)

start_root.mainloop()