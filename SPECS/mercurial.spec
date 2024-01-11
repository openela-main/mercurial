Summary: A fast, lightweight Source Control Management system
Name: mercurial
Version: 6.2
Release: 1%{?dist}

# Release: 1.rc1%%{?dist}

%define upstreamversion %{version}

License: GPLv2+
URL: https://mercurial-scm.org/
Source0: https://www.mercurial-scm.org/release/%{name}-%{upstreamversion}.tar.gz
Source1: mercurial-site-start.el
Source2: blacklist
# Patch to fix errors in the testsuite with Python 3.6
Patch0:  ssl_fix_python36_compat.patch
Patch1:  ssl_another_fix_python36_compat.patch
BuildRequires: make
BuildRequires: bash-completion
BuildRequires: emacs-el
BuildRequires: emacs-nox
BuildRequires: gcc
BuildRequires: gettext
BuildRequires: pkgconfig
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-docutils

Provides: hg = %{version}-%{release}
Requires: python3 <= 3.9
Requires: emacs-filesystem
Recommends: python3-fb-re2

%description
Mercurial is a fast, lightweight source control management system designed
for efficient handling of very large distributed projects.

Quick start: https://www.mercurial-scm.org/wiki/QuickStart
Tutorial: https://www.mercurial-scm.org/wiki/Tutorial
Extensions: https://www.mercurial-scm.org/wiki/UsingExtensions


%package hgk
Summary:    Hgk interface for mercurial
Requires:   hg = %{version}-%{release}
Requires:   tk

%description hgk
A Mercurial extension for displaying the change history graphically
using Tcl/Tk.  Displays branches and merges in an easily
understandable way and shows diffs for each revision.  Based on
gitk for the git SCM.

Adds the "hg view" command.  See
https://www.mercurial-scm.org/wiki/HgkExtension for more
documentation.


%package chg
Summary:    A fast Mercurial command without slow Python startup
Requires:   hg = %{version}-%{release}

%description chg
chg is a C wrapper for the hg command. Typically, when you type hg, a new
Python process is created, Mercurial is loaded, and your requested command runs
and the process exits.

With chg, a Mercurial command server background process is created that runs
Mercurial. When you type chg, a C program connects to that background process
and executes Mercurial commands.

%prep
%autosetup -p1 -n %{name}-%{upstreamversion}

# These are shipped as examples in /usr/share/docs and should not be executable
chmod -x hgweb.cgi contrib/hgweb.fcgi

%build
FORCE_SETUPTOOLS=1 PYTHON=%{python3} make all

# chg will invoke the 'hg' command - no direct Python dependency
pushd contrib/chg
make
popd

%install
%{python3} setup.py install -O1 --root %{buildroot} --prefix %{_prefix} --record=%{name}.files
make install-doc DESTDIR=%{buildroot} MANDIR=%{_mandir}

grep -v -e 'hgk.py*' \
        -e "%{python3_sitearch}/mercurial/" \
        -e "%{python3_sitearch}/hgext/" \
        -e "%{python3_sitearch}/hgext3rd/" \
        -e "%{python3_sitearch}/hgdemandimport/" \
        -e "%{_bindir}" \
        < %{name}.files > %{name}-base.files
grep 'hgk.py*' < %{name}.files > %{name}-hgk.files

install -D -m 755 contrib/hgk       %{buildroot}%{_libexecdir}/mercurial/hgk
install -m 755 contrib/hg-ssh       %{buildroot}%{_bindir}

bash_completion_dir=%{buildroot}$(pkg-config --variable=completionsdir bash-completion)
mkdir -p $bash_completion_dir
install -m 644 contrib/bash_completion $bash_completion_dir/hg

zsh_completion_dir=%{buildroot}%{_datadir}/zsh/site-functions
mkdir -p $zsh_completion_dir
install -m 644 contrib/zsh_completion $zsh_completion_dir/_mercurial

mkdir -p %{buildroot}%{_emacs_sitelispdir}/mercurial

pushd contrib
for file in mercurial.el mq.el; do
  #emacs -batch -l mercurial.el --no-site-file -f batch-byte-compile $file
  %{_emacs_bytecompile} $file
  install -p -m 644 $file ${file}c %{buildroot}%{_emacs_sitelispdir}/mercurial
  rm ${file}c
done
popd

pushd contrib/chg
make install DESTDIR=%{buildroot} PREFIX=%{_usr} MANDIR=%{_mandir}/man1
popd


mkdir -p %{buildroot}%{_sysconfdir}/mercurial/hgrc.d

mkdir -p %{buildroot}%{_emacs_sitestartdir} && install -m644 %SOURCE1 %{buildroot}%{_emacs_sitestartdir}

cat >hgk.rc <<EOF
[extensions]
# enable hgk extension ('hg help' shows 'view' as a command)
hgk=

[hgk]
path=%{_libexecdir}/mercurial/hgk
EOF
install -m 644 hgk.rc %{buildroot}%{_sysconfdir}/mercurial/hgrc.d

cat > certs.rc <<EOF
# see: https://www.mercurial-scm.org/wiki/CACertificates
[web]
cacerts = /etc/pki/tls/certs/ca-bundle.crt
EOF
install -m 644 certs.rc %{buildroot}%{_sysconfdir}/mercurial/hgrc.d

mv %{buildroot}%{python3_sitearch}/mercurial/locale %{buildroot}%{_datadir}/locale
rm -rf %{buildroot}%{python3_sitearch}/mercurial/locale

%find_lang hg

pathfix.py -pni "%{python3}" %{buildroot}%{_bindir}/hg-ssh

%files -f %{name}-base.files -f hg.lang
%doc CONTRIBUTORS COPYING doc/README doc/hg*.html hgweb.cgi contrib/hgweb.fcgi contrib/hgweb.wsgi
%doc %attr(644,root,root) %{_mandir}/man?/hg*.gz
%doc %attr(644,root,root) contrib/*.svg
%dir %{_datadir}/zsh/
%dir %{_datadir}/zsh/site-functions/
%dir %{_sysconfdir}/mercurial
%dir %{_sysconfdir}/mercurial/hgrc.d
%{_datadir}/bash-completion/
%{_datadir}/zsh/site-functions/_mercurial
%{python3_sitearch}/mercurial/
%{python3_sitearch}/hgext/
%{python3_sitearch}/hgext3rd/
%{python3_sitearch}/hgdemandimport/
%{_emacs_sitelispdir}/mercurial
%{_emacs_sitestartdir}/*.el
%{_bindir}/hg
%{_bindir}/hg-ssh

%config(noreplace) %{_sysconfdir}/mercurial/hgrc.d/certs.rc

%files hgk -f %{name}-hgk.files
%{_libexecdir}/mercurial/
%config(noreplace) %{_sysconfdir}/mercurial/hgrc.d/hgk.rc

%files chg
%{_bindir}/chg
%doc %attr(644,root,root) %{_mandir}/man?/chg.*.gz

%check
cd tests && HGPYTHON3=1 %{python3} run-tests.py --blacklist %{SOURCE2}

%changelog
* Mon Aug 01 2022 Ondřej Pohořelský <opohorel@redhat.com> - 6.2-2
- Add forgotten mercurial-site-start.el
- Related: rhbz#2089849

* Fri Jul 29 2022 Ondřej Pohořelský <opohorel@redhat.com> - 6.2-1
- New release Mercurial 6.2
- Resolves: rhbz#2089849
