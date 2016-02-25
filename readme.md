### 部署

#### 安装ruby

windows

```
参考
http://rubyinstaller.org/
```

linux

```
https://rvm.io/
```

#### 安装bundler

```
gem install bundler
```

#### 安装Gem包

```
在项目根目录下执行
bundle 
```

#### 配置ssh的config

```
vim .ssh/config
增加
Host dev
HostName 192.168.0.200
User root
Port 22
```
#### 部署到测试服务器

```
BRANCH=develop cap staging deploy
＃过程会提示输入服务器的odoo用户密码， 请输入。
```

#### 更新模块

如果更新代码涉及模块变更，请登陆http://192.168.0.200:9007手动更新模块。
