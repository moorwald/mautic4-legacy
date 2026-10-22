#!/bin/bash
set -euo pipefail
test "$(dpkg --print-architecture)" = amd64 || {
    echo >&2 "This pinned prototype is approved for amd64 only."
    exit 1
}
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y
apt-get install -y --no-install-recommends ca-certificates curl gnupg unzip
curl --fail --silent --show-error --location "$SURY_KEYRING_URL" -o /tmp/sury-keyring.deb
echo "$SURY_KEYRING_SHA256  /tmp/sury-keyring.deb" | sha256sum -c -
dpkg -i /tmp/sury-keyring.deb
# Only the PHP repository is enabled, not Sury Apache/nginx repositories.
printf '%s\n' 'deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ bookworm main' > /etc/apt/sources.list.d/sury-php.list
apt-get update
packages=()
for package in cli common json curl gd imap intl mbstring mysql opcache xml zip bcmath sqlite3; do
    packages+=("php7.4-${package}=${PHP_PACKAGE_VERSION}")
done
apt-get install -y --no-install-recommends "${packages[@]}" cron sudo mariadb-client git procps
# Keep the old PHP override paths while retaining the distribution module INIs.
mkdir -p /usr/local/etc/php/conf.d /usr/src/mautic /etc/mautic
ln -s /usr/bin/php7.4 /usr/local/bin/php
curl --fail --silent --show-error --location "https://getcomposer.org/download/${COMPOSER_VERSION}/composer.phar" -o /usr/local/bin/composer
echo "$COMPOSER_SHA256  /usr/local/bin/composer" | sha256sum -c -
chmod 755 /usr/local/bin/composer
printf '%s\n' 'deb.sury.org third-party PHP packages; versions in /usr/local/share/mautic-build-lock.json' > /etc/mautic/php-source.txt
rm -f /tmp/sury-keyring.deb /etc/cron.daily/*
apt-get clean
rm -rf /var/lib/apt/lists/*
