import argparse
from pathlib import Path

from .importer import import_game
from .adapt import adapt_sources
from .build import build


def main():
    parser = argparse.ArgumentParser(description='NewSnapRecomp private build tools')
    commands = parser.add_subparsers(dest='command', required=True)
    imp = commands.add_parser('import', help='verify and import your own base/update')
    imp.add_argument('--base', type=Path, required=True)
    imp.add_argument('--update', type=Path, required=True)
    imp.add_argument('--keys', type=Path, required=True)
    imp.add_argument('--work', type=Path, default=Path('build/extracted'))
    imp.add_argument('--hactool', type=Path)
    imp.add_argument('--exefs-only', action='store_true')
    adapt = commands.add_parser('adapt', help='stage the pinned runtime/lifter with reviewed Snap changes')
    adapt.add_argument('--out', type=Path, default=Path('build/source'))
    compile_cmd = commands.add_parser('build', help='build the experimental private executable')
    compile_cmd.add_argument('--sdk-root', type=Path, required=True, help='unpacked selected-upstream Windows setup folder')
    compile_cmd.add_argument('--shader-tools', type=Path, help='folder with glslc.exe and spirv-val.exe')
    compile_cmd.add_argument('--jobs', type=int, default=0)
    compile_cmd.add_argument('--cpu', choices=('v2', 'v3'), default='v3')
    compile_cmd.add_argument('--no-generate', action='store_true', help='reuse previously generated C for this exact dump')
    args = parser.parse_args()
    try:
        if args.command == 'import':
            import_game(args.base, args.update, args.keys, args.work,
                        hactool=args.hactool, exefs_only=args.exefs_only)
        elif args.command == 'adapt':
            print(adapt_sources(args.out, patch_output=Path('patches/001-snap-bringup.patch')))
        elif args.command == 'build':
            build(args.sdk_root, args.shader_tools, args.jobs, not args.no_generate, args.cpu)
    except (OSError, ValueError) as error:
        parser.exit(1, f'NewSnapRecomp: {error}\n')


if __name__ == '__main__':
    main()
