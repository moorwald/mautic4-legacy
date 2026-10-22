# syntax=docker/dockerfile:1
ARG DEBIAN_IMAGE=debian:bookworm-slim@sha256:7ff6ba31527b9e336162fa061746c366c4b2032f4d2cff2078bea43f78efe3f8
FROM ${DEBIAN_IMAGE} AS common

ARG PHP_PACKAGE_VERSION=1:7.4.33-31+0~20261021.121+debian12~1.gbpe9c428
ARG SURY_KEYRING_URL=https://packages.sury.org/debsuryorg-archive-keyring.deb
ARG SURY_KEYRING_SHA256=7511384559c9ddf1d5ce5f60be429ae9d4e7d01d9480d6f1b7a30c0810cf8b60
ARG COMPOSER_VERSION=2.10.3
ARG COMPOSER_SHA256=7a2d379d5b8ffdaa028580ef26494c36d2feef4b178d3dd1473a4dbc5e17c8d6
ENV PHP_PACKAGE_VERSION=${PHP_PACKAGE_VERSION}
COPY tools/install-runtime.sh /tmp/install-runtime.sh
RUN bash /tmp/install-runtime.sh && rm /tmp/install-runtime.sh

ARG MAUTIC_VERSION=4.4.13
ARG MAUTIC_SHA256=3d7446d29f279d17df370fd338583777f2c5f581ea1302458d7744ccac069b6a
ENV MAUTIC_VERSION=${MAUTIC_VERSION} \
    MAUTIC_SHA1=adce771ee8e35947c9d7c1dcc25bbbbb105a82a0
RUN curl --fail --silent --show-error --location \
    "https://github.com/mautic/mautic/releases/download/${MAUTIC_VERSION}/${MAUTIC_VERSION}.zip" -o /tmp/mautic.zip \
    && echo "${MAUTIC_SHA256}  /tmp/mautic.zip" | sha256sum -c - \
    && unzip -q /tmp/mautic.zip -d /usr/src/mautic \
    && rm /tmp/mautic.zip \
    && chown -R www-data:www-data /usr/src/mautic

COPY build-lock.json /usr/local/share/mautic-build-lock.json
COPY LICENSE NOTICE.md /usr/local/share/licenses/mautic4-legacy/
COPY common/docker-entrypoint.sh /entrypoint.sh
COPY common/makeconfig.php /makeconfig.php
COPY common/makedb.php /makedb.php
COPY common/mautic.crontab /usr/local/share/mautic.crontab
COPY common/check-runtime /usr/local/bin/check-runtime
RUN chmod 755 /entrypoint.sh /usr/local/bin/check-runtime \
    && chmod 644 /usr/local/share/mautic.crontab \
    && test "$(id -u www-data)" = 33 && test "$(id -g www-data)" = 33

ENV MAUTIC_RUN_CRON_JOBS=true MAUTIC_RUN_MIGRATIONS=false \
    MAUTIC_DB_USER=root MAUTIC_DB_NAME=mautic MAUTIC_DB_PORT=3306 \
    PHP_INI_DATE_TIMEZONE=UTC PHP_MEMORY_LIMIT=512M PHP_MAX_EXECUTION_TIME=300 \
    PHP_INI_DIR=/usr/local/etc/php PHPRC=/usr/local/etc/php/php.ini \
    PHP_INI_SCAN_DIR=/etc/php/7.4/cli/conf.d:/usr/local/etc/php/conf.d

ARG SOURCE_REVISION=local-uncommitted
LABEL org.opencontainers.image.source="https://github.com/moorwald/mautic4-legacy" \
    org.opencontainers.image.revision=${SOURCE_REVISION} \
    org.opencontainers.image.title="Unofficial moorwald Mautic 4 legacy image" \
    org.opencontainers.image.description="Unofficial end-of-life Mautic 4; PHP CVE-2026-109618/109619 mitigation only; no application support" \
    org.opencontainers.image.version="4.4.13-php74-r1" \
    org.opencontainers.image.licenses="GPL-3.0-or-later"

VOLUME ["/var/www/html"]
WORKDIR /var/www/html
ENTRYPOINT ["/entrypoint.sh"]

FROM common AS apache
ENV MAUTIC_VARIANT=apache PHP_MAX_UPLOAD=512M APACHE_CONFDIR=/etc/apache2 APACHE_ENVVARS=/etc/apache2/envvars
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends apache2 "libapache2-mod-php7.4=${PHP_PACKAGE_VERSION}" \
    && rm -f /var/www/html/index.html \
    && a2enmod rewrite \
    && printf '%s\n' 'ServerName localhost' 'ServerTokens Prod' 'ServerSignature Off' > /etc/apache2/conf-available/mautic.conf \
    && a2enconf mautic \
    && printf '%s\n' '<VirtualHost *:80>' 'DocumentRoot /var/www/html' '<Directory /var/www/html>' 'Options -Indexes +FollowSymLinks' 'AllowOverride All' 'Require all granted' '</Directory>' 'ErrorLog /proc/self/fd/2' 'CustomLog /proc/self/fd/1 combined' '</VirtualHost>' > /etc/apache2/sites-available/000-default.conf \
    && rm -rf /var/lib/apt/lists/*
COPY common/apache2-foreground /usr/local/bin/apache2-foreground
RUN chmod 755 /usr/local/bin/apache2-foreground && /usr/local/bin/check-runtime
EXPOSE 80
CMD ["apache2-foreground"]

FROM common AS fpm
ENV MAUTIC_VARIANT=fpm PHP_MAX_UPLOAD=128M
ARG MCRYPT_PACKAGE_VERSION=3:1.0.9-2+0~20260621.24+debian12~1.gbp389121
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "php7.4-fpm=${PHP_PACKAGE_VERSION}" "php7.4-mcrypt=${MCRYPT_PACKAGE_VERSION}" \
    && rm -rf /var/lib/apt/lists/*
COPY common/fpm.conf /etc/mautic/fpm.conf
COPY common/php-fpm /usr/local/bin/php-fpm
RUN chmod 755 /usr/local/bin/php-fpm && /usr/local/bin/check-runtime
EXPOSE 9000
CMD ["php-fpm"]
