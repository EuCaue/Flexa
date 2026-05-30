project(
    'flexa',
    version: '1.0.0',
    meson_version: '>= 1.0.0',
    default_options: [
        'warning_level=2',
        'werror=false',
    ],
)

i18n = import('i18n')
gnome = import('gnome')

dependency('glib-2.0')
dependency('gobject-2.0')
dependency('gobject-introspection-1.0')
dependency('gtk4', version: '>= 4.10.0')
dependency('libadwaita-1', version: '>= 1.5.0')

find_program('glib-compile-schemas', required: true)
find_program('gtk-update-icon-cache', required: false)
find_program('update-desktop-database', required: false)

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
    glib_compile_schemas: true,
    gtk_update_icon_cache: true,
    update_desktop_database: true,
)
