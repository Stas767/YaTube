# **Блог-платформа YaTube**
### **Описание:**
Платформа для блогов. На ней можно зарегистрироваться, создать и отредактировать пост, загрузить картинки, написать комментарии, подписаться на любимых авторов.
[Соц.сеть Yatube в интернете](http://stanislavbaldzhy.pythonanywhere.com/)

___

### **Технологии:**
+ python 3.7.14;
+ django 2.2;
+ django ORM;
+ unnittest django;
+ django-debug-toolbar.
___

### **Как запустить проект:**

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Stas767/YaTube.git
```

```
cd YaTube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
 ___
### **Автор:**
Станислав Балджи
___
