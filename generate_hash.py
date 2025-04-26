import bcrypt

# Шаг 1
password = "0123074"  #мой номер зачетки

# Шаг 2
salt = bcrypt.gensalt()

# Шаг 3
hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

# Шаг 4
print("Ваш хеш для .env файла:")
print(hashed_password.decode('utf-8'))
