import argparse
import os
import sys


def run_engine(project_dir=os.getcwd(), engine_port=None, game_port=None, model=None, logo=True):
    """
    运行引擎
    :param project_dir: 用户指定的配置目录
    """
    # 检查project_dir是否存在要求的文件 config/, llm_config.json
    # TODO: 目前引擎只能够在当前目录下存在config/llm_config.json的情况下运行
    if project_dir is None:
        print("Project dir not specified, use current dir as project dir")
        project_dir = os.getcwd()
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
        engine_url="::1",
        engine_port=engine_port,
        game_url="::1",
        game_port=game_port,
        model=model,
        logo=logo)


def build_mac(project_dir=os.getcwd(), model=None):
    pass



def main():
    from nuwa.src.config import config
    parser = argparse.ArgumentParser(description='Nuwa: A simulation engine for NPC')
    subparsers = parser.add_subparsers(help='commands', dest='command')

    # run
    run_parser = subparsers.add_parser('run', help='Run nuwa engine')
    run_parser.add_argument('-r', '--project-dir', type=str, help='Path to the config dir', default=None)
    # 端口
    run_parser.add_argument('-e', '--engine-port', type=int, help='Port of the engine', default=8199)
    run_parser.add_argument('-g', '--game-port', type=int, help='Port of the game', default=8084)
    # 模型，默认为OPENAI_MODEL
    run_parser.add_argument('-m', '--model', type=str, help='Model of the engine', default=config.OPENAI_MODEL)
    # 是否显示logo
    run_parser.add_argument('-l', '--logo', type=bool, help='Whether to show logo', default=True)

    # build
    build_parser = subparsers.add_parser('build', help='Build nuwa engine')
    build_parser.add_argument('-r', '--project-dir', type=str, help='Path to the config dir', default=None)
    # TODO:完善build的内容 build mac 或 build win 自动在当前build文件夹发布

    args = parser.parse_args()

    if args.command == 'run':
        run_engine(project_dir=args.project_dir, engine_port=args.engine_port, game_port=args.game_port, model=args.model, logo=args.logo)

if __name__ == "__main__":
    main()
