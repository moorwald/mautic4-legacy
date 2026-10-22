<?php
// Synthetic internal-network fixture only. No forwarding, authentication or public port.
$inbox = [];
file_put_contents('/tmp/inbox.json', '[]');
$server = stream_socket_server('tcp://0.0.0.0:2525', $errno, $error);
if (!$server) { fwrite(STDERR, "Cannot bind fixture SMTP socket.\n"); exit(1); }
while (true) {
    // A quiet 60-second accept timeout is expected while application fixtures install.
    $client = @stream_socket_accept($server, 60);
    if ($client === false) { continue; }
    stream_set_timeout($client, 30);
    fwrite($client, "220 smtp.fixture.invalid ESMTP\r\n");
    $recipient = null;
    while (($line = fgets($client)) !== false) {
        $command = strtoupper(strtok(rtrim($line, "\r\n"), ' '));
        if ($command === 'EHLO' || $command === 'HELO') {
            fwrite($client, "250-smtp.fixture.invalid\r\n250 SIZE 1048576\r\n");
        } elseif ($command === 'MAIL' || $command === 'RSET') {
            $recipient = null;
            fwrite($client, "250 OK\r\n");
        } elseif ($command === 'RCPT') {
            if (!preg_match('/^RCPT TO:\\s*<([^>]+@example\\.invalid)>/i', trim($line), $match)) {
                fwrite($client, "550 Only synthetic example.invalid recipients accepted\r\n");
                continue;
            }
            $recipient = $match[1];
            fwrite($client, "250 OK\r\n");
        } elseif ($command === 'DATA' && $recipient !== null) {
            fwrite($client, "354 End data with dot\r\n");
            $message = '';
            while (($data = fgets($client)) !== false && rtrim($data, "\r\n") !== '.') {
                if (substr($data, 0, 2) === '..') { $data = substr($data, 1); }
                $message .= $data;
                if (strlen($message) > 1048576) { exit(1); }
            }
            preg_match('/^Subject:\\s*(.+)$/mi', $message, $subject);
            $inbox[] = ['recipient' => $recipient, 'subject' => trim($subject[1] ?? ''),
                        'message_sha256' => hash('sha256', $message)];
            file_put_contents('/tmp/inbox.next.json', json_encode($inbox));
            rename('/tmp/inbox.next.json', '/tmp/inbox.json');
            fwrite($client, "250 Message accepted by isolated fixture\r\n");
        } elseif ($command === 'QUIT') {
            fwrite($client, "221 Bye\r\n");
            break;
        } elseif ($command === 'NOOP') {
            fwrite($client, "250 OK\r\n");
        } else {
            fwrite($client, "502 Unsupported fixture command\r\n");
        }
    }
    fclose($client);
}
