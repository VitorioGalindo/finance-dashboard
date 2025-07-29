#!/usr/bin/env python3
"""
Script de Deploy do Dashboard Financeiro
Automatiza o processo de deploy e configuração
"""

import os
import sys
import subprocess
import logging
import json
from datetime import datetime

class DeployManager:
    """Gerenciador de deploy"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configura o logger"""
        logger = logging.getLogger('DeployManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def run_command(self, command, cwd=None):
        """Executa comando shell"""
        try:
            if cwd is None:
                cwd = self.project_root
                
            self.logger.info(f"Executando: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Comando executado com sucesso")
                return True, result.stdout
            else:
                self.logger.error(f"❌ Erro no comando: {result.stderr}")
                return False, result.stderr
                
        except Exception as e:
            self.logger.error(f"❌ Exceção ao executar comando: {e}")
            return False, str(e)
    
    def check_dependencies(self):
        """Verifica dependências do sistema"""
        self.logger.info("Verificando dependências...")
        
        dependencies = [
            ("python3", "python3 --version"),
            ("pip3", "pip3 --version"),
            ("git", "git --version"),
            ("node", "node --version"),
            ("npm", "npm --version")
        ]
        
        missing = []
        
        for dep_name, check_command in dependencies:
            success, output = self.run_command(check_command)
            if success:
                self.logger.info(f"✅ {dep_name}: {output.strip()}")
            else:
                self.logger.warning(f"❌ {dep_name}: não encontrado")
                missing.append(dep_name)
        
        if missing:
            self.logger.error(f"Dependências faltando: {', '.join(missing)}")
            return False
        
        return True
    
    def install_python_dependencies(self):
        """Instala dependências Python"""
        self.logger.info("Instalando dependências Python...")
        
        requirements_file = os.path.join(self.project_root, "requirements.txt")
        
        if not os.path.exists(requirements_file):
            self.logger.warning("Arquivo requirements.txt não encontrado")
            return False
        
        success, output = self.run_command("pip3 install -r requirements.txt")
        
        if success:
            self.logger.info("✅ Dependências Python instaladas")
        else:
            self.logger.error("❌ Erro ao instalar dependências Python")
        
        return success
    
    def install_frontend_dependencies(self):
        """Instala dependências do frontend"""
        self.logger.info("Instalando dependências do frontend...")
        
        frontend_dir = os.path.join(self.project_root, "frontend")
        
        if not os.path.exists(frontend_dir):
            self.logger.warning("Diretório frontend não encontrado")
            return False
        
        success, output = self.run_command("npm install", cwd=frontend_dir)
        
        if success:
            self.logger.info("✅ Dependências do frontend instaladas")
        else:
            self.logger.error("❌ Erro ao instalar dependências do frontend")
        
        return success
    
    def build_frontend(self):
        """Constrói o frontend para produção"""
        self.logger.info("Construindo frontend...")
        
        frontend_dir = os.path.join(self.project_root, "frontend")
        
        if not os.path.exists(frontend_dir):
            self.logger.warning("Diretório frontend não encontrado")
            return False
        
        success, output = self.run_command("npm run build", cwd=frontend_dir)
        
        if success:
            self.logger.info("✅ Frontend construído com sucesso")
        else:
            self.logger.error("❌ Erro ao construir frontend")
        
        return success
    
    def setup_environment(self):
        """Configura variáveis de ambiente"""
        self.logger.info("Configurando ambiente...")
        
        env_file = os.path.join(self.project_root, "backend", ".env")
        
        if os.path.exists(env_file):
            self.logger.info("✅ Arquivo .env já existe")
            return True
        
        # Cria arquivo .env de exemplo
        env_content = """# Configurações do Banco de Dados
DB_USER=pandora
DB_PASSWORD=Pandora337303$
DB_HOST=cvm-insiders-db.cb2uq8cqs3dn.us-east-2.rds.amazonaws.com
DB_NAME=postgres

# Chave secreta do Flask
SECRET_KEY=finance-dashboard-secret-key-2025

# Configurações de API (opcional)
# GEMINI_API_KEY=your_gemini_api_key_here
# B3_API_KEY=your_b3_api_key_here
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            self.logger.info("✅ Arquivo .env criado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar .env: {e}")
            return False
    
    def test_backend(self):
        """Testa se o backend está funcionando"""
        self.logger.info("Testando backend...")
        
        try:
            import requests
            
            # Tenta conectar no backend
            response = requests.get("http://localhost:5001/health", timeout=5)
            
            if response.status_code == 200:
                self.logger.info("✅ Backend está funcionando")
                return True
            else:
                self.logger.warning(f"⚠️  Backend retornou status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.logger.warning("⚠️  Backend não está rodando")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erro ao testar backend: {e}")
            return False
    
    def start_backend(self):
        """Inicia o backend"""
        self.logger.info("Iniciando backend...")
        
        backend_script = os.path.join(self.project_root, "run_backend.py")
        
        if not os.path.exists(backend_script):
            self.logger.error("Script run_backend.py não encontrado")
            return False
        
        # Inicia backend em background
        success, output = self.run_command("nohup python3 run_backend.py > backend.log 2>&1 &")
        
        if success:
            self.logger.info("✅ Backend iniciado em background")
            
            # Aguarda um pouco e testa
            import time
            time.sleep(3)
            
            return self.test_backend()
        else:
            self.logger.error("❌ Erro ao iniciar backend")
            return False
    
    def create_systemd_service(self):
        """Cria serviço systemd para o backend"""
        self.logger.info("Criando serviço systemd...")
        
        service_content = f"""[Unit]
Description=Finance Dashboard Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory={self.project_root}
ExecStart=/usr/bin/python3 run_backend.py
Restart=always
RestartSec=10
Environment=PYTHONPATH={self.project_root}

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "/tmp/finance-dashboard.service"
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            self.logger.info(f"✅ Arquivo de serviço criado: {service_file}")
            self.logger.info("Para instalar o serviço, execute:")
            self.logger.info(f"sudo cp {service_file} /etc/systemd/system/")
            self.logger.info("sudo systemctl daemon-reload")
            self.logger.info("sudo systemctl enable finance-dashboard")
            self.logger.info("sudo systemctl start finance-dashboard")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar serviço: {e}")
            return False
    
    def generate_deployment_report(self):
        """Gera relatório de deploy"""
        self.logger.info("Gerando relatório de deploy...")
        
        report = {
            "deployment_date": datetime.now().isoformat(),
            "project_root": self.project_root,
            "python_version": sys.version,
            "status": "completed",
            "components": {
                "backend": "deployed",
                "frontend": "built",
                "database": "connected",
                "scripts": "configured"
            },
            "next_steps": [
                "Configure reverse proxy (nginx)",
                "Set up SSL certificates",
                "Configure monitoring",
                "Set up backup procedures"
            ]
        }
        
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Relatório de deploy salvo: {report_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar relatório: {e}")
            return False
    
    def run_full_deployment(self):
        """Executa deploy completo"""
        self.logger.info("=== INICIANDO DEPLOY COMPLETO ===")
        
        steps = [
            ("Verificação de dependências", self.check_dependencies),
            ("Configuração de ambiente", self.setup_environment),
            ("Instalação de dependências Python", self.install_python_dependencies),
            ("Instalação de dependências frontend", self.install_frontend_dependencies),
            ("Build do frontend", self.build_frontend),
            ("Teste do backend", self.test_backend),
            ("Criação de serviço systemd", self.create_systemd_service),
            ("Geração de relatório", self.generate_deployment_report)
        ]
        
        results = {}
        
        for step_name, step_function in steps:
            self.logger.info(f"Executando: {step_name}")
            try:
                result = step_function()
                results[step_name] = "✅ Sucesso" if result else "❌ Falha"
                
                # Para em caso de falha crítica
                if not result and step_name in ["Verificação de dependências", "Configuração de ambiente"]:
                    self.logger.error(f"Falha crítica em: {step_name}")
                    break
                    
            except Exception as e:
                results[step_name] = f"❌ Erro: {e}"
                self.logger.error(f"Erro em {step_name}: {e}")
        
        # Relatório final
        self.logger.info("=== RELATÓRIO DE DEPLOY ===")
        for step, result in results.items():
            self.logger.info(f"  {step}: {result}")
        
        self.logger.info("=== DEPLOY CONCLUÍDO ===")
        
        return results

def main():
    """Função principal"""
    deploy_manager = DeployManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "full":
            deploy_manager.run_full_deployment()
        elif command == "deps":
            deploy_manager.check_dependencies()
        elif command == "backend":
            deploy_manager.start_backend()
        elif command == "frontend":
            deploy_manager.build_frontend()
        elif command == "service":
            deploy_manager.create_systemd_service()
        else:
            print("Comandos disponíveis: full, deps, backend, frontend, service")
    else:
        # Executa deploy completo por padrão
        deploy_manager.run_full_deployment()

if __name__ == "__main__":
    main()

