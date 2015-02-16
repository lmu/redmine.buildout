#!/usr/bin/env python3.4


import imaplib

from email.message import Message

import ipdb



ipdb.set_trace()

M = imaplib.IMAP4()

M.login('lu95xez', 'Ticket#2014')
M.select()
typ, data = M.search(None, 'ALL')
for num in data[0].split():
    typ, data = M.fetch(num, '(RFC822)')
    print('Message %s\n%s\n' % (num, data[0][1]))
M.close()
M.logout()
