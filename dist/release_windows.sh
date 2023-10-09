# 自动打包当前文件到release/windows_ver

## 删除之前的code
rm -r ./code/*

## 加密项目代码到code
pyarmor g --platform windows.x86_64 --platform linux.x86_64 --platform darwin.x86_64  -O code/npc_engine/  -r -i ../../npc_engine/src
pyarmor g --platform windows.x86_64 --platform linux.x86_64 --platform darwin.x86_64  -O code/npc_engine/  -r  ../../npc_engine/src

## 删除之前的code
rm -r ./release/windows_ver/code/*

## copy数据文件到code
rsync -av --ignore-existing  --exclude-from='release_ignore.conf' ../../npc_engine code/
## mv加密包到解释器
cp -r code/npc_engine/pyarmor_runtime_00*  release/windows_ver/python_lib/python-3.9.6-embed-amd64/lib/site-packages/

## code 移动到release
cp -r code/npc_engine release/windows_ver/code



