#!/bin/python
import poplib

pop_conn = poplib.POP3_SSL('pop.gmail.com', '995')
pop_conn.user('javaapktester')
pop_conn.pass_('Avast2017!')

numMessages = len(pop_conn.list()[1])
for i in range(numMessages):
    text = ""
    for msg in pop_conn.retr(i+1)[1]:
        text = text + msg + "\n"
    p = FeedParser()
    p.feed(text)
    message = p.close()
    
    print(message.get_payload())
    
pop_conn.quit()
