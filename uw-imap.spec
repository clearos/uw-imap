
# Change the default connected directory from the user's home directory
# to the named subdirectory of the user's home directory
%define mail_subdirectory      Mail

Summary: UW Server daemons for IMAP and POP network mail protocols
Name:	 uw-imap 
Version: 2004g
Release: 5%{?dist}

License: University of Washington Free-Fork License
Group: 	 System Environment/Daemons
URL:	 http://www.washington.edu/imap/
# Old (non-latest) releases live at  ftp://ftp.cac.washington.edu/imap/old/
Source:	 ftp://ftp.cac.washington.edu/imap/imap-2004g.tar.Z
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%define soname    c-client
%define somajor  %{version} 
%define shlibname lib%{soname}.so.%{somajor}
%define imap_libs lib%{soname}%{somajor}
#Old naming
#define imap_libs	imap-libs

# FC4+ uses %%_sysconfdir/pki/tls/certs, previous releases used %%_datadir/ssl/certs
%define sslcerts  %{expand:%(if [ -d %{_sysconfdir}/pki/tls/certs ]; then echo "%{_sysconfdir}/pki/tls/certs"; else echo "%{_datadir}/ssl/certs"; fi)}

# imap -> uw-imap rename
Obsoletes: imap < 1:%{version}

# legacy/old pam setup, using pam_stack.so
Source1: imap-legacy.pam
# new pam setup, using new "include" feature
Source2: imap.pam
Source3: imap-xinetd
Source4: ipop2-xinetd
Source5: ipop3-xinetd
Source6: imaps-xinetd
Source7: pop3s-xinetd

Patch1: imap-2004-paths.patch
Patch2: imap-2004d-optflags.patch
Patch5: imap-2001a-overflow.patch
Patch7: imap-2002d-ssltype.patch
Patch9: imap-2002e-shared.patch
Patch10: imap-2002e-authmd5.patch
Patch11: imap-2004c1-mbxproto.patch

BuildRequires: krb5-devel
BuildRequires: openssl-devel
BuildRequires: pam-devel

# Prereq is shorter than separate Requires, Requires(post), Requires(postun)
Prereq: xinetd
Requires(post): openssl
Requires(triggerpostun): sed >= 4.0

%description
The %{name} package provides UW server daemons for both the IMAP (Internet
Message Access Protocol) and POP (Post Office Protocol) mail access
protocols.  The POP protocol uses a "post office" machine to collect
mail for users and allows users to download their mail to their local
machine for reading. The IMAP protocol allows a user to read mail on a
remote machine without downloading it to their local machine.

%package -n %{imap_libs} 
Summary: UW C-client mail library 
Group:	 System Environment/Libraries
%description -n %{imap_libs} 
Provides a common API for accessing mailboxes. 

%package devel
Summary: Development tools for programs which will use the UW IMAP library
Group: 	 Development/Libraries
Requires: %{imap_libs} = %{version}-%{release}
# imap -> uw-imap rename
Obsoletes: imap-devel < 1:%{version}
Conflicts: libc-client-devel
%description devel
Contains the header files and static libraries for developing programs 
which will use the UW C-client common API.

%package utils
Summary: UW IMAP Utilities to make managing your email simpler
Group: 	 Applications/System 
# imap -> uw-imap rename
Obsoletes: imap-utils < 1:%{version}
%description utils
This package contains some utilities for managing UW IMAP email.


%prep
%setup -q -n imap-%{version}

%patch1 -p1 -b .paths
%patch2 -p1 -b .optflags

%patch5 -p1 -b .overflow

%patch7 -p1 -b .ssltype

%patch9 -p1 -b .shared
%patch10 -p1 -b .authmd5
# use mbx (instead of unix/mbox) folder format by default
# its faster, allows (better) locking
%patch11 -p1 -b .mbxproto

%if "%{?fedora}" > "4"
install -p -m644 %{SOURCE2} imap.pam
%else
install -p -m644 %{SOURCE1} imap.pam
%endif


%build
# Not sure why this is included, omitting for now -- Rex
#EXTRACFLAGS="$EXTRACFLAGS -DDISABLE_POP_PROXY=1"

