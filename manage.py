"""Utilitário de linha de comando do Django para tarefas administrativas."""
import os
import sys


def main():
    """Executa tarefas administrativas do sistema."""
    # 1. Aponta onde estão as configurações globais do projeto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    try:
        # 2. Tenta importar o executor de comandos oficial do Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Você tem certeza de que ele está "
            "instalado e disponível na variável de ambiente PYTHONPATH? Você "
            "esqueceu de ativar o seu ambiente virtual (venv)?"
        ) from exc

    # 3. Pega os argumentos digitados no terminal (sys.argv) e executa o comando
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()