# scripts/manager_launcher.c

Сгенерировано из текущих объявлений. [Все модули](../README.md).

Исходник: [scripts/manager_launcher.c](../../../scripts/manager_launcher.c).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

<a id="symbol-authorize"></a>

## authorize

[scripts/manager_launcher.c](../../../scripts/manager_launcher.c) · `function`.

```c
static int authorize(const char *path)
```

Проверяет доступ приложения macOS к заданному каталогу через opendir.

Успех закрывает дескриптор; отказ возвращает код 77 с диагностикой.

<a id="symbol-forward_signal"></a>

## forward_signal

[scripts/manager_launcher.c](../../../scripts/manager_launcher.c) · `function`.

```c
static void forward_signal(int number)
```

Передаёт сигнал завершения дочернему процессу сервера Python.

Сигнал отправляется только при сохранённом положительном PID ребёнка.

<a id="symbol-main"></a>

## main

[scripts/manager_launcher.c](../../../scripts/manager_launcher.c) · `function`.

```c
int main(int argc, char **argv)
```

Проверяет доступ к каталогам либо запускает сервер Python из launchd.

Передаёт сигналы ребёнку и возвращает его код завершения.
