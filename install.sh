#!/usr/bin/env bash
# ============================================================================
#  mailserver-setup — мастер установки почтового сервера
#
#  Ведёт от чистого сервера до работающей почты: спрашивает параметры,
#  показывает, что и где настроить, сам проверяет каждый шаг и не идёт
#  дальше, пока предыдущий не сделан.
#
#  Основа: docker-mailserver (Postfix, Dovecot, Rspamd).
#  Системы: Debian 12/13, Ubuntu 22.04/24.04/26.04.
#
#  Запуск от root:
#      chmod +x install.sh && ./install.sh
#
#  Ключи:
#      --no-ui       без псевдографики, простые вопросы
#      --dry-run     показать план, ничего не менять
#      --uninstall   удалить установленное
#      -h, --help    справка
#
#  Лицензия MIT.  https://github.com/perov4265-web/mail
# ============================================================================

set -uo pipefail

VERSION="2.2"
LOG="/var/log/mailserver-install.log"
DIR="/opt/mailserver"

# ── параметры установки ──────────────────────────────────────────────────
DOMAIN=""            # почтовый домен, например protestant.ru
FQDN=""              # имя почтового сервера, например mail.protestant.ru
SERVER_IP=""         # внешний IP этого сервера
MAILBOXES=""         # список ящиков через запятую, без @домена
MAIN_BOX=""          # первый ящик — он же получатель всего непонятного
CATCHALL=1           # складывать письма на несуществующие адреса в MAIN_BOX
TZ_SET="Europe/Moscow"
MB_PASS=""

OPT_FIREWALL=1; OPT_SWAP=1; OPT_CERT=1; OPT_CRON=1
OPT_CLAMAV=0; OPT_FAIL2BAN=1
OPEN_SSH=1          # открывать ли 22-й порт в файрволе

USE_UI=1; DRY_RUN=0; DO_UNINSTALL=0

C_OK=$'\e[32m'; C_WARN=$'\e[33m'; C_ERR=$'\e[31m'; C_H=$'\e[1;36m'; C_0=$'\e[0m'
ok()   { echo "${C_OK}  ✔${C_0} $*"; }
warn() { echo "${C_WARN}  ⚠${C_0} $*"; }
fail() { echo "${C_ERR}  ✖${C_0} $*" >&2; }
log()  { echo "[$(date '+%F %T')] $*" >> "$LOG" 2>/dev/null || true; }
# Выполнить команду с записью в журнал. Аргументы намеренно склеиваются
# в строку и передаются в eval: шаги содержат конвейеры и перенаправления,
# которые иначе не отработают. Все значения формируются самим скриптом
# и проверены на предыдущем шаге, внешнего ввода здесь нет.
run()  {
  log "RUN: $*"
  if [ "$DRY_RUN" = 1 ]; then echo "      [dry-run] $*"; return 0; fi
  # shellcheck disable=SC2294
  eval "$@" >> "$LOG" 2>&1
}

while [ $# -gt 0 ]; do
  case "$1" in
    --no-ui) USE_UI=0; shift ;;
    --dry-run) DRY_RUN=1; USE_UI=0; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) fail "неизвестный ключ: $1"; exit 1 ;;
  esac
done

[ "$(id -u)" -ne 0 ] && { fail "запускайте от root"; exit 1; }
touch "$LOG" 2>/dev/null || LOG=/tmp/mailserver-install.log
log "=== мастер v$VERSION ==="

# ═════════════════════════════════════════════════════════════════════════
#  Экраны: работают и в псевдографике, и в простом тексте
# ═════════════════════════════════════════════════════════════════════════

have_wt() { command -v whiptail >/dev/null 2>&1; }

screen() {
  local title="$1" text="$2" h="${3:-24}"
  if [ "$USE_UI" = 1 ] && have_wt; then
    whiptail --title "$title" --scrolltext --ok-button "Продолжить" \
             --msgbox "$text" "$h" 78
  else
    echo; echo "${C_H}═══ $title ═══${C_0}"; echo "$text"
    [ "$DRY_RUN" = 1 ] && return 0
    read -rp "  Enter — продолжить… " _ </dev/tty 2>/dev/null || true
  fi
}

ask_yn() {
  local title="$1" text="$2" yes="${3:-Да}" no="${4:-Нет}" h="${5:-14}"
  if [ "$USE_UI" = 1 ] && have_wt; then
    whiptail --title "$title" --yes-button "$yes" --no-button "$no" \
             --yesno "$text" "$h" 78
  else
    echo; echo "${C_H}═══ $title ═══${C_0}"; echo "$text"
    [ "$DRY_RUN" = 1 ] && return 0
    local a; read -rp "  $yes / $no? [y/N] " a </dev/tty 2>/dev/null || a=n
    [ "${a,,}" = "y" ]
  fi
}

ask_line() {
  local title="$1" text="$2" def="$3" out=""
  if [ "$USE_UI" = 1 ] && have_wt; then
    out=$(whiptail --title "$title" --inputbox "$text" 14 78 "$def" \
          3>&1 1>&2 2>&3) || exit 0
  else
    echo >&2; echo "${C_H}── $title ──${C_0}" >&2; echo "$text" >&2
    if [ "$DRY_RUN" = 0 ]; then
      read -rp "  [$def]: " out </dev/tty 2>/dev/null || out=""
    fi
  fi
  echo "${out:-$def}"
}

msg_ok() { screen "$1" "$2" "${3:-14}"; }

# ── проверка введённого ───────────────────────────────────────────────────

