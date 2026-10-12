# Spec for the DEEIX Chat server RPM. Built by .github/workflows/build-rpm.yml.
# The Source0 tarball (prepared by the workflow) contains:
#   deeix-chat          Go server binary (CGO, x86_64)
#   frontend-out/       static export of apps/web (served by the binary)
#   config.yaml         default config (SQLite single-node profile)
#   deeix-chat.service  systemd unit
#   LICENSE NOTICE
#
# Local rebuild:
#   rpmbuild --define "_topdir ~/rpmbuild" --define "pkg_version 0.4.4" \
#            -bb .github/rpm/deeix-chat.spec

%{!?pkg_version:%{error:pkg_version is required, pass --define "pkg_version X.Y.Z"}}

%global _unitdir /usr/lib/systemd/system
%global _licensedir %{_prefix}/share/licenses

Name:           deeix-chat
Version:        %{pkg_version}
Release:        1%{?dist}
Summary:        DEEIX Chat self-hosted AI workspace server

License:        Apache-2.0
URL:            https://github.com/DEEIX-AI/DEEIX-Chat
Source0:        %{name}-%{version}.tar.gz

Requires:       systemd

%description
DEEIX Chat is an enterprise AI workspace for model routing, multimodal
chat, files, tools, billing, identity, and operations.

This package installs the DEEIX Chat server (Go API + bundled web UI)
as a systemd service using the single-node SQLite profile:

  service:    systemctl start deeix-chat  ->  http://localhost:8080
  config:     /etc/deeix-chat/config.yaml
  data:       /var/lib/deeix-chat (SQLite DB, uploaded files, GeoIP cache)

Replace jwt_secret and data_encryption_key in the config with strong
random values (openssl rand -hex 32) and restart the service before
exposing it beyond localhost.

%prep
%setup -q

%install
install -D -p -m 0755 deeix-chat          %{buildroot}%{_libexecdir}/%{name}/deeix-chat
mkdir -p                                  %{buildroot}%{_datadir}/%{name}/frontend
cp -a frontend-out                        %{buildroot}%{_datadir}/%{name}/frontend/out
install -D -p -m 0640 config.yaml         %{buildroot}%{_sysconfdir}/%{name}/config.yaml
install -D -p -m 0644 deeix-chat.service  %{buildroot}%{_unitdir}/%{name}.service
install -d -m 0750                        %{buildroot}/var/lib/%{name}
install -D -p -m 0644 LICENSE             %{buildroot}%{_licensedir}/%{name}/LICENSE
install -p -m 0644 NOTICE                 %{buildroot}%{_licensedir}/%{name}/NOTICE

%pre
getent passwd deeix-chat >/dev/null 2>&1 || \
  useradd --system --user-group --home-dir /var/lib/deeix-chat \
          --shell /usr/sbin/nologin --comment "DEEIX Chat server" deeix-chat || :

%post
/usr/bin/systemctl preset %{name}.service >/dev/null 2>&1 || :

%preun
if [ "$1" -eq 0 ]; then
  /usr/bin/systemctl --no-reload disable --now %{name}.service >/dev/null 2>&1 || :
fi

%postun
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ "$1" -eq 0 ]; then
  /usr/bin/systemctl reset-failed %{name}.service >/dev/null 2>&1 || :
fi

%files
%dir %attr(0755,root,root) %{_libexecdir}/%{name}
%{_libexecdir}/%{name}/deeix-chat
%{_datadir}/%{name}/
%{_unitdir}/%{name}.service
%dir %attr(0750,root,deeix-chat) %{_sysconfdir}/%{name}
%config(noreplace) %attr(0640,root,deeix-chat) %{_sysconfdir}/%{name}/config.yaml
%dir %attr(0750,deeix-chat,deeix-chat) /var/lib/%{name}
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/NOTICE
