#!/bin/sh

set -e

mkdir ~/.ssh
echo "$REMOTE_REPO_SETUP_SSH_KEY" >~/.ssh/id_rsa

for name in linode.openhatch.org 74.207.229.254; do
	echo "$name ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA4qRDf0eZWLtTSXvxItlVukrP/V+KoCgxQdhfgLgGxbAYh7UsSoXIWnHNPXDaW9G839RJtgCGy21u/01JJcRFqc29UHxDFRtaJdVcK2CZS9S87B/ryXmxNd4SA+0D82B9aV3oYzy2rwskndfYu8z/47Y+v+MjM+7dSVnemSFP/O5dInidH5sSKmLRVm7wMxKGAkZw5oWR/gjixssuNWqtT3m2Q9qKiYOiXKiVECKh1Gc5q1hnbqtPv4Oy/2fA0R9L04Zx1EoyZ3F/54bYetpK3Pg2x1KKMMhixeB4Fy+MpFTxkwhc4QrXhC0H1EDJuZfWgzSHvtw+U9/dwiwBBiz2hw==" >>~/.ssh/known_hosts
done