valid_domain() { [[ "$1" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$ ]]; }
valid_ip()     {
  [[ "$1" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || return 1
  local o; for o in ${1//./ }; do [ "$o" -le 255 ] || return 1; done
}
valid_boxes()  { [[ "$1" =~ ^[a-z0-9][a-z0-9._-]*(,[a-z0-9][a-z0-9._-]*)*$ ]]; }

# Спрашивает, пока не введут корректное значение.
ask_valid() {
  local title="$1" text="$2" def="$3" checker="$4" hint="$5" out
  while :; do
    out=$(ask_line "$title" "$text" "$def")
    out=$(echo "$out" | tr -d ' ' | tr 'A-Z' 'a-z')
    if [ -n "$out" ] && "$checker" "$out"; then echo "$out"; return 0; fi
    msg_ok "Проверьте ввод" "«$out» не подходит.

$hint" 12
  done
}

# ═════════════════════════════════════════════════════════════════════════
#  Удаление
# ═════════════════════════════════════════════════════════════════════════

uninstall() {
  ask_yn "Удаление" \
"Остановить и удалить почтовый сервер?

Каталог $DIR со ВСЕЙ почтой будет удалён.
Отменить это будет нельзя." "Удалить" "Отмена" || exit 0
  [ -f "$DIR/compose.yaml" ] && run "cd $DIR && docker compose down -v"
  run "rm -rf $DIR"
  run "rm -f /etc/cron.d/mailserver-cert"
  ok "удалено"; exit 0
}
[ "$DO_UNINSTALL" = 1 ] && uninstall

# ═════════════════════════════════════════════════════════════════════════
#  Вспомогательное
# ═════════════════════════════════════════════════════════════════════════

ensure_tools() {
  command -v dig >/dev/null 2>&1 && command -v curl >/dev/null 2>&1 && return 0
  [ "$DRY_RUN" = 1 ] && return 0
  echo "Ставлю утилиты для проверок…"
  DEBIAN_FRONTEND=noninteractive apt-get update -qq >>"$LOG" 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    bind9-dnsutils curl ca-certificates >>"$LOG" 2>&1 || \
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    dnsutils curl ca-certificates >>"$LOG" 2>&1
  return 0
}

ensure_wt() {
  have_wt && return 0
  DEBIAN_FRONTEND=noninteractive apt-get update -qq >>"$LOG" 2>&1
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq whiptail >>"$LOG" 2>&1
  have_wt
}

detect_ip() {
  local u ip
  for u in https://api.ipify.org https://ifconfig.me/ip https://icanhazip.com; do
    ip=$(curl -fsS --max-time 6 "$u" 2>/dev/null | tr -dc '0-9.')
    [ -n "$ip" ] && { echo "$ip"; return; }
  done
  hostname -I 2>/dev/null | awk '{print $1}'
}

# Запрос через публичный резолвер: видим то же, что чужой почтовый сервер.
dq() { dig +short "$@" @1.1.1.1 2>/dev/null | tr -d '"' | tr '\n' ' ' | xargs; }

port25_open() {
  timeout 8 bash -c 'exec 3<>/dev/tcp/gmail-smtp-in.l.google.com/25' 2>/dev/null
}

dkim_value() {
  local f
  f=$(ls "$DIR"/docker-data/dms/config/rspamd/dkim/*.public.key 2>/dev/null | head -1)
  [ -z "$f" ] && { echo ""; return; }
  # Файл выглядит так:
  #   mail._domainkey IN TXT ( "v=DKIM1; k=rsa; "
  #     "p=MIIBIjANBgkq..." ) ;
  # Берём всё, что в кавычках, и склеиваем ВПЛОТНУЮ: любой пробел,
  # вставленный между кусками, порвёт base64 и подпись не сойдётся.
  grep -o '"[^"]*"' "$f" | tr -d '"\n'
}

# Показать инструкцию, проверить, дать повторить.
verify_loop() {
  local title="$1" text="$2" checker="$3" done_text="$4"
  [ "$DRY_RUN" = 1 ] && return 0
  while :; do
    if "$checker"; then
      msg_ok "$title — готово" "$done_text" 12
      return 0
    fi
    if ask_yn "$title" "$text

Проверка не прошла. Нажмите «Проверить» после того,
как сделаете описанное выше." "Проверить" "Пропустить" 24; then
      continue
    else
      return 1
    fi
  done
}

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 0. Приветствие
# ═════════════════════════════════════════════════════════════════════════

if [ "$USE_UI" = 1 ]; then ensure_wt || USE_UI=0; fi
ensure_tools

screen "Мастер установки почтового сервера $VERSION" \
"Этот мастер доведёт вас от чистого сервера до работающей
почты на своём домене.

Что будет сделано:
  1. соберём параметры: домен, имя сервера, ящики
  2. проверим сервер и исходящий порт 25
  3. подскажем, какую запись DNS добавить, и проверим её
  4. установим Docker и почтовый сервер
  5. выпустим сертификат, создадим ящики и ключ DKIM
  6. покажем остальные записи DNS и проверим каждую
  7. поможем запросить PTR у хостинга
  8. проверим приём и отправку письма

После каждого шага — кнопка «Продолжить». Ничего не
делается молча: перед каждым изменением вы видите,
что произойдёт.

Журнал установки: $LOG" 26

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 1. Параметры
# ═════════════════════════════════════════════════════════════════════════

screen "Шаг 1. Параметры — что понадобится" \
"Сейчас спрошу несколько вещей. Приготовьте:

  ДОМЕН — то, что стоит после @ в будущих адресах.
  Например: protestant.ru

  ИМЯ ПОЧТОВОГО СЕРВЕРА — отдельное имя третьего уровня,
  обычно mail.<домен>. Это НЕ адрес сайта: сайт остаётся
  там, где стоял, почта живёт на новом имени.

  IP ЭТОГО СЕРВЕРА — определю сам, вам останется сверить
  с панелью хостинга.

  ЯЩИКИ — какие адреса завести. Можно несколько через
  запятую: partners, info, red

  ПАРОЛЬ для ящиков." 26

DOMAIN=$(ask_valid "Домен" \
"Почтовый домен — то, что стоит после @ в адресе.

Пример: protestant.ru
Адреса получатся вида partners@protestant.ru" "protestant.ru" \
valid_domain "Домен пишется без http:// и без косой черты, латиницей,
и содержит хотя бы одну точку. Пример: protestant.ru")

FQDN=$(ask_valid "Имя почтового сервера" \
"Полное имя именно почтового сервера (FQDN).

Обычно mail.<домен>. Для этого имени вы дальше добавите
запись A, указывающую на этот сервер.

Сайт на домене не пострадает: у него своя запись,
её мы не трогаем." "mail.$DOMAIN" \
valid_domain "Нужно полное имя вида mail.$DOMAIN — латиницей,
без http:// и без косой черты.")

AUTO_IP=$(detect_ip)
SERVER_IP=$(ask_valid "IP этого сервера" \
"Внешний адрес сервера, на котором вы сейчас работаете.

Определил автоматически — сверьте с панелью хостинга
и при необходимости исправьте." "${AUTO_IP:-}" \
valid_ip "Нужен адрес вида 186.246.51.250 — четыре числа
от 0 до 255, разделённые точками.")

MAILBOXES=$(ask_valid "Почтовые ящики" \
"Имена ящиков без @домена, через запятую.

Первый в списке станет главным: на него пойдут письма
для postmaster@ и abuse@, а также, если включите,
письма на несуществующие адреса.

Пример: partners, info, red" "partners, info" \
valid_boxes "Имена пишутся латиницей, через запятую, без @ и без
пробелов внутри имени. Пример: partners,info,red")

MAIN_BOX=$(echo "$MAILBOXES" | cut -d, -f1)

if ask_yn "Письма на несуществующие адреса" \
"Что делать с письмом на адрес, которого нет — например,
на pastor@$DOMAIN, если такого ящика вы не заводили?

  ДА — складывать всё в ${MAIN_BOX}@${DOMAIN}.
       Ни одно письмо не потеряется: ошибся ли
       отправитель в адресе, писал ли на старый —
       всё равно дойдёт.
       Обратная сторона: туда же польётся спам,
       который рассылают по словарю адресов.

  НЕТ — отправитель получит уведомление, что адреса
        не существует. Спама меньше, но письмо с
        опечаткой пропадёт.

Для переписки с организациями обычно выбирают ДА." \
"Да, всё в ${MAIN_BOX}" "Нет, отклонять" 24; then
  CATCHALL=1
else
  CATCHALL=0
fi

if ask_yn "Доступ по SSH" \
"Вы подключаетесь к серверу по SSH или через VNC-консоль
в панели хостинга?

  SSH — оставлю 22-й порт открытым в файрволе.

  VNC — закрою 22-й порт. Если SSH и так выключен,
        открывать его незачем: этот порт круглосуточно
        перебирают боты.

Если сомневаетесь — выбирайте SSH: закрыв порт, которым
вы пользуетесь, вы отрежете себе доступ." \
"По SSH" "Через VNC-консоль" 20; then
  OPEN_SSH=1
else
  OPEN_SSH=0
fi

TZ_SET=$(ask_line "Часовой пояс" "Часовой пояс сервера:" "$TZ_SET")

if [ "$DRY_RUN" = 0 ]; then
  while :; do
    if [ "$USE_UI" = 1 ] && have_wt; then
      p1=$(whiptail --title "Пароль ящиков" --passwordbox \
"Пароль для ${MAIN_BOX}@${DOMAIN}.

Этот адрес виден из интернета, и его будут перебирать.
Возьмите длинный случайный пароль, не короче 12 знаков.

Остальные ящики получат тот же пароль — смените его
потом одной командой, она будет в конце." 16 78 3>&1 1>&2 2>&3) || exit 0
      p2=$(whiptail --title "Пароль ящиков" --passwordbox "Повторите пароль:" \
           9 78 3>&1 1>&2 2>&3) || exit 0
    else
      read -rsp "  Пароль для ${MAIN_BOX}@${DOMAIN}: " p1 </dev/tty; echo
      read -rsp "  Повторите: " p2 </dev/tty; echo
    fi
    if [ -z "$p1" ]; then msg_ok "Пароль" "Пустой пароль не годится." 8
    elif [ "$p1" != "$p2" ]; then msg_ok "Пароль" "Пароли не совпали." 8
    elif [ ${#p1} -lt 10 ]; then
      msg_ok "Пароль" "Меньше 10 символов — слишком коротко для ящика, открытого в интернет." 9
    else MB_PASS="$p1"; break; fi
  done
fi

if [ "$USE_UI" = 1 ] && have_wt; then
  sel=$(whiptail --title "Дополнительные настройки" --checklist \
    "Пробел — переключить, Enter — принять:" 16 76 6 \
    "firewall" "Настроить файрвол ufw"                ON \
    "swap"     "Файл подкачки при нехватке памяти"    ON \
    "cert"     "Сертификат Let's Encrypt"             ON \
    "cron"     "Автопродление сертификата"            ON \
    "fail2ban" "Защита от перебора паролей"           ON \
    "clamav"   "Антивирус ClamAV (нужно 3+ ГБ ОЗУ)"   OFF \
    3>&1 1>&2 2>&3) || exit 0
  OPT_FIREWALL=0; OPT_SWAP=0; OPT_CERT=0; OPT_CRON=0; OPT_FAIL2BAN=0; OPT_CLAMAV=0
  [[ "$sel" == *firewall* ]] && OPT_FIREWALL=1
  [[ "$sel" == *swap*     ]] && OPT_SWAP=1
  [[ "$sel" == *cert*     ]] && OPT_CERT=1
  [[ "$sel" == *cron*     ]] && OPT_CRON=1
  [[ "$sel" == *fail2ban* ]] && OPT_FAIL2BAN=1
  [[ "$sel" == *clamav*   ]] && OPT_CLAMAV=1
fi

BOX_LIST=$(echo "$MAILBOXES" | tr ',' '\n' | sed "s/^/  /; s/\$/@${DOMAIN}/" | tr '\n' ' ')
CA_LINE="выключен, письма на неизвестные адреса отклоняются"
[ "$CATCHALL" = 1 ] && CA_LINE="включён → ${MAIN_BOX}@${DOMAIN}"

screen "Шаг 1 — итог" \
"  Домен:           $DOMAIN
  Почтовый сервер: $FQDN
  IP сервера:      $SERVER_IP
  Ящики:          $BOX_LIST
  Главный ящик:    ${MAIN_BOX}@${DOMAIN}
  Приём мусора:    $CA_LINE
  Часовой пояс:    $TZ_SET

Если что-то не так — прервите работу клавишами Ctrl+C
и запустите мастер заново." 20

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 2. Сервер и порт 25
# ═════════════════════════════════════════════════════════════════════════

RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
DISK_GB=$(df -BG --output=avail / 2>/dev/null | tail -1 | tr -dc '0-9'); : "${DISK_GB:=0}"
OS_NAME="неизвестна"; [ -f /etc/os-release ] && { . /etc/os-release; OS_NAME="$PRETTY_NAME"; }
RAM_NOTE="достаточно"
[ "$RAM_MB" -lt 1800 ] && RAM_NOTE="маловато, добавлю файл подкачки"

screen "Шаг 2. Проверка сервера" \
"  Система: $OS_NAME
  Память:  ${RAM_MB} МБ — $RAM_NOTE
  Диск:    ${DISK_GB} ГБ свободно

Сейчас проверю исходящий порт 25. Это самое важное:
через него сервер отправляет письма другим серверам.
Проверка занимает несколько секунд." 16

check_port25() { port25_open; }

verify_loop "Шаг 2. Исходящий порт 25" \
"Исходящий порт 25 ЗАКРЫТ.

Так делают почти все российские хостинги: порт закрыт
по умолчанию, чтобы через серверы не рассылали спам.
Ваш сервер сможет ПРИНИМАТЬ почту, но не отправит
ни одного письма.

ЧТО СДЕЛАТЬ. Написать в поддержку хостинга, где стоит
ЭТОТ сервер ($SERVER_IP):

  «Прошу открыть исходящий 25-й порт для сервера
   $SERVER_IP. Разворачиваю корпоративный почтовый
   сервер организации для деловой переписки.»

Обычно открывают в течение часа. Можно продолжить
установку и вернуться к этому позже — приём почты
заработает сразу." \
check_port25 \
"Исходящий порт 25 открыт — письма смогут уходить." || \
  log "порт 25 закрыт, шаг пропущен"

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 3. Запись A
# ═════════════════════════════════════════════════════════════════════════

check_a() { [ "$(dq A "$FQDN")" = "$SERVER_IP" ]; }

screen "Шаг 3. Первая запись DNS" \
"Прежде чем ставить сервер, нужна одна запись DNS.
Без неё не выпустится сертификат шифрования.

ГДЕ ЭТО ДЕЛАТЬ. В панели управления DNS домена
$DOMAIN — там же, где заданы записи сайта.
Обычно это личный кабинет регистратора домена или
хостинга сайта, раздел «Настройка DNS» или
«DNS-записи».

Это НЕ на этом сервере и НЕ в панели VDS.

ЧТО ДОБАВИТЬ:

    Тип:      A
    Имя:      ${FQDN}.
    Значение: ${SERVER_IP}

Некоторые панели просят вводить короткое имя — просто
mail вместо полного. Посмотрите, как записаны соседние
строки, и сделайте так же.

Записи сайта не трогайте: ни A для ${DOMAIN}, ни www." 30

verify_loop "Шаг 3. Запись A" \
"Запись A для ${FQDN} пока не указывает на ${SERVER_IP}.

Добавьте в панели DNS домена ${DOMAIN}:

    Тип: A    Имя: ${FQDN}.    Значение: ${SERVER_IP}

Изменения расходятся по интернету от 15 минут до двух
часов. Нажмите «Проверить» через несколько минут." \
check_a \
"Запись A на месте: ${FQDN} → ${SERVER_IP}" || \
  msg_ok "Шаг 3 пропущен" \
"Продолжаем без записи A. Сертификат выпустить не
удастся — команда для выпуска будет в конце." 12

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 4. Установка
# ═════════════════════════════════════════════════════════════════════════

screen "Шаг 4. Установка" \
"Теперь ставлю всё необходимое. Займёт 5–15 минут,
в основном на загрузку образа.

Что произойдёт:
  • обновление пакетов и базовые утилиты
  • имя сервера → $FQDN
  • часовой пояс → $TZ_SET
  • файл подкачки, если памяти мало
  • остановка postfix и exim, если заняли порты
  • файрвол: откроются $( [ "$OPEN_SSH" = 1 ] && echo '22, ' )25, 80, 143, 465, 587, 993
  • установка Docker
  • развёртывание почтового сервера
  • сертификат Let's Encrypt и автопродление
  • создание ящиков и правил пересылки
  • генерация ключа DKIM

Подробности пишутся в $LOG" 26

step_packages() {
  export DEBIAN_FRONTEND=noninteractive
  run "apt-get update -qq"
  run "apt-get install -y -qq curl ca-certificates gnupg ufw"
}
step_system() {
  run "hostnamectl set-hostname '$FQDN'"
  grep -q "$FQDN" /etc/hosts 2>/dev/null || \
    run "printf '127.0.1.1 %s %s\n' '$FQDN' '${FQDN%%.*}' >> /etc/hosts"
  run "timedatectl set-timezone '$TZ_SET'"
}
step_swap() {
  [ "$OPT_SWAP" = 1 ] || return 0
  [ "$(swapon --show 2>/dev/null | wc -l)" -gt 0 ] && return 0
  [ "$RAM_MB" -ge 2500 ] && return 0
  run "fallocate -l 1G /swapfile"; run "chmod 600 /swapfile"
  run "mkswap /swapfile"; run "swapon /swapfile"
  run "grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab"
}
step_ports() {
  local svc
  for svc in postfix exim4 dovecot sendmail opensmtpd; do
    systemctl is-active --quiet "$svc" 2>/dev/null && run "systemctl disable --now $svc"
  done
  return 0
}
step_firewall() {
  [ "$OPT_FIREWALL" = 1 ] || return 0
  run "ufw --force reset"; run "ufw default deny incoming"
  run "ufw default allow outgoing"
  local p
  for p in 25 80 143 465 587 993; do run "ufw allow ${p}/tcp"; done
  # 22-й открываем только если им пользуются: при работе через VNC-консоль
  # лишняя открытая дверь ни к чему
  [ "$OPEN_SSH" = 1 ] && run "ufw allow 22/tcp"
  run "ufw --force enable"
}
step_docker() {
  command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && return 0
  run "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh"
  run "sh /tmp/get-docker.sh"
  run "systemctl enable --now docker"
}
step_compose() {
  run "mkdir -p $DIR/docker-data/dms/config $DIR/docker-data/dms/mail-data \
       $DIR/docker-data/dms/mail-state $DIR/docker-data/dms/mail-logs \
       $DIR/docker-data/certbot/certs"
  [ "$DRY_RUN" = 1 ] && { echo "      [dry-run] compose.yaml"; return 0; }
  cat > "$DIR/compose.yaml" <<YAML
services:
  mailserver:
    image: ghcr.io/docker-mailserver/docker-mailserver:latest
    container_name: mailserver
    hostname: ${FQDN}
    ports:
      - "25:25"      # приём почты от других серверов
      - "143:143"    # IMAP
      - "465:465"    # отправка, SSL
      - "587:587"    # отправка, STARTTLS
      - "993:993"    # IMAP, SSL
    volumes:
      - ./docker-data/dms/mail-data/:/var/mail/
      - ./docker-data/dms/mail-state/:/var/mail-state/
      - ./docker-data/dms/mail-logs/:/var/log/mail/
      - ./docker-data/dms/config/:/tmp/docker-mailserver/
      - ./docker-data/certbot/certs/:/etc/letsencrypt/:ro
      - /etc/localtime:/etc/localtime:ro
    environment:
      - ENABLE_RSPAMD=1
      - ENABLE_CLAMAV=${OPT_CLAMAV}
      - ENABLE_FAIL2BAN=${OPT_FAIL2BAN}
      - ENABLE_OPENDKIM=0
      - ENABLE_OPENDMARC=0
      - ENABLE_POLICYD_SPF=0
      - SPOOF_PROTECTION=1
      - POSTMASTER_ADDRESS=postmaster@${DOMAIN}
      - SSL_TYPE=letsencrypt
      - PERMIT_DOCKER=none
      - LOG_LEVEL=info
    cap_add: [NET_ADMIN]
    restart: always
YAML
}
step_cert() {
  [ "$OPT_CERT" = 1 ] || return 0
  check_a || { log "сертификат пропущен: запись A не совпадает"; return 0; }
  run "docker run --rm -p 80:80 \
       -v $DIR/docker-data/certbot/certs/:/etc/letsencrypt/ \
       certbot/certbot certonly --standalone -d '$FQDN' \
       --agree-tos --register-unsafely-without-email -n"
}
step_cron() {
  [ "$OPT_CRON" = 1 ] || return 0
  [ "$DRY_RUN" = 1 ] && { echo "      [dry-run] cron"; return 0; }
  cat > /etc/cron.d/mailserver-cert <<CRON
# Продление сертификата Let's Encrypt и перезапуск почтового сервера
17 4 * * 1 root docker run --rm -p 80:80 -v $DIR/docker-data/certbot/certs/:/etc/letsencrypt/ certbot/certbot renew -n --standalone >> /var/log/certbot-renew.log 2>&1 && docker restart mailserver >> /var/log/certbot-renew.log 2>&1
CRON
  chmod 644 /etc/cron.d/mailserver-cert
}
step_pull() { run "cd $DIR && docker compose pull"; }
step_up()   { run "cd $DIR && docker compose up -d"; }
step_wait() {
  [ "$DRY_RUN" = 1 ] && return 0
  local i
  for i in $(seq 1 40); do
    docker exec mailserver ss -lnt 2>/dev/null | grep -q ':25 ' && return 0
    sleep 3
  done
  return 0
}
step_boxes() {
  [ "$DRY_RUN" = 1 ] && { echo "      [dry-run] ящики, алиасы, catch-all"; return 0; }
  local b
  for b in ${MAILBOXES//,/ }; do
    [ -z "$b" ] && continue
    run "docker exec mailserver setup email add '${b}@${DOMAIN}' '${MB_PASS}'"
  done
  run "docker exec mailserver setup alias add 'postmaster@${DOMAIN}' '${MAIN_BOX}@${DOMAIN}'"
  run "docker exec mailserver setup alias add 'abuse@${DOMAIN}' '${MAIN_BOX}@${DOMAIN}'"
  # приём писем на несуществующие адреса домена
  if [ "$CATCHALL" = 1 ]; then
    run "docker exec mailserver setup alias add '@${DOMAIN}' '${MAIN_BOX}@${DOMAIN}'"
  fi
}
step_dkim() {
  [ "$DRY_RUN" = 1 ] && { echo "      [dry-run] DKIM"; return 0; }
  run "docker exec mailserver setup config dkim keysize 2048 domain '$DOMAIN'"
  run "docker restart mailserver"
}

# ═════════════════════════════════════════════════════════════════════════
#  Исполнитель шагов: проверяет результат, чинит сам, спрашивает при неудаче
# ═════════════════════════════════════════════════════════════════════════

FAILED_STEPS=""      # что не удалось — покажем в итоге

# Индикатор без ожидания ввода: рисуем полосу сами.
progress() {
  local pct="$1" label="$2" filled bar i
  filled=$((pct / 5))
  bar=""
  for ((i = 0; i < 20; i++)); do
    if [ $i -lt $filled ]; then bar="${bar}█"; else bar="${bar}░"; fi
  done
  if [ "$USE_UI" = 1 ] && have_wt; then
    whiptail --title "Установка" --infobox \
"$label

  [${bar}] ${pct}%

Подробности пишутся в $LOG" 11 74
  else
    printf "\r  [%s] %3d%%  %-40s" "$bar" "$pct" "$label"
  fi
}

# Меню выбора при неудаче шага.
step_menu() {
  local title="$1" text="$2"
  if [ "$USE_UI" = 1 ] && have_wt; then
    whiptail --title "$title" --menu "$text" 22 78 4 \
      "1" "Попробовать ещё раз" \
      "2" "Починить и повторить" \
      "3" "Пропустить этот шаг" \
      "4" "Прервать установку" 3>&1 1>&2 2>&3
  else
    # Вопрос — только в stderr: stdout уходит в подстановку $(step_menu …),
    # и любой лишний символ там ломает разбор ответа.
    { echo; echo "${C_H}═══ $title ═══${C_0}"; echo "$text";
      echo "  1) повторить   2) починить и повторить   3) пропустить   4) прервать"; } >&2
    local a=""
    if [ -t 0 ] || [ -e /dev/tty ]; then
      read -rp "  Выбор [1]: " a </dev/tty 2>/dev/null || a=3
    else
      a=3    # нет терминала — пропускаем, чтобы не зациклиться
    fi
    echo "${a:-1}"
  fi
}

# run_step  <функция> <название> <процент> [проверка] [починка]
run_step() {
  local fn="$1" title="$2" pct="$3" verify="${4:-}" fixer="${5:-}"
  local rc tried_fix=0 choice

  while :; do
    progress "$pct" "$title…"
    log "--- шаг: $title"
    "$fn"; rc=$?
    # в режиме проверки ничего не выполняется, проверять нечего
    if [ "$DRY_RUN" = 1 ]; then return 0; fi
    # Если задана проверка результата — верим ей, а не коду возврата:
    # шаг мог сообщить об ошибке, но дело в итоге сделано (и наоборот).
    if [ -n "$verify" ]; then
      if "$verify"; then rc=0; else rc=1; fi
    fi
    if [ "$rc" -eq 0 ]; then
      log "шаг «$title» выполнен"
      return 0
    fi

    log "шаг «$title» НЕ выполнен (код $rc)"

    # Первая неудача — пробуем починить сами, молча.
    if [ -n "$fixer" ] && [ "$tried_fix" = 0 ]; then
      tried_fix=1
      progress "$pct" "$title — исправляю…"
      log "автоисправление шага «$title»"
      "$fixer"
      continue
    fi

    # Не помогло — спрашиваем.
    choice=$(step_menu "Шаг не выполнен: $title" \
"Не удалось выполнить: $title

$(tail -n 6 "$LOG" 2>/dev/null | sed 's/^/  /')

Что делать?

  Повторить — если вы что-то поправили вручную
  Починить  — попробовать исправить автоматически ещё раз
  Пропустить — двигаться дальше, вернуться к этому позже
  Прервать — выйти из мастера")
    case "${choice:-3}" in
      1) tried_fix=0; continue ;;
      2) [ -n "$fixer" ] && "$fixer"; continue ;;
      3) FAILED_STEPS="${FAILED_STEPS}
  • $title"; return 1 ;;
      4) msg_ok "Прервано" "Установка прервана. Журнал: $LOG" 9; exit 1 ;;
      *) FAILED_STEPS="${FAILED_STEPS}
  • $title"; return 1 ;;
    esac
  done
}

# ── проверки результата шагов ────────────────────────────────────────────

v_packages() { command -v curl >/dev/null 2>&1; }
v_docker()   { command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; }
v_compose()  { [ -s "$DIR/compose.yaml" ]; }
v_cert()     {
  [ "$OPT_CERT" = 1 ] || return 0
  check_a || return 0          # без записи A сертификата и не ждём
  [ -s "$DIR/docker-data/certbot/certs/live/$FQDN/fullchain.pem" ]
}
v_up()       { docker ps --format '{{.Names}}' 2>/dev/null | grep -qx mailserver; }
v_wait()     { docker exec mailserver ss -lnt 2>/dev/null | grep -q ':25 '; }
v_boxes()    {
  docker exec mailserver setup email list 2>/dev/null | grep -q "${MAIN_BOX}@${DOMAIN}"
}
v_dkim()     { [ -n "$(dkim_value)" ]; }

# ── попытки исправления ──────────────────────────────────────────────────

f_packages() {
  # частые причины: битый кеш apt, оборванная установка, смена релиза
  run "dpkg --configure -a"
  run "apt-get -f install -y -qq"
  run "rm -rf /var/lib/apt/lists/*"
  run "apt-get update -qq --allow-releaseinfo-change"
}

f_docker() {
  # официальный скрипт мог не отработать — ставим из репозитория дистрибутива
  run "apt-get update -qq"
  run "apt-get install -y -qq docker.io docker-compose-v2"
  run "systemctl enable --now docker"
}

f_cert() {
  # почти всегда порт 80 занят веб-сервером
  local svc
  for svc in nginx apache2 caddy lighttpd; do
    systemctl is-active --quiet "$svc" 2>/dev/null && {
      log "останавливаю $svc для выпуска сертификата"
      run "systemctl stop $svc"
    }
  done
  run "docker rm -f certbot-tmp"
  # вторая попытка выпуска
  run "docker run --rm --name certbot-tmp -p 80:80 \
       -v $DIR/docker-data/certbot/certs/:/etc/letsencrypt/ \
       certbot/certbot certonly --standalone -d '$FQDN' \
       --agree-tos --register-unsafely-without-email -n"
}

# Если сертификата так и нет — переводим сервер на самоподписанный,
# иначе он не запустится вовсе. Почта заработает, письма будут ходить;
# сертификат выпустим позже одной командой.
f_cert_fallback() {
  [ -s "$DIR/docker-data/certbot/certs/live/$FQDN/fullchain.pem" ] && return 0
  log "сертификата нет — переключаю на самоподписанный"
  run "sed -i 's|- SSL_TYPE=letsencrypt|- SSL_TYPE=self-signed|' $DIR/compose.yaml"
  CERT_FALLBACK=1
}

f_up() {
  run "systemctl restart docker"
  sleep 5
  run "cd $DIR && docker compose down"
  run "cd $DIR && docker compose up -d"
}

f_wait() {
  run "cd $DIR && docker compose restart"
  sleep 10
}

f_boxes() {
  # чаще всего контейнер ещё не готов принимать команды
  local i
  for i in $(seq 1 20); do
    docker exec mailserver ss -lnt 2>/dev/null | grep -q ':25 ' && break
    sleep 3
  done
  step_boxes
}

f_dkim() {
  local i
  for i in $(seq 1 10); do
    docker exec mailserver true 2>/dev/null && break
    sleep 3
  done
  run "docker exec mailserver setup config dkim keysize 2048 domain '$DOMAIN'"
  run "docker restart mailserver"
  sleep 5
}

STEPS=(
  "step_packages|Обновление пакетов|8|v_packages|f_packages"
  "step_system|Имя сервера и часовой пояс|15||"
  "step_swap|Файл подкачки|20||"
  "step_ports|Освобождение почтовых портов|26||"
  "step_firewall|Настройка файрвола|34||"
  "step_docker|Установка Docker|50|v_docker|f_docker"
  "step_compose|Конфигурация почтового сервера|58|v_compose|"
  "step_cert|Сертификат Let's Encrypt|66|v_cert|f_cert"
  "step_cron|Автопродление сертификата|70||"
  "step_pull|Загрузка образа|84||"
  "step_up|Запуск сервера|88|v_up|f_up"
  "step_wait|Ожидание готовности|92|v_wait|f_wait"
  "step_boxes|Ящики и правила пересылки|96|v_boxes|f_boxes"
  "step_dkim|Ключ DKIM|100|v_dkim|f_dkim"
)

CERT_FALLBACK=0

for entry in "${STEPS[@]}"; do
  IFS='|' read -r fn title pct vfn ffn <<< "$entry"
  run_step "$fn" "$title" "$pct" "$vfn" "$ffn"
  # особый случай: без сертификата сервер не поднимется вовсе —
  # переводим на самоподписанный, чтобы почта работала уже сейчас
  if [ "$fn" = "step_cert" ] && ! v_cert; then
    f_cert_fallback
  fi
done
[ "$USE_UI" = 0 ] && echo
STEP4_NOTE=""
[ -n "$FAILED_STEPS" ] && STEP4_NOTE="

НЕ УДАЛОСЬ ВЫПОЛНИТЬ:$FAILED_STEPS

Это не тупик: к пропущенному можно вернуться позже,
подсказки будут в конце. Смотрите $LOG"
[ "$CERT_FALLBACK" = 1 ] && STEP4_NOTE="$STEP4_NOTE

Сертификат Let's Encrypt выпустить не удалось, сервер
работает с самоподписанным. Почта ходит, но почтовые
программы будут ругаться на сертификат. Команда для
выпуска — в конце мастера."

screen "Шаг 4 — готово" \
"Почтовый сервер установлен и запущен.$STEP4_NOTE

  Ящики: $BOX_LIST
  postmaster@${DOMAIN} и abuse@${DOMAIN}
    пересылаются на ${MAIN_BOX}@${DOMAIN}
  Приём на несуществующие адреса: $CA_LINE

Осталось прописать записи DNS — без них письма не будут
ни уходить, ни приходить. Этим займёмся дальше." 18

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 5. Записи DNS
# ═════════════════════════════════════════════════════════════════════════

DKIM_VAL=$(dkim_value)
[ -z "$DKIM_VAL" ] && DKIM_VAL="значение не считалось — выполните после установки:
cat $DIR/docker-data/dms/config/rspamd/dkim/*.public.key"

screen "Шаг 5. Записи DNS — где именно" \
"ГДЕ. В панели управления DNS домена $DOMAIN — там же,
где вы добавляли запись A на прошлом шаге.

Это личный кабинет регистратора домена или хостинга
сайта, раздел «Настройка DNS» или «DNS-записи».
Не на этом сервере, не в панели VDS.

ВАЖНО. Если у домена $DOMAIN уже есть запись MX,
указывающая на другой почтовый сервис — её нужно
УДАЛИТЬ. Иначе письма пойдут по старому адресу,
а вы будете искать неисправность в новом сервере.

Дальше покажу четыре записи, по одной на экран." 24

screen "Запись 1 из 4 — MX" \
"Говорит всему интернету, куда доставлять письма
для адресов @${DOMAIN}.

    Тип:       MX
    Имя:       ${DOMAIN}.
    Значение:  ${FQDN}.
    Приоритет: 10

В некоторых панелях поле «Имя» для самого домена
заполняется знаком @ или оставляется пустым." 18

screen "Запись 2 из 4 — SPF" \
"Перечисляет, кому разрешено отправлять письма от имени
вашего домена. Без неё письма считают подделкой.

    Тип:      TXT
    Имя:      ${DOMAIN}.
    Значение: v=spf1 mx ~all

Знак ~ перед all — мягкий режим: письма с чужих серверов
помечаются подозрительными, но не отвергаются. Через
месяц наблюдений можно ужесточить, заменив на -all." 18

screen "Запись 3 из 4 — DMARC" \
"Указывает, что делать с письмами, не прошедшими
проверку, и куда присылать отчёты.

    Тип:      TXT
    Имя:      _dmarc.${DOMAIN}.
    Значение: v=DMARC1; p=none; rua=mailto:postmaster@${DOMAIN}

p=none означает «пока только собирать статистику,
ничего не отвергать». Это правильное начало: сперва
убедиться, что всё сходится, потом ужесточать." 18

screen "Запись 4 из 4 — DKIM" \
"Криптографическая подпись. Подтверждает, что письмо
отправлено вами и не изменено по дороге.

    Тип: TXT
    Имя: mail._domainkey.${DOMAIN}.
    Значение: на следующем экране — строка длинная

ДВЕ ЧАСТЫЕ ОШИБКИ:
  • при копировании в значение попадают переносы строк
    и лишние пробелы — вставляйте одной сплошной строкой;
  • если панель сама оборачивает значение в кавычки,
    свои кавычки добавлять не надо." 20

screen "Значение DKIM — скопируйте целиком" "$DKIM_VAL" 22

screen "Если копирование из консоли не работает" \
"В веб-консолях и VNC буфер обмена часто не работает, а
строка DKIM длинная — перепечатывать вручную нельзя,
ошибётесь в одном символе, и подпись не сойдётся.

Заберите её через браузер. На сервере выполните:

    ufw allow 8080/tcp
    cd $DIR/docker-data/dms/config/rspamd/dkim
    python3 -m http.server 8080

Откройте в браузере http://${SERVER_IP}:8080, щёлкните
по файлу и скопируйте значение оттуда.

Затем вернитесь в консоль, нажмите Ctrl+C и закройте
порт обратно:

    ufw delete allow 8080/tcp" 26

check_mx()    { [[ "$(dq MX "$DOMAIN")" == *"$FQDN"* ]]; }
check_spf()   { [[ "$(dq TXT "$DOMAIN")" == *"v=spf1"* ]]; }
check_dmarc() { [[ "$(dq TXT "_dmarc.$DOMAIN")" == *"v=DMARC1"* ]]; }
check_dkim()  { [[ "$(dq TXT "mail._domainkey.$DOMAIN")" == *"v=DKIM1"* ]]; }

verify_loop "Проверка MX" \
"Запись MX для ${DOMAIN} не найдена или указывает
не на ${FQDN}.

В панели DNS домена ${DOMAIN}:
    Тип: MX   Имя: ${DOMAIN}.   Значение: ${FQDN}.
    Приоритет: 10" \
check_mx "MX на месте: почта для @${DOMAIN} пойдёт на ${FQDN}" || true

verify_loop "Проверка SPF" \
"TXT-запись SPF для ${DOMAIN} не найдена.

В панели DNS домена ${DOMAIN}:
    Тип: TXT   Имя: ${DOMAIN}.   Значение: v=spf1 mx ~all" \
check_spf "SPF на месте." || true

verify_loop "Проверка DMARC" \
"TXT-запись _dmarc.${DOMAIN} не найдена.

В панели DNS домена ${DOMAIN}:
    Тип: TXT   Имя: _dmarc.${DOMAIN}.
    Значение: v=DMARC1; p=none; rua=mailto:postmaster@${DOMAIN}" \
check_dmarc "DMARC на месте." || true

verify_loop "Проверка DKIM" \
"TXT-запись mail._domainkey.${DOMAIN} не найдена или
значение скопировано не полностью.

Посмотреть значение заново:
  cat $DIR/docker-data/dms/config/rspamd/dkim/*.public.key" \
check_dkim "DKIM на месте — письма будут подписаны." || true

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 6. PTR
# ═════════════════════════════════════════════════════════════════════════

check_ptr() {
  local g; g=$(dig +short -x "$SERVER_IP" @1.1.1.1 2>/dev/null | xargs)
  [ "$g" = "${FQDN}." ] || [ "$g" = "$FQDN" ]
}

screen "Шаг 6. PTR — обратная запись" \
"Последняя запись, и единственная, которую нельзя
сделать самому.

ПОЧЕМУ. Обычные записи живут в зоне вашего домена —
ими управляете вы. PTR живёт в обратной зоне IP-адреса,
а она принадлежит владельцу диапазона адресов, то есть
хостингу. Из панели домена туда не попасть.

ГДЕ. В поддержке хостинга, где стоит ЭТОТ сервер
($SERVER_IP). У некоторых провайдеров есть поле «PTR»
или «Обратная зона» прямо в панели VDS — посмотрите
там сначала.

ЧТО НАПИСАТЬ:

  «Прошу настроить PTR-запись для IP ${SERVER_IP}
   на имя ${FQDN}.»

БЕЗ PTR Gmail, Mail.ru и Яндекс отвергают письма почти
всегда. Это не рекомендация, а обязательное условие." 30

verify_loop "Проверка PTR" \
"PTR для ${SERVER_IP} пока не указывает на ${FQDN}.

Пусто — запись не настроена вовсе.
Строка вида 250-51-246-186.static.hoster.ru — стоит
значение по умолчанию, его надо заменить.

Запрос в поддержку хостинга:
  «Прошу настроить PTR для ${SERVER_IP} на ${FQDN}.»

После ответа поддержки старое значение может ещё
сутки держаться в кешах — проверьте позже." \
check_ptr "PTR на месте: ${SERVER_IP} → ${FQDN}" || true

# ═════════════════════════════════════════════════════════════════════════
#  ШАГ 7. Проверка почты
# ═════════════════════════════════════════════════════════════════════════

EXTRA_CHECK=""
[ "$CATCHALL" = 1 ] && EXTRA_CHECK="
Заодно напишите на выдуманный адрес, например
proverka@${DOMAIN} — он тоже должен дойти
в ${MAIN_BOX}@${DOMAIN}."

screen "Шаг 7. Проверка приёма" \
"Отправьте письмо с любого своего ящика на адрес

    ${MAIN_BOX}@${DOMAIN}
$EXTRA_CHECK

Посмотреть, что происходит на сервере:

    cd $DIR && docker compose logs --tail 50

Нажмите «Продолжить», когда отправите." 20

screen "Шаг 7. Проверка отправки и репутации" \
"Теперь посмотрим, как ваши письма видят чужие серверы.

  1. Откройте mail-tester.com
  2. Скопируйте адрес, который он покажет
  3. Отправьте на него письмо с ${MAIN_BOX}@${DOMAIN}
     из почтовой программы
  4. Вернитесь на сайт и посмотрите оценку

НУЖНО 9 ИЗ 10 И ВЫШЕ.

Что обычно снимает баллы:
  • нет PTR — шаг 6
  • DKIM скопирован не целиком — шаг 5
  • IP в чёрном списке — проверьте на multirbl.valli.org
    и подайте заявку на исключение" 24

# ═════════════════════════════════════════════════════════════════════════
#  Самопроверка: что работает, что нет
# ═════════════════════════════════════════════════════════════════════════

selfcheck_report() {
  local r=""
  mark() { if "$1"; then echo "  [ есть ] $2"; else echo "  [  НЕТ ] $2"; fi; }

  r="$r$(mark v_up          'контейнер почтового сервера запущен')"$'\n'
  r="$r$(mark v_wait        'сервер принимает соединения на порту 25')"$'\n'
  r="$r$(mark v_boxes       "ящик ${MAIN_BOX}@${DOMAIN} создан")"$'\n'
  r="$r$(mark v_dkim        'ключ DKIM сгенерирован')"$'\n'
  r="$r$(mark check_port25  'исходящий порт 25 открыт')"$'\n'
  r="$r$(mark check_a       "запись A: ${FQDN} → ${SERVER_IP}")"$'\n'
  r="$r$(mark check_mx      'запись MX')"$'\n'
  r="$r$(mark check_spf     'запись SPF')"$'\n'
  r="$r$(mark check_dmarc   'запись DMARC')"$'\n'
  r="$r$(mark check_dkim    'запись DKIM в DNS')"$'\n'
  r="$r$(mark check_ptr     "PTR: ${SERVER_IP} → ${FQDN}")"
  echo "$r"
}

selfcheck_all_ok() {
  v_up && v_wait && v_boxes && check_port25 && check_a && \
  check_mx && check_spf && check_dmarc && check_dkim && check_ptr
}

while :; do
  [ "$DRY_RUN" = 1 ] && break
  REPORT=$(selfcheck_report)
  if selfcheck_all_ok; then
    screen "Самопроверка — всё в порядке" \
"$REPORT

Все проверки пройдены. Почта готова к работе." 22
    break
  fi
  if ask_yn "Самопроверка" \
"$REPORT

Помеченное «НЕТ» ещё не сделано. Часть пунктов зависит
от вас: записи DNS, порт 25 и PTR настраиваются вне
этого сервера.

Что делать дальше?" "Проверить снова" "Закончить" 26; then
    continue
  else
    break
  fi
done

# ═════════════════════════════════════════════════════════════════════════
#  Итог
# ═════════════════════════════════════════════════════════════════════════

TODO=""
check_port25 || TODO="$TODO
  • открыть исходящий порт 25 — запрос в поддержку хостинга"
check_a     || TODO="$TODO
  • запись A: ${FQDN} → ${SERVER_IP}"
check_mx    || TODO="$TODO
  • запись MX: ${DOMAIN}. → ${FQDN}. приоритет 10"
check_spf   || TODO="$TODO
  • запись TXT для ${DOMAIN}.: v=spf1 mx ~all"
check_dmarc || TODO="$TODO
  • запись TXT _dmarc.${DOMAIN}.: v=DMARC1; p=none; rua=mailto:postmaster@${DOMAIN}"
check_dkim  || TODO="$TODO
  • запись TXT mail._domainkey.${DOMAIN}. — значение в
    $DIR/docker-data/dms/config/rspamd/dkim/"
check_ptr   || TODO="$TODO
  • PTR для ${SERVER_IP} → ${FQDN} — запрос в поддержку хостинга"
[ "$CERT_FALLBACK" = 1 ] && TODO="$TODO
  • выпустить сертификат, когда заработает запись A:
    docker run --rm -p 80:80 -v $DIR/docker-data/certbot/certs/:/etc/letsencrypt/ \\
      certbot/certbot certonly --standalone -d $FQDN
    затем вернуть SSL_TYPE=letsencrypt в $DIR/compose.yaml
    и выполнить: cd $DIR && docker compose up -d"
[ -n "$TODO" ] && TODO="

ОСТАЛОСЬ СДЕЛАТЬ$TODO"

SUMMARY="Почтовый сервер готов.$TODO

НАСТРОЙКИ ДЛЯ ПОЧТОВОЙ ПРОГРАММЫ И РАССЫЛКИ
  Входящая (IMAP):  ${FQDN}, порт 993, SSL
  Исходящая (SMTP): ${FQDN}, порт 587, STARTTLS
  Логин:            ${MAIN_BOX}@${DOMAIN} — целиком, с доменом
  Пароль:           заданный при установке

ЯЩИКИ
 $BOX_LIST
  postmaster@${DOMAIN}, abuse@${DOMAIN} → ${MAIN_BOX}@${DOMAIN}
  Несуществующие адреса: $CA_LINE

ПРОГРЕВ
  Новый сервер — чистый IP без репутации. Резкий старт
  почтовые службы принимают за спам-атаку.
    дни 1-3        10-15 писем в день
    дни 4-7        20-30
    вторая неделя  50
    третья         100
    дальше         150-200

ОБСЛУЖИВАНИЕ
  Логи:        cd $DIR && docker compose logs -f
  Ящики:       docker exec -ti mailserver setup email list
  Новый ящик:  docker exec -ti mailserver setup email add имя@${DOMAIN}
  Пароль:      docker exec -ti mailserver setup email update имя@${DOMAIN}
  Обновление:  cd $DIR && docker compose pull && docker compose up -d
  Копия:       tar czf mail-\$(date +%F).tar.gz $DIR
  Удаление:    ./install.sh --uninstall

  Журнал установки: $LOG"

screen "Готово" "$SUMMARY" 30
echo; echo "${C_H}═══════════════════════════════════════════════════${C_0}"
echo "$SUMMARY"; echo
log "=== мастер завершён ==="
