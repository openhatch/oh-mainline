# This configuration file is for Vagrant, a simple virtual
# machine manager. It requires VirtualBox to be installed
# and working.
#
# To learn more about Vagrant, visit:
# http://vagrantup.com/

Vagrant::Config.run do |config|
  # This virtual machine (VM) is created based off a pre-configured
  # simple Ubuntu VM. We'll call it lucid32, and we'll download it
  # from vagrantup.com if necessary.
  config.vm.box = "lucid32"
  config.vm.box_url = "http://files.vagrantup.com/lucid32.box"

  # Configure the VM so that it launches Puppet when it first runs.
  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "puppet-provisioning-files/manifests"
  end

end

