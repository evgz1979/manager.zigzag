# scripts/manager_launcher.c

Срез исходников: **3 ноября 2026 года**. [Все модули](../README.md).

Исходник: [scripts/manager_launcher.c:1](../../../scripts/manager_launcher.c#L1).

Непосредственные вызовы извлечены из синтаксиса. Динамический dispatch, вызываемые callbacks и побочные эффекты вложенных функций могут находиться в других объявлениях. Комментарии описывают назначение, тело исходника остаётся точным контрактом.

## forward_signal

[scripts/manager_launcher.c:14](../../../scripts/manager_launcher.c#L14) · `function`.

```c
static void forward_signal(int number)
```

Передаёт сигнал завершения дочернему процессу сервера Python.

Сигнал отправляется только при сохранённом положительном PID ребёнка.

## authorize

[scripts/manager_launcher.c:20](../../../scripts/manager_launcher.c#L20) · `function`.

```c
static int authorize(const char *path)
```

Проверяет доступ приложения macOS к заданному каталогу через opendir.

Успех закрывает дескриптор; отказ возвращает код 77 с диагностикой.

## main

[scripts/manager_launcher.c:32](../../../scripts/manager_launcher.c#L32) · `function`.

```c
int main(int argc, char **argv)
```

Проверяет доступ к каталогам либо запускает сервер Python из launchd.

Передаёт сигналы ребёнку и возвращает его код завершения.
