# encoding: utf-8
import argparse
import io
import os
import sys, zipfile
from pathlib import Path
from nuwa.src.config.config import CODE_ROOT_PATH, NPC_MEMORY_CONFIG
from nuwa.src.utils.embedding import LocalEmbedding
from nuwa import __version__

def run_engine(project_dir:Path=Path(os.getcwd()), engine_port=None, game_port=None, logo=True):
    """
    运行引擎
    :param project_dir: 用户指定的配置目录
    """
    # 检查project_dir是否存在要求的文件 PROJECT_DIR/config/llm_config.json
    if project_dir is None:
        print("Project dir not specified, use current dir as project dir")
        project_dir = Path(os.getcwd())
    if not os.path.exists(project_dir):
        print("Project dir not exists!")
        print("Please make sure your are using nuwa run on your project dir!")
        sys.exit(1)
    if not os.path.exists(os.path.join(project_dir, "config")):
        print(f"Config dir {project_dir}/config/ not exists!")
        print("Please make sure your are using nuwa run on your project dir!")
        sys.exit(1)
    if not os.path.exists(os.path.join(project_dir, "config", "llm_config.json")):
        print(f"Config file {project_dir}/config/llm_config.json not exists!")
        print("Please make sure your are using nuwa run on your project dir!")
        sys.exit(1)

    # 运行引擎的代码...
    from nuwa.src.engine import NPCEngine
    engine = NPCEngine(
        project_root_path=project_dir,
        engine_url="::1",
        engine_port=engine_port,
        game_url="::1",
        game_port=game_port,
        logo=logo)

def init_project(target_directory, project_name):
    zip_path = CODE_ROOT_PATH / "material" / 'templates' / 'template.zip'
    target_directory = Path(target_directory)
    final_project_path = target_directory / project_name

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for info in zip_ref.infolist():
            # 解决文件名编码问题
            filename = info.filename.encode('cp437').decode('utf-8')
            target_file_path = final_project_path / filename

            # 如果是目录，则创建目录
            if info.is_dir():
                os.makedirs(target_file_path, exist_ok=True)
            else:
                # 确保文件的目录存在
                os.makedirs(target_file_path.parent, exist_ok=True)
                # 写入文件
                with zip_ref.open(info.filename) as source, open(target_file_path, "wb") as target:
                    target.write(source.read())
    print(f"project inited in: {final_project_path}")

# CLI 命令处理
def handle_init_command(args):
    target_directory = args.target_directory or os.getcwd()
    init_project(target_directory, args.project_name)


def build_mac(project_dir=os.getcwd(), model=None):
    pass

def download_model_weights(args):
    print("Downloading model weights...")
    embedding_model = LocalEmbedding(model_name=NPC_MEMORY_CONFIG["hf_model_id"], vector_width=NPC_MEMORY_CONFIG["hf_dim"])
    print("Model weights downloaded!")


def main():
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description='Nuwa: A simulation engine for NPC')
    # nuwa -v for version
    parser.add_argument('-v', '--version', action='version', version=f'{__version__}')

    subparsers = parser.add_subparsers(help='commands', dest='command')

    # run
    run_parser = subparsers.add_parser('run', help='Run nuwa engine')
    run_parser.add_argument('-r', '--project-dir', type=str, help='Path to the config dir', default=None)
    # 端口
    run_parser.add_argument('-e', '--engine-port', type=int, help='Port of the engine', default=8199)
    run_parser.add_argument('-g', '--game-port', type=int, help='Port of the game', default=8084)
    # 是否显示logo
    run_parser.add_argument('-l', '--logo', type=bool, help='Whether to show logo', default=True)

    # init
    init_parser = subparsers.add_parser('init', help='Init a new project')
    init_parser.add_argument('-t', '--target-directory', type=str, help='Path to the target dir', default=None)
    init_parser.add_argument('-n', '--project-name', type=str, help='Name of the project', default="example_project")

    # download
    download_parser = subparsers.add_parser('download', help='Download nuwa model')

    # build
    build_parser = subparsers.add_parser('build', help='Build nuwa engine')
    build_parser.add_argument('-r', '--project-dir', type=str, help='Path to the config dir', default=None)
    # TODO:完善build的内容 build mac 或 build win 自动在当前build文件夹发布

    args = parser.parse_args()

    if args.command == 'run':
        run_engine(project_dir=Path(args.project_dir), engine_port=args.engine_port,
                   game_port=args.game_port, logo=args.logo)
    elif args.command == 'init':
        """
        nuwa init 默认在本地初始化exmaple project
        nuwa init -t 会在目标文件夹初始化example project
        nuwa init -n 会在当前目录初始化指定名字的project
        nuwa init -t  -n 会在目标文件夹初始化指定名字的project
        """
        if args.target_directory is None:
            args.target_directory = Path(os.getcwd())
        handle_init_command(args)
    elif args.command == 'download':
        download_model_weights(args)

if __name__ == "__main__":
    main()
