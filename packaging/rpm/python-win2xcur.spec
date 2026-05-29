%global pypi_name win2xcur
Name:           python3-%{pypi_name}
Version:        0.2.1
Release:        1%{?dist}
Summary:        Convert Windows .cur and .ani cursors to Xcursor format
License:        GPL-3.0-or-later
URL:            https://github.com/quantum5/win2xcur
Source0:        %{url}/archive/v%{version}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  python3-build
BuildRequires:  python-installer
BuildRequires:  python3-numpy
BuildRequires:  python3-wand
BuildRequires:  ImageMagick-libs
Requires:       python3
Requires:       python3-numpy
Requires:       python3-wand
Requires:       ImageMagick-libs

%description
win2xcur is a tool that converts cursors from Windows format (*.cur, *.ani)
to Xcursor format. This allows Windows cursor themes to be used on Linux.
It also provides x2wincur for the reverse conversion, and win2xcurtheme
for converting packaged Windows cursor themes.

%prep
%autosetup -n %{pypi_name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files %{pypi_name}

%check
%pyproject_check_import

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/win2xcur
%{_bindir}/x2wincur
%{_bindir}/win2xcurtheme
%{_bindir}/x2wincurtheme
%{_bindir}/inspectcur

%changelog
* Thu May 28 2026 caue <caue@fedora> - 0.2.1-1
- Initial package for Fedora
