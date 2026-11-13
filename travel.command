#!/bin/zsh
cd "$(dirname "$0")"
printf '%s\n' '1. На MacBook' '2. На M4' '3. Проверить состояние' '4. Подготовить MacBook'
read 'choice?Выбери действие: '
case "$choice" in
    1) action=to-macbook ;;
    2) action=to-m4 ;;
    3) action=status ;;
    4) action=prepare ;;
    *) exit 0 ;;
esac
/usr/bin/python3 scripts/handoff.py "$action"
result=$?
read 'ignored?Нажми Enter, чтобы закрыть окно. '
exit "$result"
