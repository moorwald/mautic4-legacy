<?php
// Compare immutable application files, original uploads and normalized local settings.
$root = '/var/www/html';
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root, FilesystemIterator::SKIP_DOTS));
$files = [];
foreach ($it as $path => $info) {
    $relative = substr($path, strlen($root) + 1);
    if ($info->isFile()
        && !preg_match('~^(var/(cache|logs)|app/(cache|logs)|media/cache|media/js/libraries)/~', $relative)
        && $relative !== 'app/config/local.php') {
        $files[$relative] = hash_file('sha256', $path);
    }
}
ksort($files);
require $root.'/app/config/local.php';
ksort($parameters);
echo json_encode([
    'files' => count($files),
    'files_sha256' => hash('sha256', json_encode($files)),
    'configuration_sha256' => hash('sha256', serialize($parameters)),
    'application_version' => json_decode(file_get_contents($root.'/app/release_metadata.json'), true)['version'],
]);
