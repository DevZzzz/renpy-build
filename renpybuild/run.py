import jinja2
import shlex
import subprocess
import sys
import sysconfig


def build_environment(c):
    """
    Sets up the build environment inside the context.
    """

    c.var("make", "nice make -j 12")

    c.var("sysroot", c.tmp / f"sysroot.{c.platform}-{c.arch}")
    c.var("build_platform", sysconfig.get_config_var("HOST_GNU_TYPE"))

    c.env("CPPFLAGS", "-I{{ install }}/include")
    c.env("CFLAGS", "-I{{ install }}/include")

    if (c.platform == "linux") and (c.arch == "x86_64"):
        c.var("host_platform", "x86_64-pc-linux-gnu")
    elif (c.platform == "linux") and (c.arch == "i686"):
        c.var("host_platform", "i686-pc-linux-gnu")
    elif (c.platform == "windows") and (c.arch == "x86_64"):
        c.var("host_platform", "x86_64-w64-mingw32")

    c.env("LDFLAGS", "-L{{install}}/lib")

    if (c.kind == "host") or (c.kind == "cross"):

        c.env("CC", "ccache gcc -fPIC")
        c.env("CXX", "ccache g++ -fPIC")
        c.env("CPP", "ccache gcc -E")
        c.env("LD", "ccache ld")
        c.env("AR", "ccache ar")
        c.env("RANLIB", "ccache ranlib")

        c.env("LDFLAGS", "{{ LDFLAGS }} -L{{install}}/lib64")

    elif (c.platform == "linux") and (c.arch == "x86_64"):

        c.var("crossbin", "{{ cross }}/bin/{{ host_platform}}-")

        c.env("CC", "ccache {{ crossbin }}gcc -m64 -O3 -fPIC -pthread --sysroot {{ sysroot }}")
        c.env("CXX", "ccache {{ crossbin }}g++ -m64 -O3 -fPIC -pthread --sysroot {{ sysroot }}")
        c.env("CPP", "ccache {{ crossbin }}gcc -m64 -E --sysroot {{ sysroot }}")
        c.env("LD", "ccache {{ crossbin}}ld")
        c.env("AR", "ccache {{ crossbin }}gcc-ar")
        c.env("RANLIB", "ccache {{ crossbin }}gcc-ranlib")

        c.env("LDFLAGS", "{{ LDFLAGS }} -Wl,-rpath-link -Wl,{{ sysroot }}/lib/x86_64-linux-gnu")
        c.env("LDFLAGS", "{{ LDFLAGS }} -Wl,-rpath-link -Wl,{{ sysroot }}/usr/lib/x86_64-linux-gnu")
        c.env("LDFLAGS", "{{ LDFLAGS }} -L{{install}}/lib64")

    elif (c.platform == "linux") and (c.arch == "i686"):

        c.var("crossbin", "{{ cross }}/bin/{{ host_platform }}-")

        c.env("CC", "ccache {{ crossbin }}gcc -m32 -fPIC -O3 -pthread --sysroot {{ sysroot }}")
        c.env("CXX", "ccache {{ crossbin }}g++ -m32 -fPIC -O3 -pthread --sysroot {{ sysroot }}")
        c.env("CPP", "ccache {{ crossbin }}gcc -m32 -E --sysroot {{ sysroot }}")
        c.env("LD", "ccache {{ crossbin}}ld")
        c.env("AR", "ccache {{ crossbin }}gcc-ar")
        c.env("RANLIB", "ccache {{ crossbin }}gcc-ranlib")

        # Lib64 is needed since GLEW winds up in the wrong place.
        c.env("LDFLAGS", "{{ LDFLAGS }} -Wl,-rpath-link -Wl,{{ sysroot }}/lib/i386-linux-gnu")
        c.env("LDFLAGS", "{{ LDFLAGS }} -Wl,-rpath-link -Wl,{{ sysroot }}/usr/lib/i386-linux-gnu")
        c.env("LDFLAGS", "{{ LDFLAGS }} -L{{ sysroot }}/usr/lib/i386-linux-gnu -L{{install}}/lib32 -L{{install}}/lib64")

    elif (c.platform == "windows") and (c.arch == "x86_64"):

        c.var("crossbin", "/usr/bin/{{ host_platform }}-")

        c.env("CC", "ccache {{ crossbin }}gcc -fPIC -O3")
        c.env("CXX", "ccache {{ crossbin }}g++-fPIC -O3")
        c.env("CPP", "ccache {{ crossbin }}gcc -E")
        c.env("LD", "ccache {{ crossbin}}ld")
        c.env("AR", "ccache {{ crossbin }}gcc-ar")
        c.env("RANLIB", "ccache {{ crossbin }}gcc-ranlib")
        c.env("WINDRES", "ccache {{ crossbin }}windres")

    # c.env("LD", "{{ CC }}")
    # c.env("LDXX", "{{ CXX }}")

    c.env("PKG_CONFIG_PATH", "{{ install }}/lib/pkgconfig")

    c.env("CFLAGS", "{{ CFLAGS }} -DRENPY_BUILD")

    if c.kind != "host":
        c.var("cross_config", "--host={{ host_platform }} --build={{ build_platform }}")


def run(command, context, verbose=False):
    args = shlex.split(command)

    if verbose:
        print(" ".join(shlex.quote(i) for i in args))

    p = subprocess.run(args, cwd=context.cwd, env=context.environ)

    if p.returncode != 0:
        print(f"{context.task_name}: process failed with {p.returncode}.")
        print("args:", args)
        sys.exit(1)
