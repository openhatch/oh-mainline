# The classes that we 'include' are actually
# each defined in their own file. We must import
# them to have access to them.
import "classes/*"

stage { 'first': before => Stage['main'] }

class {
  'openhatch_dependencies': stage => first;
  'apt_get_update': stage => first
}

node default {
  include apt_get_update
  include openhatch_dependencies
  include openhatch_code
}
