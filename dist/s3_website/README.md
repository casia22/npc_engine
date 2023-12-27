# 使用事项
我们项目打包发布后会上传到S3上，但是需要有一网页让大家都能看到并下载里面的内容.

这个index.html就是做这个事情的
参照的项目是[这里](https://github.com/rufuspollock/s3-bucket-listing/issues/46)

## S3 bucket
我们的S3 bucket是nuwa-release 在us-west-2

项目我手动使用gpt配置了访问策略和CORS策略以及静态网站托管


上传cmd：
```
 aws s3 cp ./index.html s3://nuwa-release/index.html
```
但是一般不用动 这里只是留一个存档

