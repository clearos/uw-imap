# uw-imap

Forked version of uw-imap with ClearOS changes applied

## Update usage
  Add __#kojibuild__ to commit message to automatically build

* git clone git+ssh://git@github.com/clearos/uw-imap.git
* cd uw-imap
* git checkout epel7
* git remote add upstream git://pkgs.fedoraproject.org/uw-imap.git
* git pull upstream epel7
* git checkout clear7
* git merge --no-commit epel7
* git commit
