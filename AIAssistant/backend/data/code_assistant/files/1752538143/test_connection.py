from sqlalchemy import create_engine, text

# ======================================================================
# PASSO 1: CONFIGURAÇÃO - A PARTE MAIS IMPORTANTE
# ======================================================================

# Vá para o seu dashboard do Supabase > Settings > Database.
# Role até "Connection String" e copie a URI.
# Cole-a aqui e substitua '[YOUR-PASSWORD]' pela sua senha.
# NOTE A MUDANÇA: adicionamos '?pgbouncer=true' ao final.
# Isso instrui o Supabase a nos dar uma conexão direta, contornando o pool.
# ESTA É A MUDANÇA MAIS CRÍTICA E PROVÁVEL SOLUÇÃO.

DB_CONNECTION_STRING = "postgresql://postgres:EFunuZ0esp8VeuE9@db.jcvwnitmrjdjeocxgmiy.supabase.co:5432/postgres"

# ======================================================================

print("Tentando se conectar ao banco de dados Supabase...")
print(f"Usando a string de conexão: {DB_CONNECTION_STRING.replace('EFunuZ0esp8VeuE9', '*')}")

try:
    # Crie o motor de conexão
    engine = create_engine(DB_CONNECTION_STRING)

    # Tente estabelecer uma conexão
    with engine.connect() as connection:
        print("✅ Conexão estabelecida com sucesso!")

        # Tente executar uma consulta simples para verificar a permissão
        # Inserindo dados com um caractere especial para testar a codificação
        query = text("INSERT INTO transacoes (descricao, categoria, valor) VALUES ('Teste com acentuação', 'TESTE', 123.45)")
        
        connection.execute(query)
        connection.commit() # Necessário para salvar a inserção

        print("✅ Dados de teste inseridos com sucesso na tabela 'transacoes'!")
        print("\n🏆 Diagnóstico Concluído: A conexão e a escrita no banco de dados estão funcionando.")

except Exception as e:
    print("\n❌ FALHA NA CONEXÃO OU NA ESCRITA.")
    print("Erro detalhado:", e)

# ======================================================================