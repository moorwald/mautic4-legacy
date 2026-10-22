<?php
// Adapted from mautic/docker-mautic; see NOTICE.md. No credentials in argv/logs.
$host = getenv('MAUTIC_DB_HOST');
$port = (int) (getenv('MAUTIC_DB_PORT') ?: 3306);
if (substr_count($host, ':') === 1) {
    list($host, $hostPort) = explode(':', $host, 2);
    $port = (int) $hostPort;
}
$name = getenv('MAUTIC_DB_NAME');
if (!$host || !$name || $port < 1 || $port > 65535 || strpos($name, "\0") !== false) {
    fwrite(STDERR, "Invalid database connection settings.\n");
    exit(1);
}
mysqli_report(MYSQLI_REPORT_OFF);
fwrite(STDERR, "Ensuring Mautic database is present.\n");
for ($attempt = 0; $attempt < 10; ++$attempt) {
    $mysql = @new mysqli($host, getenv('MAUTIC_DB_USER'), getenv('MAUTIC_DB_PASSWORD'), '', $port);
    if (!$mysql->connect_error) {
        break;
    }
    if ($attempt === 9) {
        fwrite(STDERR, "Database connection failed after bounded startup retries.\n");
        exit(1);
    }
    sleep(5);
}
// Existing non-owner accounts do not need CREATE DATABASE permission.
if (!@$mysql->select_db($name)) {
    $quotedName = str_replace('`', '``', $name);
    if (!@$mysql->query('CREATE DATABASE IF NOT EXISTS `'.$quotedName.'`')) {
        fwrite(STDERR, "Database unavailable and creation failed; check grants.\n");
        exit(1);
    }
}
$mysql->close();
