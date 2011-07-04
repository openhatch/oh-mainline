## This appears to be necessary for the lucid32 VM
## provided by vagrantup. Go figure.
class apt_get_update {
  exec { "apt-get update":
    command => "/usr/bin/apt-get update",
  }

  # Ensure apt-get update has been run before installing any packages
  Exec["apt-get update"] -> Package <| |>
}

