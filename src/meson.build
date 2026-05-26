pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'flexa'
gnome = import('gnome')

gnome.compile_resources(
    'flexa',
    'flexa.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
    input: 'flexa.in',
    output: 'flexa',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x',
)

flexa_sources = [
    '__init__.py',
    'main.py',
    'window.py',
    'preferences.py',
    'cursor_converter.py',
]

install_data(flexa_sources, install_dir: moduledir)
