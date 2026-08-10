#!/bin/sh
set -e

echo "Aplicando migrations..."
python manage.py migrate --noinput

if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
  echo "Coletando arquivos estáticos..."
  python manage.py collectstatic --noinput
fi

exec "$@"
