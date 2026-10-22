<?php
// Exercise Mautic's configured sample-mail helper, not a separately constructed SMTP client.
define('MAUTIC_ROOT_DIR', '/var/www/html');
require '/var/www/html/autoload.php';
date_default_timezone_set('UTC');
$label = $argv[1];
if (!preg_match('/^(apache|fpm)-(fresh|existing-4\\.4\\.12)$/', $label)) {
    fwrite(STDERR, "Unexpected synthetic fixture label.\n");
    exit(1);
}
$kernel = new AppKernel('prod', false);
$kernel->boot();
$helper = $kernel->getContainer()->get('mautic.helper.mailer')->getSampleMailer();
$helper->setFrom('sender@example.invalid', 'Synthetic fixture');
$helper->setTo($label.'@example.invalid');
$helper->setSubject('M4 SMTP '.$label);
$helper->setBody('Synthetic isolated SMTP smoke. Do not deliver externally.', 'text/plain', null, true);
if (!$helper->send(false)) {
    fwrite(STDERR, "Mautic sample-mail helper reported failure.\n");
    exit(1);
}
$kernel->shutdown();
echo json_encode(['mautic_sample_mail_helper' => true]);
