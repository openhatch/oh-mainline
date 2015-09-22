"""
Extension functions to help query/assert name service information.

Functions:

  * dns_resolves -- assert that a host resolves to a specific IP address.
  * dns_a -- assert that a host directly resolves to a specific IP address
  * dns_cname -- assert that a host is an alias for another hostname.
  * dnx_mx -- assert that a given host is a mail exchanger for the given name.
  * dns_ns -- assert that a given hostname is a name server for the given name.
"""

import socket
from twill.errors import TwillAssertionError

try:
    import dns.resolver
except ImportError:
    raise Exception("ERROR: must have dnspython installed to use the DNS extension module")

def dns_a(host, ipaddress, server=None):
    """
    >> dns_a <name> <ipaddress> [<name server>]

    Assert that <name> resolves to <ipaddress> (and is an A record).
    Optionally use the given name server.
    """
    if not is_ip_addr(ipaddress):
        raise Exception("<ipaddress> parameter must be an IP address, not a hostname")

    for answer in _query(host, 'A', server):
        if ipaddress == answer.address:
            return True

    raise TwillAssertionError

def dns_cname(host, cname, server=None):
    """
    >> dns_cname <name> <alias_for> [<name server>]

    Assert that <name> is a CNAME alias for <alias_for>  Optionally use
    <name server>.
    """
    if is_ip_addr(cname):
        raise Exception("<alias_for> parameter must be a hostname, not an IP address")
    
    cname = dns.name.from_text(cname)
    
    for answer in _query(host, 'CNAME', server):
        if cname == answer.target:
            return True

    raise TwillAssertionError

def dns_resolves(host, ipaddress, server=None):
    """
    >> dns_resolves <name> <name2/ipaddress> [<name server>]
    
    Assert that <name> ultimately resolves to the given IP address (or
    the same IP address that 'name2' resolves to).  Optionally use the
    given name server.
    """
    if not is_ip_addr(ipaddress):
        ipaddress = _resolve_name(ipaddress, server)
        
    for answer in _query(host, 1, server):
        if ipaddress == answer.address:
            return True

    raise TwillAssertionError

def dns_mx(host, mailserver, server=None):
    """
    >> dns_mx <name> <mailserver> [<name server>]

    Assert that <mailserver> is a mailserver for <name>.
    """
    mailserver = dns.name.from_text(mailserver)
    
    for rdata in _query(host, 'MX', server):
        if mailserver == rdata.exchange:
            return True

    raise TwillAssertionError

def dns_ns(host, query_ns, server=None):
    """
    >> dns_ns <domain> <nameserver> [<name server to use>]

    Assert that <nameserver> is a mailserver for <domain>.
    """
    query_ns = dns.name.from_text(query_ns)
    
    for answer in _query(host, 'NS', server):
        if query_ns == answer.target:
            return True

    raise TwillAssertionError

###

def is_ip_addr(text):
    """
    Check the 'name' to see if it's just an IP address.
    """
    
    try:
        v = dns.ipv4.inet_aton(text)
        return True
    except socket.error:
        return False

def _resolve_name(name, server):
    """
    Resolve the given name to an IP address.
    """
    if is_ip_addr(name):
        return name
    
    r = dns.resolver.Resolver()
    if server:
        r.nameservers = [_resolve_name(server, None)]

    answers = r.query(name)

    answer = None
    for answer in answers:              # @CTB !?
        break

    assert answer
    return str(answer)

def _query(query, query_type, server):
    """
    Query, perhaps via the given name server.  (server=None to use default).
    """
    r = dns.resolver.Resolver()
    if server:
        r.nameservers = [_resolve_name(server, None)]

    return r.query(query, query_type)
