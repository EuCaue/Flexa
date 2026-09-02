%global appid io.github.eucaue.flexa
%global debug_package %{nil}
Name:           flexa
Version:        1.2.1
Release:        1%{?dist}
Summary:        Convert Windows cursor themes to Linux format
License:        GPL-3.0-or-later
URL:            https://github.com/eucaue/flexa
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  gettext
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  python3-devel
BuildRequires:  gtk4-devel >= 4.10.0
BuildRequires:  libadwaita-devel >= 1.5.0
BuildRequires:  gobject-introspection-devel
BuildRequires:  glib2-devel
BuildRequires:  python3-gobject
Requires:       python3
Requires:       python3-gobject
Requires:       gtk4 >= 4.10.0
Requires:       libadwaita >= 1.5.0
Requires:       python3-win2xcur

%description
Flexa is a simple GNOME application that converts Windows cursor themes
(.cur and .ani files) to the Linux XCursor format. It provides a clean,
intuitive interface following the GNOME Human Interface Guidelines.

%prep
%setup -q

%build
%meson
%meson_build

%install
%meson_install
%find_lang %{name}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{appid}.desktop

%files -f %{name}.lang
%license COPYING
%doc README.md
%{_bindir}/flexa
%{_datadir}/%{name}/
%{_datadir}/applications/%{appid}.desktop
%{_datadir}/metainfo/%{appid}.metainfo.xml
%{_datadir}/glib-2.0/schemas/%{appid}.gschema.xml
%{_datadir}/dbus-1/services/%{appid}.service
%{_datadir}/icons/hicolor/scalable/apps/%{appid}.svg
%{_datadir}/icons/hicolor/symbolic/apps/%{appid}-symbolic.svg

%changelog
* Tue May 26 2026 caue <caue@fedora> - 1.0.0-1
- Initial package
