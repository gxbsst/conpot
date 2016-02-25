lock '3.4.0'
set :application, 'mj_scada'
set :repo_url, 'https://github.com/gxbsst/conpot.git'
set :deploy_to, "/root/#{fetch(:application)}"
set :pty, true
set :scm, :git
set :git_strategy, Capistrano::Git::SubmoduleStrategy


set :use_sudo, false


set :branch, ENV["BRANCH"] || 'master'

namespace :deploy do

  desc "Makes sure local git is in sync with remote."
  task :restart do
    on roles(:app), in: :sequence, limit: 3, wait: 3 do
      sudo "/etc/init.d/#{fetch(:application)} restart"
    end
  end

  desc "Makes sure local git is in sync with remote."
  task :stop do
    on roles(:app), in: :sequence, limit: 3, wait: 3 do
      sudo "/etc/init.d/#{fetch(:application)} stop"
    end
  end

  after :finishing, :clear_cache do
   on roles(:app), in: :sequence, limit: 3, wait: 3 do
      name = 'openerp-server'
      #execute "ps -ef | grep #{name} | grep -v grep | awk '{print $2}' | xargs kill || echo 'no process with name #{name} found'"
      puts "开始重启SCADA"
      puts ('*' * 100)
      execute "cd #{current_path};python setup.py install"
      #sudo "python setup.py install"
      # sudo "/root/#{fetch(:application)}/current/bin/conpot --template opcua"
      execute "/etc/init.d/supervisord restart"
      puts ('#' * 100)
      puts "成功启动scada"
    end
  end
end


