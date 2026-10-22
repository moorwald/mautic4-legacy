<?php
// Synthetic isolated fixture only. Never copied into a published runtime image.
header('Content-Type: application/json');
if (isset($_GET['oom'])) {
    ini_set('memory_limit', '16M');
    register_shutdown_function(function () { echo 'UNSAFE_SHUTDOWN_CALLBACK'; });
    $value = str_repeat('x', 64 * 1024 * 1024);
    exit;
}
$upload = null;
if (isset($_FILES['fixture'])) {
    $file = $_FILES['fixture'];
    if ($file['error'] !== UPLOAD_ERR_OK || !is_uploaded_file($file['tmp_name'])) {
        http_response_code(500);
        echo json_encode(['upload' => false]);
        exit;
    }
    $upload = hash_file('sha256', $file['tmp_name']);
}
echo json_encode([
    'php' => PHP_VERSION,
    'sapi' => PHP_SAPI,
    'extensions' => get_loaded_extensions(),
    'memory_limit' => ini_get('memory_limit'),
    'upload_max_filesize' => ini_get('upload_max_filesize'),
    'timezone' => ini_get('date.timezone'),
    'custom_override' => ini_get('max_input_vars'),
    'upload_sha256' => $upload,
]);
