# 自动打包当前文件到release/windows_ver

## 加密项目代码到code
pyarmor g -O code/ -r -i ../../npc_engine

## 删除之前的code
rm -r ./code/*
rm -r ./release/windows_ver/code/*

## copy数据文件到code
rsync -av --exclude-from='release_ignore.conf' ../../npc_engine code/

## code 移动到release
cp -r code/npc_engine release/windows_ver/code



