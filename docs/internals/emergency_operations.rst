=============================================
Emergency operations for the OpenHatch server
=============================================

The main OpenHatch server is a virtual machine hosted by linode.com.


What to do when the site isn't working
======================================

* Check if SSH is alive ::

    telnet linode.openhatch.org 22

  You should get a banner message. If so, things are not *so* bad. Someone with
  root (like Asheesh/paulproteus) can probably SSH in and figure out what's
  going on.

* If SSH is not alive, and the website is down...
  **Find Asheesh**, if possible. Otherwise, well, you might want to know about
  Lish.


Lish: Emergency reboots, and more
=================================

If you can't load the website, and if the Linode doesn't even respond to SSH,
then people with access can connect over the Linode Shell and read console
messages or reboot the virtual machine.

If you want to help us by being part of an emergency crew who can reboot it,
see the next section.

**PLEASE** do not reboot the machine without getting in touch with paulproteus
(Asheesh), unless it's *clearly* a good idea to reboot it!

* http://library.linode.com/troubleshooting/using-lish-the-linode-shell
* Lish via SSH

  * ssh linode22043@atlanta76.linode.com
  * Lish listens on ports 22, 443, and 2200


To get your key in the list
===========================

* File a bug, and assign it to paulproteus.

  * The subject should be, "Add my SSH key to lish for linode.openhatch.org"
  * Explain who you are and why it is a good thing for you to be able to see
    the "physical console" of the virtual machine.

* You should hear an answer back within 2 days.

