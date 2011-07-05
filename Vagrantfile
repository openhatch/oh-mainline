# This configuration file is for Vagrant, a simple virtual
# machine manager. It requires VirtualBox to be installed
# and working.
#
# To learn more about Vagrant, visit:
# http://vagrantup.com/

Vagrant::Config.run do |config|
  # This virtual machine (VM) is created based off a tiny pre-configured
  # Debian VM. We'll call it squeeze, and we'll download it from
  # the creator's S3 URL, if necessary.
  config.vm.box = "squeeze"
  config.vm.box_url = "http://mathie-vagrant-boxes.s3.amazonaws.com/debian_squeeze_32.box"

  # Configure the VM so that it launches Puppet when it first runs.
  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "puppet-provisioning-files/manifests"
  end

end

