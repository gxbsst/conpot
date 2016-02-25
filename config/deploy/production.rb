set :deploy_to, "/home/mes/#{fetch(:application)}"
server 'sfy_local',
   user: 'mes',
   roles: %w{web app},
   ssh_options: {
     user: 'mes', # overrides user setting above
     forward_agent: false,
     #auth_methods: %w(publickey),
     password: 'mes'
  }


namespace :odoo do
  desc "复制odoo的启动脚本"
  task :setup do
  on roles(:app), in: :sequence, limit: 3, wait: 3 do
    config_file = 'odoo_config_staging.erb'
    template config_file, "/tmp/odoo_config", 0750
    sudo "mv /tmp/odoo_config /etc/#{fetch(:application)}.conf"

    template "odoo_server.erb", "/tmp/odoo_server", 0750
    sudo "mv /tmp/odoo_server /etc/init.d/#{fetch(:application)}"
    # restart
   end
  end
  #after "deploy:starting", "odoo:setup"
end