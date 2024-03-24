![workflow](https://github.com/AlekseySuhorukov/foodgram-project-react/actions/workflows/master.yml/badge.svg)
# Foodgram
Яндекс Практикум, Спринт 17

Проект foodgram позволяет пользователям выкладывать свои рецепты, просматривать рецепты, выложенные другими пользователями. Есть возможность подписаться на пользователя, добавить рецепт в избранное и в список покупок. Список покупок можно скачать в формате txt.

**_Ссылка на [проект](https://foodgram.cherryd.dev/)_**

### Как подготовить сервер:

На сервере, где разворачивается проект, должен быть установлен Docker

1. Установитть докер:
Windows: установите WSL [по инструкции](https://learn.microsoft.com/ru-ru/windows/wsl/install), после чего установите [Docker Desktop](https://www.docker.com/products/docker-desktop/).
macOS: установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)
Linux: установите Docker Engine, используя готовый скрипт от Docker:
```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
```

2. Создать директорию проекта на сервере:
```
mkdir ~/foodgram
```

### Как запустить проект:

1. Форкнуть репозиторий.

2. Настроить переменные окружения:
В проекте foodgram переменные окружения передаются на сервер из форкнутого репозитория на github.
В окне Actions secrets and variables (https://github.com/ ***username*** /foodgram-project-react/settings/secrets/actions) необходимо создать следующие секреты:
```
ALLOWED_HOSTS: список хостов/доменов. Писать через запятую, без пробелов
DB_HOST: IP базы данных, или имя контейнера, где запущен сервер БД
DB_PORT: порт, по которому Django будет обращаться к базе данных
DOCKER_PASSWORD: пароль от вашего докер аккаунта
DOCKER_USERNAME: username вашего докер аккаунта
HOST: IP-адрес вашего сервера
POSTGRES_DB: название БД
POSTGRES_PASSWORD: пароль от БД
POSTGRES_USER: логин БД
SSH_KEY: содержимое закрытого ключа SSH для доступа к серверу
SSH_PASSPHRASE: passphrase для доступа к серверу
TELEGRAM_TO: ID вашего телеграм-аккаунта
TELEGRAM_TOKEN: токен вашего телеграм-бота
USER: ваше имя пользователя на сервере
```

3. Клонировать форкнутый репозиторий и перейти в него в командной строке:
```
cd foodgram-project-react
```

4. Из этой директории запушить приложение на github:
```
git add .
git commit -m 'my commit'
git push
```

5. При пуше проект пройдёт встроенные тесты. Скрипты создадут необходимые файлы на сервере в директории ~/foodgram. Будут развёрнуты контейнеры, и приложение будет готово к работе.

#### Дополнительные функции:

- Чтобы добавить суперюзера выполнить на сервере команду:
```
sudo docker exec -it backend python manage.py createsuperuser
```

- Чтобы добавить готовый список ингредиентов можно выполнить на сервере команду:
```
sudo docker exec -it backend python manage.py loaddata newdata.json
```

### Основные ссылки после запуска проекта:

- Ссылка на проект: http:// ***Ваше доменное имя*** 

- Ссылка на админ-зону: http:// ***Ваше доменное имя*** /admin 

- Ссылка на документацию к API: http:// ***Ваше доменное имя*** /api/docs

### Использованные технологии:
```
Django
docker
nginx
Git
PostgreSQL
python
```
**_Контактная информация_**
Автор проекта:

Алексей Сухоруков
https://github.com/AlekseySuhorukov

eMail: aleksey.suhorukov2@gmail.com