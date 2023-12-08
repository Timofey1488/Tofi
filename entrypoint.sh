#!/bin/bash

# Проверка наличия миграций
if [[ $(python manage.py showmigrations) ]]; then
    # Выполнение миграций, если они есть
    python manage.py migrate
fi

# Создание суперпользователя (если не существует)
echo "from accounts.models import User; \
           from django.contrib.auth import get_user_model; \
           User = get_user_model(); \
           User.objects.create_superuser('${DJANGO_SUPERUSER_EMAIL}', \
                                      '${DJANGO_SUPERUSER_PASSWORD}')" | python manage.py shell

python manage.py runserver 0.0.0.0:8000