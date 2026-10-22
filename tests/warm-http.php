<?php
// Complete first-request initialization on the original CLI runtime, without a listener.
define('MAUTIC_ROOT_DIR', '/var/www/html');
require '/var/www/html/autoload.php';
date_default_timezone_set('UTC');
$app = (new Mautic\Middleware\MiddlewareBuilder(new AppKernel('prod', false)))->resolve();
$request = Symfony\Component\HttpFoundation\Request::create(getenv('MAUTIC_URL').'/s/login');
$response = $app->handle($request);
if ($app instanceof Symfony\Component\HttpKernel\TerminableInterface) {
    $app->terminate($request, $response);
}
if ($response->getStatusCode() !== 200 || strpos($response->getContent(), 'name="_username"') === false) {
    fwrite(STDERR, 'Original runtime did not render the expected login response.\n');
    exit(1);
}
echo "Original HTTP kernel initialized without a network listener.\n";