# Kerberos setup (proabably legacy-only -- Rex)
if [ -x %{_sysconfdir}/profile.d/krb5.sh ]; then
  . %{_sysconfdir}/profile.d/krb5.sh
elif ! echo ${PATH} | grep -q %{_prefix}kerberos/bin ; then
  export PATH=%{_prefix}/kerberos/bin:${PATH}
fi
GSSDIR=$(krb5-config --prefix)

# SSL setup (probably legacy-only -- Rex)
export EXTRACFLAGS="$EXTRACFLAGS $(pkg-config --cflags openssl 2>/dev/null)"

make %{?_smp_mflags} lnp \
EXTRACFLAGS="$EXTRACFLAGS" \
EXTRALDFLAGS="$EXTRALDFLAGS" \
EXTRAAUTHENTICATORS=gss \
SPECIALS="GSSDIR=${GSSDIR} LOCKPGM=%{_sbindir}/mlock SSLCERTS=%{sslcerts} SSLDIR=%{_datadir}/ssl SSLINCLUDE=%{_includedir}/openssl SSLLIB=%{_libdir}" \
SSLTYPE=unix \
CCLIENTLIB=$(pwd)/c-client/%{shlibname} \
SHLIBBASE=%{soname} \
SHLIBNAME=%{shlibname}
# Blank line


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT%{_libdir}/
install -p -m644 ./c-client/c-client.a $RPM_BUILD_ROOT%{_libdir}/
ln -s c-client.a $RPM_BUILD_ROOT%{_libdir}/libc-client.a

install -p -m755 ./c-client/%{shlibname} $RPM_BUILD_ROOT%{_libdir}/
ln -s %{shlibname} $RPM_BUILD_ROOT%{_libdir}/lib%{soname}.so

