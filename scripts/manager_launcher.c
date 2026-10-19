// Сохраняет идентичность приложения macOS при запуске Python через launchd.
#include <dirent.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static pid_t child = -1;

static void forward_signal(int number) { // Передаёт завершение серверу.
    if (child > 0) kill(child, number);
}

static int authorize(const char *path) { // Запрашивает разрешение macOS на каталог.
    DIR *directory = opendir(path);
    if (directory == NULL) {
        fprintf(stderr, "Нет доступа к %s: %s\n", path, strerror(errno));
        return 77;
    }
    closedir(directory);
    return 0;
}

int main(int argc, char **argv) { // Проверяет доступ или запускает сервер.
    if (argc != 4) return 64;
    if (strcmp(argv[1], "--authorize") == 0) {
        int result = authorize(argv[2]);
        return result == 0 ? authorize(argv[3]) : result;
    }
    child = fork();
    if (child < 0) return 71;
    if (child == 0) {
        char *arguments[] = {argv[1], "-u", argv[2], NULL};
        execv(argv[1], arguments);
        perror("Не удалось запустить менеджер");
        _exit(71);
    }
    signal(SIGTERM, forward_signal);
    signal(SIGINT, forward_signal);
    int status;
    while (waitpid(child, &status, 0) < 0) {
        if (errno != EINTR) return 71;
    }
    child = -1;
    if (WIFEXITED(status)) return WEXITSTATUS(status);
    return WIFSIGNALED(status) ? 128 + WTERMSIG(status) : 71;
}
