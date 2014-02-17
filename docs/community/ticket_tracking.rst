Ticket tracking
===============

This document explains how we handle inbound email to the OpenHatch organization.

Our "ticket tracker" is a tool we use to reply to emails people send to OpenHatch. The "ticket tracker" is a fairly internal tool, although if you're excited about getting involved, we welcome you! Crucially, it is distinct from our "bug tracker," which tracks issues in the open source code of the OpenHatch project. By contrast, the ticket tracker helps us keep track of email conversations.

The URL to the ticket tracking site
-----------------------------------

http://tickets.openhatch.org/rt/

Our normal workflow
-------

Somebody sends an email to hello@openhatch.org. By default, this ticket goes into the "General" queue and is not assigned to anybody.

*To move the conversation forward:*

A ticket responder can reply by email with a helpful message, which changes the ticket status from "new" to "open", or they can write a reply specifically to support-comment at tickets.openhatch.org to write a message only viewable by ticket responders.

On the RT website, a ticket responder can click "reply" to reply with a helpful message, or they can click "comment" to write a message only viewable by ticket responders.

*To keep the tickets organized:*

On the RT website, go to a ticket and visit the "basics" menu option (in the grey bar) to put the ticket in the appropriate queue, assign the ticket to somebody, and assign a new status to the ticket.

When a ticket is resolved, we should assign it the status "resolved".

*In the future:*

We plan to also be able to assign queues, ownership, and statuses by email (using `CommandByMail <http://search.cpan.org/dist/RT-Extension-CommandByMail/lib/RT/Extension/CommandByMail.pm>`_). We have a ticket filed with the hosting provider to set this up.

*Workflow notes:*

There are some slight differences from the default RT workflow, which might be worth highlighting in case you're comparing this with past RT experiences or the official docs:

* We've disabled the "Auto-Reply to requestor" scrip. We thought this seemed impersonal; additionally, Asheesh was concerned it would cause us to send replies to spam we receive.

* We've disabled the scrip that causes the requestor to receive an email when the ticket is marked as "resolved". We thought this seemed impersonal.


Request Tracker Admin Team
-----------------------------------

These people have "privileged" accounts in RT and the password to the separate "root" account within RT:

* Britta
* Asheesh
* Shauna


How to help out
-------------------

If you want to help answer people's questions that they email to OpenHatch, please email us and we'll give you an account with some degree of appropriate privilege to do that. We haven't configured this yet, but we're excited to figure it out!


hello@ migration
----------------

(This section written on Sun Feb 16. Hopefully, it will go away by the end of February.)

Right now, hello at openhatch.org forwards to a bunch of people.

In the near future (~1 week from now), we'll turn that forwarding off. People who were on the hello@ alias can get something similar to what they used to have by requesting an RT account.

The best way to request an RT account is to email hello@, as we already have things set up so that emails to hello@ will create a ticket.


Importing past mails
---------------------

(This section written on Sun Feb 16. Hopefully, it will go away by the end of March.)

We haven't imported any past threads or emails yet.

For bulk import of historical archives, Asheesh hopes to get to this in the future (the next 2 to 6 weeks). He'll make an "archive" queue that hopefully contains one "ticket" per email thread. That way, new email helpers can read the archives within RT.

If you want to reply to a hello@ mail that isn't in RT yet, try to use the following workflow:

* Forward the most recent mail in the thread to support at tickets.openhatch.org.

* Modify the ticket so the person who sent it is the "Requestor."

* (Optional: Move it into the appropriate queue.)

* Reply to the ticket via your email, now that it has a ticket number.

That's a bit cumbersome. Sorry about that.

How the ticket tracker is administered
----------------------------

* tickets.openhatch.org points at an IP address of a VM run by Gossamer Threads.
* They are generously donating their hosted RT service, and for this, we plan to thank them on the OpenHatch sponsors page.
* From what I understand, we have a virtual machine that they administer. We can file support tickets with them, and we can also FTP into the machine and make changes if we want.
* hello at openhatch.org forwards to a few email addresses, including bountyarchive at rose.makesad.us; a procmail rule there forwards the email further into our RT instance. This is hackish and should be replaced in the future. (This remark written on 2014-02-16.)


Further thoughts
-------------------

Maybe it would be interesting for us to CC: the ticket tracker on emails to sponsors, generally. That way, we'd have a shared archive.