mkdir -p $RPM_BUILD_ROOT%{_includedir}/imap/
install -m644 ./c-client/*.h $RPM_BUILD_ROOT%{_includedir}/imap
# Added linkage.c to fix (#34658) <mharris>
install -m644 ./c-client/linkage.c $RPM_BUILD_ROOT%{_includedir}/imap
install -m644 ./src/osdep/tops-20/shortsym.h $RPM_BUILD_ROOT%{_includedir}/imap

mkdir -p $RPM_BUILD_ROOT%{_mandir}/man8/
install -p -m644 src/{ipopd/ipopd,imapd/imapd}.8 $RPM_BUILD_ROOT%{_mandir}/man8/
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
install -p -m755 ipopd/ipop{2d,3d} $RPM_BUILD_ROOT%{_sbindir}/
install -p -m755 imapd/imapd $RPM_BUILD_ROOT%{_sbindir}/
install -p -m755 mlock/mlock $RPM_BUILD_ROOT%{_sbindir}/

mkdir -p $RPM_BUILD_ROOT%{_bindir}/
install -p -m755 dmail/dmail mailutil/mailutil mtest/mtest tmail/tmail $RPM_BUILD_ROOT%{_bindir}/
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1/
install -p -m644 src/{dmail/dmail,mailutil/mailutil,tmail/tmail}.1 $RPM_BUILD_ROOT%{_mandir}/man1/

install -p -m644 -D imap.pam $RPM_BUILD_ROOT%{_sysconfdir}/pam.d/imap
install -p -m644 -D imap.pam $RPM_BUILD_ROOT%{_sysconfdir}/pam.d/pop

install -p -m644 -D %{SOURCE3} $RPM_BUILD_ROOT%{_sysconfdir}/xinetd.d/imap
install -p -m644 -D %{SOURCE6} $RPM_BUILD_ROOT%{_sysconfdir}/xinetd.d/imaps
install -p -m644 -D %{SOURCE4} $RPM_BUILD_ROOT%{_sysconfdir}/xinetd.d/ipop2
install -p -m644 -D %{SOURCE5} $RPM_BUILD_ROOT%{_sysconfdir}/xinetd.d/ipop3
install -p -m644 -D %{SOURCE7} $RPM_BUILD_ROOT%{_sysconfdir}/xinetd.d/pop3s

# Generate ghost *.pem files
mkdir -p $RPM_BUILD_ROOT%{sslcerts}/
touch $RPM_BUILD_ROOT%{sslcerts}/{imapd,ipop3d}.pem

# c-client.cf: mail_subdirectory
cat > c-client.cf <<EOF
I accept the risk of using UW-IMAP
set mail-subdirectory %{mail_subdirectory}
EOF
install -p -m644 -D c-client.cf $RPM_BUILD_ROOT%{_sysconfdir}/c-client.cf


%post
{
cd %{sslcerts} &> /dev/null || :
for CERT in imapd.pem ipop3d.pem ;do
   if [ ! -e $CERT ];then
      if [ -e stunnel.pem ];then
         cp stunnel.pem $CERT &> /dev/null || :
      elif [ -e Makefile ];then
         make $CERT << EOF &> /dev/null || :
--
SomeState
SomeCity
SomeOrganization
SomeOrganizationalUnit
localhost.localdomain
root@localhost.localdomain
EOF
      fi
   fi
done
} || :
/sbin/service xinetd reload > /dev/null 2>&1 || :

%postun
/sbin/service xinetd reload > /dev/null 2>&1 || :

%post -n %{imap_libs} -p /sbin/ldconfig

%postun -n %{imap_libs} -p /sbin/ldconfig

%triggerpostun -- imap < 1:2004
#if upgrading from old version, don't change/set (default) MailDir
if [ -f %{_sysconfdir}/c-client.cf ]; then
  if grep -q "^set mail-subdirectory %{mail_subdirectory}" %{_sysconfdir}/c-client.cf; then
    sed -i -e 's/^set mail-subdirectory/\#set mail-subdirectory/g' \
      %{_sysconfdir}/c-client.cf
  fi
fi


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc docs/SSLBUILD
%config %{_sysconfdir}/pam.d/imap
%config %{_sysconfdir}/pam.d/pop
%config(noreplace) %{_sysconfdir}/xinetd.d/imap
%config(noreplace) %{_sysconfdir}/xinetd.d/ipop2
%config(noreplace) %{_sysconfdir}/xinetd.d/ipop3
# These need to be replaced (ie, can't use %%noreplace), or imaps/pop3s will fail after an upgrade
%config %{_sysconfdir}/xinetd.d/imaps
%config %{_sysconfdir}/xinetd.d/pop3s
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{sslcerts}/imapd.pem
%attr(0600,root,root) %ghost %config(missingok,noreplace) %verify(not md5 size mtime) %{sslcerts}/ipop3d.pem
%config(noreplace) %{_sysconfdir}/c-client.cf
%{_mandir}/man8/*
%{_sbindir}/ipop2d
%{_sbindir}/ipop3d
%{_sbindir}/imapd

%files utils
%defattr(-,root,root,-)
%{_bindir}/*
%attr(2755, root, mail) %{_sbindir}/mlock
%{_mandir}/man1/*

%files -n lib%{soname}%{version}
%defattr(-,root,root)
%doc docs/RELNOTES docs/*.txt
%{_libdir}/lib%{soname}.so.*

%files devel
%defattr(-,root,root,-)
%{_includedir}/imap/
%{_libdir}/c-client.a
%{_libdir}/libc-client.a
%{_libdir}/lib%{soname}.so


%changelog
* Fri Aug 18 2006 Rex Dieter <rexdieter[AT]users.sf.net> 2004g-5
- cleanup, respin for fc6

* Wed Mar 1 2006 Rex Dieter <rexdieter[AT]users.sf.net> 
- fc5: gcc/glibc respin

* Thu Nov 17 2005 Rex Dieter <rexdieter[AT]users.sf.net> 2004g-4
- use pam's "include" feature on fc5
- cleanup %%doc handling, remove useless bits

* Thu Nov 17 2005 Rex Dieter <rexdieter[AT]users.sf.net> 2004g-3
- omit trailing whitespace in default c-client.cf

* Wed Nov 16 2005 Rex Dieter <rexdieter[AT]users.sf.net> 2004g-2 
- rebuild for new openssl

* Mon Sep 26 2005 Rex Dieter <rexdieter[AT]users.sf.net> 2004g-1
- imap-2004g
- /etc -> %%_sysconfdir
- use %%{?_smp_mflags}

* Mon Aug 15 2005 Rex Dieter <rexdieter[AT]users.sf.net> 2004e-1
- imap-2004e
- rename: imap -> uw-imap (yay, we get to drop the Epoch)
- sslcerts=%{_sysconfdir}/pki/tls/certs if exists, else /usr/share/ssl/certs

* Fri Apr 29 2005 Rex Dieter <rexdieter[AT]users.sf.net> 1:2004d-1
- 2004d
- imap-libs -> lib%%{soname}%%{version} (ie, libc-client2004d), so we can 
  have multiple versions (shared-lib only) installed
- move mlock to -utils.
- revert RFC2301, locks out too many folks where SSL is unavailable

* Thu Apr 28 2005 Rex Dieter <rexdieter[AT]users.sf.net> 1:2004-0.fdr.11.c1
- change default driver from mbox to mbx
- comply with RFC 3501 security: Unencrypted plaintext passwords are prohibited

* Fri Jan 28 2005 Rex Dieter <rexdieter[AT]users.sf.net> 1:2004-0.fdr.10.c1
- imap-2004c1 security release:
  http://www.kb.cert.org/vuls/id/702777

* Thu Jan 20 2005 Rex Dieter <rexdieter[AT]users.sf.net> 1:2004-0.fdr.9.c
- imap2004c
- -utils: dmail,mailutil,tmail
- -libs: include mlock (so it's available for other imap clients, like pine)
- remove extraneous patches
- %%_sysconfigdir/c-client.cf: use to set MailDir (but don't if upgrading from
  an older version (ie, if folks don't want/expect a change in behavior)

* Mon Sep 13 2004 Rex Dieter <rexdieter at sf.net. 1:2004-0.fdr.8.a
- don't use mailsubdir patch (for now)

* Wed Aug 11 2004 Rex Dieter <rexdieter at sf.net> 1:2004-0.fdr.7.a
- mailsubdir patch (default to ~/Mail instead of ~)

* Fri Jul 23 2004 Rex Dieter <rexdieter at sf.net> 1:2004-0.fdr.6.a
- remove Obsoletes/Provides: libc-client (they can, in fact, co-xist)
- -devel: remove O/P: libc-client-devel -> Conflicts: libc-client-devel

* Thu Jul 16 2004 Rex Dieter <rexdieter at sf.net> 1:2004-0.fdr.5.a
- imap2004a

* Tue Jul 13 2004 Rex Dieter <rexdieter at sf.net> 1:2004-0.fdr.4
- -devel: Req: %%{name}-libs

* Tue Jul 13 2004 Rex Dieter <rexdieter at sf.net> 1:2004-0.fdr.3
- previous imap pkgs had Epoch: 1, we need it too.

* Wed Jul 07 2004 Rex Dieter <rexdieter at sf.net> 2004-0.fdr.2
- use %%version as %%somajver (like how openssl does it)

* Wed Jul 07 2004 Rex Dieter <rexdieter at sf.net> 2004-0.fdr.1
- imap-2004
- use mlock, if available.
- Since libc-client is an attrocious name choice, we'll trump it, 
  and provide imap, imap-libs, imap-devel instead (redhat bug #120873)

* Wed Apr 07 2004 Kaj J. Niemi <kajtzu@fi.basen.net> 2002e-4
- Use CFLAGS (and RPM_OPT_FLAGS) during the compilation
- Build the .so through gcc instead of directly calling ld 

* Fri Mar  5 2004 Joe Orton <jorton@redhat.com> 2002e-3
- install .so with permissions 0755
- make auth_md5.c functions static to avoid symbol conflicts
- remove Epoch: 0

* Tue Mar 02 2004 Kaj J. Niemi <kajtzu@fi.basen.net> 0:2002e-2
- "lnp" already uses RPM_OPT_FLAGS
- have us conflict with imap, imap-devel

* Tue Mar  2 2004 Joe Orton <jorton@redhat.com> 0:2002e-1
- add post/postun, always use -fPIC

* Tue Feb 24 2004 Kaj J. Niemi <kajtzu@fi.basen.net>
- Name change from c-client to libc-client

* Sat Feb 14 2004 Kaj J. Niemi <kajtzu@fi.basen.net> 0:2002e-0.1
- c-client 2002e is based on imap-2002d
- Build shared version, build logic is copied from FreeBSD net/cclient

