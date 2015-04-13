=====================================================
Security Considerations for the OpenHatch Application
=====================================================

Policy
======

OpenHatch will make its best effort to protect our users, including their
accounts and any identifying or personal information they store with us.
To that end, we care deeply about security issues that result in 
compromises to:

- Authentication
- Authorization
- User accounts
- Cross-site scripting attacks
- SQL injection attacks
- any other vulnerability that affects our data or our users

There are certain classes of issues that we de-prioritize, because they 
do not materially affect what we are trying to protect as listed above.
These classes include, but are not limited to:

- Open redirections in OpenHatch applications

Known Issues
============

- It is known the the OpenID registration flow has the possibility of an
  open redirect to another site. Since it would be non-trivial to exploit
  this vulnerability in a way that would compromise the user, we are 
  erring on the side of having a less complicated code base and leaving
  the bug unpatched. If a future version of one of our vendor libraries
  patches the bug, we may upgrade the library to close the open 
  redirect.